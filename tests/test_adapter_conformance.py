"""Reusable adapter conformance and immutable observation regression fixtures."""

from dataclasses import replace
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.text_source import TextSourceAdapter
from mindgarden.application.ingestion import apply_ingestion
from mindgarden.application.storage import content_resolver
from mindgarden.domain.contracts import ContractRegistry
from mindgarden.domain.garden import inspect_garden
from mindgarden.domain.sources import (AdapterRegistry, NormalizedBundle, NormalizedUnit,
                                       check_adapter_conformance, describe_adapter, normalize_source)
from mindgarden.domain.validation import ContractError
from tests import test_source_adapters as fixtures

ROOT = Path(__file__).parents[1]


class AdapterConformanceTests(unittest.TestCase):
    def test_built_in_declaration_and_golden(self):
        adapter = TextSourceAdapter()
        declaration = describe_adapter(adapter)
        self.assertEqual(ContractRegistry().errors(declaration, "source-adapter"), [])
        proof = check_adapter_conformance(adapter, b"\xef\xbb\xbfSynthetic.\r\n\r\n", {"source_id": "example", "media_type": "text/plain"})
        self.assertEqual(proof["units"][0]["locators"], ["artifact"])
        self.assertEqual(normalize_source(adapter, b"Synthetic.\r\n", {"source_id": "example", "media_type": "text/plain"}).units[0].content,
                         b"Synthetic.\n")

    def test_invalid_and_changed_declarations_and_ambiguous_selection(self):
        adapter = TextSourceAdapter()
        registry = AdapterRegistry((adapter,))
        adapter.version = "2.0.0"
        with self.assertRaisesRegex(ContractError, "ADAPTER_CHANGED"):
            registry.select("text/plain", None)
        adapter.version = "unversioned"
        with self.assertRaisesRegex(ContractError, "ADAPTER_DECLARATION"):
            AdapterRegistry((adapter,))
        second = TextSourceAdapter(); second.adapter_id = "other-text"
        registry = AdapterRegistry((TextSourceAdapter(), second))
        with self.assertRaisesRegex(ContractError, "ADAPTER_UNSUPPORTED"):
            registry.select("text/plain", None)
        self.assertIs(registry.select("text/plain", None, "other-text"), second)

    def test_output_negative_matrix_and_empty_success(self):
        class Adapter(TextSourceAdapter):
            def normalize(self, captured, metadata):
                return self.result
        adapter = Adapter()
        unit = NormalizedUnit("synthetic:one", b"Synthetic.\n")
        cases = [
            ("ADAPTER_OUTPUT", None),
            ("SOURCE_DUPLICATE", NormalizedBundle((unit, unit), ())),
            ("ADAPTER_OUTPUT", NormalizedBundle((replace(unit, identity="/private/source"),), ())),
            ("ADAPTER_METADATA", NormalizedBundle((replace(unit, metadata={"bad": float("nan")}),), ())),
            ("ADAPTER_METADATA", NormalizedBundle((replace(unit, metadata={1: "coerced"}),), ())),
            ("ADAPTER_TRANSFORMATION", NormalizedBundle((unit,), ({"name": "missing-version"},))),
            ("EVIDENCE", NormalizedBundle((replace(unit, locators=("lines:99-100",)),), ())),
        ]
        for code, output in cases:
            with self.subTest(code=code):
                adapter.result = output
                with self.assertRaisesRegex(ContractError, code):
                    normalize_source(adapter, b"Synthetic", {})
        adapter.result = NormalizedBundle((), ())
        self.assertEqual(check_adapter_conformance(adapter, b"Synthetic", {})["status"], "success")
        adapter.limits = {"capture_bytes": 1}
        with self.assertRaisesRegex(ContractError, "SOURCE_OVERSIZED"):
            normalize_source(adapter, b"too big", {})
        adapter.limits = {"units": 1}; adapter.result = NormalizedBundle((unit, replace(unit, identity="synthetic:two")), ())
        with self.assertRaisesRegex(ContractError, "ADAPTER_LIMIT"):
            normalize_source(adapter, b"Synthetic", {})

    def test_nondeterminism_mutation_and_failure_are_distinct(self):
        class Adapter(TextSourceAdapter):
            count = 0
            def normalize(self, captured, metadata):
                self.count += 1
                return NormalizedBundle((NormalizedUnit("synthetic", str(self.count).encode()),), ())
        with self.assertRaisesRegex(ContractError, "ADAPTER_NONDETERMINISTIC"):
            check_adapter_conformance(Adapter(), b"Synthetic", {})
        class Mutating(TextSourceAdapter):
            def normalize(self, captured, metadata):
                metadata["bad"] = True
                return NormalizedBundle((), ())
        metadata = {}
        with self.assertRaisesRegex(ContractError, "ADAPTER_MUTATION"):
            normalize_source(Mutating(), b"", metadata)
        self.assertEqual(metadata, {})
        class Failed(TextSourceAdapter):
            def normalize(self, captured, metadata):
                raise RuntimeError("PRIVATE SOURCE CONTENT")
        with self.assertRaisesRegex(ContractError, "^ADAPTER_FAILURE: normalization failed; no successful bundle produced$"):
            normalize_source(Failed(), b"", {})

    def test_reference_extension_plan_apply_without_network_or_domain_edits(self):
        fixtures.SourceAdapterTests.setUp(self)
        spec = spec_from_file_location("reference_extension", ROOT / "examples/adapters/reference_capture.py")
        module = module_from_spec(spec); spec.loader.exec_module(module)
        adapter = module.ReferenceCaptureAdapter()
        self.input.write_bytes((ROOT / "tests/fixtures/source-adapters/references.json").read_bytes())
        self.metadata["media_type"] = "application/vnd.example.references+json"
        with patch("socket.socket", side_effect=AssertionError("Network attempted")), patch("subprocess.run", side_effect=AssertionError("Execution attempted")):
            proof = check_adapter_conformance(adapter, self.input.read_bytes(), self.metadata)
            self.assertEqual(len(proof["units"]), 2)
            plan = fixtures.SourceAdapterTests.plan(self, registry=AdapterRegistry((adapter,)), manifest_version="1")
            self.assertTrue(apply_ingestion(plan, plan.digest, self.bindings, "synthetic-vault"))
            again = fixtures.SourceAdapterTests.plan(self, registry=AdapterRegistry((adapter,)), manifest_version="1")
            self.assertFalse(apply_ingestion(again, again.digest, self.bindings, "synthetic-vault"))
        self.assertTrue(all(item["metadata"]["page_content"] == "not-captured" for item in plan.inputs["normalized_sources"]))

    def test_new_adapter_version_and_capture_metadata_preserve_old_references(self):
        fixtures.SourceAdapterTests.setUp(self)
        plan = fixtures.SourceAdapterTests.plan(self)
        apply_ingestion(plan, plan.digest, self.bindings, "synthetic-vault")
        originals = {path: (self.workspace / ".garden" / path).read_bytes() for path in plan.files}
        adapter = TextSourceAdapter(); adapter.version = "2.0.0"
        original_normalize = adapter.normalize
        def changed(captured, metadata):
            bundle = original_normalize(captured, metadata)
            return replace(bundle, transformations=(*bundle.transformations,
                           {"name": "observe-new-version", "version": adapter.version, "parameters": {}}))
        adapter.normalize = changed
        self.metadata["captured_at"] = "2026-11-05T00:00:00Z"
        second = fixtures.SourceAdapterTests.plan(self, registry=AdapterRegistry((adapter,)))
        self.assertTrue(apply_ingestion(second, second.digest, self.bindings, "synthetic-vault"))
        again = fixtures.SourceAdapterTests.plan(self, registry=AdapterRegistry((adapter,)))
        self.assertFalse(apply_ingestion(again, again.digest, self.bindings, "synthetic-vault"))
        for path, content in originals.items():
            self.assertEqual((self.workspace / ".garden" / path).read_bytes(), content)
        self.assertEqual(inspect_garden(self.workspace, content_resolver=content_resolver(self.bindings)).report()["status"], "valid")
