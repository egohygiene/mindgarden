"""Bounded reviewed Markdown, exact evidence, and opaque freshness failures."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.retrieval import build_index
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.domain.scope import local_scope
from mindgarden.interfaces.cli import ExitCode, main
from tests import test_v1_retrieval as retrieval_tests
from tests.support_v1 import add_knowledge, write_json


class GardenBriefTests(unittest.TestCase):
    def setUp(self):
        retrieval_tests.RetrievalTests.setUp(self)
        self.arguments = [
            "brief", "--local-config", str(self.configuration), "--scope", str(self.session_path),
        ]

    def invoke(self, *arguments):
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main([*self.arguments, *arguments])
        return code, stdout.getvalue(), stderr.getvalue()

    def refresh(self, **changes):
        session = json.loads(self.session_path.read_bytes())
        session.update(changes)
        write_json(self.session_path, bind_session_revisions(self.configuration, session))

    def brief(self):
        code, output, errors = self.invoke()
        self.assertEqual((code, errors), (ExitCode.SUCCESS, ""))
        return output

    def fail(self, failure, *arguments):
        code, output, errors = self.invoke(*arguments, "--diagnostic-format", "json")
        self.assertEqual((code, output), (ExitCode.CONTRACT, ""))
        self.assertEqual(json.loads(errors)["diagnostics"][0]["code"], failure)
        self.assertNotIn(str(self.root), errors)
        self.assertNotIn("private-canary", errors)

    def test_reviewed_titles_citations_connections_and_qualifications(self):
        citation = next(record["sources"][0] for record in build_index(self.context)["records"]
                        if record["id"] == "synthetic-prompt")
        record_path = self.workspace / ".garden/knowledge/synthetic-prompt.json"
        note = json.loads(record_path.read_bytes())
        note.update(title="Reviewed <img src=x> [[link]]\n# Fake heading",
                    **{"x-curation": {
                        "caveats": ["Only fictional source data."],
                        "uncertainty": ["Check the date?"],
                    }})
        write_json(record_path, note)
        self.refresh()
        output = self.brief()
        self.assertEqual(output, self.brief())
        self.assertIn("## Represented garden revisions", output)
        self.assertIn("`synthetic-garden/synthetic-prompt` · approved", output)
        self.assertIn("Open question · Check the date?", output)
        self.assertIn("Caveat · Only fictional source data&#46;", output)
        self.assertIn("`synthetic-garden/synthetic-prompt` → `synthetic-garden/second-note` · `supports`", output)
        source = citation["source"]
        for exact in (f"{source['garden']}/{source['id']}", source["revision"], citation["locator"], citation["content_sha256"]):
            self.assertIn(f"`{exact}`", output)
        self.assertIn("`mindgarden llms`", output)
        self.assertIn("`mindgarden research`", output)
        self.assertNotIn("<img", output)
        self.assertNotIn("[[link]]", output)
        self.assertNotIn("\n# Fake heading", output)
        self.assertNotIn("A second reviewed synthetic procedure.", output)
        self.assertNotIn(str(self.root), output)

    def test_denied_changes_do_not_affect_text_revisions_or_counts(self):
        baseline = self.brief()
        add_knowledge(self.workspace, "private-canary-unreviewed", body="private-canary-body", reviewed=False)
        denied = add_knowledge(self.workspace, "private-canary-restricted", body="private-canary-body")
        denied["scope"] = local_scope("restricted")
        write_json(self.workspace / ".garden/knowledge/private-canary-restricted.json", denied)
        self.assertEqual(self.brief(), baseline)
        self.assertNotIn("unreviewed-unique-marker", baseline)
        self.assertNotIn("private-canary", baseline)

    def test_projection_gates_and_tight_budgets(self):
        budgets = self.context.session["budgets"]
        self.refresh(projections=["index"])
        output = self.brief()
        self.assertGreater(output.count(" · approved · "), 1)
        self.assertNotIn("## Connections", output)
        self.assertNotIn("mindgarden graph", output)
        self.assertNotIn("mindgarden evidence", output)
        self.assertNotIn("mindgarden research", output)

        self.refresh(projections=["index"], budgets={**budgets, "max_results": 1, "max_output_bytes": 1600})
        output = self.brief()
        self.assertEqual(output.count(" · approved · "), 1)
        self.assertLessEqual(len(output.encode("utf8")), 1600)
        self.refresh(projections=["index", "graph"], budgets={**budgets, "max_results": 1})
        self.assertNotIn("## Connections", self.brief())
        self.refresh(projections=["index"], budgets={**budgets, "max_output_bytes": 256})
        self.fail("CONTEXT_BUDGET")
        self.refresh(projections=["index"], budgets={**budgets, "max_context_bytes": 128})
        self.fail("CONTEXT_BUDGET")
        self.refresh(projections=["graph"], budgets=budgets)
        self.fail("PROJECTION_DENIED")

    def test_check_requires_fresh_authority_then_current_bytes(self):
        output_path = self.root / "private-canary-brief.md"
        unchecked = self.brief().encode("utf8")
        output_path.write_bytes(unchecked)
        self.assertEqual(self.invoke("--check", str(output_path)), (ExitCode.SUCCESS, "mindgarden brief is current\n", ""))
        output_path.write_bytes(unchecked + b"\nprivate-canary")
        self.fail("PROJECTION_STALE", "--check", str(output_path))
        output_path.write_bytes(unchecked)

        record_path = self.workspace / ".garden/knowledge/synthetic-prompt.json"
        note = json.loads(record_path.read_bytes())
        write_json(record_path, {**note, "title": "Revised approved synthetic prompt"})
        self.fail("SESSION_REVISION", "--check", str(output_path))
        self.refresh()
        self.fail("PROJECTION_STALE", "--check", str(output_path))
        self.assertEqual(output_path.read_bytes(), unchecked)
        updated = self.brief().encode("utf8")
        self.assertIn(b"Revised approved synthetic prompt", updated)
        self.assertNotEqual(updated, unchecked)
        output_path.write_bytes(updated)
        self.assertEqual(self.invoke("--check", str(output_path))[0], ExitCode.SUCCESS)

        config = json.loads(self.configuration.read_bytes())
        config["revoked_sessions"] = [self.context.session["id"]]
        write_json(self.configuration, config)
        self.fail("SESSION_REVOKED", "--check", str(output_path))
