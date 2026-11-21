"""Qualify Studio Models in Chromium with offline fixture providers."""

from argparse import ArgumentParser
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory
from threading import Thread
from urllib.parse import urlsplit
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PROVIDER_PROMPT_RESULT = "<strong>Fictional comparison result.</strong>"
DOWNLOAD_ID = "fake-local:1b"
DOWNLOAD_LABEL = "Fictional local model"


@dataclass
class FixtureProvider:
    id: str
    name: str
    disclosure: str
    approved_prompt: str
    calls: list[tuple] = field(default_factory=list)
    installed: bool = False
    signed_in: bool = False

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
            if self.signed_in:
                state.update(models=[{"id": "small", "label": "Plan text model"}], can_run=True)
            else:
                state.update(status="unconfigured", detail="The fictional profile needs consent.")
        if self.id == "ollama":
            model = {"id": DOWNLOAD_ID, "label": DOWNLOAD_LABEL}
            if self.installed:
                state.update(models=[model], can_run=True)
            else:
                state["downloadable"] = [model]
        return state

    def run(self, model, prompt):
        if self.id == "chatgpt" and not self.signed_in:
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
def serve(config, scope, mode: str, providers: tuple[FixtureProvider, ...] = ()) -> Iterator[str]:
    from mindgarden.interfaces.local_web import make_server

    with patch("mindgarden.application.model_lab.configured_providers", return_value=providers):
        server = make_server(config, scope, demo=True, interface="studio", assistant=mode)
    with server:
        worker = Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            yield server.url
        finally:
            server.shutdown()
            worker.join()


def check_models(browser, url, width, providers, axe, artifacts):
    from playwright.sync_api import expect

    page = browser.new_page(
        viewport={"width": width, "height": 950},
        reduced_motion="reduce" if width < 760 else "no-preference",
    )
    codex_provider, gemini_provider, ollama_provider, chatgpt_provider = providers
    errors = []
    posts = []
    authority = urlsplit(url).netloc

    def local_only(route):
        request = route.request
        parsed = urlsplit(request.url)
        if parsed.netloc != authority:
            errors.append("Unexpected remote URL")
            route.abort()
            return
        if request.method == "POST":
            posts.append((parsed.path, request.post_data_json))
        route.continue_()

    def audit():
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        if axe:
            page.evaluate(axe)
            violations = page.evaluate("async () => (await axe.run()).violations")
            assert not violations, [item["id"] for item in violations]

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
    setup = chatgpt.get_by_role("region", name="ChatGPT plan setup", exact=True)
    expect(setup).to_have_count(0)
    assert not posts and all(not provider.calls for provider in providers)
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
    expect(setup.get_by_text("mindgarden chatgpt connect --state-directory <private-dir>", exact=True)).to_be_visible()
    expect(setup.get_by_text("--chatgpt-state-directory <private-dir>", exact=True)).to_be_visible()
    expect(setup.get_by_role("link", name="Read the ChatGPT plan usage guide")).to_have_attribute(
        "href", "https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference"
    )
    expect(selector.locator('option[value="chatgpt"]')).to_be_disabled()
    audit()
    # Represent consent completed separately in the terminal.
    chatgpt_provider.signed_in = True
    chatgpt.get_by_role("button", name="Check connection").click()
    expect(chatgpt.get_by_text("Models available", exact=True)).to_be_visible()
    expect(setup).to_have_count(0)

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
    assert chatgpt_provider.calls == [("check",), ("check",)]
    preview.click()
    expect(prompt.get_by_text("The request may count against your ChatGPT plan usage.", exact=False)).to_be_visible()
    assert prompt.locator("pre").text_content() == chatgpt_provider.approved_prompt
    page.get_by_role("button", name="Authorize cloud run").click()
    expect(output.locator("pre").first).to_have_text(PROVIDER_PROMPT_RESULT)
    assert chatgpt_provider.calls == [("check",), ("check",), ("run", "small")]
    audit()

    preview.click()
    expect(prompt).to_be_visible()
    chatgpt_provider.signed_in = False
    with page.expect_response("**/api/models/run") as expired_run:
        page.get_by_role("button", name="Authorize cloud run").click()
    assert expired_run.value.status == 401 and expired_run.value.json()["error"]["code"] == "MODEL_REAUTH"
    expect(page.get_by_role("alert")).to_contain_text("mindgarden chatgpt refresh")
    expect(selector.locator('option[value="chatgpt"]')).to_be_disabled()
    expect(setup).to_be_visible()
    expect(output).to_have_count(0)
    assert chatgpt_provider.calls == [("check",), ("check",), ("run", "small")]

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
    assert not errors, errors
    audit()
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
    from mindgarden.interfaces.visit_demo import prepare_demo
    from playwright.sync_api import expect, sync_playwright

    axe = args.axe.read_text(encoding="utf-8") if args.axe else None
    expect.set_options(timeout=20_000)
    with TemporaryDirectory(prefix="mindgarden-model-browser-") as workspace:
        config, scope = prepare_demo(Path(workspace), assistant=True)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=args.chromium, args=["--disable-background-networking"])
            for width in (1440, 390):
                providers = (
                    FixtureProvider("codex", "Codex", "cloud", PROMPT),
                    FixtureProvider("gemini", "Gemini", "cloud", PROMPT),
                    FixtureProvider("ollama", "Ollama", "loopback", PROMPT),
                    FixtureProvider("chatgpt", "ChatGPT", "cloud", PROMPT),
                )
                with serve(config, scope, "providers", providers) as url:
                    check_models(browser, url, width, providers, axe, args.artifacts)
            with serve(config, scope, "fixture") as url:
                page = browser.new_page()
                page.goto(url)
                expect(page.get_by_role("button", name="Chat", exact=True)).to_be_visible()
                expect(page.get_by_role("button", name="Models", exact=True)).to_have_count(0)
                page.close()
            browser.close()
    print("Studio Models browser proof passed at 1440 and 390 pixels with offline fixture providers.")


if __name__ == "__main__":
    main()
