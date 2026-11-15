#!/usr/bin/env python3
"""Verify shared synthetic ADR input using explicit, hash-pinned owner sources.

This optional development proof needs requirements/test.txt, never credentials.
Acquire the recorded public owner revisions separately; processing is offline.
"""

from argparse import ArgumentParser
import html
import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/decisions"


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def verify(owner_sources):
    from jsonschema import Draft202012Validator, FormatChecker
    from mindgarden.application.decisions import project_decisions
    from mindgarden.domain.contracts import canonical_json, digest_bytes, read_object

    manifest = read_object(FIXTURES / "owner-inputs.json")
    # Verify executable owner inputs before importing any of them. Physical
    # paths never enter the report or portable projection.
    for name, owner in manifest["owners"].items():
        for relative, expected in owner["files"].items():
            path = owner_sources / name / relative
            if (
                any(item.is_symlink() for item in (path, *path.parents))
                or digest_bytes(path.read_bytes()) != expected
            ):
                raise ValueError("Explicit pinned owner input differs")
    with (
        patch("socket.socket", side_effect=AssertionError("Network attempted")),
        patch(
            "subprocess.Popen", side_effect=AssertionError("External process attempted")
        ),
    ):
        hygiene = module(
            "decision_proof_hygiene", owner_sources / "hygiene/tools/intelligence.py"
        )
        observatory = module(
            "decision_proof_observatory",
            owner_sources / "observatory/src/observatory/intelligence.py",
        )
        relay = module(
            "decision_proof_relay",
            owner_sources
            / "relay/actions/repository-intelligence/scripts/generate_repository_intelligence_site.py",
        )
        projection = read_object(FIXTURES / "relationships-projection.json")
        schema = read_object(
            owner_sources / "hygiene/schemas/repository-intelligence.alpha2.schema.json"
        )
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(
            projection
        )
        vocabulary = read_object(
            owner_sources / "hygiene/catalog/repository-intelligence-vocabulary.json"
        )
        errors = hygiene.validate_snapshot(projection, vocabulary)
        if errors:
            raise ValueError(
                "Synthetic input fails the pinned Hygiene semantic validator"
            )
        snapshot = observatory.build_repository_snapshot(projection)
        assert snapshot == read_object(FIXTURES / "relationships-snapshot.json")
        schema = read_object(
            owner_sources
            / "observatory/schemas/repository-intelligence-read-model.v1.schema.json"
        )
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(snapshot)
        result = project_decisions(
            snapshot,
            represented_commit=snapshot["represented_commit"],
            include_related=True,
        )
        assert result == read_object(FIXTURES / "expected-relationships.json")
        relay.validate_snapshot(
            snapshot,
            snapshot["repository"]["repository"],
            snapshot["represented_commit"],
        )
        rendered = relay.decisions_body(snapshot)
        # Both consumers use the same machine-readable source metadata; no
        # reverse parsing of the rendered page is used to construct knowledge.
        for node in result["nodes"]:
            assert html.escape(node["source"], quote=True) in rendered
        assert "DENIED" not in rendered
    return {
        "schema": "example.decision-owner-proof/v1",
        "status": "passed",
        "network": "blocked-in-process",
        "model": "unused",
        "canonical_adr_bodies": "not-copied",
        "publication": "not-performed",
        "owner_revisions": {
            key: value["revision"] for key, value in manifest["owners"].items()
        },
        "input_sha256": digest_bytes(canonical_json(projection)),
        "snapshot_sha256": digest_bytes(canonical_json(snapshot)),
        "projection_sha256": digest_bytes(canonical_json(result)),
        "decisions": len(result["nodes"]),
        "related_artifacts": len(result["artifacts"]),
        "typed_edges": len(result["edges"]),
        "context_entries": len(result["context"]),
        "limitations": [
            "Synthetic assertions do not establish human approval, whole-repository conformance or actual consumer deployment.",
            "Claims, architecture-component/projection kinds and private authority need their own supported contracts.",
        ],
    }


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--owner-sources", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--require-source", action="store_true")
    mode.add_argument("--require-installed", action="store_true")
    args = parser.parse_args()
    if args.require_source:
        sys.path.insert(0, str(ROOT / "src"))
    import mindgarden

    expected = ROOT / "src" if args.require_source else Path(sys.prefix)
    if not Path(mindgarden.__file__).resolve().is_relative_to(expected.resolve()):
        raise RuntimeError("Requested engine origin is unavailable")
    report = verify(args.owner_sources.absolute())
    content = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()
    if args.report:
        with args.report.open("xb") as output:
            output.write(content)
    print(content.decode(), end="")


if __name__ == "__main__":
    main()
