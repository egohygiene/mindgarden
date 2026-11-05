"""Synthetic scope inheritance and explicit local binding contracts."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.bindings import LocalBindings, garden_fingerprint
from mindgarden.domain.contracts import ContractRegistry
from mindgarden.domain.scope import POLICY_REFERENCE, inherit_scope, local_scope, record_scope, validate_scope
from mindgarden.domain.validation import ContractError
from tests.support_v1 import add_knowledge, create_garden, write_json


class ScopeTests(unittest.TestCase):
    def test_independent_axes_and_restricted_requirements(self):
        scope = local_scope("personal", execution="networked", publication="never-exportable")
        self.assertEqual(scope["execution"], "networked")
        self.assertEqual(scope["publication"], "never-exportable")
        restricted = local_scope("restricted")
        self.assertEqual(ContractRegistry().errors(restricted, "scope"), [])
        restricted["persistence"] = "machine-local"
        with self.assertRaisesRegex(ContractError, "SCOPE_CONFLICT"):
            validate_scope(restricted)

    def test_inheritance_is_commutative_and_never_weakens_restrictions(self):
        public, personal, organization = [local_scope(value) for value in ("public", "personal", "organization")]
        self.assertEqual(inherit_scope([public, personal]), inherit_scope([personal, public]))
        self.assertEqual(inherit_scope([public, personal])["visibility"], "personal")
        mixed = inherit_scope([personal, organization])
        self.assertEqual(mixed["visibility"], "restricted")
        self.assertEqual(mixed["publication"], "never-exportable")
        self.assertEqual(mixed["persistence"], "encrypted-vault")
        self.assertEqual(mixed["execution"], "offline")

    def test_unknown_conflicting_and_missing_policy_fail_closed(self):
        for change in ({"policy": {"id": "unknown", "revision": "sha256:" + "0" * 64}},
                       {"visibility": "unknown"}, {"execution": "unknown"}):
            scope = {**local_scope(), **change}
            with self.assertRaises(ContractError):
                validate_scope(scope)
        with self.assertRaisesRegex(ContractError, "SCOPE_CONFLICT"):
            validate_scope(local_scope("personal"), "public")
        with self.assertRaisesRegex(ContractError, "SCOPE_MISSING"):
            record_scope({"visibility": "internal"}, local_scope("personal"))
        with self.assertRaisesRegex(ContractError, "SCOPE_MISSING"):
            inherit_scope([])


class BindingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.private = self.root / "private"
        create_garden(self.private)
        self.path = self.root / "bindings.json"
        self.document = {"schema": "mindgarden.local-bindings/v1", "gardens": [{
            "id": "synthetic-garden", "root": str(self.private), "scope": local_scope()}],
            "vaults": [{"id": "synthetic-vault", "root": str(self.root / "vault"), "adapter": "filesystem"}],
            "revoked_sessions": []}
        write_json(self.path, self.document)

    def test_bindings_do_not_modify_canonical_records_and_fingerprint_is_portable(self):
        before = garden_fingerprint(self.private)
        bindings = LocalBindings.load(self.path)
        self.assertEqual(bindings.garden("synthetic-garden")["root"], self.private)
        self.assertEqual(garden_fingerprint(self.private), before)
        record = add_knowledge(self.private)
        self.assertNotEqual(garden_fingerprint(self.private), before)
        self.assertNotIn(str(self.root), json.dumps(record))

    def test_duplicates_mismatched_identity_unsafe_and_nested_roots_fail(self):
        mutations = []
        duplicate = deepcopy(self.document)
        duplicate["gardens"].append(deepcopy(duplicate["gardens"][0]))
        mutations.append(duplicate)
        mismatch = deepcopy(self.document); mismatch["gardens"][0]["id"] = "other"
        mutations.append(mismatch)
        nested = deepcopy(self.document); nested["vaults"][0]["root"] = str(self.private / "vault")
        mutations.append(nested)
        unsafe = deepcopy(self.document); unsafe["gardens"][0]["root"] = "relative"
        mutations.append(unsafe)
        linked = self.root / "linked"; linked.symlink_to(self.private, target_is_directory=True)
        symlink = deepcopy(self.document); symlink["gardens"][0]["root"] = str(linked)
        mutations.append(symlink)
        for document in mutations:
            write_json(self.path, document)
            with self.assertRaises(ContractError):
                LocalBindings.load(self.path)

    def test_canonical_scope_and_machine_binding_must_agree(self):
        manifest_path = self.private / ".garden/garden.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["scope"] = local_scope("restricted")
        write_json(manifest_path, manifest)
        with self.assertRaisesRegex(ContractError, "BINDING_SCOPE"):
            LocalBindings.load(self.path)
