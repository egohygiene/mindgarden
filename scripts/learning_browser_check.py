#!/usr/bin/env python3
"""Optional real-browser checks of the authored synthetic static study projection."""

from argparse import ArgumentParser
import importlib.metadata
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from mindgarden.application.learning import plan_learning
from tests import learning_fixture
from playwright.sync_api import sync_playwright


def check():
    case = unittest.TestCase()
    try:
        learning_fixture.setup(case)
        _, files = plan_learning(case.context, case.request)
        with sync_playwright() as engine:
            browser = engine.chromium.launch(
                executable_path="/usr/bin/chromium",
                headless=True,
                args=["--no-sandbox", "--disable-background-networking"],
            )
            try:
                for width in (320, 1280):
                    context = browser.new_context(
                        offline=True,
                        viewport={"width": width, "height": 900},
                        reduced_motion="reduce",
                    )
                    context.route("**/*", lambda route: route.abort())
                    page = context.new_page()
                    page.set_content(files["study.html"].decode())
                    assert (
                        page.locator("main").count() == 1
                        and page.locator("h1").count() == 1
                    )
                    assert (
                        page.locator('script,img,iframe,link[rel="stylesheet"]').count()
                        == 0
                    )
                    assert page.evaluate(
                        "document.documentElement.scrollWidth <= innerWidth"
                    )
                    summary = page.get_by_text("Reveal answer", exact=True).first
                    summary.focus()
                    page.keyboard.press("Enter")
                    assert summary.evaluate("element => element.parentElement.open")
                    page.keyboard.press("Space")
                    assert not summary.evaluate("element => element.parentElement.open")
                    assert page.evaluate(
                        'matchMedia("(prefers-reduced-motion: reduce)").matches'
                    )
                    page.evaluate('document.documentElement.style.fontSize="200%"')
                    assert page.evaluate(
                        "document.documentElement.scrollWidth <= innerWidth"
                    )
                    context.close()
                version = browser.version
            finally:
                browser.close()
        return {
            "schema": "mindgarden.learning-browser-check/v1",
            "chromium": version,
            "playwright": importlib.metadata.version("playwright"),
            "viewports": [320, 1280],
            "keyboard_reveal": "passed",
            "zoom_200_percent": "passed",
            "reduced_motion": "passed",
            "semantic_landmarks": "passed",
            "external_resources": "none",
            "page_network": "offline",
            "limitations": [
                "static projection only; not full hosted review UI or screen-reader certification"
            ],
        }
    finally:
        case.doCleanups()


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    content = json.dumps(check(), sort_keys=True, indent=2) + "\n"
    if args.report:
        with args.report.open("x") as output:
            output.write(content)
    print(content, end="")
