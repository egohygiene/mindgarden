#!/usr/bin/env python3
"""Reproduce authored archive compaction through the existing private workflow."""

from argparse import ArgumentParser
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
try:
    import mindgarden
except ModuleNotFoundError:
    sys.path.insert(0, str(ROOT / "src"))
    import mindgarden

from mindgarden.application.compaction import preview_compaction
from mindgarden.application.curation import apply_curation, build_curation_plan
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import render_context, search_payload
from mindgarden.application.storage import open_vault
from mindgarden.domain.contracts import canonical_json, digest_bytes


def run_demo(workspace):
    if any(path.is_symlink() for path in (workspace, *workspace.parents)) or (workspace.exists() and any(workspace.iterdir())):
        raise ValueError("Synthetic proof requires a new or empty ordinary workspace")
    sys.path.insert(0, str(ROOT))
    from tests.compaction_fixture import FIXTURES, create_fixture
    from tests.support_v1 import write_session

    with patch.dict(os.environ, {}, clear=True), patch("socket.socket", side_effect=AssertionError("Network attempted")), \
            patch("subprocess.run", side_effect=AssertionError("Model/process attempted")):
        fixture = create_fixture(workspace)
        context = fixture["context"]
        vault = open_vault(context.bindings, "synthetic-vault"); original = vault.export_bundle()
        archive = fixture["archive"].read_bytes()
        preview = preview_compaction(context, fixture["plan"], curation=fixture["curation"])
        assert preview == preview_compaction(context, fixture["plan"], curation=fixture["curation"])
        selected = preview["selected"][0]["statements"]
        assert [statement["text"] for statement in selected] == ["Use exact evidence; preserve uncertainty.", "Alternative remains unverified."]
        plan = build_curation_plan(context.bindings, FIXTURES / "curation.json")
        assert apply_curation(plan, plan.digest, context.bindings)
        assert not apply_curation(plan, plan.digest, context.bindings)
        assert original == vault.export_bundle() and archive == fixture["archive"].read_bytes()
        write_session(fixture["session_path"], fixture["configuration"])
        context = QueryContext.load(fixture["configuration"], fixture["session_path"])
        result = next(item for item in search_payload(context, "evidence")["results"] if item["reference"]["id"] == "compacted-prompt")
        profile = {"schema": "mindgarden.context-profile/v1", "id": "compaction-proof", "garden": "synthetic-garden", "title": "Synthetic context",
                   "description": "Authored compacted knowledge", "query": "evidence", "include": [result["reference"]], "exclude": [], "kinds": [],
                   "max_items": 1, "max_bytes": 8192, "max_candidates": 10}
        pack = render_context(context, profile, "json")
        assert len(pack) <= 8192 and json.loads(pack)["included"][0]["reference"] == result["reference"]
        assert "synthetic-malicious-command" not in json.dumps(preview) and b"synthetic-malicious-command" not in pack
        return {"schema": "mindgarden.synthetic-compaction-proof/v1", "status": "passed", "engine_version": mindgarden.__version__,
                "manifest_sha256": digest_bytes(canonical_json(preview["manifest"])), "metrics": preview["metrics"],
                "authored_fixture_facts": {"represented": 2, "expected": 2, "method": "exact-authored-statement-and-source-bindings"},
                "retrieved": result["reference"], "sources": result["sources"], "review_state": result["review"]["state"],
                "context_bytes": len(pack), "context_max_bytes": 8192, "context_sha256": digest_bytes(pack),
                "original_vault_sha256": digest_bytes(original), "originals": "unchanged", "retention": preview["retention"],
                "checks": ["scoped-exact-message-evidence", "uncertainty-contradiction-and-validity-preserved", "deterministic-read-only-preview",
                           "separate-explicit-human-curation", "digest-bound-idempotent-application", "superseded-knowledge-retained",
                           "search-and-bounded-context", "no-source-instruction-execution"],
                "integrations": {"network": "blocked-in-process", "subprocess": "blocked-in-process", "model": "unused", "google": "unused"}}


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--require-source", action="store_true")
    mode.add_argument("--require-installed", action="store_true")
    arguments = parser.parse_args()
    engine = Path(mindgarden.__file__).resolve()
    if arguments.require_source and not engine.is_relative_to(ROOT / "src"):
        parser.error("Source engine from this checkout is required")
    if arguments.require_installed and (engine.is_relative_to(ROOT / "src") or not engine.is_relative_to(Path(sys.prefix).resolve())):
        parser.error("Installed engine in the interpreter prefix is required")
    report = run_demo(arguments.workspace.absolute())
    if report != json.loads((ROOT / "tests/fixtures/compaction/expected-proof.json").read_text()):
        raise AssertionError("Synthetic compaction golden differs")
    if arguments.report:
        with arguments.report.open("xb") as stream: stream.write(canonical_json(report))
    print(canonical_json(report).decode(), end="")


if __name__ == "__main__":
    main()
