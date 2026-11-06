"""Synthetic PDF classification, exact page evidence and failure boundaries."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.pdf_tools import layout_pages, run_tool
from mindgarden.application.bindings import LocalBindings, garden_fingerprint
from mindgarden.application.documents import build_document_plan
from mindgarden.application.ingestion import apply_ingestion, build_ingestion_plan
from mindgarden.application.storage import content_resolver
from mindgarden.domain.contracts import ContractRegistry, canonical_json, digest_bytes
from mindgarden.domain.garden import evidence_bytes, inspect_garden
from mindgarden.domain.scope import local_scope
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests import test_local_vault as fixtures
from tests.support_v1 import TIME, write_json

FIXTURES = Path(__file__).parent / "fixtures/documents"


class FixturePDFReader:
    """Captured Poppler 25.03.0 layout, not a claim that CI has PDF tools."""
    source_checks = []

    def __init__(self, status="complete"):
        self.status = status

    def read(self, content):
        result = json.loads((FIXTURES / "layout.json").read_bytes())
        result["status"] = self.status
        return result


class DocumentTests(unittest.TestCase):
    def setUp(self):
        fixtures.LocalVaultTests.setUp(self); fixtures.LocalVaultTests.initialize(self)
        self.bindings = LocalBindings.load(self.configuration)
        self.input = self.root / "synthetic.pdf"; self.input.write_bytes((FIXTURES / "complete.pdf").read_bytes())
        self.review = self.root / "classification.json"
        self.classification = {"schema": "mindgarden.document-classification/v1", "kind": "initial-classification",
                               "source_sha256": digest_bytes(self.input.read_bytes()), "scope": local_scope(),
                               "authority": {"kind": "human", "id": "synthetic-owner"},
                               "review": {"state": "approved", "reviewers": ["synthetic-owner"],
                                          "reviewed_at": TIME, "rationale": "New wholly synthetic ordinary fixture."}}
        write_json(self.review, self.classification)
        self.metadata = {"source_id": "synthetic-pdf", "title": "Synthetic document", "origin": "urn:synthetic:pdf",
                         "owner": "synthetic-owner", "rights": "Wholly synthetic fixture.", "captured_at": TIME}

    def plan(self, **options):
        return build_document_plan(self.bindings, "synthetic-garden", "synthetic-vault", self.input,
                                   self.metadata, self.review, reader=options.pop("reader", FixturePDFReader()), **options)

    def test_page_bundle_evidence_originals_and_repeat_import_are_deterministic(self):
        with patch("socket.socket", side_effect=AssertionError("Network attempted")):
            plan = self.plan(); self.assertEqual(plan.document(), self.plan().document())
            self.assertTrue(apply_ingestion(plan, plan.digest, self.bindings, "synthetic-vault"))
            self.assertFalse(apply_ingestion(plan, plan.digest, self.bindings, "synthetic-vault"))
            repeat = self.plan(); self.assertFalse(apply_ingestion(repeat, repeat.digest, self.bindings, "synthetic-vault"))
        snapshot = inspect_garden(self.workspace, content_resolver=content_resolver(self.bindings)).require_valid()
        sources = [record for record in snapshot.records.values() if record["schema"] == "mindgarden.source/v1"]
        self.assertEqual(len(sources), 4)
        for source in sources:
            self.assertEqual(source["publication"], "excluded")
            self.assertEqual(source["x-source-trust"], "untrusted-evidence")
            content = content_resolver(self.bindings)(source["artifact"])
            if source["kind"] == "captured": self.assertEqual(content, self.input.read_bytes())
            elif ":page:1" in source["x-source-identity"]:
                page = json.loads(content)
                self.assertEqual(ContractRegistry().errors(page, "document-page"), [])
                self.assertEqual(evidence_bytes(content, "json:/text"), b"Synthetic design prompt.\nKeep assumptions explicit; cite exact evidence.\n")
                for word in page["words"]:
                    self.assertEqual(page["text"].encode()[word["start_byte"]:word["end_byte"]], word["text"].encode())
                self.assertEqual(source["x-adapter"]["metadata"]["original_selector"]["page"], 1)
        self.assertFalse((self.root / "synthetic-malicious-command").exists())
        self.assertNotIn(str(self.root), json.dumps(plan.document()))

    def test_default_restricted_and_mixed_policy_stop_before_reader_or_input(self):
        with patch("mindgarden.application.documents.captured_bytes", side_effect=AssertionError("Input opened")):
            with self.assertRaisesRegex(ContractError, "RUNTIME_UNVERIFIED"):
                build_document_plan(self.bindings, "synthetic-garden", "synthetic-vault", self.input, self.metadata, None)
        for scope in (local_scope("restricted"), local_scope("organization")):
            self.classification["scope"] = scope; write_json(self.review, self.classification)
            with patch.object(FixturePDFReader, "read", side_effect=AssertionError("Reader ran")):
                with self.assertRaisesRegex(ContractError, "RUNTIME_UNVERIFIED|DOCUMENT_CLASSIFICATION"):
                    self.plan()
        self.assertEqual(self.vault.audit()["objects"], [])

    def test_classification_authority_and_hash_are_bound_to_application(self):
        for key, value in (("kind", "declassification"), ("authority", {"kind": "agent", "id": "synthetic-agent"}),
                           ("authority", {"kind": "human", "id": "different-human"}),
                           ("source_sha256", "0" * 64)):
            bad = deepcopy(self.classification); bad[key] = value; write_json(self.review, bad)
            with self.assertRaisesRegex(ContractError, "DOCUMENT_CLASSIFICATION|DOCUMENT_CHANGED"): self.plan()
        write_json(self.review, self.classification)
        plan = self.plan(); self.review.write_text("changed synthetic review")
        with self.assertRaisesRegex(ContractError, "PLAN_STALE"):
            apply_ingestion(plan, plan.digest, self.bindings, "synthetic-vault")
        self.assertEqual(self.vault.audit()["objects"], [])

    def test_partial_ocr_encrypted_and_malformed_never_apply_empty_success(self):
        before = garden_fingerprint(self.workspace)
        for status, code in (("partial", "PARTIAL"), ("ocr-needed", "OCR_NEEDED"), ("encrypted", "ENCRYPTED"),
                             ("malformed", "MALFORMED"), ("unsupported", "UNSUPPORTED"), ("unavailable", "UNAVAILABLE")):
            with self.subTest(status=status), self.assertRaisesRegex(ContractError, "DOCUMENT_" + code):
                self.plan(reader=FixturePDFReader(status))
        self.assertEqual(garden_fingerprint(self.workspace), before)
        self.assertEqual(self.vault.audit()["objects"], [])

    def test_bad_geometry_and_normalized_spans_are_rejected(self):
        for xml in (b"<page/>", b"<!DOCTYPE x [<!ENTITY a 'unsafe'>]><x>&a;</x>",
                    b'<x><page width="nan" height="10"/></x>'):
            with self.assertRaisesRegex(ContractError, "DOCUMENT_MALFORMED"): layout_pages(xml, 1)
        result = FixturePDFReader().read(b""); result["pages"][0]["words"][0]["end_byte"] += 1
        with patch.object(FixturePDFReader, "read", return_value=result):
            with self.assertRaisesRegex(ContractError, "DOCUMENT_MALFORMED"): self.plan()

    def test_generic_adapter_cannot_weaken_declared_source_scope(self):
        with patch("mindgarden.application.ingestion.captured_bytes", side_effect=AssertionError("Input opened")):
            with self.assertRaisesRegex(ContractError, "SOURCE_BOUNDARY"):
                build_ingestion_plan(self.bindings, "synthetic-garden", "synthetic-vault", self.input,
                                     {**self.metadata, "source_scope": local_scope("restricted"), "media_type": "text/plain"})

    def test_cli_diagnostics_contain_neither_path_nor_document_text(self):
        arguments = ["document", "--local-config", str(self.configuration), "--garden-id", "synthetic-garden",
                     "--vault-id", "synthetic-vault", "--input", str(self.input), "--source-id", "synthetic-pdf",
                     "--title", "private-title-canary", "--origin", "urn:synthetic:pdf", "--owner", "synthetic-owner",
                     "--rights", "Synthetic fixture.", "--captured", TIME, "--plan", "--diagnostic-format", "json"]
        with redirect_stdout(io.StringIO()) as output, redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(main(arguments), 3)
        self.assertEqual(output.getvalue(), "")
        self.assertNotIn(str(self.root), errors.getvalue()); self.assertNotIn("private-title-canary", errors.getvalue())
        self.assertEqual(json.loads(errors.getvalue())["diagnostics"][0]["code"], "RUNTIME_UNVERIFIED")

    @unittest.skipUnless(sys.platform.startswith("linux"), "bounded optional PDF runner supports Linux")
    def test_local_runner_strips_credentials_and_bounds_output(self):
        with patch.dict("os.environ", {"SYNTHETIC_PROVIDER_SECRET": "private-canary"}):
            status, content, errors = run_tool(Path(sys.executable), ["-I", "-S", "-c",
                "import os; print(os.environ.get('SYNTHETIC_PROVIDER_SECRET', 'absent'))"], b"", self.vault.root)
        self.assertEqual((status, content, errors), (0, b"absent\n", b""))
        with self.assertRaisesRegex(ContractError, "DOCUMENT_LIMIT"):
            run_tool(Path(sys.executable), ["-I", "-S", "-c", "import sys; sys.stdout.buffer.write(b'x' * 9000000)"],
                     b"", self.vault.root)
