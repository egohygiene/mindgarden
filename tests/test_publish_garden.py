# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT
# pylint: disable=wrong-import-position
# ruff: noqa: PT027

from __future__ import annotations

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import textwrap
import unittest

MINDGARDEN_ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(MINDGARDEN_ROOT))

from scripts.publish_garden import (  # noqa: E402
    ContractError,
    project_garden,
    projection_digests,
    verify_projection,
)

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
  - projects
generated_roots:
  - .index
provenance_root: provenance
context_pack_root: context-packs
private_overlay: ../.garden.local
"""

PROFILE = """
schema: mindgarden.publish-profile/v0
id: example-quartz-pages
adapter: quartz-v5
garden_root: .garden
entrypoint: home.md
repository: https://github.com/egohygiene/example
repository_ref: main
base_url: egohygiene.github.io/example
quartz_repository: https://github.com/jackyzha0/quartz.git
quartz_commit: 075afd3f712da0088a07f5284a7b3aba37dd61b6
node_major: 24
statuses:
  - reviewed
visibilities:
  - public
"""


def note(  # noqa: PLR0913
    note_id: str,
    *,
    title: str = "Example note",
    status: str = "reviewed",
    reviewed: str = "true",
    body: str = "Example body.",
    related: list[str] | None = None,
) -> str:
    lines = [
        "---",
        "schema: mindgarden.note/v0",
        f"id: {note_id}",
        f"title: {title}",
        "kind: note",
        f"status: {status}",
        f"reviewed: {reviewed}",
        "confidence: high",
        "visibility: public",
        "owners:",
        "  - egohygiene",
        "created: 2026-08-14",
        "updated: 2026-08-14",
        "sources: []",
    ]
    if related:
        lines.append("related:")
        lines.extend(f"  - {value}" for value in related)
    else:
        lines.append("related: []")
    lines.extend(["supersedes: []", "---", "", f"# {title}", "", body, ""])
    return "\n".join(lines)


class PublishFixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.garden = root / ".garden"
        self.profile = root / "mindgarden/profiles/quartz/profile.yaml"
        for directory in (
            self.garden / "concepts",
            self.garden / "projects",
            self.garden / "provenance",
            self.garden / "context-packs",
            self.garden / "views",
            self.profile.parent,
        ):
            directory.mkdir(parents=True, exist_ok=True)
        (self.garden / "garden.yaml").write_text(
            textwrap.dedent(MANIFEST).lstrip(), encoding="utf8"
        )
        self.profile.write_text(textwrap.dedent(PROFILE).lstrip(), encoding="utf8")
        (root / "README.md").write_text("# Example repository\n", encoding="utf8")
        (self.garden / "views/knowledge.base").write_text("views: []\n", encoding="utf8")
        (self.garden / "home.md").write_text(
            note(
                "example-home",
                title="Example Garden",
                body=(
                    "[[concepts/reviewed|Reviewed note]]\n\n"
                    "[Repository](../README.md)\n\n"
                    "![[views/knowledge.base#Knowledge]]"
                ),
                related=["example-reviewed"],
            ),
            encoding="utf8",
        )
        (self.garden / "concepts/reviewed.md").write_text(
            note("example-reviewed", title="Reviewed note", related=["example-home"]),
            encoding="utf8",
        )
        (self.garden / "concepts/draft.md").write_text(
            note(
                "example-draft",
                title="Draft note",
                status="draft",
                reviewed="false",
            ),
            encoding="utf8",
        )
        (self.garden / "projects/README.md").write_text(
            note("example-projects", title="Projects"), encoding="utf8"
        )


class MindgardenPublishingTests(unittest.TestCase):
    def test_projection_is_deterministic_and_fail_closed(self) -> None:
        with TemporaryDirectory() as directory:
            fixture = PublishFixture(Path(directory))
            first = fixture.root / "first"
            second = fixture.root / "second"

            first_paths = project_garden(fixture.root, first)
            second_paths = project_garden(fixture.root, second)

            self.assertEqual(first_paths, second_paths)
            self.assertEqual(projection_digests(first), projection_digests(second))
            self.assertEqual(
                [path.as_posix() for path in first_paths],
                ["concepts/reviewed.md", "index.md", "projects/index.md"],
            )
            self.assertFalse((first / "concepts/draft.md").exists())
            self.assertFalse((first / "provenance").exists())
            self.assertFalse((first / "context-packs").exists())
            self.assertFalse((first / "views").exists())

    def test_projection_rewrites_repository_links_and_vault_only_bases(self) -> None:
        with TemporaryDirectory() as directory:
            fixture = PublishFixture(Path(directory))
            output = fixture.root / "output"
            project_garden(fixture.root, output)
            home = (output / "index.md").read_text(encoding="utf8")

            self.assertIn("publish: true", home)
            self.assertIn("draft: false", home)
            self.assertIn("[[concepts/reviewed|Reviewed note]]", home)
            self.assertIn("https://github.com/egohygiene/example/blob/main/README.md", home)
            self.assertIn("Vault-only view", home)
            self.assertNotIn("knowledge.base", home)

    def test_link_to_excluded_note_fails_instead_of_leaking(self) -> None:
        with TemporaryDirectory() as directory:
            fixture = PublishFixture(Path(directory))
            home_path = fixture.garden / "home.md"
            home_path.write_text(
                note(
                    "example-home",
                    title="Example Garden",
                    body="[[concepts/draft|Do not publish]]",
                    related=["example-reviewed"],
                ),
                encoding="utf8",
            )
            with self.assertRaisesRegex(ContractError, "links to excluded note"):
                project_garden(fixture.root, fixture.root / "output")

    def test_unowned_output_directory_is_never_replaced(self) -> None:
        with TemporaryDirectory() as directory:
            fixture = PublishFixture(Path(directory))
            output = fixture.root / "output"
            output.mkdir()
            (output / "keep.txt").write_text("user material\n", encoding="utf8")

            with self.assertRaisesRegex(ContractError, "refusing to replace unowned"):
                project_garden(fixture.root, output)
            self.assertEqual((output / "keep.txt").read_text(encoding="utf8"), "user material\n")

    def test_projection_never_writes_inside_the_canonical_garden(self) -> None:
        with TemporaryDirectory() as directory:
            fixture = PublishFixture(Path(directory))
            with self.assertRaisesRegex(ContractError, "outside the canonical garden"):
                project_garden(fixture.root, fixture.garden / "generated-site")

    def test_profile_rejects_a_floating_quartz_reference(self) -> None:
        with TemporaryDirectory() as directory:
            fixture = PublishFixture(Path(directory))
            fixture.profile.write_text(
                fixture.profile.read_text(encoding="utf8").replace(
                    "075afd3f712da0088a07f5284a7b3aba37dd61b6", "v5"
                ),
                encoding="utf8",
            )
            with self.assertRaisesRegex(ContractError, "full commit SHA"):
                project_garden(fixture.root, fixture.root / "output")

    def test_verify_builds_the_projection_twice(self) -> None:
        with TemporaryDirectory() as directory:
            fixture = PublishFixture(Path(directory))
            self.assertEqual(
                verify_projection(fixture.root, Path("mindgarden/profiles/quartz/profile.yaml")),
                3,
            )


if __name__ == "__main__":
    unittest.main()
