"""Private operator preflight is metadata-only, non-destructive and fail closed."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.pilot import preflight
from mindgarden.domain.contracts import canonical_json
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests.research_fixture import create_fixture
from tests.support_v1 import write_json


class PilotTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(dir=Path("/var/tmp").resolve())
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.fixture = create_fixture(self.root)
        for key in ("configuration", "session_path"):
            self.fixture[key].chmod(0o600)
        self.fixture["garden"].chmod(0o700)
        self.binding = self.root / "drive-binding.json"
        shape = Path(__file__).parent / "fixtures/contracts/v1/valid/drive-binding.json"
        write_json(self.binding, json.loads(shape.read_bytes()))
        self.binding.chmod(0o600)

    def run_preflight(self, **kwargs):
        return preflight(
            self.fixture["configuration"],
            self.fixture["session_path"],
            "synthetic-garden",
            "synthetic-vault",
            "personal",
            **kwargs,
        )

    def test_metadata_only_local_readiness_keeps_files_identical_and_network_disabled(
        self,
    ):
        before = {
            p.relative_to(self.root): p.read_bytes()
            for p in self.root.rglob("*")
            if p.is_file()
        }
        original = Path.read_bytes

        def guard(path):
            if path.suffix != ".json" and path.is_relative_to(self.root):
                raise AssertionError("Original/body read in preflight")
            return original(path)

        with (
            patch.object(Path, "read_bytes", guard),
            patch.dict(os.environ, {}, clear=True),
            patch("socket.socket", side_effect=AssertionError("Network")),
        ):
            result = self.run_preflight()
        self.assertEqual(result["status"], "ready-to-attempt")
        self.assertEqual(
            [
                result[k]
                for k in ("original_reads", "network_calls", "model_calls", "writes")
            ],
            [0, 0, 0, 0],
        )
        self.assertNotIn(str(self.root).encode(), canonical_json(result))
        self.assertEqual(
            before,
            {
                p.relative_to(self.root): p.read_bytes()
                for p in self.root.rglob("*")
                if p.is_file()
            },
        )

    def test_drive_missing_credential_is_blocked_and_presence_is_never_live_authentication(
        self,
    ):
        with patch.dict(os.environ, {}, clear=True):
            result = self.run_preflight(drive_binding=self.binding)
        self.assertEqual(result["status"], "blocked")
        with (
            patch.dict(
                os.environ,
                {"MINDGARDEN_DRIVE_ACCESS_TOKEN": "synthetic-secret-never-output"},
                clear=True,
            ),
            patch("socket.socket", side_effect=AssertionError("Network")),
        ):
            result = self.run_preflight(drive_binding=self.binding)
        self.assertEqual(result["status"], "ready-to-attempt")
        self.assertIn(
            {"check": "cached-drive-credential", "status": "present-not-live-verified"},
            result["checks"],
        )
        self.assertNotIn("synthetic-secret", json.dumps(result))

    def test_restricted_classification_and_unsafe_control_permissions_are_blocked(self):
        with self.assertRaisesRegex(ContractError, "PILOT_CLASSIFICATION"):
            preflight(
                self.fixture["configuration"],
                self.fixture["session_path"],
                "synthetic-garden",
                "synthetic-vault",
                "restricted",
            )
        self.fixture["configuration"].chmod(0o644)
        with self.assertRaisesRegex(ContractError, "PILOT_LOCATION"):
            self.run_preflight()

    def test_invalid_capture_review_and_unknown_vault_manifest_are_not_readiness(self):
        binding = json.loads(self.binding.read_bytes())
        changed = deepcopy(binding)
        changed["review"]["state"] = "unreviewed"
        write_json(self.binding, changed)
        with self.assertRaises(ContractError):
            self.run_preflight(drive_binding=self.binding)
        write_json(self.binding, binding)
        (self.root / "vault/vault.json").write_bytes(b"{}")
        with self.assertRaisesRegex(ContractError, "PILOT_UNAVAILABLE"):
            self.run_preflight()

    def test_revoked_session_and_public_cli_diagnostic_do_not_expose_private_paths(
        self,
    ):
        config = json.loads(self.fixture["configuration"].read_bytes())
        config["revoked_sessions"].append(self.fixture["context"].session["id"])
        write_json(self.fixture["configuration"], config)
        with (
            redirect_stdout(io.StringIO()) as stdout,
            redirect_stderr(io.StringIO()) as stderr,
        ):
            result = main(
                [
                    "pilot",
                    "preflight",
                    "--local-config",
                    str(self.fixture["configuration"]),
                    "--scope",
                    str(self.fixture["session_path"]),
                    "--garden-id",
                    "synthetic-garden",
                    "--vault-id",
                    "synthetic-vault",
                    "--classification",
                    "personal",
                    "--diagnostic-format",
                    "json",
                ]
            )
        self.assertEqual(result, 3)
        self.assertEqual(stdout.getvalue(), "")
        self.assertNotIn(str(self.root), stderr.getvalue())
        self.assertIn("SESSION_REVOKED", stderr.getvalue())
