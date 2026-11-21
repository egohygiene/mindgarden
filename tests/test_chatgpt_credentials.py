"""Synthetic conformance for the protected single-owner credential store."""

from dataclasses import replace
import os
from pathlib import Path
import stat
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from uuid import UUID

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters import chatgpt_credentials as adapter
from mindgarden.adapters.chatgpt_credentials import ChatGPTCredentials, ChatGPTStore
from mindgarden.domain.contracts import canonical_json, read_object
from mindgarden.domain.validation import ContractError


EXAMPLE = ChatGPTCredentials(
    issuer="https://issuer.example.invalid",
    subject="synthetic-owner-subject",
    client_id="synthetic-client",
    scopes=("openid", "offline_access"),
    access_token="synthetic-access-token",
    refresh_token="synthetic-refresh-token",
    id_token="synthetic-id-token",
    expires_at=1893456000,
    earliest_refresh_at=1893455700,
)


@unittest.skipUnless(sys.platform in {"linux", "darwin"}, "Registry control paths use Linux and macOS")
class ChatGPTStoreTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.directory = self.root / "chatgpt-owner"
        self.store = ChatGPTStore(self.directory)
        self.connection = self.directory / "connection.json"
        self.host = self.directory / "host.json"

    def test_read_only_probes_do_not_initialize_owner_data(self):
        self.assertIsNone(self.store.read())
        self.assertIsNone(self.store.registration())
        self.assertFalse(self.directory.exists())

    def test_owner_and_host_survive_atomic_sign_out_and_same_owner_reconnect(self):
        with self.store.writer():
            identifier = self.store.host_id()
            self.assertEqual(UUID(identifier).version, 4)
            self.store.save(EXAMPLE)
        opened = ChatGPTStore(self.directory)
        self.assertEqual(opened.host_id(), identifier)
        self.assertEqual(opened.read(), EXAMPLE)
        self.assertEqual(opened.registration(), EXAMPLE.registration)
        self.assertEqual(stat.S_IMODE(self.directory.stat().st_mode), 0o700)
        self.assertEqual({stat.S_IMODE(path.stat().st_mode) for path in self.directory.iterdir()}, {0o600})

        opened.clear()
        self.assertEqual(opened.registration(), EXAMPLE.registration)
        self.assertEqual(opened.host_id(), identifier)
        self.assertIsNone(opened.read())
        self.assertIsNone(read_object(self.connection)["credentials"])
        for field in ("access_token", "refresh_token", "id_token"):
            token = getattr(EXAMPLE, field)
            self.assertNotIn(token, repr(EXAMPLE))
            self.assertFalse(any(token.encode() in path.read_bytes() for path in self.directory.iterdir()))
        self.assertNotIn(EXAMPLE.subject, repr(EXAMPLE.registration))
        rotated = replace(EXAMPLE, access_token="synthetic-renewal", earliest_refresh_at=None)
        opened.save(rotated)
        self.assertEqual(opened.read(), rotated)

    def test_owner_cannot_change_when_connected_or_after_clear(self):
        self.store.save(EXAMPLE)
        for connected in (True, False):
            if not connected:
                self.store.clear()
            prior = self.connection.read_bytes()
            for values in ({"issuer": "https://other.example.invalid"}, {"subject": "other-owner"}, {"client_id": "other-client"}):
                with self.subTest(connected=connected, values=values):
                    with self.assertRaisesRegex(ContractError, "CHATGPT_OWNER_MISMATCH") as captured:
                        self.store.save(replace(EXAMPLE, **values))
                    self.assertNotIn(EXAMPLE.subject, str(captured.exception))
                    self.assertEqual(self.connection.read_bytes(), prior)

    def test_writer_locks_other_store_instances_and_save_is_reentrant(self):
        other = ChatGPTStore(self.directory)
        with self.store.writer():
            self.store.save(EXAMPLE)
            with self.assertRaisesRegex(ContractError, "CHATGPT_STATE_BUSY"):
                other.clear()
            self.assertEqual(other.read(), EXAMPLE)
        other.clear()
        self.assertIsNone(self.store.read())

    def test_failed_replace_retains_previous_owner_tokens_and_cleans_temporary_file(self):
        self.store.save(EXAMPLE)
        previous = self.connection.read_bytes()
        rotation = replace(EXAMPLE, access_token="synthetic-not-committed")
        with (
            patch.object(adapter.os, "replace", side_effect=OSError(rotation.access_token)),
            self.assertRaisesRegex(ContractError, "CHATGPT_STATE_UNAVAILABLE") as captured,
        ):
            self.store.save(rotation)
        self.assertNotIn(rotation.access_token, str(captured.exception))
        self.assertTrue(captured.exception.__suppress_context__)
        self.assertEqual(self.connection.read_bytes(), previous)
        self.assertEqual(self.store.read(), EXAMPLE)
        self.assertFalse(any(path.name.startswith(".chatgpt-state-") for path in self.directory.iterdir()))

    def test_invalid_credentials_and_corrupt_envelopes_fail_closed(self):
        for values in (
            {"expires_at": True}, {"issuer": "https://user@example.invalid"}, {"refresh_token": "a\nb"},
            {"scopes": ("openid", "openid")}, {"id_token": "x" * (adapter.MAX_TOKEN_LENGTH + 1)},
        ):
            with self.subTest(fields=list(values)), self.assertRaisesRegex(ContractError, "CHATGPT_STATE_INVALID"):
                self.store.save(replace(EXAMPLE, **values))
        self.assertFalse(self.directory.exists())
        self.store.save(EXAMPLE)
        valid = read_object(self.connection)
        for invalid in (
            b'{"schema":"one","schema":"two"}', b" " * (adapter.MAX_STATE_BYTES + 1),
            canonical_json({**valid, "unexpected": "synthetic-private-input"}),
            canonical_json({**valid, "credentials": {**valid["credentials"], "scopes": "openid"}}),
        ):
            with self.subTest(length=len(invalid)):
                self.connection.write_bytes(invalid)
                with self.assertRaisesRegex(ContractError, "CHATGPT_STATE_INVALID") as captured:
                    self.store.read()
                self.assertNotIn("synthetic-private-input", str(captured.exception))
                with self.assertRaisesRegex(ContractError, "CHATGPT_STATE_INVALID"):
                    self.store.clear()
                self.assertEqual(self.connection.read_bytes(), invalid)

    def test_insecure_file_and_directory_aliases_fail_before_read_or_update(self):
        self.store.save(EXAMPLE)
        self.directory.chmod(0o755)
        with self.assertRaisesRegex(ContractError, "CHATGPT_STATE_UNAVAILABLE"):
            self.store.read()
        self.directory.chmod(0o700)
        self.connection.chmod(0o644)
        with self.assertRaisesRegex(ContractError, "CHATGPT_STATE_UNAVAILABLE"):
            self.store.read()
        self.connection.chmod(0o600)
        alias = self.root / "other-directory"
        alias.symlink_to(self.directory, target_is_directory=True)
        with self.assertRaisesRegex(ContractError, "CHATGPT_STATE_UNAVAILABLE"):
            ChatGPTStore(alias).read()
        copy = self.root / "other-file"
        os.link(self.connection, copy)
        with self.assertRaisesRegex(ContractError, "CHATGPT_STATE_UNAVAILABLE"):
            self.store.clear()
        copy.unlink()
        self.connection.rename(copy)
        self.connection.symlink_to(copy)
        with self.assertRaisesRegex(ContractError, "CHATGPT_STATE_UNAVAILABLE"):
            self.store.registration()
        self.assertEqual(read_object(copy)["credentials"]["access_token"], EXAMPLE.access_token)

    def test_state_paths_inside_git_and_garden_are_rejected(self):
        git = self.root / "versioned"
        git.mkdir()
        (git / ".git").write_text("gitdir: owner-test-fixture\n")
        garden = self.root / "garden"
        manifest = garden / ".garden/garden.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text("{}\n")
        for parent in (git, garden):
            with self.subTest(parent=parent.name):
                selected = parent / "owner-state"
                untrusted = ChatGPTStore(selected)
                with self.assertRaisesRegex(ContractError, "CHATGPT_STATE_UNAVAILABLE"):
                    untrusted.read()
                with self.assertRaisesRegex(ContractError, "CHATGPT_STATE_UNAVAILABLE"):
                    untrusted.host_id()
                self.assertFalse(selected.exists())
