"""Subprocess doubles for the opt-in Codex status check."""

import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from mindgarden.adapters import studio_codex


RPC_DOUBLE = r"""
import json
import sys
import time

case = json.loads(sys.argv[1])

def receive(method):
    frame = json.loads(sys.stdin.readline())
    assert frame["method"] == method
    return frame

def send(frame):
    print(json.dumps(frame), flush=True)

initial = receive("initialize")
assert initial["params"]["clientInfo"]["name"] == "mindgarden_studio"
if case.get("timeout"):
    time.sleep(60)
if case.get("oversize"):
    print("x" * 100000, flush=True)
    sys.exit(0)
if case.get("unexpected_request"):
    send({"id": 78, "method": "tool/requestUserInput", "params": {"payload": "private-canary"}})
    assert not sys.stdin.readline()
    sys.exit(0)
send({"id": initial["id"], "result": {"userAgent": "local-runtime", "codexHome": "/private-canary"}})
send({"method": "warning", "params": {"message": "private-canary"}})
assert receive("initialized") == {"method": "initialized", "params": {}}
account = receive("account/read")
assert account["params"] == {"refreshToken": False}
send({"id": account["id"], "result": case["account"]})
if "quota" in case:
    request = receive("account/rateLimits/read")
    assert request["params"] == {}
    send({"id": request["id"], **case["quota"]})
assert not sys.stdin.readline()
"""


@unittest.skipUnless(os.name == "posix", "Codex status check uses local POSIX stdio")
class StudioCodexTests(unittest.TestCase):
    def check_with(self, case, *, expect_clean_exit=True):
        launch = subprocess.Popen
        observed = []

        def isolated_double(command, **options):
            self.assertEqual(
                command[:5],
                [
                    "/fixture/bin/codex",
                    "app-server",
                    "--listen",
                    "stdio://",
                    "--strict-config",
                ],
            )
            for feature in ("hooks", "plugins", "shell_tool", "workspace_dependencies"):
                self.assertIn(("--disable", feature), list(zip(command, command[1:])))
            self.assertIn(
                'chatgpt_base_url="https://chatgpt.com/backend-api/"', command
            )
            self.assertNotIn("cloud-canary", options["env"].values())
            self.assertNotIn("OPENAI_API_KEY", options["env"])
            self.assertEqual(options["env"]["HOME"], "/fixture/home")
            self.assertEqual(options["env"]["CODEX_HOME"], "/fixture/home/.codex")
            self.assertEqual(
                options["env"]["CODEX_INTERNAL_APP_SERVER_REMOTE_CONTROL_DISABLED"], "1"
            )
            self.assertIs(options["stderr"], subprocess.DEVNULL)
            self.assertTrue(options["start_new_session"])
            workspace = Path(options["cwd"])
            self.assertEqual(list(workspace.iterdir()), [])
            process = launch(
                [sys.executable, "-S", "-c", RPC_DOUBLE, json.dumps(case)], **options
            )
            observed.append((process, workspace))
            return process

        environment = {
            "HOME": "/fixture/home",
            "CODEX_HOME": "/fixture/home/.codex",
            "CODEX_API_KEY": "cloud-canary",
            "OPENAI_API_KEY": "cloud-canary",
        }
        with (
            patch.object(studio_codex.sys, "platform", "linux"),
            patch.object(
                studio_codex.shutil, "which", return_value="/fixture/bin/codex"
            ),
            patch.object(studio_codex.subprocess, "Popen", side_effect=isolated_double),
            patch.dict(os.environ, environment, clear=True),
        ):
            result = studio_codex.CodexProvider().check()
            self.assertEqual(dict(os.environ), environment)
        self.assertEqual(len(observed), 1)
        process, workspace = observed[0]
        self.assertIsNotNone(process.poll())
        if expect_clean_exit:
            self.assertEqual(process.returncode, 0)
        self.assertFalse(workspace.exists())
        self.assertNotIn("private-canary", json.dumps(result))
        self.assertFalse(result["can_run"])
        self.assertEqual(result["models"], [])
        return result

    def test_chatgpt_reports_only_valid_windows_and_credit_fields(self):
        result = self.check_with(
            {
                "account": {
                    "account": {
                        "type": "chatgpt",
                        "planType": "plus",
                        "email": "private-canary",
                    },
                    "requiresOpenaiAuth": True,
                },
                "quota": {
                    "result": {
                        "accountId": "private-canary",
                        "rateLimits": {
                            "primary": {
                                "usedPercent": 37,
                                "windowDurationMins": 300,
                                "resetsAt": 1790000000,
                            },
                            "secondary": {
                                "usedPercent": True,
                                "windowDurationMins": 30,
                            },
                            "credits": {
                                "balance": "12.50",
                                "hasCredits": True,
                                "unlimited": False,
                            },
                        },
                    },
                },
            }
        )
        self.assertEqual(result["status"], "ready")
        self.assertIn("Plus", result["detail"])
        self.assertEqual(
            result["limits"],
            {
                "windows": [
                    {
                        "label": "Primary quota",
                        "used_percent": 37,
                        "window_minutes": 300,
                        "resets_at": 1790000000,
                    },
                ],
                "credits": {
                    "balance": "12.50",
                    "has_credits": True,
                    "unlimited": False,
                },
            },
        )

    def test_disconnected_and_api_key_skip_chatgpt_quota(self):
        for account, expected in (
            (None, "unconfigured"),
            ({"type": "apiKey"}, "ready"),
        ):
            with self.subTest(account=account):
                result = self.check_with(
                    {"account": {"account": account, "requiresOpenaiAuth": True}}
                )
                self.assertEqual(result["status"], expected)
                self.assertNotIn("limits", result)
                if account:
                    self.assertIn("API billing", result["detail"])

    def test_rpc_quota_failure_leaves_cached_sign_in_and_returns_no_details(self):
        result = self.check_with(
            {
                "account": {
                    "account": {"type": "chatgpt", "planType": "private-canary"},
                    "requiresOpenaiAuth": True,
                },
                "quota": {"error": {"code": -32603, "message": "private-canary"}},
            }
        )
        self.assertEqual(result["status"], "ready")
        self.assertIn("Quota details are unavailable.", result["detail"])
        self.assertNotIn("limits", result)

    def test_unexpected_server_request_is_refused_without_an_account_probe(self):
        self.assertEqual(
            self.check_with({"unexpected_request": True})["status"], "unavailable"
        )

    def test_byte_and_time_limits_stop_and_reap_the_process(self):
        with patch.object(studio_codex, "TIMEOUT_SECONDS", 0.15):
            for case in ("timeout", "oversize"):
                with self.subTest(case=case):
                    self.assertEqual(
                        self.check_with({case: True}, expect_clean_exit=False)[
                            "status"
                        ],
                        "unavailable",
                    )

    def test_missing_binary_skips_the_process(self):
        with (
            patch.object(studio_codex.sys, "platform", "darwin"),
            patch.object(studio_codex.shutil, "which", return_value=None),
            patch.object(
                studio_codex.subprocess,
                "Popen",
                side_effect=AssertionError("Codex started"),
            ),
        ):
            result = studio_codex.CodexProvider().check()
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("Install the Codex CLI", result["detail"])

    def test_npm_launcher_finds_node_on_operator_path(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            tools = root / "bin"
            tools.mkdir()
            launcher = tools / "codex"
            launcher.write_text("#!/usr/bin/env node\n")
            launcher.chmod(0o700)
            fake_node = tools / "node"
            fixture = root / "fake-runtime.py"
            fixture.write_text(RPC_DOUBLE)
            case = json.dumps(
                {"account": {"account": None, "requiresOpenaiAuth": True}}
            )
            fake_node.write_text(
                "#!/bin/sh\nexec "
                + shlex.join([sys.executable, "-S", str(fixture), case])
                + "\n"
            )
            fake_node.chmod(0o700)
            with (
                patch.object(studio_codex.sys, "platform", "darwin"),
                patch.dict(os.environ, {"PATH": str(tools)}, clear=True),
            ):
                result = studio_codex.CodexProvider().check()
        self.assertEqual(result["status"], "unconfigured")
        self.assertFalse(result["can_run"])
