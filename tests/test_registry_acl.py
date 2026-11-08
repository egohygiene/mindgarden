"""ACL boundary doubles exercise denial before private bytes, on every test host."""

import ctypes
import errno
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.registry_files import create_control, read_control
from mindgarden.domain.validation import ContractError


class ACLDouble:
    def __init__(self, outcome): self.outcome, self.freed = outcome, []

    def acl_get_fd_np(self, descriptor, kind):
        assert kind == 0x100
        if stat.S_ISDIR(os.fstat(descriptor).st_mode) or self.outcome == "absent":
            ctypes.set_errno(errno.ENOENT); return None
        if self.outcome == "unavailable":
            ctypes.set_errno(errno.EACCES); return None
        if self.outcome == "unknown-null":
            ctypes.set_errno(0); return None
        return 1

    def acl_valid(self, acl): return -1 if self.outcome == "invalid" else 0

    def acl_get_entry(self, acl, kind, entry):
        assert kind == 0
        if self.outcome == "entry": return 0
        ctypes.set_errno(errno.EIO if self.outcome == "unknown-entry" else errno.EINVAL)
        return -1

    def acl_free(self, acl):
        self.freed.append(acl)
        return -1 if self.outcome == "free-error" else 0


class RegistryACLTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.path = self.root / "control/registry.json"
        self.content = b"Synthetic private control canary.\n"
        create_control(self.path, self.content)

    def test_private_mode_with_an_extended_entry_denies_before_body_read(self):
        double = ACLDouble("entry")
        with patch("sys.platform", "darwin"), patch("mindgarden.adapters.registry_acl.native_acl_api", return_value=double), \
                patch("mindgarden.adapters.registry_files.require_canonical_path"), \
                patch("os.fdopen", side_effect=AssertionError("Private bytes opened before ACL decision")):
            with self.assertRaisesRegex(ContractError, "REGISTRY_ACL:"): read_control(self.path)
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.path.read_bytes(), self.content)
        self.assertEqual(double.freed, [1])

    def test_absent_and_empty_acl_allow_the_existing_private_control(self):
        for outcome in ("absent", "empty"):
            double = ACLDouble(outcome)
            with self.subTest(outcome=outcome), patch("sys.platform", "darwin"), \
                    patch("mindgarden.adapters.registry_files.require_canonical_path"), \
                    patch("mindgarden.adapters.registry_acl.native_acl_api", return_value=double):
                self.assertEqual(read_control(self.path), self.content)
            self.assertEqual(double.freed, [] if outcome == "absent" else [1])

    def test_unknown_invalid_or_unavailable_acl_never_reads_control_bytes(self):
        for outcome in ("unavailable", "unknown-null", "invalid", "unknown-entry", "free-error"):
            double = ACLDouble(outcome)
            with self.subTest(outcome=outcome), patch("sys.platform", "darwin"), \
                    patch("mindgarden.adapters.registry_files.require_canonical_path"), \
                    patch("mindgarden.adapters.registry_acl.native_acl_api", return_value=double), \
                    patch("os.fdopen", side_effect=AssertionError("Unverified private bytes read")):
                with self.assertRaisesRegex(ContractError, "REGISTRY_ACL_UNAVAILABLE"): read_control(self.path)
            self.assertEqual(self.path.read_bytes(), self.content)

    def test_missing_native_interface_fails_before_any_new_control_write(self):
        target = self.root / "not-created/registry.json"
        with patch("sys.platform", "darwin"), patch("mindgarden.adapters.registry_acl.native_acl_api",
                side_effect=ContractError("REGISTRY_PLATFORM: synthetic unavailable native API")):
            with self.assertRaisesRegex(ContractError, "REGISTRY_PLATFORM"): create_control(target, self.content)
        self.assertFalse(target.parent.exists())
