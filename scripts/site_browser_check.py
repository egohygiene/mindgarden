#!/usr/bin/env python3
"""Optional real Quartz/browser/portal proof using only synthetic public gardens."""

from argparse import ArgumentParser
from copy import deepcopy
import functools
import http.server
import importlib.metadata
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from mindgarden.adapters.site_files import read_site
from mindgarden.application.portal import build_portal
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import build_index
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.application.site import build_site
from mindgarden.domain.contracts import canonical_json, digest_bytes, read_object
from mindgarden.domain.site import QUARTZ_COMMIT, SITE_MARKER, verify_site
from mindgarden.domain.validation import ContractError
from tests.site_fixture import create_fixture
from tests.support_v1 import add_knowledge, write_json


def fixture(root, variant):
    data = create_fixture(root, empty=variant == "empty")
    if variant == "large":
        for index in range(202):
            record = add_knowledge(
                data["workspace"],
                f"synthetic-{index:03d}",
                body=f"Synthetic public procedure {index}: retain exact evidence.\n",
                visibility="public",
                sources=data["evidence"],
            )
            record["publication"] = "eligible"
            write_json(
                data["workspace"] / ".garden/knowledge" / (record["id"] + ".json"),
                record,
            )
        session = read_object(data["session_path"])
        session["budgets"]["max_results"] = 1000
        write_json(
            data["session_path"], bind_session_revisions(data["configuration"], session)
        )
        data["context"] = QueryContext.load(data["configuration"], data["session_path"])
        index = build_index(data["context"])
        data["profile"].update(
            source_revision=next(
                item["revision"]
                for item in index["inputs"]
                if item["garden"] == "repository-garden"
            ),
            inputs=[record["reference"] for record in index["records"]],
        )
    data["profile"]["x-site"]["theme"] = "mindgarden-v1"
    write_json(data["profile_path"], data["profile"])
    return data


def render(data, renderer, npm_cache):
    engine = data["engine"]
    engine.parent.mkdir(parents=True)
    subprocess.run(
        [
            "git",
            "clone",
            "--quiet",
            "--shared",
            "--no-checkout",
            "--",
            str(renderer),
            str(engine),
        ],
        check=True,
    )
    subprocess.run(
        ["git", "checkout", "--quiet", "--detach", QUARTZ_COMMIT],
        cwd=engine,
        check=True,
    )
    shutil.copytree(
        npm_cache, engine.parent / "npm", ignore=shutil.ignore_patterns("_logs")
    )
    projection = build_site(
        data["context"], data["profile"], profile_path=data["profile_path"]
    )
    started = time.monotonic()
    plan = projection.plan(
        data["context"], data["export"], operation="build", engine_directory=engine
    )
    assert projection.apply(
        data["context"],
        data["export"],
        plan["plan_sha256"],
        operation="build",
        engine_directory=engine,
    )
    duration = round(time.monotonic() - started, 3)
    files = read_site(data["export"] / "garden")
    manifest = verify_site(files)
    for canary in (
        "unreviewed-body-canary",
        "private-review-rationale-canary",
        "hidden-root-canary",
        str(data["workspace"]),
    ):
        assert canary.encode() not in b"".join(files.values())
    # A second real render proves declared byte determinism, not a mocked renderer.
    if len(manifest["routes"]) == 3:
        second = data["export"].parent / "render-repeat"
        second.mkdir()
        repeated = projection.plan(
            data["context"], second, operation="build", engine_directory=engine
        )
        assert projection.apply(
            data["context"],
            second,
            repeated["plan_sha256"],
            operation="build",
            engine_directory=engine,
        )
        assert read_site(second / "garden") == files
    return {
        "nodes": len(manifest["routes"]),
        "files": len(files),
        "revision": manifest["revision"],
        "manifest_sha256": digest_bytes(files[SITE_MARKER]),
        "build_seconds": duration,
    }


def portal_proof(source, destination):
    shutil.copytree(ROOT / "tests/fixtures/portal-composition", destination)
    siblings = {
        path.relative_to(destination).as_posix(): path.read_bytes()
        for path in destination.rglob("*")
        if path.is_file()
    }
    files = read_site(source)
    manifest = verify_site(files)
    request = {
        "schema": "mindgarden.portal-request/v1",
        "classification": "machine-local-control",
        "publication": "never-exportable",
        "source": {
            "directory": str(source),
            "expected_revision": manifest["revision"],
            "expected_manifest_sha256": digest_bytes(files[SITE_MARKER]),
        },
        "portal": {
            "directory": str(destination),
            "base_uri": manifest["base_uri"].removesuffix("garden/"),
            "mount": "garden",
        },
    }
    composition = build_portal(request)
    plan = composition.plan()
    assert not (destination / "garden").exists()
    with patch(
        "mindgarden.application.portal.create_receipt",
        side_effect=ContractError("SYNTHETIC_INTERRUPTION: receipt unavailable"),
    ):
        try:
            composition.apply(plan["plan_sha256"])
        except ContractError:
            pass
        else:
            raise AssertionError("Interrupted publication gate was ignored")
    assert not (destination / ".mindgarden-portal.json").exists()
    try:
        composition.verify()
    except ContractError:
        pass
    else:
        raise AssertionError("Incomplete receipt was accepted")
    assert composition.apply(plan["plan_sha256"])
    assert not composition.apply(plan["plan_sha256"])
    receipt = composition.verify()
    assert read_site(destination / "garden") == files
    assert all(
        (destination / name).read_bytes() == content
        for name, content in siblings.items()
    )
    # A later damaged candidate fails while a complete prior portal is retained.
    damaged = source.parent / "damaged-site"
    shutil.copytree(source, damaged)
    (damaged / "index.html").write_bytes(b"Synthetic corrupted candidate")
    changed = deepcopy(request)
    changed["source"]["directory"] = str(damaged)
    try:
        build_portal(changed)
    except ContractError:
        pass
    else:
        raise AssertionError("Corrupted candidate was accepted")
    assert composition.verify() == receipt
    return {
        "owned_files": len(receipt["owned"]),
        "receipt_sha256": digest_bytes(canonical_json(receipt)),
        "checks": [
            "actual-renderer-manifest",
            "receipt-failure-blocks-verification",
            "retry-and-repeat",
            "siblings-preserved",
            "corrupted-candidate-denied",
            "previous-portal-retained",
        ],
        "deployment": "not-invoked",
        "relay_action": "unavailable-at-inspected-pin",
    }


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_arguments):
        pass


def browser_proof(data, axe_script, chromium):
    from playwright.sync_api import sync_playwright

    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0),
        functools.partial(Handler, directory=str(data["export"])),
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    nodes = len(data["profile"]["inputs"])
    observations = []
    try:
        with sync_playwright() as engine:
            browser = engine.chromium.launch(
                executable_path=chromium,
                headless=True,
                args=["--no-sandbox", "--disable-background-networking"],
            )
            try:
                for width in (320, 1280):
                    context = browser.new_context(
                        viewport={"width": width, "height": 900},
                        reduced_motion="reduce",
                    )
                    context.route(
                        "**/*",
                        lambda route: route.continue_()
                        if route.request.url.startswith(base + "/")
                        else route.abort(),
                    )
                    page = context.new_page()
                    started = time.monotonic()
                    page.goto(base + "/garden/relationships.html")
                    page.wait_for_function(
                        "!document.querySelector('#mindgarden-graph [role=status]').textContent.startsWith('Loading')"
                    )
                    elapsed = round(time.monotonic() - started, 3)
                    assert page.locator('[role="main"]').count() == 1
                    assert (
                        page.get_by_role(
                            "heading", name="Complete relationship list", exact=True
                        ).count()
                        == 1
                    )
                    assert page.locator("#mindgarden-graph a").count() == (
                        nodes if nodes <= 200 else 0
                    )
                    assert page.locator(
                        "#mindgarden-graph button:disabled"
                    ).count() == (3 if nodes == 0 or nodes > 200 else 0)
                    assert page.evaluate(
                        "document.documentElement.scrollWidth <= innerWidth"
                    )
                    assert page.evaluate(
                        'matchMedia("(prefers-reduced-motion: reduce)").matches'
                    )
                    page.locator(".mindgarden-skip-link").focus()
                    assert page.locator(".mindgarden-skip-link").evaluate(
                        "element => element === document.activeElement"
                    )
                    page.keyboard.press("Enter")
                    page.wait_for_function(
                        'document.activeElement.id === "mindgarden-main"'
                    )
                    if 0 < nodes <= 200:
                        zoom = page.locator('[data-zoom="in"]')
                        zoom.focus()
                        before = page.locator("#mindgarden-graph svg").get_attribute(
                            "viewBox"
                        )
                        page.keyboard.press("Enter")
                        assert (
                            page.locator("#mindgarden-graph svg").get_attribute(
                                "viewBox"
                            )
                            != before
                        )
                        page.locator("#mindgarden-graph a").first.focus()
                        page.keyboard.press("Enter")
                        page.wait_for_url("**/notes/**")
                        assert (
                            page.get_by_role(
                                "heading", name="Exact evidence", exact=True
                            ).count()
                            == 1
                        )
                    page.goto(base + "/garden/")
                    page.get_by_role("button", name="Search", exact=True).click()
                    search = page.get_by_role(
                        "textbox", name="Search for something...", exact=True
                    )
                    search.fill("evidence")
                    assert search.evaluate(
                        "element => element === document.activeElement"
                    )
                    page.keyboard.press("Escape")
                    page.add_script_tag(path=str(axe_script))
                    audits = []
                    for theme in ("light", "dark"):
                        if (
                            page.evaluate(
                                "document.documentElement.getAttribute('saved-theme')"
                            )
                            != theme
                        ):
                            page.get_by_role(
                                "button",
                                name="Dark mode" if theme == "dark" else "Light mode",
                                exact=True,
                            ).click()
                        result = page.evaluate(
                            """async () => {const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}});return {version:axe.version, violations:r.violations.map(v=>({id:v.id,impact:v.impact,targets:v.nodes.map(n=>n.target),details:v.nodes.map(n=>n.failureSummary)})),incomplete:r.incomplete.map(v=>v.id)}}"""
                        )
                        assert result["version"] == "4.10.3"
                        # Retain the pinned external renderer defect, never hide it.
                        assert {item["id"] for item in result["violations"]} <= {
                            "aria-allowed-attr"
                        }, result
                        audits.append({"theme": theme, **result})
                    page.evaluate('document.documentElement.style.fontSize="200%"')
                    assert page.evaluate(
                        "document.documentElement.scrollWidth <= innerWidth"
                    )
                    observations.append(
                        {
                            "width": width,
                            "graph_ready_seconds": elapsed,
                            "checks": "passed",
                            "axe": audits,
                        }
                    )
                    context.close()
                static = browser.new_context(java_script_enabled=False)
                static.route(
                    "**/*",
                    lambda route: route.continue_()
                    if route.request.url.startswith(base + "/")
                    else route.abort(),
                )
                page = static.new_page()
                page.goto(base + "/garden/relationships.html")
                assert (
                    page.get_by_role(
                        "heading", name="Complete relationship list", exact=True
                    ).count()
                    == 1
                )
                assert page.locator("#mindgarden-graph button:disabled").count() == 3
                static.close()
                failed = browser.new_context()
                failed.route(
                    "**/*",
                    lambda route: route.continue_()
                    if route.request.url.startswith(base + "/")
                    else route.abort(),
                )
                failed.route(
                    "**/garden/graph.json",
                    lambda route: route.fulfill(
                        status=503, body="Synthetic unavailable graph"
                    ),
                )
                page = failed.new_page()
                page.goto(base + "/garden/relationships.html")
                page.wait_for_function(
                    "document.querySelector('#mindgarden-graph [role=status]').textContent.includes('unavailable')"
                )
                assert page.locator("#mindgarden-graph button:disabled").count() == 3
                failed.close()
                return {
                    "chromium": browser.version,
                    "playwright": importlib.metadata.version("playwright"),
                    "viewports": observations,
                    "javascript_disabled_list": "passed",
                    "unavailable_graph": "passed",
                    "browser_requests": "loopback-only",
                }
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument(
        "--renderer",
        type=Path,
        required=True,
        help="Prepared immutable Quartz checkout; no acquisition here",
    )
    parser.add_argument("--npm-cache", type=Path, required=True)
    parser.add_argument(
        "--axe-script",
        type=Path,
        required=True,
        help="Locally prepared axe-core 4.10.3 axe.min.js",
    )
    parser.add_argument("--chromium", default="/usr/bin/chromium")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    workspace = args.workspace.absolute()
    if (
        any(path.is_symlink() for path in (workspace, *workspace.parents))
        or workspace.exists()
        and any(workspace.iterdir())
    ):
        parser.error("Use a new or empty ordinary synthetic workspace")
    reports = {}
    for variant in ("empty", "small", "large"):
        data = fixture(workspace / variant, variant)
        reports[variant] = {
            "render": render(data, args.renderer.absolute(), args.npm_cache.absolute()),
            "browser": browser_proof(data, args.axe_script.absolute(), args.chromium),
        }
        if variant == "small":
            reports[variant]["portal"] = portal_proof(
                data["export"] / "garden", workspace / "portal"
            )
    report = {
        "schema": "mindgarden.rendered-browser-portal-proof/v1",
        "status": "partial-renderer-accessibility-findings",
        "renderer_commit": QUARTZ_COMMIT,
        "variants": reports,
        "models": "unused",
        "google": "unused",
        "limitations": [
            "Pinned Quartz Explorer has an unsupported aria-expanded attribute; retained axe finding",
            "Automated rules/keyboard checks are not full WCAG or screen-reader certification",
            "Relay #40 action, host promotion and production publication remain unverified",
        ],
    }
    content = canonical_json(report)
    if args.report:
        with args.report.open("xb") as output:
            output.write(content)
    print(content.decode(), end="")


if __name__ == "__main__":
    main()
