"""Reproducible projection matrix and context-fitting work bound."""

from contextlib import redirect_stdout
import io
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import build_index, outbound_payload, backlinks_payload, graph_payload, render_context, search_payload
from mindgarden.domain.contracts import ContractRegistry, canonical_json, digest_bytes
from mindgarden.interfaces.cli import main
from tests.projection_corpus import create_corpus
from tests.support_v1 import write_json, write_session

FIXTURE = Path(__file__).parent / "fixtures/projection-corpus/expected.json"


def projections(context, profile):
    payloads = {"index":canonical_json(build_index(context)), "search":canonical_json(search_payload(context,"claimneedle")),
                "graph":canonical_json(graph_payload(context,start="synthetic-garden/corpus-00000")),
                "backlinks":canonical_json(backlinks_payload(context,"synthetic-garden/corpus-00001")),
                "outbound":canonical_json(outbound_payload(context,"synthetic-garden/corpus-00000")),
                "context_json":render_context(context,profile,"json"), "context_markdown":render_context(context,profile,"markdown")}
    with redirect_stdout(io.StringIO()) as output:
        result = main(["llms", "--repository-root",str(context.bindings.garden("synthetic-garden")["root"]),
                       "--local-config",str(context.bindings.path),"--scope",str(context.session_path)])
    if result != 0: raise AssertionError("Synthetic llms projection failed")
    payloads["llms"] = output.getvalue().encode()
    return payloads


class ProjectionCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(); cls.addClassCleanup(cls.temporary.cleanup)
        cls.context, cls.profile = create_corpus(Path(cls.temporary.name),32)

    def test_projection_golden_schema_matrix_and_exact_claim_evidence(self):
        first = projections(self.context,self.profile)
        expected = json.loads(FIXTURE.read_text())
        self.assertEqual({name:digest_bytes(content) for name,content in first.items()}, expected["sha256"])
        registry = ContractRegistry()
        for name,contract in {"index":"index","search":"search-results","graph":"graph","backlinks":"backlinks","outbound":"outbound-links","context_json":"context"}.items():
            with self.subTest(projection=name): self.assertEqual(registry.errors(json.loads(first[name]),contract),[])
        self.assertEqual(registry.errors(json.loads(first["llms"].decode().split("```json\n")[1].split("```",1)[0]),"agent-entrypoint"),[])
        self.assertEqual(len(json.loads(first["index"])["records"]),33)
        self.assertEqual(json.loads(first["search"])["results"][0]["reference"]["id"],"corpus-claim")
        self.assertTrue(json.loads(first["search"])["results"][0]["sources"][0]["content_sha256"])
        for name in ("context_json","context_markdown"): self.assertLessEqual(len(first[name]),4096)
        self.assertEqual(first,projections(QueryContext.load(self.context.bindings.path,self.context.session_path),self.profile))

    def test_context_prefix_fitting_has_logarithmic_work_and_keeps_reasons(self):
        index = build_index(self.context)
        expanded = {**index,"records":[{**record,"id":str(number),"reference":{**record["reference"],"id":f"synthetic-{number:05d}"}}
                    for number in range(1024) for record in index["records"][:1]]}
        profile = {**self.profile,"max_candidates":1024,"max_bytes":2048}
        calls = 0
        def count(value):
            nonlocal calls
            if isinstance(value,dict) and value.get("schema") == "mindgarden.context/v1": calls += 1
            return canonical_json(value)
        self.context.session["budgets"]["max_candidates"] = 1024
        with patch("mindgarden.application.retrieval.build_index",return_value=expanded), patch.object(self.context,"check_live"), patch("mindgarden.application.retrieval.canonical_json",side_effect=count):
            result = json.loads(render_context(self.context,profile,"json"))
        self.context.session["budgets"]["max_candidates"] = 33
        considered = result["budget"]["considered_candidates"]
        self.assertLessEqual(calls,math.ceil(math.log2(1025)) + 2 * considered + 4)
        self.assertLessEqual(len(canonical_json(result)),2048)
        self.assertTrue(all(item["reason"] in {"byte-budget","item-budget","not-selected-candidate"} for item in result["excluded"]))

    def test_redaction_provenance_is_selected_and_conforms(self):
        with tempfile.TemporaryDirectory() as temporary:
            context, profile = create_corpus(Path(temporary), 2)
            path = context.bindings.garden("synthetic-garden")["root"] / ".garden/knowledge/corpus-00000.json"
            record = json.loads(path.read_text())
            record["x-curation"] = {"redactions":[{"source":record["sources"][0], "rationale":"Authored synthetic omission.",
                "unowned-extra":"private-extra-canary"},
                {"source":{"source":{"garden":"denied-garden","id":"denied-marker","revision":None},
                           "locator":"artifact","content_sha256":"0" * 64},"rationale":"Denied marker."}]}
            write_json(path, record)
            write_session(context.session_path, context.bindings.path)
            context = QueryContext.load(context.bindings.path, context.session_path)
            result = search_payload(context,"needle00000")
            self.assertEqual(len(result["results"][0]["qualifications"]["redactions"]),1)
            self.assertNotIn("denied-marker",json.dumps(result))
            self.assertNotIn("private-extra-canary",json.dumps(result))
            self.assertEqual(ContractRegistry().errors(result,"search-results"),[])
            profile.update(query="needle00000",max_bytes=8192)
            pack = json.loads(render_context(context,profile,"json"))
            self.assertEqual(ContractRegistry().errors(pack,"context"),[])
            self.assertTrue(pack["included"][0]["qualifications"]["redactions"])
