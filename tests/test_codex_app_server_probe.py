"""Offline regressions for a protocol probe that must stay disconnected."""

from contextlib import redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import monotonic
import unittest
from unittest.mock import patch

from scripts import check_codex_app_server as probe


class CodexAppServerProbeTests(unittest.TestCase):
    def test_sandbox_mounts_and_environment_exclude_credentials(self):
        original = {
            "HOME": "/home/example",
            "CODEX_HOME": "/home/example/.codex",
            "OPENAI_API_KEY": "credential-canary",
        }
        with patch.dict(os.environ, original, clear=True):
            command, environment = probe.sandbox_inputs(
                "/bin/bwrap",
                Path("/bin/codex-test"),
                Path("/var/tmp/probe-test"),
            )
            self.assertEqual(dict(os.environ), original)
        self.assertEqual(
            environment,
            {key: original[key] for key in ("HOME", "CODEX_HOME")},
        )
        self.assertIn("--unshare-all", command)
        self.assertIn("--die-with-parent", command)
        self.assertIn("--new-session", command)
        self.assertNotIn("--share-net", command)
        self.assertEqual(command.count("--bind"), 1)
        self.assertEqual(
            command[command.index("--bind") + 1 :][:2], ["/var/tmp/probe-test", "/work"]
        )
        self.assertEqual(command.count("--ro-bind"), 1)
        self.assertEqual(
            command[command.index("--ro-bind") + 1 :][:2],
            ["/bin/codex-test", "/probe/codex"],
        )

    @unittest.skipUnless(os.name == "posix", "Probe reads POSIX process pipes")
    def test_sends_only_handshake_messages(self):
        code = r"""
import json
import sys
request = json.loads(sys.stdin.readline())
assert request["method"] == "initialize"
print(json.dumps({
    "id": request["id"],
    "result": {"userAgent": "value-canary", "platformFamily": "unix", "platformOs": "linux"},
}) + "\n" + json.dumps({"method": "warning", "params": {"message": "value-canary"}}), flush=True)
assert json.loads(sys.stdin.readline()) == {"method": "initialized", "params": {}}
assert not sys.stdin.readline()
"""
        output = StringIO()
        with redirect_stdout(output):
            probe.handshake(
                [sys.executable, "-c", code],
                {},
                monotonic() + 4,
                {"userAgent", "platformFamily", "platformOs"},
            )
        self.assertEqual(output.getvalue(), "")

    @unittest.skipUnless(os.name == "posix", "Probe reads POSIX process pipes")
    def test_response_bounds_failure_and_child_cleanup(self):
        for code, reason in (
            ("print('x' * 100000, flush=True)", "stdout-limit"),
            (
                "print('{bad private-path-canary}', flush=True)",
                "handshake-incompatible",
            ),
            ("import time; time.sleep(60)", "timeout"),
        ):
            with self.subTest(reason=reason):
                real_popen = subprocess.Popen
                processes = []

                def observe(*args, **kwargs):
                    process = real_popen(*args, **kwargs)
                    processes.append(process)
                    return process

                with patch.object(probe.subprocess, "Popen", side_effect=observe):
                    with self.assertRaisesRegex(probe.ProbeBlocked, f"^{reason}$"):
                        probe.handshake(
                            [sys.executable, "-c", code],
                            {},
                            monotonic() + (0.05 if reason == "timeout" else 4),
                            {"userAgent"},
                        )
                self.assertEqual(len(processes), 1)
                self.assertIsNotNone(processes[0].poll())

    def test_schema_limits_and_missing_handshake_contract(self):
        with TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            directory = workspace / "schema"
            directory.mkdir()
            bundle = directory / probe.SCHEMA_BUNDLE
            bundle.write_text("{}")
            with self.assertRaisesRegex(probe.ProbeBlocked, "^schema-incompatible$"):
                probe.schema_check(workspace)
            bundle.write_bytes(b"x" * (probe.MAX_SCHEMA_BYTES + 1))
            with self.assertRaisesRegex(probe.ProbeBlocked, "^schema-limit$"):
                probe.schema_check(workspace)

    def test_no_isolation_stops_before_version_or_handshake(self):
        output = StringIO()
        with (
            patch.object(probe.sys, "platform", "darwin"),
            patch.object(
                probe.subprocess, "Popen", side_effect=AssertionError("Process started")
            ),
            patch.object(probe.sys, "argv", ["check_codex_app_server.py"]),
            redirect_stdout(output),
        ):
            self.assertEqual(probe.main(), 3)
        self.assertEqual(
            json.loads(output.getvalue()),
            {
                "status": "blocked",
                "reason": "isolation-unavailable",
                "connected": False,
                "account_checked": False,
                "model_calls": 0,
            },
        )
