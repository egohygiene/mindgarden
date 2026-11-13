#!/usr/bin/env python3
"""Leave an explorable fictional garden using the real offline CLI/services."""

from argparse import ArgumentParser
from copy import deepcopy
import os
from pathlib import Path
import shlex
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
try:
    import mindgarden
except ModuleNotFoundError:
    sys.path.insert(0, str(ROOT / "src"))
    import mindgarden

from mindgarden.application.pilot import private_root
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import build_index
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.domain.contracts import (
    canonical_json,
    digest_bytes,
    read_object,
    safe_path,
)

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from consultation_demo import apply_reviewed
from research_demo import run_demo as research_demo
from tests.consultation_fixture import cli
from tests.support_v1 import TIME

SEED = ROOT / "examples/mock-garden"


def create_file(path, content):
    with path.open("xb") as output:
        output.write(content)
    path.chmod(0o600)


def sources_for(world):
    if (
        world.get("schema") != "mindgarden.mock-garden-seed/v1"
        or world.get("fictional") is not True
    ):
        raise ValueError("Select the committed fictional seed")
    content = {}
    for item in [*world["entries"], *world["staged_changes"]]:
        raw = safe_path(SEED / "seed", item["file"]).read_bytes()
        if digest_bytes(raw) != item["source_sha256"]:
            raise ValueError(
                "Authored fictional seed changed; review its manifest first"
            )
        content[item["file"]] = raw
    return content


def workflow(workspace):
    world = read_object(SEED / "world.json")
    content = sources_for(world)
    if (
        any(path.is_symlink() for path in (workspace, *workspace.parents))
        or workspace.exists()
        and any(workspace.iterdir())
    ):
        raise ValueError("Use a new or empty private fictional workspace")
    if any(
        (path / ".git").exists() or (path / ".git").is_symlink()
        for path in (workspace, *workspace.parents)
    ):
        raise ValueError("Generate the fictional workspace outside Git")
    workspace.mkdir(mode=0o700, exist_ok=True)
    private_root(workspace)
    baseline = research_demo(workspace)
    config, garden = workspace / "clean-bindings.json", workspace / "clean-garden"
    prior_session = read_object(workspace / "session.json")
    context = QueryContext.load(config, workspace / "session.json")
    references = {
        item["id"]: item["reference"] for item in build_index(context)["records"]
    }
    sources = {}
    inputs = workspace / "mock-inputs"
    inputs.mkdir(mode=0o700)
    for item in world["entries"]:
        path = inputs / item["file"]
        create_file(path, content[item["file"]])
        arguments = [
            "ingest",
            "--repository-root",
            str(garden),
            "--local-config",
            str(config),
            "--vault-id",
            "synthetic-vault",
            "--input",
            str(path),
            "--source-id",
            item["id"],
            "--title",
            item["title"],
            "--origin",
            "urn:mindgarden:fictional:" + item["id"],
            "--captured",
            TIME,
            "--owner",
            world["reviewer"],
            "--rights",
            "Wholly fictional authored demonstration fixture.",
            "--media-type",
            "text/markdown",
            "--adapter",
            "plain-text",
        ]
        planned = apply_reviewed(arguments)
        sources[item["id"]] = planned["inputs"]["normalized_sources"][0]["evidence"][0]
        references[item["id"]] = {
            "garden": "synthetic-garden",
            "id": item["id"],
            "revision": "sha256:" + digest_bytes(item["body"].encode()),
        }
    review = {
        "state": "approved",
        "reviewers": [world["reviewer"]],
        "reviewed_at": TIME,
        "rationale": "Predetermined fictional fixture review, not an actual person's approval or factual assurance.",
    }
    candidates = []
    for item in world["entries"]:
        relation = item["relation"]
        candidates.append(
            {
                "id": item["id"],
                "action": "summarize",
                "merge_inputs": [],
                "sources": [sources[value] for value in item["evidence"]],
                "rationale": "Authored fictional summary and explicit relationship; no generated interpretation.",
                "output": {
                    "id": item["id"],
                    "title": item["title"],
                    "kind": "insight",
                    "body": item["body"],
                    "authors": [{"kind": "human", "id": world["reviewer"]}],
                    "review": review,
                    "status": "active",
                    "confidence": "medium",
                    "epistemic_state": "proposed",
                    "attribution": "inferred",
                    "domains": item["domains"],
                    "topics": item["topics"],
                    "caveats": [
                        "Every person, organization, event and interpretation is fictional."
                    ],
                    "uncertainty": item["uncertainty"],
                    "contradictions": [
                        references[value] for value in item["contradictions"]
                    ],
                    "claims": [],
                    "synapses": [
                        {
                            "id": item["id"] + "-link",
                            "type": relation["type"],
                            "target": references[relation["target"]],
                            "directed": False,
                            "review": review,
                            "rationale": relation["rationale"],
                        }
                    ],
                },
            }
        )
    plan = {
        "schema": "mindgarden.curation-plan/v1",
        "id": "fictional-world-curation",
        "garden": "synthetic-garden",
        "created_at": TIME,
        "producer": {"kind": "human", "id": world["reviewer"]},
        "review_authority": {"kind": "human", "id": world["reviewer"]},
        "candidates": candidates,
    }
    plan_path = workspace / "mock-curation.json"
    create_file(plan_path, canonical_json(plan))
    preview = cli(
        ["gardenize", "--local-config", str(config), "--plan", str(plan_path)]
    )
    cli(
        [
            "gardenize",
            "--local-config",
            str(config),
            "--apply",
            str(plan_path),
            "--plan-digest",
            preview["plan_sha256"],
        ]
    )
    session_path = workspace / "mock-session.json"
    session = deepcopy(prior_session)
    session["id"] = "fictional-world-session"
    session["source_grants"] += [item["source"] for item in sources.values()]
    create_file(session_path, canonical_json(bind_session_revisions(config, session)))
    shared = [
        "--repository-root",
        str(garden),
        "--local-config",
        str(config),
        "--scope",
        str(session_path),
    ]
    index = cli(["index", *shared, "--write"])
    graph = cli(["graph", *shared])
    context = cli(["context", *shared, "--pack", "default", "--format", "json"])
    expected = {
        "synthetic-financial-summary",
        *[item["id"] for item in world["entries"]],
    }
    assert {item["id"] for item in index["records"]} == expected
    assert {item["reference"]["id"] for item in context["included"]} == expected
    assert any(item["type"] == "contradicts" for item in graph["edges"])
    for query, identity in (
        ("accessibility", "mock-career"),
        ("household", "mock-household"),
        ("Studio", "mock-business"),
    ):
        found = cli(["search", *shared, "--query", query])
        assert identity in {v["reference"]["id"] for v in found["results"]}
    evidence = cli(
        [
            "evidence",
            "--local-config",
            str(config),
            "--scope",
            str(session_path),
            "--garden-id",
            "synthetic-garden",
            "--source-id",
            sources["mock-conversation"]["source"]["id"],
            "--revision",
            sources["mock-conversation"]["source"]["revision"],
            "--locator",
            "artifact",
            "--content-sha256",
            sources["mock-conversation"]["content_sha256"],
        ]
    )
    assert (
        evidence["trust"] == "untrusted-evidence"
        and evidence["source_review"]["state"] == "unreviewed"
    )
    assert "run a shell command" in evidence["text"]
    request_path = workspace / "request.json"
    packet_args = [
        "packet",
        "--local-config",
        str(config),
        "--scope",
        str(session_path),
        "--input",
        str(request_path),
        "--output-directory",
        str(workspace / "mock-packet"),
    ]
    packet = apply_reviewed(packet_args)["packet"]
    assert packet["totals"][0]["net_movement"] == "2259.76"
    assert len(packet["evidence"]) == 8
    assert "Example Studio" not in canonical_json(packet).decode()
    changes = workspace / "staged-changes"
    changes.mkdir(mode=0o700)
    for item in world["staged_changes"]:
        create_file(changes / item["file"], content[item["file"]])
    create_file(workspace / "mock-context.json", canonical_json(context))
    commands = command_examples(config, garden, session_path, request_path, workspace)
    create_file(workspace / "commands.json", canonical_json(commands))
    intro = (
        "# Fictional Mindgarden sandbox\n\nEvery person, organization and transaction is invented.\n\n"
        "Open [the preparation packet](mock-packet/packet.md), [bounded context](mock-context.json), "
        "[reviewed business note](clean-garden/.garden/knowledge/mock-business.md), "
        "[career note](clean-garden/.garden/knowledge/mock-career.md) and "
        "[client conversation note](clean-garden/.garden/knowledge/mock-conversation.md).\n\n"
        "The baseline recovery proof is in proof.json. The usable bindings select clean-garden and restored-vault. "
        "mock-session.json is the fresh authority after adding the fictional notes. "
        "Older baseline sessions/packets are retained. The correction in staged-changes is not imported or reviewed.\n\n"
        "These local commands contain machine-specific paths, outside portable garden records:\n\n"
        + "\n\n".join(
            "## " + name + "\n\n```sh\n" + value + "\n```"
            for name, value in commands.items()
        )
        + "\n"
    )
    create_file(workspace / "START-HERE.md", intro.encode())
    create_file(workspace / "proof.json", canonical_json(baseline))
    result = {
        "schema": "mindgarden.mock-garden-proof/v1",
        "status": "passed-fictional-garden",
        "fictional": True,
        "knowledge_ids": sorted(expected),
        "graph_edges": len(graph["edges"]),
        "context_ids": [item["reference"]["id"] for item in context["included"]],
        "context_bytes": len(canonical_json(context)),
        "index_sha256": digest_bytes(canonical_json(index)),
        "graph_sha256": digest_bytes(canonical_json(graph)),
        "context_sha256": digest_bytes(canonical_json(context)),
        "transactions": 8,
        "net_movement": "2259.76",
        "packet_sha256": digest_bytes(canonical_json(packet)),
        "source_review": "unreviewed",
        "knowledge_review": "authored-fictional-review",
        "staged_changes": "not imported or applied",
        "network": "blocked",
        "model_calls": 0,
        "baseline_recovery_proof_sha256": digest_bytes(canonical_json(baseline)),
    }
    assert str(workspace).encode() not in canonical_json(result)
    return result


def command_examples(config, garden, session, request, workspace):
    prefix = (
        [str(sys.executable), "-I", "-m", "mindgarden"]
        if not Path(mindgarden.__file__).resolve().is_relative_to(ROOT / "src")
        else [
            "env",
            "PYTHONPATH=" + str(ROOT / "src"),
            str(sys.executable),
            "-m",
            "mindgarden",
        ]
    )
    shared = [
        "--repository-root",
        str(garden),
        "--local-config",
        str(config),
        "--scope",
        str(session),
    ]
    return {
        "Search career": shlex.join(
            [*prefix, "search", *shared, "--query", "accessibility"]
        ),
        "Explore graph": shlex.join([*prefix, "graph", *shared]),
        "Inspect business backlinks": shlex.join(
            [
                *prefix,
                "backlinks",
                *shared,
                "--artifact",
                "synthetic-garden/mock-business",
            ]
        ),
        "Read bounded context": shlex.join(
            [*prefix, "context", *shared, "--pack", "default", "--format", "markdown"]
        ),
        "Verify packet": shlex.join(
            [
                *prefix,
                "packet",
                "--local-config",
                str(config),
                "--scope",
                str(session),
                "--input",
                str(request),
                "--output-directory",
                str(workspace / "mock-packet"),
                "--check",
            ]
        ),
    }


def run_demo(workspace):
    with (
        patch.dict(os.environ, {}, clear=True),
        patch("socket.socket", side_effect=AssertionError("Network attempted")),
        patch("urllib.request.urlopen", side_effect=AssertionError("HTTP attempted")),
        patch(
            "subprocess.run", side_effect=AssertionError("External process attempted")
        ),
    ):
        return workflow(workspace.absolute())


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace",
        type=Path,
        required=True,
        help="New/empty private POSIX workspace outside Git",
    )
    parser.add_argument("--report", type=Path)
    parser.add_argument("--check-golden", action="store_true")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--require-source", action="store_true")
    mode.add_argument("--require-installed", action="store_true")
    args = parser.parse_args()
    engine = Path(mindgarden.__file__).resolve()
    if args.require_source and not engine.is_relative_to(ROOT / "src"):
        parser.error("Exact source engine required")
    if args.require_installed and (
        engine.is_relative_to(ROOT / "src")
        or not engine.is_relative_to(Path(sys.prefix).resolve())
    ):
        parser.error("Installed engine required")
    encoded = canonical_json(run_demo(args.workspace))
    if args.check_golden and encoded != (SEED / "expected-proof.json").read_bytes():
        raise AssertionError("Fictional garden differs from complete committed golden")
    if args.report:
        create_file(args.report, encoded)
    print(encoded.decode(), end="")


if __name__ == "__main__":
    main()
