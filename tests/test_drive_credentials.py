"""OAuth setup is opt-in; credentials stay private and offline tests use fakes."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.drive_credentials import (
    READ_SCOPE,
    TOKEN_URI,
    authorize,
    cached_access_token,
)
from mindgarden.domain.contracts import canonical_json
from mindgarden.domain.validation import ContractError


class DriveCredentialsTests(unittest.TestCase):
    def setUp(self):
        # The managed environment can itself mount /tmp as a Git worktree.
        # Exercise credential storage outside Git rather than weakening the guard.
        temporary = TemporaryDirectory(dir=Path("/var/tmp").resolve())
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.client = self.root / "client.json"
        self.token = self.root / "token.json"
        self.client.write_bytes(
            canonical_json(
                {
                    "installed": {
                        "client_id": "synthetic-client",
                        "client_secret": "synthetic-private-secret",
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": TOKEN_URI,
                    }
                }
            )
        )
        self.client.chmod(0o600)
        self.saved = {
            "client_id": "synthetic-client",
            "client_secret": "synthetic-private-secret",
            "token_uri": TOKEN_URI,
            "token": "synthetic-access-token",
            "refresh_token": "synthetic-refresh-token",
            "expiry": "2099-01-01T00:00:00Z",
        }

    def test_desktop_setup_requests_readonly_pkce_loopback_and_writes_private_token(
        self,
    ):
        events = []
        credential = SimpleNamespace(to_json=lambda: json.dumps(self.saved))

        def factory(client, **kwargs):
            events.append(kwargs)

            def run(**options):
                events.append(options)
                return credential

            return SimpleNamespace(
                oauth2session=SimpleNamespace(request=lambda *_a, **_k: None),
                run_local_server=run,
            )

        result = authorize(self.client, self.token, flow_factory=factory)
        self.assertEqual(
            events[0], {"scopes": [READ_SCOPE], "autogenerate_code_verifier": True}
        )
        self.assertEqual(events[1]["host"], "127.0.0.1")
        self.assertEqual(events[1]["timeout_seconds"], 180)
        self.assertEqual(self.token.stat().st_mode & 0o777, 0o600)
        self.assertNotIn("synthetic-access-token", json.dumps(result))
        with patch.dict(
            os.environ, {"MINDGARDEN_DRIVE_TOKEN_FILE": str(self.token)}, clear=True
        ):
            self.assertEqual(cached_access_token(), "synthetic-access-token")
            with self.assertRaisesRegex(ContractError, "CAPTURE_AUTH_EXPIRED"):
                cached_access_token(
                    clock=lambda: datetime(2100, 1, 1, tzinfo=timezone.utc)
                )

    def test_no_credentials_are_written_inside_git_or_from_non_google_client(self):
        (self.root / ".git").mkdir()
        with self.assertRaisesRegex(ContractError, "CAPTURE_AUTH_LOCATION"):
            authorize(
                self.client,
                self.token,
                flow_factory=lambda *_a, **_k: self.fail("SDK invoked"),
            )
        (self.root / ".git").rmdir()
        value = json.loads(self.client.read_bytes())
        value["installed"]["token_uri"] = "https://example.invalid/token"
        self.client.write_bytes(canonical_json(value))
        with self.assertRaisesRegex(ContractError, "CAPTURE_AUTH_CONFIG"):
            authorize(
                self.client,
                self.token,
                flow_factory=lambda *_a, **_k: self.fail("SDK invoked"),
            )
        self.assertFalse(self.token.exists())

    def test_refresh_calls_only_canonical_endpoint_with_bounded_network_and_no_secret_output(
        self,
    ):
        self.token.write_bytes(
            canonical_json(
                {
                    "schema": "mindgarden.local-drive-credential/v1",
                    "scopes": [READ_SCOPE],
                    "credentials": self.saved,
                }
            )
        )
        self.token.chmod(0o600)
        calls = []

        def request(**kwargs):
            calls.append(kwargs)
            return None

        def factory(value, scopes):
            def refresh(transport):
                transport(TOKEN_URI, method="POST", body=b"synthetic-private-body")

            return SimpleNamespace(
                refresh=refresh, to_json=lambda: json.dumps(self.saved)
            )

        result = authorize(
            None,
            self.token,
            refresh=True,
            flow_factory=lambda: None,
            credentials_factory=factory,
            token_request=request,
        )
        self.assertEqual(calls[0]["timeout"], 10)
        self.assertFalse(calls[0]["allow_redirects"])
        self.assertNotIn("synthetic-private", json.dumps(result))
        with patch.dict(
            os.environ,
            {
                "MINDGARDEN_DRIVE_ACCESS_TOKEN": "one",
                "MINDGARDEN_DRIVE_TOKEN_FILE": str(self.token),
            },
            clear=True,
        ):
            with self.assertRaisesRegex(ContractError, "CAPTURE_AUTH_CONFIG"):
                cached_access_token()
