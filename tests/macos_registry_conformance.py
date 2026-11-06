"""Native Darwin ACL controls, run explicitly by the macOS CI job."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.registry_files import create_control, read_control, registry_writer
from mindgarden.application.bindings import explicit_root
from mindgarden.domain.validation import ContractError


class NativeMacRegistryTests(unittest.TestCase):
    def setUp(self):
        self.assertEqual(sys.platform, "darwin", "This conformance scenario requires an actual macOS host")
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.path = self.root / "control/registry.json"
        self.content = b"Wholly synthetic private registry canary.\n"
        create_control(self.path, self.content)
        self.assertEqual(read_control(self.path), self.content)

    def add_extended_read(self, path):
        subprocess.run(["/bin/chmod", "+a", "everyone allow read", str(path)], check=True,
                       capture_output=True, text=True)

    def test_native_acl_grant_on_0600_file_is_rejected_without_mutation(self):
        self.add_extended_read(self.path)
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        with self.assertRaisesRegex(ContractError, "REGISTRY_ACL:"): read_control(self.path)
        self.assertEqual(self.path.read_bytes(), self.content)

    def test_native_acl_on_0700_directory_is_rejected_before_a_write(self):
        self.add_extended_read(self.path.parent)
        self.assertEqual(self.path.parent.stat().st_mode & 0o777, 0o700)
        target = self.path.parent / "must-not-be-created.json"
        with self.assertRaisesRegex(ContractError, "REGISTRY_ACL:"): create_control(target, self.content)
        self.assertFalse(target.exists())

    def test_native_acl_on_writer_lease_is_rejected(self):
        with registry_writer(self.path): pass
        lock = self.path.parent / ("." + self.path.name + ".lock")
        self.add_extended_read(lock)
        self.assertEqual(lock.stat().st_mode & 0o777, 0o600)
        with self.assertRaisesRegex(ContractError, "REGISTRY_ACL:"):
            with registry_writer(self.path): self.fail("Unverified lease granted")
        self.assertEqual(self.path.read_bytes(), self.content)

    def test_native_control_case_alias_is_denied_or_a_distinct_missing_file(self):
        alias = self.path.with_name("Registry.json")
        if alias.exists():
            self.assertTrue(alias.samefile(self.path))
            with self.assertRaisesRegex(ContractError, "REGISTRY_PATH:"): read_control(alias)
        else:
            self.assertIsNone(read_control(alias, missing_ok=True))
        self.assertEqual(read_control(self.path), self.content)

    def test_native_root_case_alias_is_denied_or_a_distinct_directory(self):
        root = self.root / "CanonicalGarden"; root.mkdir()
        self.assertEqual(explicit_root(str(root)), root)
        alias = root.with_name("canonicalgarden")
        if alias.exists():
            self.assertTrue(alias.samefile(root))
            with self.assertRaisesRegex(ContractError, "BINDING_PATH:"): explicit_root(str(alias))
        else:
            alias.mkdir()
            self.assertFalse(alias.samefile(root))
            self.assertEqual(explicit_root(str(alias)), alias)
