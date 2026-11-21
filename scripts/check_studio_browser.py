"""Run the built Studio against the real fictional garden in Chromium."""

from __future__ import annotations

from argparse import ArgumentParser
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def visit(url, chromium, axe, screenshots, webgl):
    from playwright.sync_api import expect, sync_playwright

    expect.set_options(timeout=15_000)

    def audit(page):
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        if axe:
            page.evaluate(axe)
            violations = page.evaluate("async () => (await axe.run()).violations")
            assert not violations, [violation["id"] for violation in violations]

    def screenshot(page, name):
        if screenshots:
            page.screenshot(path=screenshots / f"studio-{name}.png", full_page=True, animations="disabled")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=chromium,
            args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] if webgl else ["--disable-webgl"],
        )
        for width in (1440, 390, 320):
            page = browser.new_page(
                viewport={"width": width, "height": 950},
                reduced_motion="reduce" if width < 760 else "no-preference",
            )
            failures = []
            requests = []

            def route_local(route):
                address = route.request.url
                requests.append(address)
                if urlsplit(address).netloc == urlsplit(url).netloc:
                    route.continue_()
                else:
                    failures.append("Unexpected remote request")
                    route.abort()

            page.on("pageerror", lambda error: failures.append(str(error)))
            page.route("http*://**/*", route_local)
            page.goto(url)
            expect(page.get_by_role("heading", level=1)).to_contain_text("knowledge connects")
            expect(page.get_by_text("Visible notes", exact=True)).to_be_visible()
            expect(page.get_by_text("Google Drive", exact=True)).to_be_visible()
            expect(page.get_by_text("Fictional example · 8 reviewed citations", exact=True)).to_be_visible()
            assert not any("graph-scene-" in address for address in requests)
            assert "access=" not in page.url
            audit(page)
            if width != 320:
                screenshot(page, "desktop" if width == 1440 else "mobile")

            page.get_by_role("link", name="Skip to content").focus()
            page.keyboard.press("Enter")
            expect(page.get_by_role("main")).to_be_focused()
            page.keyboard.press("Control+k")
            dialog = page.get_by_role("dialog")
            query = dialog.get_by_role("searchbox")
            expect(query).to_be_focused()
            audit(page)
            query.fill("accessibility")
            query.press("Enter")
            expect(page.get_by_role("heading", name="Search results")).to_be_visible()
            assert "accessibility" not in page.url
            audit(page)
            page.get_by_role("button", name="Fictional career and accessibility learning", exact=True).click()
            expect(page.get_by_role("heading", name="Reviewed knowledge")).to_be_visible()
            evidence = page.get_by_role("button", name="Open source excerpt", exact=False).first
            evidence.focus()
            page.keyboard.press("Enter")
            expect(page.locator(".fv-excerpt")).to_contain_text("keyboard")
            expect(page.get_by_role("button", name="Hide source excerpt", exact=False).first).to_be_focused()
            audit(page)
            if width == 1440:
                screenshot(page, "source")

            nav = page.get_by_role("navigation", name="Garden", exact=True)
            page.get_by_role("button", name="Find on map").click()
            expect(page.get_by_role("heading", name="Knowledge explorer", exact=True)).to_be_visible()
            career = "Fictional career and accessibility learning"
            studio = "Fictional Example Studio overview"
            inspector = page.get_by_role("region", name=career)
            expect(inspector.get_by_role("heading", name="Connected notes")).to_be_visible()
            expect(inspector.get_by_text("Mutual · Related", exact=True)).to_be_visible()
            audit(page)
            if width == 1440:
                screenshot(page, "explorer")
            inspector.get_by_role("button", name=f"Focus {studio}", exact=True).click()
            trail = page.get_by_role("navigation", name="Graph trail")
            expect(trail.get_by_role("button", name=career, exact=True)).to_be_visible()
            page.get_by_role("button", name="Open note", exact=True).click()
            expect(page.get_by_role("heading", name=studio, level=1)).to_be_visible()
            page.get_by_role("button", name="Back to map", exact=True).click()
            expect(page.get_by_role("region", name=studio)).to_be_visible()
            trail.get_by_role("button", name="Full map").click()
            page.get_by_role("searchbox", name="Find a note or topic").fill("accessibility")
            expect(page.get_by_text("1 matching note", exact=True)).to_be_visible()
            assert "accessibility" not in page.url
            page.get_by_role("button", name="Clear filters").click()
            page.get_by_role("combobox", name="Topic", exact=True).select_option("portfolio")
            expect(page.get_by_role("heading", name="Matching notes")).to_be_visible()
            page.get_by_role("button", name="Clear filters").click()
            assert not any("graph-scene-" in address for address in requests)
            if width == 1440:
                page.get_by_role("button", name="Explore in 3D", exact=True).click()
                if webgl:
                    expect(page.locator("canvas")).to_be_visible()
                    assert any("graph-scene-" in address for address in requests)
                    screenshot(page, "3d")
                    page.get_by_role("button", name="Back to 2D").click()
                else:
                    expect(page.get_by_text("3D is unavailable on this device.", exact=False)).to_be_visible()
            expect(page.get_by_role("group", name="Interactive map of visible notes")).to_be_visible()
            audit(page)

            with page.expect_response("**/api/connectors") as source_summary:
                nav.get_by_role("button", name="Sources", exact=True).click()
            expect(page.get_by_role("heading", name="Sources", level=1)).to_be_visible()
            expect(page.get_by_text("Fictional example", exact=True)).to_be_visible()
            connectors = source_summary.value.json()
            assert connectors["google_drive"]["state"] == "demo"
            assert connectors["local_vault"]["state"] == "visible-evidence"
            expect(page.get_by_role("heading", name="Local source vault")).to_be_visible()
            if width == 1440:
                screenshot(page, "sources")
            audit(page)

            nav.get_by_role("button", name="Context packs", exact=True).click()
            page.get_by_role("searchbox", name="Topic or keywords").fill("consultation")
            with page.expect_response("**/api/context?*") as response:
                page.get_by_role("button", name="Build context pack").click()
            download = page.get_by_role("button", name="Download JSON")
            with page.expect_download() as saved:
                download.click()
            emitted = Path(saved.value.path()).read_bytes()
            assert emitted == response.value.body()
            pack = json.loads(emitted)
            assert len(emitted) <= pack["budget"]["max_bytes"]
            assert all(note["sources"] for note in pack["included"])
            assert "consultation" not in page.url
            audit(page)

            nav.get_by_role("button", name="Library", exact=True).click()
            expect(page.get_by_role("heading", name="All visible notes")).to_be_visible()
            nav.get_by_role("button", name="Library", exact=True).click()
            expect(page.get_by_role("heading", name="All visible notes")).to_be_visible()
            assert not failures, failures
            page.close()
        browser.close()


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--chromium", help="Path to an optional local Chromium binary")
    parser.add_argument("--axe", type=Path, help="Path to a local axe-core JavaScript bundle")
    parser.add_argument("--screenshots", type=Path, help="Save fictional previews here")
    parser.add_argument("--webgl", action="store_true", help="Exercise 3D with Chromium's software WebGL")
    args = parser.parse_args()
    if args.screenshots:
        args.screenshots.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="mindgarden-studio-proof-") as workspace:
        with subprocess.Popen(
            [sys.executable, "-m", "mindgarden", "visit", "--interface", "studio", "--demo", "--workspace", workspace],
            cwd=ROOT,
            env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
            stdout=subprocess.PIPE,
            text=True,
        ) as server:
            try:
                url = server.stdout.readline().strip()
                assert urlsplit(url).hostname == "127.0.0.1", "Studio did not print a loopback launch link"
                visit(url, args.chromium, args.axe.read_text() if args.axe else None, args.screenshots, args.webgl)
            finally:
                if server.poll() is None:
                    server.send_signal(signal.SIGINT)
            assert server.wait(timeout=10) == 0
    print("Studio browser qualification passed at 1440, 390, and 320 pixels.")


if __name__ == "__main__":
    main()
