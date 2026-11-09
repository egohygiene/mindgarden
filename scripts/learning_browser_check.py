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


def check(*, due_only=False, axe_script=None):
    case = unittest.TestCase()
    try:
        learning_fixture.setup(case)
        _, files = plan_learning(
            case.context,
            case.request,
            due_only=due_only,
            review_limit=1 if due_only else None,
        )
        with sync_playwright() as engine:
            browser = engine.chromium.launch(
                executable_path="/usr/bin/chromium",
                headless=True,
                args=["--no-sandbox", "--disable-background-networking"],
            )
            try:
                audits = []
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
                    if axe_script is not None:
                        page.add_script_tag(path=str(axe_script))
                        result = page.evaluate(
                            """async () => {const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}});return {version:axe.version,violations:r.violations.map(v=>({id:v.id,impact:v.impact})),incomplete:r.incomplete.map(v=>v.id)}}"""
                        )
                        assert (
                            result["version"] == "4.10.3" and not result["violations"]
                        ), result
                        audits.append({"width": width, **result})
                    context.close()
                version = browser.version
            finally:
                browser.close()
        report = {
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
        if due_only:
            report["study_selection"] = (
                "one-due-card-with-private-history-and-exact-provenance"
            )
        if axe_script is not None:
            report["axe_audits"] = audits
        return report
    finally:
        case.doCleanups()


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--due-only", action="store_true")
    parser.add_argument("--axe-script", type=Path)
    args = parser.parse_args()
    content = (
        json.dumps(
            check(due_only=args.due_only, axe_script=args.axe_script),
            sort_keys=True,
            indent=2,
        )
        + "\n"
    )
    if args.report:
        with args.report.open("x") as output:
            output.write(content)
    print(content, end="")
