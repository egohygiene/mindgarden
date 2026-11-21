"""Exercise Studio's fictional assistant and cited booklet in Chromium."""

from argparse import ArgumentParser
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
CAREER = "Fictional career and accessibility learning"


def check_studio(url, chromium, axe, artifacts):
    from playwright.sync_api import expect, sync_playwright

    expect.set_options(timeout=20_000)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=chromium)
        for width in (1440, 390):
            page = browser.new_page(
                viewport={"width": width, "height": 950},
                reduced_motion="reduce" if width < 760 else "no-preference",
            )
            failures = []

            def route_local(route):
                if urlsplit(route.request.url).netloc == urlsplit(url).netloc:
                    route.continue_()
                else:
                    failures.append("Unexpected remote request")
                    route.abort()

            def audit():
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                if axe:
                    page.evaluate(axe)
                    issues = page.evaluate("async () => (await axe.run()).violations")
                    assert not issues, [issue["id"] for issue in issues]

            def save(name):
                if artifacts and width == 1440:
                    page.screenshot(path=artifacts / f"{name}.png", full_page=True, animations="disabled")

            page.on("pageerror", lambda error: failures.append(str(error)))
            page.route("http*://**/*", route_local)
            page.set_default_timeout(45_000)
            page.goto(url)
            expect(page.get_by_role("heading", level=1)).to_contain_text("knowledge connects")
            page.get_by_role("button", name=CAREER, exact=False).first.click()
            expect(page.get_by_role("heading", name=CAREER, level=1)).to_be_visible()
            page.get_by_role("button", name="Ask about this note").click()
            question = page.get_by_role("textbox", name="Question")
            question.fill("What accessibility experiment is proposed?")
            with page.expect_response("**/api/assistant/preview") as preview:
                page.get_by_role("button", name="Preview context").click()
            approved = preview.value.json()
            assert approved["provider"] == "fixture"
            assert len(approved["records"]) == 1
            assert "keyboard" in approved["records"][0]["content"]
            assert approved["records"][0]["sources"]
            assert "accessibility" not in page.url and "access=" not in page.url
            audit()

            with page.expect_response("**/api/assistant/run") as run:
                page.get_by_role("button", name="Run fictional assistant").click()
            citation = page.get_by_role("button", name="Open cited note", exact=False).first
            expect(citation).to_be_visible()
            assert run.value.headers["content-type"].startswith("application/x-ndjson")
            audit()
            save("studio-assistant")
            citation.click()
            expect(page.get_by_role("heading", name=CAREER, level=1)).to_be_visible()

            nav = page.get_by_role("navigation", name="Garden", exact=True)
            nav.get_by_role("button", name="Chat", exact=True).click()
            expect(page.get_by_role("button", name="Open cited note", exact=False).first).to_be_visible()
            page.get_by_role("combobox", name="Lens").select_option("finance")
            expect(page.get_by_role("button", name="Preview context")).to_be_disabled()
            page.get_by_role("combobox", name="Scope").select_option("")
            question.fill("What do the spending notes say about my monthly finances and booklet?")
            with page.expect_response("**/api/assistant/preview") as preview:
                page.get_by_role("button", name="Preview context").click()
            finance_context = preview.value.json()
            assert finance_context["lens"] == "finance"
            assert finance_context["records"] and all(record["sources"] for record in finance_context["records"])
            assert all(record["title"] != CAREER for record in finance_context["records"])
            page.get_by_role("button", name="Run fictional assistant").click()
            page.get_by_role("button", name="Open consultation booklet", exact=True).click()
            with page.expect_response("**/api/booklet/preview") as preview:
                page.get_by_role("button", name="Preview booklet").click()
            reviewed = preview.value.json()
            assert reviewed["month"] == "2026-01"
            assert re.fullmatch("[0-9a-f]{64}", reviewed["plan_sha256"])
            assert reviewed["totals"][0]["net_movement"] == "2259.76"
            assert len(reviewed["evidence"]) == 8
            expect(page.get_by_role("heading", name="Open questions")).to_be_visible()
            for question_text in reviewed["questions"]:
                expect(page.get_by_text(question_text, exact=True)).to_be_visible()
            page.get_by_text("8 selected transactions", exact=True).click()
            transactions = page.get_by_role("list", name="Selected transactions").get_by_role("listitem")
            expect(transactions).to_have_count(len(reviewed["transactions"]))
            for row, transaction in zip(transactions.all(), reviewed["transactions"]):
                expect(row).to_contain_text(transaction["date"])
                expect(row).to_contain_text(transaction["amount"] + " " + transaction["currency"])
                expect(row).to_contain_text(transaction["citation"])
            expect(page.get_by_role("button", name="Download PDF")).to_be_disabled()
            audit()
            page.get_by_role("button", name="Approve preview for download").click()
            with page.expect_download() as downloaded_pdf:
                page.get_by_role("button", name="Download PDF").click()
            payload = Path(downloaded_pdf.value.path()).read_bytes()
            assert payload.startswith(b"%PDF-") and payload.rstrip().endswith(b"%%EOF")
            with page.expect_download() as downloaded_evidence:
                page.get_by_role("button", name="Download evidence").click()
            evidence = Path(downloaded_evidence.value.path()).read_bytes()
            manifest = json.loads(evidence)
            assert manifest["pdf_sha256"] == sha256(payload).hexdigest()
            assert manifest["evidence"] == reviewed["evidence"]
            audit()
            save("studio-booklet")
            if artifacts and width == 1440:
                (artifacts / "fictional-monthly-booklet.pdf").write_bytes(payload)
                (artifacts / "fictional-booklet-evidence.json").write_bytes(evidence)
            assert not failures, failures
            page.close()
        browser.close()


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--chromium", help="Path to a local Chromium binary")
    parser.add_argument("--axe", type=Path, help="Path to a local axe-core bundle")
    parser.add_argument("--artifacts", type=Path, help="Optional directory for fictional outputs")
    args = parser.parse_args()
    if args.artifacts:
        args.artifacts.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="mindgarden-assistant-proof-") as workspace:
        with subprocess.Popen(
            [sys.executable, "-m", "mindgarden", "visit", "--interface", "studio",
             "--demo", "--assistant", "fixture", "--workspace", workspace],
            cwd=ROOT,
            env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
            stdout=subprocess.PIPE,
            text=True,
        ) as server:
            try:
                url = server.stdout.readline().strip()
                assert urlsplit(url).hostname == "127.0.0.1", "Studio did not print a loopback launch link"
                check_studio(url, args.chromium, args.axe.read_text() if args.axe else None, args.artifacts)
            finally:
                if server.poll() is None:
                    server.send_signal(signal.SIGINT)
            assert server.wait(timeout=10) == 0
    print("Fictional assistant and booklet browser qualification passed at 1440 and 390 pixels.")


if __name__ == "__main__":
    main()
