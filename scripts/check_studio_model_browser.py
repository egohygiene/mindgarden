"""Qualify Studio Models in Chromium with offline fixture providers."""

from argparse import ArgumentParser
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory
from threading import Event, Thread
from time import time
from urllib.parse import parse_qs, urlencode, urlsplit
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PROVIDER_PROMPT_RESULT = "<strong>Fictional comparison result.</strong>"
DOWNLOAD_ID = "fake-local:1b"
DOWNLOAD_LABEL = "Fictional local model"
CATALOG_DENIED = "MODEL_CATALOG_NO_ENTITLEMENT"
CATALOG_EMPTY = "MODEL_CATALOG_EMPTY"
CATALOG_RESPONSE = "MODEL_CATALOG_RESPONSE"
DIAGNOSTIC_CANARY = "fictional-provider-detail-not-for-diagnostics"
CONSOLE_CANARY = "https://example.invalid/private?signature=fictional-console-secret"


@dataclass
class FixtureConsent:
    directory: Path
    opened: list[str] = field(default_factory=list)
    exchanges: int = 0
    revocations: int = 0
    exchange_allowed: Event = field(default_factory=Event)

    def require_oidc(self):
        pass

    def open_browser(self, url):
        assert urlsplit(url).netloc == "auth.openai.com"
        self.opened.append(url)
        return True

    def callback_url(self, **parameters):
        fields = parse_qs(urlsplit(self.opened[-1]).query)
        callback = fields["redirect_uri"][0]
        assert urlsplit(callback).hostname == "127.0.0.1"
        return callback + "?" + urlencode({"state": fields["state"][0], **parameters})

    def exchange(self, attempt, code, client_id):
        from mindgarden.adapters.chatgpt_credentials import ChatGPTCredentials

        assert attempt.authorization_url == self.opened[-1]
        assert code == "fixture-code" and client_id == "oaiapp_browser_fixture"
        assert self.exchange_allowed.wait(12), "The browser test did not release token verification"
        self.exchanges += 1
        return ChatGPTCredentials(
            issuer="https://auth.openai.com", subject="fictional-owner", client_id=client_id,
            scopes=("chatgpt.tokens.use.direct", "resource.invoke"),
            access_token="fictional-browser-access", refresh_token="fictional-browser-refresh",
            id_token="fictional-browser-id", expires_at=int(time()) + 3600,
        )

    def active(self):
        from mindgarden.adapters.chatgpt_credentials import ChatGPTStore

        return ChatGPTStore(self.directory).read() is not None

    def revoke(self, credentials):
        assert credentials.client_id == "oaiapp_browser_fixture"
        self.revocations += 1


@dataclass
class FixtureProvider:
    id: str
    name: str
    disclosure: str
    approved_prompt: str
    calls: list[tuple] = field(default_factory=list)
    installed: bool = False
    consent: FixtureConsent | None = None
    expired: bool = False
    catalog_diagnostic: str | None = None

    def signed_in(self):
        return self.consent is not None and not self.expired and self.consent.active()

    def check(self):
        self.calls.append(("check",))
        state = {"status": "ready", "detail": "Offline fixture connection.", "models": [], "can_run": False}
        if self.id == "codex":
            state["limits"] = {
                "windows": [{"label": "Primary quota", "used_percent": 37, "window_minutes": 300, "resets_at": 1_800_000_000}],
                "credits": {"balance": "12.50", "has_credits": True, "unlimited": False},
            }
        if self.id == "gemini":
            state.update(models=[{"id": "small", "label": "Small"}, {"id": "large", "label": "Large"}], can_run=True)
        if self.id == "chatgpt":
            if not self.signed_in():
                state.update(status="unconfigured", detail="The fictional profile needs consent.")
            elif self.catalog_diagnostic == CATALOG_DENIED:
                state.update(status="unavailable", detail=DIAGNOSTIC_CANARY, diagnostic_code=CATALOG_DENIED)
            elif self.catalog_diagnostic == CATALOG_EMPTY:
                state.update(detail="The fictional plan has no visible models.", diagnostic_code=CATALOG_EMPTY)
            elif self.catalog_diagnostic == CATALOG_RESPONSE:
                state.update(status="unavailable", detail="The fictional model catalog is invalid.",
                             diagnostic_code=CATALOG_RESPONSE)
            else:
                state.update(models=[{"id": "small", "label": "Plan text model"}], can_run=True)
        if self.id == "ollama":
            model = {"id": DOWNLOAD_ID, "label": DOWNLOAD_LABEL}
            if self.installed:
                state.update(models=[model], can_run=True)
            else:
                state["downloadable"] = [model]
        return state

    def run(self, model, prompt):
        if self.id == "chatgpt" and not self.signed_in():
            from mindgarden.domain.validation import ContractError

            raise ContractError("MODEL_REAUTH: the fictional plan consent expired")
        assert prompt == self.approved_prompt
        self.calls.append(("run", model))
        return PROVIDER_PROMPT_RESULT

    def install(self, model):
        assert self.id == "ollama" and model == DOWNLOAD_ID
        self.calls.append(("install", model))
        self.installed = True


@contextmanager
def serve(config, scope, mode: str, providers: tuple[FixtureProvider, ...] = (), consent=None) -> Iterator[str]:
    from mindgarden.interfaces.local_web import make_server
    from mindgarden.interfaces.studio_chatgpt_login import StudioChatGPTLogin

    def build_login(directory):
        return StudioChatGPTLogin(directory, oauth=consent, browse=consent.open_browser)

    with (
        patch("mindgarden.application.model_lab.configured_providers", return_value=providers),
        patch("mindgarden.interfaces.studio_chatgpt_login.StudioChatGPTLogin", side_effect=build_login),
    ):
        server = make_server(config, scope, demo=True, interface="studio", assistant=mode,
                             chatgpt_state_directory=consent.directory if consent else None)
    with server:
        worker = Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            yield server.url
        finally:
            server.shutdown()
            worker.join()


def check_callback(browser, url, width, axe, *, destination, heading, status=200, screenshot=None):
    from playwright.sync_api import expect

    page = browser.new_page(viewport={"width": width, "height": 700})
    requests = []
    page.on("request", lambda request: requests.append(request.url))
    page.route("**/*", lambda route: route.continue_() if route.request.url == url else route.abort())
    try:
        response = page.goto(url)
        assert response.status == status
        assert response.header_value("cache-control") == "no-store"
        assert response.header_value("referrer-policy") == "no-referrer"
        expected_return = "Return to Models" if destination == "studio" else "Return to your terminal"
        expect(page.get_by_role("heading", name=heading)).to_be_visible()
        expect(page.get_by_role("heading", name=expected_return)).to_be_visible()
        assert all(value not in page.content() for values in parse_qs(urlsplit(url).query).values() for value in values)
        assert page.evaluate('getComputedStyle(document.body).display === "grid"')
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        if axe:
            page.evaluate(axe)
            violations = page.evaluate("async () => (await axe.run()).violations")
            assert not violations, [item["id"] for item in violations]
        assert requests == [url]
        if screenshot is not None:
            page.screenshot(path=screenshot)
    finally:
        page.close()


def check_diagnostics(page, url, width, consent, scenario_prompt, diagnostics_reads, audit, artifacts):
    from playwright.sync_api import expect

    assert not diagnostics_reads, "Diagnostics requested while its view was closed"
    page.evaluate("(value) => console.warn(value, {privateExample: value})", CONSOLE_CANARY)
    entry = page.get_by_role("button", name="Diagnostics", exact=True)
    entry.focus()
    expect(entry).to_be_focused()
    with page.expect_response("**/api/diagnostics") as received:
        page.keyboard.press("Enter")
    expect(page.get_by_role("heading", name="Diagnostics", level=1)).to_be_visible()
    expect(page.get_by_role("heading", name="Operation durations")).to_be_visible()
    expect(page.get_by_role("heading", name="Event timeline")).to_be_visible()
    assert diagnostics_reads and set(diagnostics_reads) == {"GET"}

    response = received.value
    assert response.ok and response.header_value("cache-control") == "no-store"
    events = response.json()["events"]
    assert [event["id"] for event in events] == sorted({event["id"] for event in events})
    catalog_events = [
        event for event in events
        if event["source"] == "server" and event["provider"] == "chatgpt" and event["operation"] == "check"
    ]
    codes = [event["code"] for event in catalog_events]
    malformed = codes.index(CATALOG_RESPONSE)
    denied = codes.index(CATALOG_DENIED)
    empty = codes.index(CATALOG_EMPTY)
    assert malformed < denied < empty < codes.index("MODEL_CHECK_OK", empty), codes
    sign_in = [event["code"] for event in events if event["operation"] == "sign-in"]
    assert sign_in.index("CHATGPT_LOGIN_VERIFYING") < sign_in.index("CHATGPT_LOGIN_AUTHORIZED"), sign_in
    assert {event["operation"] for event in events if event["provider"] == "chatgpt"} >= {
        "sign-in", "cancel", "disconnect",
    }
    assert all(event["duration_ms"] >= 0 for event in events)

    page.context.grant_permissions(["clipboard-read", "clipboard-write"],
                                   origin=f"http://{urlsplit(url).netloc}")
    copy = page.get_by_role("button", name="Copy visible events")
    copy.click()
    expect(page.get_by_text("Visible diagnostics copied.", exact=True)).to_be_visible()
    copied_text = page.evaluate("navigator.clipboard.readText()")
    assert copied_text.startswith("Mindgarden Studio diagnostics\n")
    assert "| Browser | Studio | Browser console | Needs attention | BROWSER_CONSOLE_WARNING |" in copied_text

    timeline = page.get_by_role("region", name="Event timeline")
    timeline.get_by_role("combobox", name="Provider").select_option("chatgpt")
    timeline.get_by_role("combobox", name="Outcome").select_option("attention")
    expect(timeline.get_by_text(CATALOG_DENIED, exact=True)).to_be_visible()
    expect(timeline.get_by_text(CATALOG_EMPTY, exact=True)).to_be_visible()
    copy.click()
    expect(page.get_by_text("Visible diagnostics copied.", exact=True)).to_be_visible()
    filtered_copy = page.evaluate("navigator.clipboard.readText()")
    assert CATALOG_DENIED in filtered_copy and CATALOG_EMPTY in filtered_copy
    assert "BROWSER_CONSOLE_WARNING" not in filtered_copy and "| Gemini |" not in filtered_copy
    canaries = (
        DIAGNOSTIC_CANARY, CONSOLE_CANARY, "fictional-console-secret", "fixture-code",
        "fictional-browser-access", "fictional-browser-refresh", "fictional-browser-id",
        "fictional-optional-session", "oaiapp_browser_fixture", PROVIDER_PROMPT_RESULT,
        str(consent.directory), "Plan text model",
        scenario_prompt, scenario_prompt.splitlines()[0],
        parse_qs(urlsplit(consent.opened[-1]).query)["state"][0],
        parse_qs(urlsplit(url).fragment)["access"][0],
    )
    for output in (response.text(), page.get_by_role("main").inner_text(), copied_text, filtered_copy):
        assert not any(value in output for value in canaries), "A raw diagnostic value was exposed"
    with page.expect_response("**/api/diagnostics") as refreshed:
        page.get_by_role("button", name="Refresh events").click()
    assert refreshed.value.ok
    if artifacts:
        page.screenshot(path=artifacts / f"studio-diagnostics-{width}.png", full_page=True, animations="disabled")
    audit()


def check_models(browser, url, width, providers, axe, artifacts):
    from playwright.sync_api import expect

    page = browser.new_page(
        viewport={"width": width, "height": 950},
        reduced_motion="reduce" if width < 760 else "no-preference",
    )
    codex_provider, gemini_provider, ollama_provider, chatgpt_provider = providers
    consent = chatgpt_provider.consent
    errors = []
    posts = []
    diagnostics_reads = []
    missed_reads = 0
    drop_next_status = False
    authority = urlsplit(url).netloc

    def local_only(route):
        nonlocal missed_reads, drop_next_status
        request = route.request
        parsed = urlsplit(request.url)
        if parsed.netloc != authority:
            errors.append("Unexpected remote URL")
            route.abort()
            return
        if parsed.path == "/api/diagnostics":
            diagnostics_reads.append(request.method)
        if request.method == "POST":
            posts.append((parsed.path, request.post_data_json))
            if parsed.path == "/api/models/chatgpt/connect" and len(consent.opened) == 0:
                # Studio must recover even when the server starts the attempt
                # but the browser does not receive the opening status.
                assert route.fetch(max_redirects=0).ok
                route.abort()
                return
        if parsed.path == "/api/models/chatgpt/connection" and drop_next_status:
            drop_next_status = False
            missed_reads += 1
            route.abort()
            return
        route.continue_()

    def audit():
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        if axe:
            page.evaluate(axe)
            violations = page.evaluate("async () => (await axe.run()).violations")
            assert not violations, [
                (item["id"], [(node["target"], node.get("failureSummary")) for node in item["nodes"]])
                for item in violations
            ]

    page.on("pageerror", lambda error: errors.append(str(error)))
    page.route("http*://**/*", local_only)
    page.goto(url)
    page.get_by_role("button", name="Models", exact=True).click()
    expect(page.get_by_role("heading", name="Models", exact=True)).to_be_visible()
    codex = page.get_by_role("region", name="Codex", exact=True)
    gemini = page.get_by_role("region", name="Gemini", exact=True)
    ollama = page.get_by_role("region", name="Ollama", exact=True)
    chatgpt = page.get_by_role("region", name="ChatGPT plan", exact=True)
    expect(codex.get_by_text("Connection unchecked")).to_be_visible()
    expect(chatgpt.get_by_text("Connection unchecked")).to_be_visible()
    assert not posts and all(not provider.calls for provider in providers)
    assert not consent.directory.exists() and not consent.opened
    assert "access=" not in page.url

    codex.get_by_role("button", name="Check connection").click()
    expect(codex.get_by_text("Account checked", exact=True)).to_be_visible()
    expect(page.get_by_text("Codex: Account checked.", exact=True)).to_be_visible()
    codex.get_by_text("Reported usage and credits", exact=True).click()
    expect(codex.get_by_text("37% used", exact=True)).to_be_visible()
    expect(codex.get_by_text("Reported balance 12.50", exact=True)).to_be_visible()
    selector = page.get_by_role("combobox", name="Provider", exact=True)
    expect(selector.locator('option[value="codex"]')).to_be_disabled()

    chatgpt.get_by_role("button", name="Check connection").click()
    expect(chatgpt.get_by_text("Setup required", exact=True)).to_be_visible()
    expect(selector.locator('option[value="chatgpt"]')).to_be_disabled()
    connect = chatgpt.get_by_role("button", name="Continue with ChatGPT", exact=True)
    expect(connect).to_have_attribute("data-oai-siwc-button", "")
    connect.click()
    expect(chatgpt.get_by_text("Waiting for ChatGPT consent", exact=False)).to_be_visible()
    assert len(consent.opened) == 1 and consent.exchanges == 0
    chatgpt.get_by_role("button", name="Cancel sign-in", exact=True).click()
    expect(chatgpt.get_by_text("Sign-in canceled", exact=False)).to_be_visible()
    assert not consent.active()
    audit()
    connect.click()
    expect(chatgpt.get_by_text("Waiting for ChatGPT consent", exact=False)).to_be_visible()
    assert len(consent.opened) == 2
    check_callback(browser, consent.callback_url(error="server_error"), width, axe, destination="studio",
                   heading="Sign-in response could not be verified", status=400)
    expect(chatgpt.get_by_role("alert")).to_contain_text("could not complete browser authorization")
    assert not consent.active() and consent.exchanges == 0
    connect.click()
    expect(chatgpt.get_by_text("Waiting for ChatGPT consent", exact=False)).to_be_visible()
    assert len(consent.opened) == 3
    drop_next_status = True
    try:
        check_callback(
            browser, consent.callback_url(code="fixture-code", client_id="oaiapp_browser_fixture",
                                          session_state="fictional-optional-session"), width, axe,
            destination="studio", heading="Sign-in response received",
            screenshot=artifacts / f"studio-chatgpt-return-{width}.png" if artifacts else None,
        )
        expect(chatgpt.get_by_text("Verifying the connection", exact=False)).to_be_visible()
        assert missed_reads == 1 and not consent.active()
    finally:
        consent.exchange_allowed.set()
    expect(chatgpt.get_by_text("Signed in", exact=False)).to_be_visible()
    assert consent.exchanges == 1 and consent.active()
    page.reload()
    page.get_by_role("button", name="Models", exact=True).click()
    expect(chatgpt.get_by_text("Signed in", exact=False)).to_be_visible()
    assert chatgpt_provider.calls == [("check",)]
    expect(selector.locator('option[value="chatgpt"]')).to_be_disabled()
    chatgpt_provider.catalog_diagnostic = CATALOG_RESPONSE
    chatgpt.get_by_role("button", name="Check connection").click()
    expect(chatgpt.get_by_text("The fictional model catalog is invalid.", exact=True)).to_be_visible()
    chatgpt_provider.catalog_diagnostic = CATALOG_DENIED
    chatgpt.get_by_role("button", name="Check connection").click()
    expect(chatgpt.get_by_text(DIAGNOSTIC_CANARY, exact=True)).to_be_visible()
    expect(selector.locator('option[value="chatgpt"]')).to_be_disabled()
    chatgpt_provider.catalog_diagnostic = CATALOG_EMPTY
    chatgpt.get_by_role("button", name="Check connection").click()
    expect(chatgpt.get_by_text("The fictional plan has no visible models.", exact=True)).to_be_visible()
    expect(selector.locator('option[value="chatgpt"]')).to_be_disabled()
    chatgpt_provider.catalog_diagnostic = None
    chatgpt.get_by_role("button", name="Check connection").click()
    expect(chatgpt.get_by_text("Models available", exact=True)).to_be_visible()
    checked_chatgpt = [("check",)] * 5

    gemini.get_by_role("button", name="Check connection").click()
    expect(gemini.get_by_text("Connected", exact=True)).to_be_visible()
    selector.select_option("gemini")
    models = page.get_by_role("combobox", name="Model", exact=True)
    models.select_option("small")
    preview = page.get_by_role("button", name="Preview fixture", exact=True)
    with page.expect_response("**/api/models/preview") as prior_preview:
        preview.click()
    gemini_approval = prior_preview.value.json()["preview_sha256"]
    prompt = page.get_by_role("region", name="Prompt preview")
    expect(prompt.locator("pre")).to_have_text(gemini_provider.approved_prompt)
    expect(page.get_by_role("button", name="Authorize cloud run")).to_be_enabled()
    models.select_option("large")
    expect(prompt).to_have_count(0)
    assert not any(path.endswith("/run") for path, _ in posts)
    preview.click()
    expect(prompt.locator("pre")).to_have_text(gemini_provider.approved_prompt)
    assert prompt.locator("pre").text_content() == gemini_provider.approved_prompt
    audit()
    if artifacts:
        page.screenshot(path=artifacts / f"studio-models-cloud-{width}.png", full_page=True, animations="disabled")
    page.get_by_role("button", name="Authorize cloud run").click()
    output = page.get_by_role("region", name="Model response")
    expect(output.locator("pre").first).to_have_text(PROVIDER_PROMPT_RESULT)
    expect(output.locator("strong")).to_have_count(0)
    expect(output.get_by_role("heading", name="Generated result for review")).to_be_visible()
    output.get_by_text("Compare with approved fixture", exact=True).click()
    expect(output.locator("details pre")).to_be_visible()
    assert output.locator("details pre").text_content() == gemini_provider.approved_prompt
    assert gemini_provider.calls == [("check",), ("run", "large")]

    preview.click()
    expect(prompt.locator("pre")).to_have_text(gemini_provider.approved_prompt)
    selector.select_option("chatgpt")
    expect(prompt).to_have_count(0)
    expect(models).to_have_value("")
    models.select_option("small")
    other_provider_attempt = {"provider": "chatgpt", "model": "small", "preview_sha256": gemini_approval}
    # Both providers list this model ID. The exact approval still belongs to Gemini.
    denied_status, denied_code = page.evaluate(
        """async (body) => {
          const response = await fetch("/api/models/run", {
            method: "POST",
            headers: {
              "Authorization": "Bearer " + sessionStorage.getItem("mindgarden-access"),
              "Content-Type": "application/json",
            },
            body: JSON.stringify(body),
          });
          return [response.status, (await response.json()).error?.code];
        }""",
        other_provider_attempt,
    )
    assert (denied_status, denied_code) == (409, "MODEL_REVIEW")
    assert chatgpt_provider.calls == checked_chatgpt
    preview.click()
    expect(prompt.get_by_text("The request may count against your ChatGPT plan usage.", exact=False)).to_be_visible()
    assert prompt.locator("pre").text_content() == chatgpt_provider.approved_prompt
    page.get_by_role("button", name="Authorize cloud run").click()
    expect(output.locator("pre").first).to_have_text(PROVIDER_PROMPT_RESULT)
    assert chatgpt_provider.calls == [*checked_chatgpt, ("run", "small")]
    audit()

    preview.click()
    expect(prompt).to_be_visible()
    chatgpt_provider.expired = True
    with page.expect_response("**/api/models/run") as expired_run:
        page.get_by_role("button", name="Authorize cloud run").click()
    assert expired_run.value.status == 401 and expired_run.value.json()["error"]["code"] == "MODEL_REAUTH"
    expect(page.get_by_role("alert")).to_contain_text("Continue with ChatGPT")
    expect(selector.locator('option[value="chatgpt"]')).to_be_disabled()
    expect(connect).to_be_visible()
    expect(output).to_have_count(0)
    assert chatgpt_provider.calls == [*checked_chatgpt, ("run", "small")]

    ollama.get_by_role("button", name="Check connection").click()
    expect(ollama.get_by_text("Connected", exact=True)).to_be_visible()
    page.get_by_role("combobox", name="Model to download", exact=True).select_option(DOWNLOAD_ID)
    download = page.get_by_role("button", name=f"Download {DOWNLOAD_LABEL}", exact=True)
    expect(download).to_have_count(0)
    with page.expect_response("**/api/models/install/preview") as previewed_download:
        page.get_by_role("button", name="Review model download", exact=True).click()
    approved_download = previewed_download.value.json()
    assert approved_download["model"] == DOWNLOAD_ID and re.fullmatch(r"[a-f0-9]{64}", approved_download["preview_sha256"])
    expect(page.get_by_text("use disk space", exact=False)).to_be_visible()
    assert ("install", DOWNLOAD_ID) not in ollama_provider.calls
    download.click()
    expect(page.get_by_text(f"{DOWNLOAD_LABEL} is available in Ollama.", exact=True)).to_be_visible()
    selector.select_option("ollama")
    models.select_option(DOWNLOAD_ID)
    preview.click()
    expect(prompt.locator("pre")).to_have_text(ollama_provider.approved_prompt)
    expect(page.get_by_role("button", name="Authorize cloud run")).to_have_count(0)
    page.get_by_role("button", name="Authorize loopback run").click()
    expect(output.locator("pre").first).to_have_text(PROVIDER_PROMPT_RESULT)
    assert ollama_provider.calls == [("check",), ("install", DOWNLOAD_ID), ("check",), ("run", DOWNLOAD_ID)]
    assert codex_provider.calls == [("check",)]
    run_requests = [body for path, body in posts if path.endswith("/run")]
    assert len(run_requests) == 5 and run_requests[1] == other_provider_attempt
    assert [(body["provider"], body["model"]) for body in run_requests] == [
        ("gemini", "large"), ("chatgpt", "small"), ("chatgpt", "small"), ("chatgpt", "small"), ("ollama", DOWNLOAD_ID),
    ]
    assert all(body.keys() == {"provider", "model", "preview_sha256"} for body in run_requests)
    assert [body for path, body in posts if path == "/api/models/install/preview"] == [{"model": DOWNLOAD_ID}]
    assert [body for path, body in posts if path == "/api/models/install"] == [approved_download]
    # After a fresh view, an explicit check must offer renewal even before a run fails.
    page.reload()
    page.get_by_role("button", name="Models", exact=True).click()
    chatgpt.get_by_role("button", name="Check connection").click()
    expect(connect).to_be_visible()
    chatgpt.get_by_role("button", name="Sign out of ChatGPT", exact=True).click()
    expect(chatgpt.get_by_text("Signed out of ChatGPT", exact=False)).to_be_visible()
    assert consent.revocations == 1 and not consent.active()
    assert [body for path, body in posts if path == "/api/models/chatgpt/connect"] == [{}, {}, {}]
    assert [body for path, body in posts if path == "/api/models/chatgpt/cancel"] == [{}]
    assert [body for path, body in posts if path == "/api/models/chatgpt/disconnect"] == [{}]
    audit()
    post_count = len(posts)
    check_diagnostics(page, url, width, consent, chatgpt_provider.approved_prompt,
                      diagnostics_reads, audit, artifacts)
    assert len(posts) == post_count, "Diagnostics performed an application action"
    assert not errors, errors
    page.close()


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--chromium", help="Path to a local Chromium binary")
    parser.add_argument("--axe", type=Path, help="Path to a local axe-core bundle")
    parser.add_argument("--artifacts", type=Path, help="Optional directory for fictional screenshots")
    args = parser.parse_args()
    if args.artifacts:
        args.artifacts.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(ROOT / "src"))
    from mindgarden.application.model_lab import PROMPT
    from mindgarden.interfaces.chatgpt_callback import LocalChatGPTCallback
    from mindgarden.interfaces.visit_demo import prepare_demo
    from playwright.sync_api import expect, sync_playwright

    axe = args.axe.read_text(encoding="utf-8") if args.axe else None
    expect.set_options(timeout=20_000)
    with TemporaryDirectory(prefix="mindgarden-model-browser-") as workspace:
        config, scope = prepare_demo(Path(workspace), assistant=True)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=args.chromium, args=["--disable-background-networking"])
            for width in (1440, 390):
                consent = FixtureConsent(Path(workspace).resolve() / f"fictional-consent-{width}")
                providers = (
                    FixtureProvider("codex", "Codex", "cloud", PROMPT),
                    FixtureProvider("gemini", "Gemini", "cloud", PROMPT),
                    FixtureProvider("ollama", "Ollama", "loopback", PROMPT),
                    FixtureProvider("chatgpt", "ChatGPT", "cloud", PROMPT, consent=consent),
                )
                with serve(config, scope, "providers", providers, consent) as url:
                    check_models(browser, url, width, providers, axe, args.artifacts)
                with LocalChatGPTCallback() as callback:
                    state = "fictional-terminal-state"
                    callback.arm(state, timeout=20)
                    query = urlencode({"state": state, "code": "fictional-terminal-code"})
                    check_callback(browser, callback.redirect_uri + "?" + query, width, axe, destination="terminal",
                                   heading="Sign-in response received")
                    assert callback.wait(state) == ("fictional-terminal-code", None)
            with serve(config, scope, "fixture") as url:
                page = browser.new_page()
                page.goto(url)
                expect(page.get_by_role("button", name="Chat", exact=True)).to_be_visible()
                expect(page.get_by_role("button", name="Models", exact=True)).to_have_count(0)
                page.close()
            browser.close()
    print("Studio Models and Diagnostics browser proof passed at 1440 and 390 pixels with offline fixture providers.")


if __name__ == "__main__":
    main()
