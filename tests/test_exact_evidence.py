"""Reviewed-citation authority, original selectors and bounded exact evidence."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.curation import apply_curation, build_curation_plan
from mindgarden.application.evidence import resolve_evidence
from mindgarden.application.ingestion import apply_ingestion
from mindgarden.application.query import QueryContext
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.domain.contracts import ContractRegistry, digest_bytes
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests.support_v1 import write_json, write_session
from tests import test_conversation_archives as archive_tests


class ExactEvidenceTests(unittest.TestCase):
    def setUp(self):
        archive_tests.ConversationArchiveTests.setUp(self)
        imported = archive_tests.ConversationArchiveTests.plan(self)
        apply_ingestion(imported, imported.digest, self.bindings, "synthetic-vault")
        proposal = Path(__file__).parent / "fixtures/conversation-archives/authored-plan.json"
        plan = build_curation_plan(self.bindings, proposal)
        apply_curation(plan, plan.digest, self.bindings)
        self.citation = next(item["evidence"][0] for item in imported.inputs["normalized_sources"]
                             if item["metadata"].get("message_id") == "message-prompt")
        self.uncited = next(item["evidence"][0] for item in imported.inputs["normalized_sources"]
                            if item["metadata"].get("message_id") == "message-user")
        self.session_path = self.root / "session.json"; write_session(self.session_path, self.configuration)
        self.context = QueryContext.load(self.configuration, self.session_path)

    def test_exact_text_original_member_pointer_and_source_review_are_preserved(self):
        with patch("socket.socket", side_effect=AssertionError("Network attempted")):
            evidence = resolve_evidence(self.context, **self.citation)
        self.assertEqual(ContractRegistry().errors(evidence, "evidence"), [])
        self.assertEqual(evidence["text"], "Cite exact evidence; preserve uncertainty.")
        self.assertEqual(digest_bytes(evidence["text"].encode()), evidence["content_sha256"])
        self.assertEqual(evidence["origin"]["speaker"], "assistant")
        self.assertEqual(evidence["origin"]["original_selector"]["json_pointer"], "/messages/1")
        self.assertEqual(evidence["lineage"][0]["revision"], "sha256:" + digest_bytes(self.input.read_bytes()))
        self.assertEqual(evidence["source_review"]["state"], "unreviewed")
        self.assertEqual(evidence["authorized_by"][0]["review"]["state"], "approved")
        self.assertNotIn(str(self.root), json.dumps(evidence))

    def test_uncited_absent_or_changed_selections_are_identical_denials(self):
        cases = [self.uncited, {**self.citation, "source": {**self.citation["source"], "id": "absent-source"}},
                 {**self.citation, "content_sha256": "0" * 64}, {**self.citation, "locator": "bytes:0-4"}]
        errors = []
        for citation in cases:
            with self.assertRaises(ContractError) as raised:
                resolve_evidence(self.context, **citation)
            errors.append(str(raised.exception))
        self.assertEqual(len(set(errors)), 1)
        self.assertNotIn("absent-source", errors[0])
        self.assertNotIn("synthetic-malicious-command", errors[0])

    def test_cli_returns_bounded_evidence_and_small_budget_fails_closed(self):
        citation = self.citation
        arguments = ["evidence", "--local-config", str(self.configuration), "--scope", str(self.session_path),
                     "--garden-id", citation["source"]["garden"], "--source-id", citation["source"]["id"],
                     "--revision", citation["source"]["revision"], "--locator", citation["locator"],
                     "--content-sha256", citation["content_sha256"]]
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(arguments), 0)
        self.assertEqual(json.loads(output.getvalue())["source"], citation["source"])
        session = json.loads(self.session_path.read_text()); session["budgets"]["max_context_bytes"] = 128
        write_json(self.session_path, bind_session_revisions(self.configuration, session))
        with self.assertRaisesRegex(ContractError, "CONTEXT_BUDGET"):
            resolve_evidence(QueryContext.load(self.configuration, self.session_path), **citation)
