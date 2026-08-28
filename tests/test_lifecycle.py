# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

try:
    from jsonschema import Draft202012Validator, FormatChecker
    from referencing import Registry, Resource
except ModuleNotFoundError:  # pragma: no cover - exercised without test extras
    Draft202012Validator = None  # type: ignore[assignment,misc]
    FormatChecker = None  # type: ignore[assignment,misc]
    Registry = None  # type: ignore[assignment,misc]
    Resource = None  # type: ignore[assignment,misc]

MINDGARDEN_ROOT = Path(__file__).parents[1]
SOURCE_ROOT = MINDGARDEN_ROOT / "src"
FIXTURE_ROOT = MINDGARDEN_ROOT / "tests/fixtures/public-garden"
CONTRACT_ROOT = MINDGARDEN_ROOT / "contracts/v1"

import sys

sys.path.insert(0, str(SOURCE_ROOT))

from mindgarden.application.lifecycle import (  # noqa: E402
    build_init_plan,
    build_migration_plan,
    check_v1_tree,
    GardenIdentity,
    sha256_bytes,
)
from mindgarden.interfaces.cli import ExitCode, main  # noqa: E402


def copy_fixture(destination: Path) -> None:
    """Copy the synthetic v0 consumer without sharing mutable state."""
    shutil.copytree(FIXTURE_ROOT, destination, dirs_exist_ok=True)


def tree_bytes(root: Path) -> dict[str, bytes]:
    """Capture every regular file as an exact relative-byte mapping."""
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


def public_identity() -> GardenIdentity:
    """Return stable explicit initialization inputs."""
    return GardenIdentity(
        garden_id="example-garden",
        title="Example Garden",
        kind="repository",
        visibility="public",
        owners=("egohygiene",),
        canonical_uri="urn:mindgarden:garden:example-garden",
        repository="https://github.com/example/example-garden",
        domains=("software-engineering",),
        topics=("knowledge-systems",),
    )


@unittest.skipUnless(Draft202012Validator, "install requirements/test.txt")
class V1TreeSchemaMixin:
    """Validate lifecycle output against the complete local v1 registry."""

    @classmethod
    def setUpClass(cls) -> None:
        schemas = {
            path.stem.removesuffix(".schema"): json.loads(path.read_text(encoding="utf8"))
            for path in sorted(CONTRACT_ROOT.glob("*.schema.json"))
        }
        resources = [
            (str(schema["$id"]), Resource.from_contents(schema))
            for schema in schemas.values()
        ]
        cls.schemas = schemas
        cls.registry = Registry().with_resources(resources)

    def assert_v1_tree_conforms(self, garden: Path) -> None:
        """Validate every instantiated v1 JSON record in one garden tree."""
        observed = set()
        for path in sorted(garden.rglob("*.json")):
            instance = json.loads(path.read_text(encoding="utf8"))
            discriminator = instance.get("schema")
            if not isinstance(discriminator, str) or not discriminator.endswith("/v1"):
                self.fail(f"missing v1 discriminator: {path}")
            contract = discriminator.removeprefix("mindgarden.").split("/")[0]
            observed.add(contract)
            Draft202012Validator(
                self.schemas[contract],
                registry=self.registry,
                format_checker=FormatChecker(),
            ).validate(instance)
        self.assertIn("garden", observed)


class InitializationTests(V1TreeSchemaMixin, unittest.TestCase):
    def test_init_plan_is_deterministic_complete_and_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            plan = build_init_plan(public_identity())
            first = plan.document()
            second = build_init_plan(public_identity()).document()

            self.assertEqual(first, second)
            self.assertEqual(first["operation"], "init")
            self.assertEqual(len(first["plan_sha256"]), 64)
            self.assertFalse((repository / ".garden").exists())
            self.assertEqual(
                {item["path"] for item in first["files"]},
                {planned.path for planned in plan.files},
            )
            self.assertNotIn(str(repository), json.dumps(first))

            baseline_paths = {planned.path for planned in plan.files}
            for kind, visibility in (
                ("repository", "public"),
                ("personal", "private"),
                ("organization", "internal"),
            ):
                identity = replace(
                    public_identity(),
                    kind=kind,
                    visibility=visibility,
                )
                configured = build_init_plan(identity)
                manifest_file = next(
                    value
                    for value in configured.files
                    if value.path == ".garden/garden.json"
                )
                manifest = json.loads(manifest_file.content)
                self.assertEqual(manifest["kind"], kind)
                self.assertEqual(manifest["visibility"], visibility)
                self.assertEqual(
                    {planned.path for planned in configured.files},
                    baseline_paths,
                )

    def test_init_apply_check_and_rerun_are_safe(self) -> None:
        plan = build_init_plan(public_identity())
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            arguments = [
                "init",
                "--repository-root",
                str(repository),
                "--visibility",
                "public",
                "--garden-id",
                "example-garden",
                "--title",
                "Example Garden",
                "--kind",
                "repository",
                "--owner",
                "egohygiene",
                "--canonical-uri",
                "urn:mindgarden:garden:example-garden",
                "--repository-uri",
                "https://github.com/example/example-garden",
                "--domain",
                "software-engineering",
                "--topic",
                "knowledge-systems",
                "--apply",
                "--plan-digest",
                plan.digest,
            ]
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(arguments), ExitCode.SUCCESS)
            self.assertIn("initialization applied", output.getvalue())
            self.assertFalse((repository / ".garden.local").exists())
            self.assertEqual(check_v1_tree(repository / ".garden"), 0)
            self.assert_v1_tree_conforms(repository / ".garden")

            templates = "\n".join(
                path.read_text(encoding="utf8")
                for path in sorted((repository / ".garden/templates").glob("*.md"))
            )
            for role in ("sources/", "knowledge/", "synapses/", "publishing/"):
                self.assertIn(role, templates)
            self.assertIn("never the taxonomy", templates)

            before = tree_bytes(repository / ".garden")
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(arguments), ExitCode.SUCCESS)
            self.assertIn("already current", output.getvalue())
            self.assertEqual(tree_bytes(repository / ".garden"), before)

            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(
                    main(["init", "--repository-root", str(repository), "--check"]),
                    ExitCode.SUCCESS,
                )
            self.assertIn("initialization check passed", output.getvalue())

    def test_init_refuses_wrong_digest_conflict_traversal_and_symlink(self) -> None:
        plan = build_init_plan(public_identity())
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            base = [
                "init",
                "--repository-root",
                str(repository),
                "--visibility",
                "public",
                "--garden-id",
                "example-garden",
                "--title",
                "Example Garden",
                "--owner",
                "egohygiene",
                "--canonical-uri",
                "urn:mindgarden:garden:example-garden",
                "--repository-uri",
                "https://github.com/example/example-garden",
                "--domain",
                "software-engineering",
                "--topic",
                "knowledge-systems",
                "--apply",
            ]
            with redirect_stderr(io.StringIO()):
                self.assertEqual(
                    main([*base, "--plan-digest", "0" * 64]),
                    ExitCode.CONTRACT,
                )
            self.assertFalse((repository / ".garden").exists())

            with redirect_stderr(io.StringIO()):
                self.assertEqual(
                    main(
                        [
                            "init",
                            "--repository-root",
                            str(repository),
                            "--visibility",
                            "public",
                            "--garden-id",
                            "../escape",
                        ]
                    ),
                    ExitCode.CONTRACT,
                )
            self.assertFalse((repository.parent / "escape").exists())

            (repository / ".garden").mkdir()
            (repository / ".garden/garden.json").write_text("conflict\n", encoding="utf8")
            before = tree_bytes(repository)
            with redirect_stderr(io.StringIO()):
                self.assertEqual(
                    main([*base, "--plan-digest", plan.digest]),
                    ExitCode.CONTRACT,
                )
            self.assertEqual(tree_bytes(repository), before)

        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            outside = repository / "outside"
            outside.mkdir()
            (repository / ".garden").symlink_to(outside, target_is_directory=True)
            with redirect_stderr(io.StringIO()):
                self.assertEqual(
                    main(
                        [
                            "init",
                            "--repository-root",
                            str(repository),
                            "--visibility",
                            "public",
                            "--garden-id",
                            "example-garden",
                            "--apply",
                            "--plan-digest",
                            plan.digest,
                        ]
                    ),
                    ExitCode.CONTRACT,
                )
            self.assertEqual(list(outside.iterdir()), [])


class MigrationTests(V1TreeSchemaMixin, unittest.TestCase):
    def test_v0_plan_apply_check_and_rerun_preserve_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            copy_fixture(repository)
            canonical = repository / ".garden"
            original = tree_bytes(canonical)
            plan = build_migration_plan(repository, ["software-engineering"], [])
            self.assertEqual(
                plan.document(),
                build_migration_plan(repository, ["software-engineering"], []).document(),
            )
            self.assertEqual(tree_bytes(canonical), original)

            with redirect_stderr(io.StringIO()):
                self.assertEqual(
                    main(
                        [
                            "migrate",
                            "--repository-root",
                            str(repository),
                            "--apply",
                            "--domain",
                            "software-engineering",
                            "--plan-digest",
                            "0" * 64,
                        ]
                    ),
                    ExitCode.CONTRACT,
                )
            self.assertEqual(tree_bytes(canonical), original)
            self.assertFalse((repository / ".garden.v0").exists())

            arguments = [
                "migrate",
                "--repository-root",
                str(repository),
                "--apply",
                "--domain",
                "software-engineering",
                "--plan-digest",
                plan.digest,
            ]
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(arguments), ExitCode.SUCCESS)
            self.assertIn("migration applied", output.getvalue())
            self.assertEqual(tree_bytes(repository / ".garden.v0"), original)
            self.assertEqual(check_v1_tree(canonical), 3)
            self.assert_v1_tree_conforms(canonical)

            for source in (
                "home.md",
                "concepts/architecture.md",
                "concepts/draft.md",
            ):
                metadata = json.loads(
                    (
                        canonical
                        / "knowledge"
                        / f"{parse_v0_identifier(repository / '.garden.v0' / source)}.json"
                    ).read_text(encoding="utf8")
                )
                migrated = canonical / metadata["content"]["path"]
                self.assertEqual(
                    migrated.read_bytes(),
                    (repository / ".garden.v0" / source).read_bytes(),
                )
                if metadata["x-v0-reviewed"]:
                    self.assertEqual(metadata["review"]["state"], "in-review")
                    self.assertEqual(metadata["review"]["reviewers"], [])

            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(
                    main(["migrate", "--repository-root", str(repository), "--check"]),
                    ExitCode.SUCCESS,
                )
            self.assertIn("migration check passed", output.getvalue())

            before = tree_bytes(canonical)
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(arguments), ExitCode.SUCCESS)
            self.assertIn("already current", output.getvalue())
            self.assertEqual(tree_bytes(canonical), before)

    def test_failed_migration_leaves_canonical_v0_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            copy_fixture(repository)
            plan = build_migration_plan(repository, [], [])
            canonical = repository / ".garden"
            before = tree_bytes(canonical)
            (repository / ".garden.v0").write_text("conflict\n", encoding="utf8")

            with redirect_stderr(io.StringIO()) as error:
                result = main(
                    [
                        "migrate",
                        "--repository-root",
                        str(repository),
                        "--apply",
                        "--plan-digest",
                        plan.digest,
                    ]
                )
            self.assertEqual(result, ExitCode.CONTRACT)
            self.assertIn("conflicting migration backup", error.getvalue())
            self.assertEqual(tree_bytes(canonical), before)

    def test_migration_refuses_symlinks_before_planning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            copy_fixture(repository)
            canonical = repository / ".garden"
            before = tree_bytes(canonical)
            (canonical / "unsafe-link").symlink_to(repository / "README.md")

            with redirect_stderr(io.StringIO()) as error:
                result = main(
                    [
                        "migrate",
                        "--repository-root",
                        str(repository),
                        "--plan",
                    ]
                )
            self.assertEqual(result, ExitCode.CONTRACT)
            self.assertIn("symlink", error.getvalue())
            self.assertEqual(tree_bytes(canonical), before)

    def test_failed_atomic_cutover_restores_the_v0_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            copy_fixture(repository)
            plan = build_migration_plan(repository, [], [])
            canonical = repository / ".garden"
            before = tree_bytes(canonical)
            real_replace = os.replace
            calls = 0

            def fail_second_replace(source: Path, destination: Path) -> None:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("synthetic cutover failure")
                real_replace(source, destination)

            with (
                patch(
                    "mindgarden.application.lifecycle.os.replace",
                    side_effect=fail_second_replace,
                ),
                redirect_stderr(io.StringIO()) as error,
            ):
                result = main(
                    [
                        "migrate",
                        "--repository-root",
                        str(repository),
                        "--apply",
                        "--plan-digest",
                        plan.digest,
                    ]
                )

            self.assertEqual(result, ExitCode.IO)
            self.assertIn("synthetic cutover failure", error.getvalue())
            self.assertEqual(tree_bytes(canonical), before)
            self.assertFalse((repository / ".garden.v0").exists())

    def test_v0_source_becomes_source_not_durable_knowledge(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            copy_fixture(repository)
            garden = repository / ".garden"
            manifest = garden / "garden.yaml"
            manifest.write_text(
                manifest.read_text(encoding="utf8").replace(
                    "  - concepts\n",
                    "  - concepts\n  - sources\n",
                ),
                encoding="utf8",
            )
            sources = garden / "sources"
            sources.mkdir()
            source_note = """---
schema: mindgarden.note/v0
id: captured-source
title: Captured source
kind: source
status: proposed
reviewed: false
confidence: uncertain
visibility: public
owners:
  - egohygiene
created: 2026-08-28
updated: 2026-08-28
sources:
  - urn:example:captured-source
related: []
supersedes: []
tags:
  - evidence
---

# Captured source

## Captured content

Exact evidence.\n"""
            artifact = sources / "captured-source.md"
            artifact.write_text(source_note, encoding="utf8")
            captured_content = "Exact evidence.\n"
            provenance = {
                "schema": "mindgarden.provenance/v0",
                "id": "provenance-captured-source",
                "noteId": "captured-source",
                "artifact": "sources/captured-source.md",
                "origin": "urn:example:captured-source",
                "mediaType": "text/markdown",
                "captured": "2026-08-28",
                "contentSha256": sha256_bytes(captured_content.encode("utf8")),
                "artifactSha256": sha256_bytes(source_note.encode("utf8")),
                "transformations": ["decode-utf8"],
                "generator": "mindgarden.ingest/v0",
                "rights": "Synthetic test evidence",
            }
            (garden / "provenance/provenance-captured-source.json").write_text(
                json.dumps(provenance, indent=2, sort_keys=True) + "\n",
                encoding="utf8",
            )

            plan = build_migration_plan(repository, [], [])
            with redirect_stdout(io.StringIO()):
                self.assertEqual(
                    main(
                        [
                            "migrate",
                            "--repository-root",
                            str(repository),
                            "--apply",
                            "--plan-digest",
                            plan.digest,
                        ]
                    ),
                    ExitCode.SUCCESS,
                )
            self.assertTrue((garden / "sources/captured-source.json").is_file())
            self.assertFalse((garden / "knowledge/captured-source.json").exists())
            self.assertEqual(
                (garden / "sources/captured-source.md").read_text(encoding="utf8"),
                source_note,
            )
            self.assert_v1_tree_conforms(garden)


def parse_v0_identifier(path: Path) -> str:
    """Read the stable id from a synthetic v0 note frontmatter."""
    for line in path.read_text(encoding="utf8").splitlines():
        if line.startswith("id: "):
            return line.removeprefix("id: ")
    raise AssertionError(f"missing id: {path}")


if __name__ == "__main__":
    unittest.main()
