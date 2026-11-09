"""Synthetic child processes stay in the ordinary local reader's owned lifetime."""

import json
import os
from pathlib import Path
import stat
import sys
from tempfile import TemporaryDirectory
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.pdf_tools import LocalPDFReader, run_tool
from mindgarden.domain.validation import ContractError

PROBE = Path(__file__).parent / "fixtures/documents/runner_probe.py"


@unittest.skipUnless(
    sys.platform.startswith("linux"), "bounded PDF process runner supports Linux"
)
class PDFProcessLifecycleTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def assert_stopped(self, pid):
        deadline = time.monotonic() + 1
        while time.monotonic() < deadline:
            try:
                state = (
                    Path(f"/proc/{pid}/stat").read_text().split(")", 1)[1].split()[0]
                )
            except FileNotFoundError:
                return
            if state == "Z":
                return
            time.sleep(0.01)
        self.fail("Synthetic reader descendant is still running")

    def probe(self, mode):
        return run_tool(
            Path(sys.executable), ["-I", "-S", str(PROBE), mode], b"", self.root
        )

    def test_completed_parent_cannot_leave_a_running_group_child(self):
        status, content, errors = self.probe("complete")
        self.assertEqual((status, content, errors), (0, b"", b""))
        state = json.loads((self.root / "probe-state.json").read_bytes())
        self.assertEqual(state["pid"], state["group"])
        self.assert_stopped(state["child_pid"])

    def test_timeout_stops_the_entire_started_group_without_input_diagnostics(self):
        with patch("mindgarden.adapters.pdf_tools.TOOL_TIMEOUT_SECONDS", 1):
            with self.assertRaisesRegex(ContractError, "DOCUMENT_LIMIT") as error:
                self.probe("timeout")
        self.assertNotIn(str(self.root), str(error.exception))
        state = json.loads((self.root / "probe-state.json").read_bytes())
        self.assert_stopped(state["pid"])
        self.assert_stopped(state["child_pid"])

    def test_created_files_are_owner_only_and_environment_is_vault_local(self):
        with patch.dict(
            os.environ, {"SYNTHETIC_PROVIDER_SECRET": "not-inherited-canary"}
        ):
            self.probe("complete")
        state = json.loads((self.root / "probe-state.json").read_bytes())
        self.assertEqual(state["cwd"], str(self.root))
        self.assertNotIn("SYNTHETIC_PROVIDER_SECRET", state["environment"])
        for name in (
            "HOME",
            "TMPDIR",
            "TMP",
            "TEMP",
            "XDG_CACHE_HOME",
            "XDG_CONFIG_HOME",
            "XDG_DATA_HOME",
            "XDG_STATE_HOME",
        ):
            self.assertEqual(state["environment"][name], str(self.root))
        for path in self.root.iterdir():
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_resource_failure_does_not_echo_stderr_or_payload(self):
        source = "import sys; sys.stderr.write('private-reader-canary'); sys.stdout.buffer.write(b'x' * 9000000)"
        with self.assertRaisesRegex(ContractError, "DOCUMENT_LIMIT") as error:
            run_tool(Path(sys.executable), ["-I", "-S", "-c", source], b"", self.root)
        self.assertNotIn("canary", str(error.exception))

    def test_unavailable_tool_is_constant_and_retains_no_work_files(self):
        with self.assertRaisesRegex(ContractError, "DOCUMENT_UNAVAILABLE") as error:
            LocalPDFReader(self.root / "private-tool-canary", self.root).read(
                b"%PDF-1.7\nSynthetic"
            )
        self.assertNotIn("canary", str(error.exception))
        self.assertEqual(list(self.root.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
