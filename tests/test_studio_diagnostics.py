"""Keep the local per-visit diagnostics inventory bounded and sanitized."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
from time import monotonic_ns
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.interfaces.studio_diagnostics import StudioDiagnostics


class StudioDiagnosticsTests(unittest.TestCase):
    def test_evicts_old_events_and_copies_the_snapshot_with_concurrent_writers(self):
        diagnostics = StudioDiagnostics()

        def record(_):
            diagnostics.record("private-provider-canary", "check", "private-code-canary", monotonic_ns())

        with ThreadPoolExecutor(max_workers=8) as workers:
            list(workers.map(record, range(95)))

        diagnostics.record("chatgpt", "private-operation-canary", "MODEL_BUSY", monotonic_ns())
        snapshot = diagnostics.snapshot()
        self.assertEqual(snapshot["capacity"], 80)
        self.assertEqual([item["id"] for item in snapshot["events"]], list(range(16, 96)))
        self.assertTrue(all(item["provider"] == "studio" for item in snapshot["events"]))
        self.assertTrue(all(item["code"] == "DIAGNOSTIC_UNAVAILABLE" for item in snapshot["events"]))
        self.assertNotIn("canary", str(snapshot))
        snapshot["events"][0]["code"] = "private-tampered-copy"
        self.assertEqual(diagnostics.snapshot()["events"][0]["code"], "DIAGNOSTIC_UNAVAILABLE")
        self.assertEqual(StudioDiagnostics().snapshot(), {"events": [], "capacity": 80})
