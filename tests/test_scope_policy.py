"""Existing scope contracts consume one inspectable policy decision boundary."""

from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0,str(Path(__file__).parents[1] / "src"))

from mindgarden.domain.contracts import ContractRegistry, canonical_json
from mindgarden.domain.scope import local_scope, POLICY_REFERENCE
from mindgarden.domain.scope_policy import decide_scope, require_destination
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main


class ScopePolicyTests(unittest.TestCase):
    def test_positive_negative_and_mixed_fixture_matrix(self):
        fixture=json.loads((Path(__file__).parent / "fixtures/scope-policy/cases.json").read_text())
        for case in fixture["cases"]:
            with self.subTest(case=case["id"]):
                args={"destination":local_scope(case["destination"])} if "destination" in case else {}
                result=decide_scope(case["operation"],[local_scope(value) for value in case["sources"]],**args)
                self.assertEqual(result["outcome"],case["outcome"])
                self.assertEqual(result["code"],case["code"])
                self.assertEqual(result["scope"]["visibility"],case["visibility"])
                self.assertEqual(result["assurance"],"not-asserted")
                self.assertEqual(ContractRegistry().errors(result,"scope-decision"),[])
                self.assertEqual(result,decide_scope(case["operation"],[local_scope(value) for value in case["sources"]],**args))

    def test_unknown_policy_conflicts_and_missing_classification_fail_closed(self):
        for mutate in (lambda scope:scope["policy"].update(revision="sha256:" + "0" * 64),
                       lambda scope:scope.update(visibility="unknown"),lambda scope:scope.pop("execution")):
            scope=deepcopy(local_scope());mutate(scope)
            result=decide_scope("query",[scope])
            self.assertEqual(result["outcome"],"deny")
            self.assertIsNone(result["scope"])
            self.assertEqual(ContractRegistry().errors(result,"scope-decision"),[])
        self.assertEqual(decide_scope("query",[])["code"],"SCOPE_MISSING")

    def test_review_is_not_declassification_or_runtime_assurance(self):
        review={"state":"approved","reviewers":["synthetic-reviewer"],"reviewed_at":"2026-11-06T00:00:00Z","rationale":"Synthetic review only."}
        decision=decide_scope("declassify",[local_scope("restricted")],destination=local_scope("public"),
                              review=review,authority={"kind":"human","id":"synthetic-reviewer"})
        self.assertEqual(decision["outcome"],"unavailable")
        self.assertEqual(decision["code"],"DECLASSIFICATION_UNAVAILABLE")
        self.assertEqual(decision["scope"]["visibility"],"restricted")
        self.assertNotIn("synthetic-reviewer",json.dumps(decision))

    def test_execution_persistence_and_publication_are_independent(self):
        source=local_scope("personal",execution="offline",publication="never-exportable")
        self.assertEqual(require_destination([source],local_scope("personal")),source)
        with self.assertRaisesRegex(ContractError,"EXECUTION_DENIED"):
            require_destination([source],local_scope("personal",execution="networked"))
        with self.assertRaisesRegex(ContractError,"OUTPUT_SCOPE"):
            require_destination([source],local_scope("personal",persistence="git-tracked"))
        with self.assertRaisesRegex(ContractError,"PUBLICATION_DENIED"):
            require_destination([local_scope("public")],local_scope("public",publication="publishable"),operation="export")

    def test_policy_cli_is_read_only_and_emits_no_supplied_authority_text(self):
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(["policy","inspect"]),0)
        self.assertEqual(json.loads(output.getvalue())["policy"],POLICY_REFERENCE)
        self.assertEqual(json.loads(output.getvalue())["organization_policy"],"unavailable")
        with TemporaryDirectory() as temporary:
            path=Path(temporary)/"request.json"
            request={"schema":"mindgarden.scope-request/v1","operation":"export","scopes":[local_scope()],"destination":local_scope("public")}
            content=canonical_json(request);path.write_bytes(content)
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(["policy","evaluate","--input",str(path)]),3)
            self.assertEqual(path.read_bytes(),content)
            self.assertNotIn(str(path),output.getvalue())
