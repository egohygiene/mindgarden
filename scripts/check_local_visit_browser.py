"""Exercise the fictional visit in Chromium with an optional local axe bundle."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]


def verify_visit(url, chromium, axe, screenshots):
    from playwright.sync_api import expect, sync_playwright

    expect.set_options(timeout=20_000)

    def audit(page):
        if axe:
            page.evaluate(axe.read_text())
            violations = page.evaluate("async () => (await axe.run()).violations")
            assert not violations, [(violation["id"], violation["nodes"]) for violation in violations]

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=chromium)
        errors = []
        external = []

        def route_request(route):
            if urlsplit(route.request.url).netloc == urlsplit(url).netloc:
                route.continue_()
            else:
                external.append(route.request.url)
                route.abort()

        for width in (1440, 390, 320):
            page = browser.new_page(
                viewport={"width": width, "height": 900},
                reduced_motion="reduce" if width < 760 else "no-preference",
            )
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.route("http*://**/*", route_request)
            page.goto(url)
            expect(page.get_by_role("heading", name="A garden for what you know.")).to_be_visible()
            expect(page.get_by_text("Fictional demo garden")).to_be_visible()
            assert "access=" not in page.url
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            audit(page)
            if screenshots and width in (1440, 390):
                name = "desktop" if width == 1440 else "mobile"
                page.screenshot(path=screenshots / f"mindgarden-{name}.png", full_page=True, animations="disabled")
            if width < 760:
                assert page.locator(".enter").evaluate("(node) => getComputedStyle(node).animationDuration") == "0s"
            page.get_by_role("link", name="Skip to content").focus()
            page.keyboard.press("Enter")
            expect(page.get_by_role("main")).to_be_focused()
            page.locator("#global-query").fill("accessibility")
            page.locator("#global-query").press("Enter")
            expect(page.get_by_role("heading", name="Search results")).to_be_visible()
            audit(page)
            page.get_by_role("link", name="Fictional career and accessibility learning").click()
            excerpt = page.get_by_role("button", name="Open source excerpt").first
            excerpt.focus()
            page.keyboard.press("Enter")
            expect(page.locator(".evidence-text")).to_contain_text("keyboard")
            expect(page.get_by_role("button", name="Hide source excerpt").first).to_be_focused()
            audit(page)
            page.get_by_role("link", name="Fictional Example Studio overview").first.click()
            expect(page.locator(".note-text")).to_contain_text("2026-05-15")
            expect(page.locator(".note-text")).to_contain_text("2026-05-22")
            expect(page.get_by_role("heading", name="Questions and caveats")).to_be_visible()
            page.reload()
            expect(page.get_by_role("heading", name="Fictional Example Studio overview")).to_be_visible()
            page.get_by_role("link", name="Connections", exact=True).click()
            expect(page.get_by_role("heading", name="Linked notes")).to_be_visible()
            assert page.locator(".graph-node").count() == 5
            assert page.locator(".graph-edge").count() == 4
            audit(page)
            page.get_by_role("link", name="Context pack", exact=True).click()
            page.get_by_role("searchbox", name="Topic or keywords").fill("consultation")
            with page.expect_response("**/api/context?*") as response:
                page.get_by_role("button", name="Build context pack").click()
            with page.expect_download() as download:
                page.get_by_role("button", name="Download JSON").click()
            emitted = Path(download.value.path()).read_bytes()
            assert emitted == response.value.body()
            pack = json.loads(emitted)
            assert len(emitted) <= pack["budget"]["max_bytes"]
            assert 0 < len(pack["included"]) <= pack["budget"]["max_items"]
            assert all(item["sources"] and item["selection_reason"] for item in pack["included"])
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            audit(page)
            page.close()
        without_scripts = browser.new_page(java_script_enabled=False)
        without_scripts.goto(url)
        expect(without_scripts.get_by_text("Enable JavaScript to visit", exact=False)).to_be_visible()
        assert not errors, errors
        assert not external, external
        browser.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chromium", help="Path to a local Chromium binary")
    parser.add_argument("--axe", type=Path, help="Optional local axe.min.js path")
    parser.add_argument("--screenshots", type=Path, help="Optional directory for fictional screenshots")
    args = parser.parse_args()
    if args.screenshots:
        args.screenshots.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="mindgarden-browser-proof-") as temporary:
        with subprocess.Popen(
            [sys.executable, "-m", "mindgarden", "visit", "--demo", "--workspace", temporary],
            cwd=ROOT,
            env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
            stdout=subprocess.PIPE,
            text=True,
        ) as server:
            try:
                url = server.stdout.readline().strip()
                assert urlsplit(url).hostname == "127.0.0.1", "The local visit did not start"
                verify_visit(url, args.chromium, args.axe, args.screenshots)
            finally:
                if server.poll() is None:
                    server.send_signal(signal.SIGINT)
            assert server.wait(timeout=10) == 0
    print("Local visit passed at 1440, 390 and 320 pixels" + (" with 15 axe checks" if args.axe else ""))


if __name__ == "__main__":
    main()
