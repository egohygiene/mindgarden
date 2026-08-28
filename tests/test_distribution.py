# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

from __future__ import annotations

from email.parser import Parser
from pathlib import Path
import tarfile
import unittest
from zipfile import ZipFile

MINDGARDEN_ROOT = Path(__file__).parents[1]
DIST_ROOT = MINDGARDEN_ROOT / ".cache/dist"


@unittest.skipUnless(DIST_ROOT.is_dir(), "distribution artifacts have not been built")
class DistributionTests(unittest.TestCase):
    def test_wheel_contains_code_resources_and_dependency_free_metadata(self) -> None:
        wheel_path = next(DIST_ROOT.glob("mindgarden-0.1.0-*.whl"))
        with ZipFile(wheel_path) as wheel:
            names = set(wheel.namelist())
            metadata_name = next(
                name for name in names if name.endswith(".dist-info/METADATA")
            )
            metadata = Parser().parsestr(wheel.read(metadata_name).decode("utf8"))

        for expected in (
            "mindgarden/__init__.py",
            "mindgarden/__main__.py",
            "mindgarden/domain/validation.py",
            "mindgarden/application/agent.py",
            "mindgarden/application/lifecycle.py",
            "mindgarden/adapters/publishing.py",
            "mindgarden/adapters/quartz.py",
            "mindgarden/interfaces/cli.py",
            "mindgarden-0.1.0.data/data/share/mindgarden/contracts/garden.schema.json",
            "mindgarden-0.1.0.data/data/share/mindgarden/contracts/v1/knowledge.schema.json",
            "mindgarden-0.1.0.data/data/share/mindgarden/profiles/quartz/profile.yaml",
            "mindgarden-0.1.0.data/data/share/mindgarden/templates/note.md",
        ):
            self.assertIn(expected, names)

        self.assertEqual(metadata["Name"], "mindgarden")
        self.assertEqual(metadata["Version"], "0.1.0")
        self.assertEqual(metadata["Requires-Python"], ">=3.12")
        self.assertIsNone(metadata["Requires-Dist"])

    def test_source_distribution_contains_build_and_contract_sources(self) -> None:
        source_path = DIST_ROOT / "mindgarden-0.1.0.tar.gz"
        with tarfile.open(source_path, "r:gz") as archive:
            names = set(archive.getnames())

        for expected in (
            "mindgarden-0.1.0/LICENSE",
            "mindgarden-0.1.0/MANIFEST.in",
            "mindgarden-0.1.0/README.md",
            "mindgarden-0.1.0/pyproject.toml",
            "mindgarden-0.1.0/contracts/garden.schema.json",
            "mindgarden-0.1.0/docs/cli.md",
            "mindgarden-0.1.0/docs/contracts-v1.md",
            "mindgarden-0.1.0/docs/initialization-migration.md",
            "mindgarden-0.1.0/docs/v0-v1-compatibility.md",
            "mindgarden-0.1.0/requirements/test.txt",
            "mindgarden-0.1.0/scripts/validate_garden.py",
            "mindgarden-0.1.0/src/mindgarden/interfaces/cli.py",
            "mindgarden-0.1.0/src/mindgarden/application/lifecycle.py",
            "mindgarden-0.1.0/tests/test_lifecycle.py",
            "mindgarden-0.1.0/tests/fixtures/contracts/v1/valid/garden.json",
            "mindgarden-0.1.0/tests/fixtures/contracts/v1/invalid/cases.json",
            "mindgarden-0.1.0/tests/fixtures/public-garden/.garden/garden.yaml",
            "mindgarden-0.1.0/tests/fixtures/public-garden/.garden/provenance/.gitkeep",
            "mindgarden-0.1.0/tests/fixtures/public-garden/llms.txt",
        ):
            self.assertIn(expected, names)


if __name__ == "__main__":
    unittest.main()
