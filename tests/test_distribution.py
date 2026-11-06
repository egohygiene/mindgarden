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
            "mindgarden/domain/publication.py",
            "mindgarden/application/evidence.py",
            "mindgarden/application/assets.py",
            "mindgarden/domain/assets.py",
            "mindgarden/adapters/media_source.py",
            "mindgarden/adapters/pdf_source.py",
            "mindgarden/adapters/pdf_tools.py",
            "mindgarden/application/documents.py",
            "mindgarden/application/registry_cache.py",
            "mindgarden/application/vault_recovery.py",
            "mindgarden/application/query_view.py",
            "mindgarden/application/federation.py",
            "mindgarden/domain/federation.py",
            "mindgarden/adapters/federation_files.py",
            "mindgarden/application/site.py",
            "mindgarden/application/portal.py",
            "mindgarden/application/compaction.py",
            "mindgarden/domain/compaction.py",
            "mindgarden/domain/portal.py",
            "mindgarden/adapters/portal_files.py",
            "mindgarden/domain/site.py",
            "mindgarden/domain/design.py",
            "mindgarden/domain/public_diagnostics.py",
            "mindgarden/adapters/site_files.py",
            "mindgarden/domain/registry.py",
            "mindgarden/application/registry.py",
            "mindgarden/adapters/registry_files.py",
            "mindgarden/adapters/conversation_archive.py",
            "mindgarden/adapters/vault_bundle.py",
            "mindgarden/application/agent.py",
            "mindgarden/application/lifecycle.py",
            "mindgarden/adapters/publishing.py",
            "mindgarden/adapters/quartz.py",
            "mindgarden/interfaces/cli.py",
            "mindgarden-0.1.0.data/data/share/mindgarden/contracts/garden.schema.json",
            "mindgarden-0.1.0.data/data/share/mindgarden/contracts/v1/knowledge.schema.json",
            "mindgarden-0.1.0.data/data/share/mindgarden/contracts/v1/asset-manifest.schema.json",
            "mindgarden-0.1.0.data/data/share/mindgarden/contracts/v1/asset-review.schema.json",
            "mindgarden-0.1.0.data/data/share/mindgarden/contracts/v1/document-bundle.schema.json",
            "mindgarden-0.1.0.data/data/share/mindgarden/contracts/v1/storage-capabilities.schema.json",
            "mindgarden-0.1.0.data/data/share/mindgarden/contracts/v1/vault.schema.json",
            "mindgarden-0.1.0.data/data/share/mindgarden/contracts/v1/evidence.schema.json",
            "mindgarden-0.1.0.data/data/share/mindgarden/contracts/v1/federation-descriptor.schema.json",
            "mindgarden-0.1.0.data/data/share/mindgarden/contracts/v1/federation-catalog.schema.json",
            "mindgarden-0.1.0.data/data/share/mindgarden/contracts/v1/vault-export.schema.json",
            "mindgarden-0.1.0.data/data/share/mindgarden/contracts/v1/registry.schema.json",
            "mindgarden-0.1.0.data/data/share/mindgarden/contracts/v1/registry-view.schema.json",
            "mindgarden-0.1.0.data/data/share/mindgarden/contracts/v1/registry-plan.schema.json",
            "mindgarden-0.1.0.data/data/share/mindgarden/contracts/v1/site-adapter.schema.json",
            "mindgarden-0.1.0.data/data/share/mindgarden/contracts/v1/site-manifest.schema.json",
            "mindgarden-0.1.0.data/data/share/mindgarden/contracts/v1/site-plan.schema.json",
            "mindgarden-0.1.0.data/data/share/mindgarden/contracts/v1/portal-request.schema.json",
            "mindgarden-0.1.0.data/data/share/mindgarden/contracts/v1/portal-manifest.schema.json",
            "mindgarden-0.1.0.data/data/share/mindgarden/contracts/v1/portal-plan.schema.json",
            "mindgarden-0.1.0.data/data/share/mindgarden/contracts/v1/retention-policy.schema.json",
            "mindgarden-0.1.0.data/data/share/mindgarden/contracts/v1/compaction-plan.schema.json",
            "mindgarden-0.1.0.data/data/share/mindgarden/contracts/v1/compaction-manifest.schema.json",
            "mindgarden-0.1.0.data/data/share/mindgarden/profiles/quartz/v1.config.json",
            "mindgarden-0.1.0.data/data/share/mindgarden/profiles/quartz/v1.graph.js",
            "mindgarden-0.1.0.data/data/share/mindgarden/profiles/quartz/v1.css",
            "mindgarden-0.1.0.data/data/share/mindgarden/design/tokens/mindgarden.tokens.json",
            "mindgarden-0.1.0.data/data/share/mindgarden/design/schemas/design-tokens.schema.json",
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
            "mindgarden-0.1.0/scripts/private_garden_demo.py",
            "mindgarden-0.1.0/scripts/document_demo.py",
            "mindgarden-0.1.0/scripts/mixed_vault_demo.py",
            "mindgarden-0.1.0/tests/fixtures/assets/expected-proof.json",
            "mindgarden-0.1.0/tests/fixtures/assets/synthetic.png",
            "mindgarden-0.1.0/tests/fixtures/assets/synthetic.wav",
            "mindgarden-0.1.0/tests/fixtures/documents/complete.pdf",
            "mindgarden-0.1.0/scripts/federation_demo.py",
            "mindgarden-0.1.0/scripts/registry_demo.py",
            "mindgarden-0.1.0/scripts/site_demo.py",
            "mindgarden-0.1.0/tests/site_fixture.py",
            "mindgarden-0.1.0/design/README.md",
            "mindgarden-0.1.0/design/tokens/mindgarden.tokens.json",
            "mindgarden-0.1.0/design/schemas/design-tokens.schema.json",
            "mindgarden-0.1.0/tests/fixtures/site/expected-proof.json",
            "mindgarden-0.1.0/docs/local-registry.md",
            "mindgarden-0.1.0/tests/registry_fixture.py",
            "mindgarden-0.1.0/tests/fixtures/registry/source.txt",
            "mindgarden-0.1.0/tests/fixtures/registry/expected-proof.json",
            "mindgarden-0.1.0/tests/fixtures/federation/expected-proof.json",
            "mindgarden-0.1.0/tests/fixtures/federation/expected/.mindgarden-federation.json",
            "mindgarden-0.1.0/src/mindgarden/interfaces/cli.py",
            "mindgarden-0.1.0/src/mindgarden/application/lifecycle.py",
            "mindgarden-0.1.0/scripts/publication_conformance.py",
            "mindgarden-0.1.0/scripts/compaction_demo.py",
            "mindgarden-0.1.0/tests/fixtures/compaction/authored-plan.json",
            "mindgarden-0.1.0/tests/fixtures/compaction/expected-proof.json",
            "mindgarden-0.1.0/tests/fixtures/publication-conformance/cases.json",
            "mindgarden-0.1.0/tests/test_lifecycle.py",
            "mindgarden-0.1.0/tests/fixtures/contracts/v1/valid/garden.json",
            "mindgarden-0.1.0/tests/fixtures/conversation-archives/authored-plan.json",
            "mindgarden-0.1.0/tests/fixtures/conversation-archives/expected-proof.json",
            "mindgarden-0.1.0/tests/fixtures/conversation-archives/full-source/CONVERSATION.json",
            "mindgarden-0.1.0/tests/fixtures/contracts/v1/invalid/cases.json",
            "mindgarden-0.1.0/tests/fixtures/public-garden/.garden/garden.yaml",
            "mindgarden-0.1.0/tests/fixtures/public-garden/.garden/provenance/.gitkeep",
            "mindgarden-0.1.0/tests/fixtures/public-garden/llms.txt",
        ):
            self.assertIn(expected, names)


if __name__ == "__main__":
    unittest.main()
