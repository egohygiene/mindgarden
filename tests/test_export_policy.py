"""Reviewed exports retain every contributing policy axis before body access."""

from copy import deepcopy
from itertools import permutations
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.federation import build_federation
from mindgarden.domain.contracts import ContractRegistry, canonical_json
from mindgarden.domain.scope import POLICY_REFERENCE, inherit_scope, local_scope
from mindgarden.domain.scope_policy import decide_scope
from mindgarden.domain.validation import ContractError
from tests.federation_fixture import create_fixture


class ExportPolicyTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.fixture = create_fixture(Path(temporary.name) / "public")
        self.context = self.fixture["context"]
        self.profile = deepcopy(self.fixture["profile"])

    def test_execution_and_persistence_weakening_deny_before_index_access(self):
        for changes, code in (
            ({"execution": "networked"}, "EXECUTION_DENIED"),
            ({"execution": "controlled-import"}, "EXECUTION_DENIED"),
            ({"persistence": "git-tracked"}, "OUTPUT_SCOPE"),
            ({"persistence": "encrypted-vault"}, "RUNTIME_UNVERIFIED"),
        ):
            self.profile["scope"] = local_scope(
                "public", publication="publishable", **changes
            )
            with (
                self.subTest(changes=changes),
                patch(
                    "mindgarden.application.federation.build_index",
                    side_effect=AssertionError("Bodies opened"),
                ),
                self.assertRaisesRegex(ContractError, code),
            ):
                build_federation(self.context, self.profile)

    def test_explicit_compatible_scope_preserves_all_existing_public_bytes(self):
        self.profile["scope"] = local_scope("public", publication="publishable")
        self.assertEqual(
            build_federation(self.context, self.profile).files,
            self.fixture["bundle"].files,
        )
        self.assertEqual(self.context.session["policy"], POLICY_REFERENCE)

    def test_review_does_not_override_unknown_policy_or_publication_limits(self):
        for changes, code in (
            ({"publication": "never-exportable"}, "FEDERATION_SCOPE"),
            (
                {"policy": {"id": "unknown", "revision": "sha256:" + "0" * 64}},
                "POLICY_UNSUPPORTED",
            ),
        ):
            self.profile["scope"] = {
                **local_scope("public", publication="publishable"),
                **changes,
            }
            with (
                self.subTest(changes=changes),
                self.assertRaisesRegex(ContractError, code),
            ):
                build_federation(self.context, self.profile)

    def test_sensitivity_join_is_order_independent_and_never_downgrades_mixed_inputs(
        self,
    ):
        scopes = [
            local_scope(value)
            for value in ("public", "organization", "personal", "restricted")
        ]
        for ordered in permutations(scopes):
            self.assertEqual(inherit_scope(list(ordered)), local_scope("restricted"))
            self.assertEqual(
                inherit_scope([inherit_scope(list(ordered[:2])), *ordered[2:]]),
                local_scope("restricted"),
            )

    def test_unsupported_operation_diagnostics_never_echo_supplied_text(self):
        decision = decide_scope("private-operation-canary", [local_scope()])
        self.assertEqual(
            (decision["operation"], decision["outcome"], decision["code"]),
            ("unsupported", "deny", "SCOPE_OPERATION"),
        )
        self.assertNotIn(b"canary", canonical_json(decision))
        self.assertEqual(ContractRegistry().errors(decision, "scope-decision"), [])


if __name__ == "__main__":
    unittest.main()
