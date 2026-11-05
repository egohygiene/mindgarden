"""Reviewed search, typed relationships and bounded context from explicit v1 inputs."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import shutil
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.ingestion import apply_ingestion
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import (
    backlinks_payload, build_index, graph_payload, render_context, search_payload,
)
from mindgarden.domain.contracts import ContractRegistry, canonical_json
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests.support_v1 import FIXTURES, add_knowledge, reference, write_json, write_session
from tests import test_source_adapters as source_tests


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        source_tests.SourceAdapterTests.setUp(self)
        plan = source_tests.SourceAdapterTests.plan(self)
        apply_ingestion(plan, plan.digest, self.bindings, "synthetic-vault")
        evidence = plan.inputs["normalized_sources"][0]["evidence"]
        first = add_knowledge(self.workspace, sources=evidence)
        second = add_knowledge(self.workspace, "second-note", body="A second reviewed synthetic procedure.\n", sources=evidence)
        add_knowledge(self.workspace, "unreviewed-note", body="unreviewed-unique-marker\n", reviewed=False)
        edge = json.loads((FIXTURES / "synapse.json").read_text())
        edge.update(id="synthetic-relationship", garden="synthetic-garden", type="supports", directed=True,
                    source=reference("synthetic-garden", first["id"]),
                    target=reference("synthetic-garden", second["id"]), visibility="private", status="active",
                    review=first["review"], evidence=evidence)
        write_json(self.workspace / ".garden/synapses/synthetic-relationship.json", edge)
        claim = json.loads((FIXTURES / "claim.json").read_text())
        claim.update(id="synthetic-claim", garden="synthetic-garden", statement="Synthetic prompt evidence is retained.",
                     subject=reference("synthetic-garden", first["id"]), visibility="private",
                     status="active", review=first["review"], evidence=[{
                         "relationship": "supports", "target": evidence[0], "rationale": "Exact synthetic source."}])
        write_json(self.workspace / ".garden/claims/synthetic-claim.json", claim)
        self.session_path = self.root / "session.json"
        write_session(self.session_path, self.configuration)
        self.context = QueryContext.load(self.configuration, self.session_path)
        self.profile = json.loads((self.workspace / ".garden/context-packs/default.json").read_text())

    def test_reviewed_search_has_exact_evidence_and_explainable_scores(self):
        with patch("socket.socket", side_effect=AssertionError("Network attempted")):
            result = search_payload(self.context, "prompt")
        self.assertEqual(result["schema"], "mindgarden.search-results/v1")
        self.assertEqual(ContractRegistry().errors(result, "search-results"), [])
        self.assertTrue(result["results"])
        self.assertTrue(result["results"][0]["sources"][0]["content_sha256"])
        self.assertTrue(result["results"][0]["reference"]["revision"].startswith("sha256:"))
        self.assertTrue(result["results"][0]["selection_reasons"])
        self.assertNotIn("unreviewed-unique-marker", json.dumps(result))
        self.assertNotIn(str(self.root), json.dumps(result))

    def test_index_graph_backlinks_and_rebuild_are_deterministic(self):
        index = build_index(self.context)
        self.assertEqual(ContractRegistry().errors(index, "index"), [])
        self.assertEqual(canonical_json(index), canonical_json(build_index(self.context)))
        graph = graph_payload(self.context, start="synthetic-garden/synthetic-prompt", depth=2)
        self.assertEqual(ContractRegistry().errors(graph, "graph"), [])
        self.assertEqual(graph["edges"][0]["type"], "supports")
        backlinks = backlinks_payload(self.context, "synthetic-garden/second-note")
        self.assertEqual(ContractRegistry().errors(backlinks, "backlinks"), [])
        self.assertEqual(backlinks["links"][0]["from"], "synthetic-garden/synthetic-prompt")
        other = self.root / "relocated-garden"
        shutil.copytree(self.workspace, other)
        configuration = json.loads(self.configuration.read_text())
        configuration["gardens"][0]["root"] = str(other)
        alternative = self.root / "other-bindings.json"
        write_json(alternative, configuration)
        context = QueryContext.load(alternative, self.session_path)
        self.assertEqual(canonical_json(index), canonical_json(build_index(context)))

    def test_context_formats_are_bounded_and_provenance_backed(self):
        for format in ("json", "markdown"):
            with self.subTest(format=format):
                content = render_context(self.context, self.profile, format)
                self.assertLessEqual(len(content), self.profile["max_bytes"])
                self.assertIn(b"sha256:", content)
                self.assertIn(b"untrusted", content)
                self.assertNotIn(b"unreviewed-unique-marker", content)
                self.assertEqual(content, render_context(self.context, self.profile, format))
                if format == "json":
                    self.assertEqual(ContractRegistry().errors(json.loads(content), "context"), [])
        tiny = {**self.profile, "max_bytes": 16}
        with self.assertRaisesRegex(ContractError, "CONTEXT_BUDGET"):
            render_context(self.context, tiny, "json")

    def test_cli_search_index_context_and_verify_use_the_same_services(self):
        shared = ["--repository-root", str(self.workspace), "--local-config", str(self.configuration),
                  "--scope", str(self.session_path)]
        for operation, extra in [("search", ["--query", "prompt"]), ("index", ["--write"]),
                                 ("index", ["--check"]), ("context", ["--pack", "default", "--format", "json"]),
                                 ("verify", [])]:
            with self.subTest(operation=operation), redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main([operation, *shared, *extra]), 0)
            self.assertNotIn(str(self.root), output.getvalue())
        with self.assertRaisesRegex(ContractError, "PROJECTION_DENIED"):
            session = json.loads(self.session_path.read_text())
            session["projections"] = ["search"]
            write_json(self.session_path, session)
            build_index(QueryContext.load(self.configuration, self.session_path))
