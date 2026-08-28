# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT
# pylint: disable=wrong-import-position
# ruff: noqa: PLR0913, PT027

from __future__ import annotations

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import textwrap
import unittest

MINDGARDEN_ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(MINDGARDEN_ROOT))

from scripts.validate_garden import ContractError, validate_repository  # noqa: E402

MANIFEST = """
schema: mindgarden.garden/v0
id: example-repository
title: Example Garden
version: 0.1.0
status: incubating
owners:
  - egohygiene
repository: https://github.com/egohygiene/example
visibility: public
entrypoint: home.md
content_roots:
  - home.md
  - concepts
generated_roots:
  - .index
provenance_root: provenance
context_pack_root: context-packs
private_overlay: ../.garden.local
"""


def note(
    note_id: str,
    *,
    status: str = "reviewed",
    reviewed: str = "true",
    visibility: str = "public",
    sources: list[str] | None = None,
    related: list[str] | None = None,
) -> str:
    lines = [
        "---",
        "schema: mindgarden.note/v0",
        f"id: {note_id}",
        "title: Example note",
        "kind: note",
        f"status: {status}",
        f"reviewed: {reviewed}",
        "confidence: high",
        f"visibility: {visibility}",
        "owners:",
        "  - egohygiene",
        "created: 2026-08-13",
        "updated: 2026-08-13",
    ]
    if sources:
        lines.append("sources:")
        lines.extend(f"  - {value}" for value in sources)
    else:
        lines.append("sources: []")
    if related:
        lines.append("related:")
        lines.extend(f"  - {value}" for value in related)
    else:
        lines.append("related: []")
    lines.extend(["supersedes: []", "---", "", "# Example note", ""])
    return "\n".join(lines)


class GardenFixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.garden = root / ".garden"
        self.garden.mkdir()
        (self.garden / "concepts").mkdir()
        (self.garden / "provenance").mkdir()
        (self.garden / "context-packs").mkdir()
        (self.garden / "garden.yaml").write_text(
            textwrap.dedent(MANIFEST).lstrip(),
            encoding="utf8",
        )
        (root / "README.md").write_text("# Example\n", encoding="utf8")
        (self.garden / "home.md").write_text(
            note("example-home", sources=["../README.md"]),
            encoding="utf8",
        )


class MindgardenContractTests(unittest.TestCase):
    def test_contract_schemas_are_valid_json(self) -> None:
        for schema_path in (MINDGARDEN_ROOT / "contracts").glob("*.schema.json"):
            schema = json.loads(schema_path.read_text(encoding="utf8"))
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_valid_public_repository_passes(self) -> None:
        with TemporaryDirectory() as directory:
            fixture = GardenFixture(Path(directory))
            self.assertEqual(validate_repository(fixture.root), 1)

    def test_public_repository_rejects_private_note(self) -> None:
        with TemporaryDirectory() as directory:
            fixture = GardenFixture(Path(directory))
            (fixture.garden / "home.md").write_text(
                note("example-home", visibility="private"),
                encoding="utf8",
            )
            with self.assertRaisesRegex(ContractError, "public garden cannot commit private"):
                validate_repository(fixture.root)

    def test_proposed_note_cannot_claim_human_review(self) -> None:
        with TemporaryDirectory() as directory:
            fixture = GardenFixture(Path(directory))
            (fixture.garden / "home.md").write_text(
                note("example-home", status="proposed", reviewed="true"),
                encoding="utf8",
            )
            with self.assertRaisesRegex(ContractError, "cannot be reviewed"):
                validate_repository(fixture.root)

    def test_duplicate_note_identifier_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            fixture = GardenFixture(Path(directory))
            (fixture.garden / "concepts/duplicate.md").write_text(
                note("example-home"),
                encoding="utf8",
            )
            with self.assertRaisesRegex(ContractError, "duplicate note id"):
                validate_repository(fixture.root)

    def test_dangling_relationship_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            fixture = GardenFixture(Path(directory))
            (fixture.garden / "home.md").write_text(
                note("example-home", related=["missing-note"]),
                encoding="utf8",
            )
            with self.assertRaisesRegex(ContractError, "dangling related"):
                validate_repository(fixture.root)

    def test_missing_local_source_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            fixture = GardenFixture(Path(directory))
            (fixture.garden / "home.md").write_text(
                note("example-home", sources=["../missing.md"]),
                encoding="utf8",
            )
            with self.assertRaisesRegex(ContractError, "source does not resolve"):
                validate_repository(fixture.root)

    def test_private_overlay_must_be_external(self) -> None:
        with TemporaryDirectory() as directory:
            fixture = GardenFixture(Path(directory))
            manifest = (fixture.garden / "garden.yaml").read_text(encoding="utf8")
            (fixture.garden / "garden.yaml").write_text(
                manifest.replace("../.garden.local", "private"),
                encoding="utf8",
            )
            with self.assertRaisesRegex(ContractError, "must live outside"):
                validate_repository(fixture.root)


if __name__ == "__main__":
    unittest.main()
