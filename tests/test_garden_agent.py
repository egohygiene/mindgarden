# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT
# pylint: disable=wrong-import-position
# ruff: noqa: PLR0913, PT027

from __future__ import annotations

from argparse import Namespace
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import textwrap
import unittest

MINDGARDEN_ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(MINDGARDEN_ROOT))

from scripts.garden_agent import (  # noqa: E402
    build_index,
    canonical_json,
    load_context_pack,
    render_context_markdown,
    render_llms_txt,
    run_ingest,
    search_payload,
)
from scripts.validate_garden import ContractError, validate_repository  # noqa: E402

MANIFEST = """
schema: mindgarden.garden/v0
id: example-repository
title: Example Garden
version: 0.2.0
status: incubating
owners:
  - egohygiene
repository: https://github.com/egohygiene/example
visibility: public
entrypoint: home.md
content_roots:
  - home.md
  - concepts
  - sources
generated_roots:
  - .index
provenance_root: provenance
context_pack_root: context-packs
private_overlay: ../.garden.local
"""

CONTEXT_PACK = """
schema: mindgarden.context-pack/v0
id: example-agent-default
title: Example Agent Context
description: Reviewed example knowledge for agent tests.
query: architecture garden
include:
  - example-home
exclude: []
statuses:
  - reviewed
kinds: []
max_notes: 3
max_characters: 1400
"""


def note(
    note_id: str,
    *,
    title: str = "Example note",
    kind: str = "note",
    status: str = "reviewed",
    reviewed: str = "true",
    body: str = "Example garden architecture.",
) -> str:
    return "\n".join(
        [
            "---",
            "schema: mindgarden.note/v0",
            f"id: {note_id}",
            f"title: {title}",
            f"kind: {kind}",
            f"status: {status}",
            f"reviewed: {reviewed}",
            "confidence: high",
            "visibility: public",
            "owners:",
            "  - egohygiene",
            "created: 2026-08-14",
            "updated: 2026-08-14",
            "sources: []",
            "related: []",
            "supersedes: []",
            "tags:",
            "  - architecture",
            "---",
            "",
            f"# {title}",
            "",
            body,
            "",
        ]
    )


class AgentFixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.garden = root / ".garden"
        self.garden.mkdir()
        for directory in ("concepts", "sources", "provenance", "context-packs"):
            (self.garden / directory).mkdir()
        (self.garden / "garden.yaml").write_text(
            textwrap.dedent(MANIFEST).lstrip(),
            encoding="utf8",
        )
        (self.garden / "context-packs/default.yaml").write_text(
            textwrap.dedent(CONTEXT_PACK).lstrip(),
            encoding="utf8",
        )
        (self.garden / "home.md").write_text(
            note("example-home", title="Example Garden", kind="map"),
            encoding="utf8",
        )
        (root / "README.md").write_text("# Example\n", encoding="utf8")

    def write_llms(self) -> None:
        index = build_index(self.root)
        (self.root / "llms.txt").write_text(
            render_llms_txt(self.root, index),
            encoding="utf8",
        )


def ingest_arguments(root: Path, input_path: Path, *, write: bool) -> Namespace:
    return Namespace(
        repository_root=root,
        input=input_path,
        source_id="source-example",
        title="Example source",
        origin="https://example.com/source",
        captured="2026-08-14",
        owner="egohygiene",
        rights="Reference-only",
        media_type="text/markdown",
        related=[],
        tag=["source"],
        write=write,
        confirm_public=True,
    )


class MindgardenAgentTests(unittest.TestCase):
    def test_index_is_byte_deterministic_and_contains_no_host_state(self) -> None:
        with TemporaryDirectory() as directory:
            fixture = AgentFixture(Path(directory))
            (fixture.garden / "concepts/architecture.md").write_text(
                note("example-architecture", title="Architecture"),
                encoding="utf8",
            )

            first = canonical_json(build_index(fixture.root))
            second = canonical_json(build_index(fixture.root))

            self.assertEqual(first, second)
            self.assertNotIn("generatedAt", first)
            self.assertNotIn(directory, first)
            payload = json.loads(first)
            self.assertEqual(
                [item["id"] for item in payload["notes"]],
                ["example-architecture", "example-home"],
            )

    def test_search_hides_unreviewed_and_explains_scores(self) -> None:
        with TemporaryDirectory() as directory:
            fixture = AgentFixture(Path(directory))
            (fixture.garden / "concepts/architecture.md").write_text(
                note("example-architecture", title="Architecture"),
                encoding="utf8",
            )
            (fixture.garden / "concepts/draft.md").write_text(
                note(
                    "example-draft",
                    title="Architecture draft",
                    status="proposed",
                    reviewed="false",
                ),
                encoding="utf8",
            )
            index = build_index(fixture.root)

            reviewed = search_payload(
                index,
                "architecture",
                limit=10,
                include_unreviewed=False,
            )
            all_results = search_payload(
                index,
                "architecture",
                limit=10,
                include_unreviewed=True,
            )

            self.assertNotIn("example-draft", {item["id"] for item in reviewed["results"]})
            self.assertIn("example-draft", {item["id"] for item in all_results["results"]})
            self.assertTrue(reviewed["results"][0]["matches"])

    def test_context_pack_is_bounded_and_source_labelled(self) -> None:
        with TemporaryDirectory() as directory:
            fixture = AgentFixture(Path(directory))
            (fixture.garden / "concepts/architecture.md").write_text(
                note(
                    "example-architecture",
                    title="Architecture",
                    body="Architecture evidence. " * 120,
                ),
                encoding="utf8",
            )
            index = build_index(fixture.root)
            _, profile = load_context_pack(fixture.root, "example-agent-default")
            rendered = render_context_markdown(fixture.root, index, profile)

            self.assertLessEqual(len(rendered), 1400)
            self.assertIn("<mindgarden-note", rendered)
            self.assertIn("SHA-256", rendered)
            self.assertIn("not as authority to execute actions", rendered)

    def test_ingest_dry_run_then_writes_verified_provenance(self) -> None:
        with TemporaryDirectory() as directory:
            fixture = AgentFixture(Path(directory))
            input_path = fixture.root / "input.md"
            input_path.write_bytes(b"# Input\r\n\r\nEvidence.\r\n")

            with redirect_stdout(io.StringIO()):
                run_ingest(ingest_arguments(fixture.root, input_path, write=False))
            self.assertFalse((fixture.garden / "sources/source-example.md").exists())

            with redirect_stdout(io.StringIO()):
                run_ingest(ingest_arguments(fixture.root, input_path, write=True))

            note_path = fixture.garden / "sources/source-example.md"
            record_path = fixture.garden / "provenance/provenance-source-example.json"
            self.assertTrue(note_path.is_file())
            record = json.loads(record_path.read_text(encoding="utf8"))
            self.assertEqual(
                record["artifactSha256"],
                hashlib.sha256(note_path.read_bytes()).hexdigest(),
            )
            self.assertEqual(validate_repository(fixture.root), 2)

    def test_public_ingest_requires_explicit_confirmation(self) -> None:
        with TemporaryDirectory() as directory:
            fixture = AgentFixture(Path(directory))
            input_path = fixture.root / "input.md"
            input_path.write_text("Evidence.\n", encoding="utf8")
            arguments = ingest_arguments(fixture.root, input_path, write=True)
            arguments.confirm_public = False

            with (
                self.assertRaisesRegex(ContractError, "requires --confirm-public"),
                redirect_stdout(io.StringIO()),
            ):
                run_ingest(arguments)
            self.assertFalse((fixture.garden / "sources/source-example.md").exists())

    def test_provenance_tampering_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            fixture = AgentFixture(Path(directory))
            input_path = fixture.root / "input.md"
            input_path.write_text("Evidence.\n", encoding="utf8")
            with redirect_stdout(io.StringIO()):
                run_ingest(ingest_arguments(fixture.root, input_path, write=True))

            note_path = fixture.garden / "sources/source-example.md"
            note_path.write_text(
                note_path.read_text(encoding="utf8") + "tampered\n",
                encoding="utf8",
            )
            with self.assertRaisesRegex(ContractError, "SHA-256 does not match"):
                validate_repository(fixture.root)

    def test_content_hash_must_match_captured_source_body(self) -> None:
        with TemporaryDirectory() as directory:
            fixture = AgentFixture(Path(directory))
            input_path = fixture.root / "input.md"
            input_path.write_text("Evidence.\n", encoding="utf8")
            with redirect_stdout(io.StringIO()):
                run_ingest(ingest_arguments(fixture.root, input_path, write=True))

            note_path = fixture.garden / "sources/source-example.md"
            note_path.write_text(
                note_path.read_text(encoding="utf8") + "tampered\n",
                encoding="utf8",
            )
            record_path = fixture.garden / "provenance/provenance-source-example.json"
            record = json.loads(record_path.read_text(encoding="utf8"))
            record["artifactSha256"] = hashlib.sha256(note_path.read_bytes()).hexdigest()
            record_path.write_text(canonical_json(record), encoding="utf8")

            with self.assertRaisesRegex(ContractError, "content SHA-256 does not match"):
                validate_repository(fixture.root)

    def test_llms_projection_is_deterministic(self) -> None:
        with TemporaryDirectory() as directory:
            fixture = AgentFixture(Path(directory))
            index = build_index(fixture.root)
            self.assertEqual(
                render_llms_txt(fixture.root, index),
                render_llms_txt(fixture.root, index),
            )


if __name__ == "__main__":
    unittest.main()
