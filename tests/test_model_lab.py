"""Test per-request model selection and disclosure with offline adapters."""

import threading
import unittest
from unittest.mock import Mock, patch

from mindgarden.application.model_lab import MAX_RESULT_BYTES, ModelLab, PROMPT, SCENARIO
from mindgarden.domain.validation import ContractError


def fixture_provider(provider_id, disclosure, *, can_run=True):
    provider = Mock(id=provider_id, disclosure=disclosure)
    provider.name = provider_id
    provider.check.return_value = {
        "status": "ready",
        "detail": "Fictional connected provider",
        "models": [{"id": "small", "label": "Small"}, {"id": "large", "label": "Large"}],
        "can_run": can_run,
    }
    provider.run.return_value = "January's net movement was 2259.76 USD [S1]."
    return provider


class ModelLabTests(unittest.TestCase):
    def setUp(self):
        self.gemini = fixture_provider("gemini", "cloud")
        self.ollama = fixture_provider("ollama", "loopback")
        self.codex = fixture_provider("codex", "cloud", can_run=False)
        self.lab = ModelLab((self.codex, self.gemini, self.ollama))
        self.selected = {"provider": "gemini", "model": "small"}

    def approve(self):
        preview = self.lab.preview(self.selected)
        self.assertEqual(preview["prompt"], PROMPT)
        self.assertEqual(preview["scenario"], SCENARIO["id"])
        self.assertEqual(preview["disclosure"], "cloud")
        return {**self.selected, "preview_sha256": preview["preview_sha256"]}

    def test_lookup_and_preview_do_not_call_adapters(self):
        snapshot = self.lab.snapshot()
        self.assertEqual([item["status"] for item in snapshot["providers"]], ["unchecked"] * 3)
        with self.assertRaisesRegex(ContractError, "MODEL_NOT_CONFIGURED"):
            self.lab.preview(self.selected)
        for provider in (self.gemini, self.ollama, self.codex):
            self.assertEqual(provider.mock_calls, [])

    def test_approved_request_dispatches_once_and_cannot_change_model_or_provider(self):
        for provider in ("gemini", "ollama"):
            self.lab.check({"provider": provider})
        approved = self.approve()
        for overridden in ({"provider": "ollama"}, {"model": "large"}):
            with self.assertRaisesRegex(ContractError, "MODEL_REVIEW"):
                self.lab.run({**approved, **overridden})
        self.assertEqual(self.lab.run(approved), {**self.selected, "text": self.gemini.run.return_value})
        self.gemini.run.assert_called_once_with("small", PROMPT)
        self.ollama.run.assert_not_called()
        with self.assertRaisesRegex(ContractError, "MODEL_REVIEW"):
            self.lab.run(approved)
        self.assertEqual(self.gemini.run.call_count, 1)

    def test_denies_unknown_extra_or_expired_request_before_dispatch(self):
        self.lab.check({"provider": "gemini"})
        for invalid in ({"model": "models/unknown"}, {"prompt": "private inputs"}, {"provider": "other"}):
            with self.assertRaisesRegex(ContractError, "MODEL_INVALID"):
                self.lab.preview({**self.selected, **invalid})
        with patch("mindgarden.application.model_lab.monotonic", return_value=10):
            approved = self.approve()
        with patch("mindgarden.application.model_lab.monotonic", return_value=311):
            with self.assertRaisesRegex(ContractError, "MODEL_REVIEW"):
                self.lab.run(approved)
        self.gemini.run.assert_not_called()

    def test_refresh_invalidates_prior_approval_and_sanitizes_adapter_failure(self):
        self.lab.check({"provider": "gemini"})
        approved = self.approve()
        self.lab.check({"provider": "gemini"})
        with self.assertRaisesRegex(ContractError, "MODEL_REVIEW"):
            self.lab.run(approved)
        self.gemini.check.side_effect = OSError("private arbitrary diagnostic")
        result = self.lab.check({"provider": "gemini"})
        self.assertNotIn("private arbitrary diagnostic", repr(result))
        self.assertEqual(result["providers"][1]["status"], "unavailable")
        with self.assertRaisesRegex(ContractError, "MODEL_NOT_CONFIGURED"):
            self.lab.preview(self.selected)

    def test_codex_status_does_not_enable_text_when_the_adapter_only_reports_account(self):
        self.codex.check.return_value.update(
            raw="private provider metadata",
            limits={"windows": [{"label": "Primary", "used_percent": 50, "raw": "private provider metadata"}]},
        )
        result = self.lab.check({"provider": "codex"})
        self.assertEqual(result["providers"][0]["limits"], {"windows": [{"label": "Primary", "used_percent": 50}]})
        self.assertNotIn("private provider metadata", repr(result))
        with self.assertRaisesRegex(ContractError, "MODEL_NOT_CONFIGURED"):
            self.lab.preview({"provider": "codex", "model": "small"})
        self.codex.run.assert_not_called()

    def test_install_requires_checked_explicit_allowlist_and_refreshes_catalog(self):
        self.ollama.check.return_value["downloadable"] = [
            {"id": "gemma3:1b", "label": "Gemma"}, {"id": "gemma4:e2b", "label": "Gemma 4"}
        ]
        with self.assertRaisesRegex(ContractError, "MODEL_NOT_CONFIGURED"):
            self.lab.install_preview({"model": "gemma3:1b"})
        self.lab.check({"provider": "ollama"})
        with self.assertRaisesRegex(ContractError, "MODEL_INVALID"):
            self.lab.install_preview({"model": "remote/cloud-model"})
        with self.assertRaisesRegex(ContractError, "MODEL_INVALID"):
            self.lab.install({"model": "gemma3:1b"})
        with self.assertRaisesRegex(ContractError, "MODEL_REVIEW"):
            self.lab.install({"model": "gemma3:1b", "preview_sha256": "0" * 64})
        approved = self.lab.install_preview({"model": "gemma3:1b"})
        with self.assertRaisesRegex(ContractError, "MODEL_REVIEW"):
            self.lab.install({**approved, "model": "gemma4:e2b"})
        self.ollama.install.assert_not_called()
        self.lab.install(approved)
        self.ollama.install.assert_called_once_with("gemma3:1b")
        self.assertEqual(self.ollama.check.call_count, 2)
        with self.assertRaisesRegex(ContractError, "MODEL_REVIEW"):
            self.lab.install(approved)

    def test_concurrent_request_cannot_reuse_approval_or_block_status_view(self):
        self.lab.check({"provider": "gemini"})
        approved = self.approve()
        started = threading.Event()
        finish = threading.Event()
        replies = []

        def run(_model, _prompt):
            started.set()
            if not finish.wait(timeout=5):
                raise AssertionError("test timed out")
            return "Fictional result"

        self.gemini.run.side_effect = run
        worker = threading.Thread(target=lambda: replies.append(self.lab.run(approved)), daemon=True)
        worker.start()
        try:
            self.assertTrue(started.wait(timeout=5))
            self.assertTrue(self.lab.snapshot()["providers"][1]["can_run"])
            with self.assertRaisesRegex(ContractError, "MODEL_BUSY"):
                self.lab.run(approved)
        finally:
            finish.set()
            worker.join(timeout=5)
        self.assertEqual(replies, [{**self.selected, "text": "Fictional result"}])
        self.gemini.run.assert_called_once_with("small", PROMPT)

    def test_oversized_response_consumes_approval_without_returning_partial_text(self):
        self.lab.check({"provider": "gemini"})
        approved = self.approve()
        self.gemini.run.return_value = "x" * (MAX_RESULT_BYTES + 1)
        with self.assertRaisesRegex(ContractError, "MODEL_UNAVAILABLE"):
            self.lab.run(approved)
        with self.assertRaisesRegex(ContractError, "MODEL_REVIEW"):
            self.lab.run(approved)

    def test_reset_prevents_a_stale_catalog_check_from_restoring_model_choices(self):
        started = threading.Event()
        finish = threading.Event()
        state = self.gemini.check.return_value
        snapshots = []

        def check():
            started.set()
            if not finish.wait(timeout=5):
                raise AssertionError("test timed out")
            return state

        self.gemini.check.side_effect = check
        worker = threading.Thread(
            target=lambda: snapshots.append(self.lab.check({"provider": "gemini"})),
            daemon=True,
        )
        worker.start()
        try:
            self.assertTrue(started.wait(timeout=5))
            self.lab.reset_connection("gemini")
        finally:
            finish.set()
            worker.join(timeout=5)
        self.assertEqual(snapshots[0]["providers"][1]["status"], "unchecked")
        self.assertEqual(snapshots[0]["providers"][1]["models"], [])
