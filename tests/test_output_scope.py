"""Every supported query output shares live authority, privacy and byte bounds."""

from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).parents[1] / "src"))

from mindgarden.application.evidence import resolve_evidence
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import (build_index,search_payload,graph_payload,backlinks_payload,
    outbound_payload,render_context,write_projection,projection_directory)
from mindgarden.application.scope_cache import CACHE_MARKER, verify_cache
from mindgarden.domain.contracts import canonical_json
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests import test_v1_retrieval as fixtures
from tests.support_v1 import add_knowledge, write_json


class OutputScopeTests(unittest.TestCase):
    def setUp(self):
        fixtures.RetrievalTests.setUp(self)
        self.citation=build_index(self.context)["records"][0]["sources"][0]

    def operations(self,context):
        return {"index":lambda:build_index(context),"search":lambda:search_payload(context,"prompt"),
            "graph":lambda:graph_payload(context),"backlinks":lambda:backlinks_payload(context,"synthetic-garden/second-note"),
            "outbound":lambda:outbound_payload(context,"synthetic-garden/synthetic-prompt"),
            "context-json":lambda:render_context(context,self.profile,"json"),
            "context-markdown":lambda:render_context(context,self.profile,"markdown"),
            "evidence":lambda:resolve_evidence(context,**self.citation)}

    def test_denied_metadata_is_inert_for_all_queries_and_agent_entrypoint(self):
        before={name:operation() for name,operation in self.operations(self.context).items()}
        note=add_knowledge(self.workspace,"denied-output-canary",body="denied-output-body-canary",reviewed=False)
        note["content"]["path"]="../denied-escape-canary"
        write_json(self.workspace / ".garden/knowledge/denied-output-canary.json",note)
        read=Path.read_bytes
        def guarded(path):
            if path.name=="denied-output-canary.md":raise AssertionError("Denied body read")
            return read(path)
        with patch.object(Path,"read_bytes",guarded):
            after={name:operation() for name,operation in self.operations(self.context).items()}
            for name in before:
                self.assertEqual(before[name],after[name],name)
                self.assertNotIn("denied-output",str(after[name]))
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(["llms","--repository-root",str(self.workspace),"--local-config",str(self.configuration),"--scope",str(self.session_path)]),0)
            self.assertNotIn("denied-output",output.getvalue())

    def test_expired_and_revoked_authority_stops_every_api_and_cache_write(self):
        now=[datetime(2026,11,6,tzinfo=timezone.utc)]
        context=QueryContext.load(self.configuration,self.session_path,clock=lambda:now[0])
        now[0]=datetime(2100,1,1,tzinfo=timezone.utc)
        for name,operation in self.operations(context).items():
            with self.subTest(state="expired",output=name),self.assertRaisesRegex(ContractError,"SESSION_EXPIRED"):operation()
        config=json.loads(self.configuration.read_text());config["revoked_sessions"]=[self.context.session["id"]];write_json(self.configuration,config)
        for name,operation in self.operations(self.context).items():
            with self.subTest(state="revoked",output=name),self.assertRaisesRegex(ContractError,"SESSION_REVOKED"):operation()
        with self.assertRaisesRegex(ContractError,"SESSION_REVOKED"):
            write_projection(self.context,self.workspace,"index.json",b"must-not-write")

    def test_serialized_budget_applies_to_outputs_without_limiting_internal_index(self):
        session=json.loads(self.session_path.read_text());session["budgets"]["max_output_bytes"]=2048;write_json(self.session_path,session)
        context=QueryContext.load(self.configuration,self.session_path)
        with self.assertRaisesRegex(ContractError,"QUERY_BUDGET"):build_index(context)
        result=search_payload(context,"absent-unique-token")
        self.assertEqual(result["results"],[])
        self.assertLessEqual(len(canonical_json(result)),2048)
        with self.assertRaisesRegex(ContractError,"QUERY_BUDGET"):
            write_projection(context,self.workspace,"index.json",b"x" * 2049)

    def test_query_diagnostics_never_echo_supplied_failures_or_partial_output(self):
        args=["search","--repository-root",str(self.workspace),"--local-config",str(self.configuration),
              "--scope",str(self.session_path),"--query","prompt","--diagnostic-format","json"]
        for error in (OSError("/private/filename-canary with private payload"),ContractError("UNTRUSTED_CANARY: private text")):
            with patch("mindgarden.application.retrieval.search_payload",side_effect=error),redirect_stdout(io.StringIO()) as output,redirect_stderr(io.StringIO()) as diagnostics:
                self.assertEqual(main(args),3)
            self.assertEqual(output.getvalue(),"")
            report=json.loads(diagnostics.getvalue())
            self.assertEqual(report["diagnostics"][0]["code"],"QUERY_UNAVAILABLE")
            self.assertNotIn("canary",diagnostics.getvalue().lower())
            self.assertNotIn("private",diagnostics.getvalue())

    def test_scope_cache_inventory_verifies_members_and_preserves_unowned_state(self):
        content=canonical_json(build_index(self.context))
        write_projection(self.context,self.workspace,"index.json",content)
        directory=projection_directory(self.context,self.workspace)
        manifest=verify_cache(directory,"synthetic-garden",self.context.scope_digest())
        self.assertEqual(manifest["files"][0]["path"],"index.json")
        self.assertTrue((directory/CACHE_MARKER).is_file())
        human=directory/"human-canary.txt";human.write_text("Synthetic human content stays intact.")
        with self.assertRaisesRegex(ContractError,"CACHE_INTEGRITY"):
            write_projection(self.context,self.workspace,"llms.txt",b"new projection")
        self.assertTrue(human.exists())
        self.assertEqual((directory/"index.json").read_bytes(),content)
