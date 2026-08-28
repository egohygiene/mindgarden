# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

MINDGARDEN_ROOT = Path(__file__).parents[1]
SOURCE_ROOT = MINDGARDEN_ROOT / "src"
FIXTURE_ROOT = MINDGARDEN_ROOT / "tests/fixtures/public-garden"
sys.path.insert(0, str(SOURCE_ROOT))

import mindgarden  # noqa: E402
from mindgarden.interfaces.cli import ExitCode, build_parser, main  # noqa: E402


class PackageTests(unittest.TestCase):
    def test_public_library_operates_without_network_access(self) -> None:
        with patch("socket.socket", side_effect=AssertionError("network access attempted")):
            self.assertEqual(mindgarden.validate_repository(FIXTURE_ROOT), 3)
            index = mindgarden.build_index(FIXTURE_ROOT)

        self.assertEqual(index["schema"], "mindgarden.index/v0")
        self.assertEqual(len(index["notes"]), 3)

    def test_unified_validate_verify_and_publish_commands(self) -> None:
        for arguments, expected_fragment in (
            (
                ["validate", "--repository-root", str(FIXTURE_ROOT)],
                "validation passed",
            ),
            (
                ["verify", "--repository-root", str(FIXTURE_ROOT)],
                "agent verification passed",
            ),
            (
                ["publish", "verify", "--repository-root", str(FIXTURE_ROOT)],
                "Verified deterministic public projection",
            ),
        ):
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(arguments), ExitCode.SUCCESS)
            self.assertIn(expected_fragment, output.getvalue())

    def test_cli_exposes_every_compatibility_command(self) -> None:
        help_text = build_parser().format_help()
        for command in (
            "validate",
            "ingest",
            "index",
            "search",
            "context",
            "llms",
            "publish",
            "site",
            "verify",
            "version",
        ):
            self.assertIn(command, help_text)

        site = build_parser().parse_args(
            ["site", "build", "--repository-root", str(FIXTURE_ROOT)]
        )
        self.assertEqual(site.repository_root, FIXTURE_ROOT)
        self.assertEqual(site.command, "build")

        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(["version"]), ExitCode.SUCCESS)
        self.assertEqual(output.getvalue().strip(), f"mindgarden {mindgarden.__version__}")

    def test_contract_failure_has_stable_exit_code_and_diagnostic(self) -> None:
        missing = FIXTURE_ROOT / "missing"
        with redirect_stderr(io.StringIO()) as error:
            result = main(["validate", "--repository-root", str(missing)])

        self.assertEqual(result, ExitCode.CONTRACT)
        self.assertIn("mindgarden contract error:", error.getvalue())
        self.assertIn("missing garden manifest", error.getvalue())

    def test_module_entrypoint_reports_package_version(self) -> None:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(SOURCE_ROOT)
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "mindgarden", "--version"],
            check=True,
            capture_output=True,
            encoding="utf8",
            env=environment,
        )
        self.assertEqual(result.stdout.strip(), f"mindgarden {mindgarden.__version__}")

    def test_legacy_script_entrypoint_remains_available(self) -> None:
        result = subprocess.run(  # noqa: S603
            [
                sys.executable,
                str(MINDGARDEN_ROOT / "scripts/validate_garden.py"),
                "--repository-root",
                str(FIXTURE_ROOT),
            ],
            check=True,
            capture_output=True,
            encoding="utf8",
        )
        self.assertIn("mindgarden validation passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
