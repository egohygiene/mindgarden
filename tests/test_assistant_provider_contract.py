"""Exercise the Studio adapter seam with two offline implementations."""

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.query import QueryContext  # noqa: E402
from mindgarden.application.studio_assistant import FixtureAssistant, prepare_turn, turn_lines  # noqa: E402
from mindgarden.domain.contracts import canonical_json, read_object  # noqa: E402
from mindgarden.domain.validation import ContractError  # noqa: E402
from mindgarden.interfaces.visit_demo import prepare_demo  # noqa: E402


REQUEST = {
    "question": "What accessibility experiment is proposed?",
    "lens": "garden",
    "focus": "synthetic-garden/mock-career",
}


class AlternateOfflineProvider:
    name = "alternate-offline"
    capabilities = frozenset({"preview", "stream", "cancel"})

    def __init__(self):
        self.calls = 0

    def events(self, approved):
        self.calls += 1
        events = [{"type": "text", "text": "Second offline implementation."}]
        for record in approved.records:
            events.extend(
                {"type": "citation", "reference": record["reference"], "citation": citation}
                for citation in record["sources"]
            )
        return iter(events)


def citations(lines):
    return [event for line in lines if (event := json.loads(line))["type"] == "citation"]


class AssistantProviderContractTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory(prefix="assistant-provider-test-")
        self.addCleanup(directory.cleanup)
        self.config, self.scope = prepare_demo(Path(directory.name))
        self.context = QueryContext.load(self.config, self.scope)

    def test_switching_adapter_reuses_evidence_and_requires_its_own_approval(self):
        first = FixtureAssistant()
        second = AlternateOfflineProvider()
        first_plan = prepare_turn(self.context, first, REQUEST)
        second_plan = prepare_turn(self.context, second, REQUEST)
        self.assertEqual(first_plan.preview["records"], second_plan.preview["records"])
        self.assertNotEqual(first_plan.preview["preview_sha256"], second_plan.preview["preview_sha256"])
        with self.assertRaisesRegex(ContractError, "ASSISTANT_APPROVAL"):
            prepare_turn(self.context, second, {**REQUEST, "preview_sha256": first_plan.preview["preview_sha256"]}, run=True)
        self.assertEqual(second.calls, 0)

        def run(provider, plan):
            approved = {**REQUEST, "preview_sha256": plan.preview["preview_sha256"]}
            current = prepare_turn(self.context, provider, approved, run=True)
            return turn_lines(self.context, provider, current)

        expected = citations(run(first, first_plan))
        self.assertTrue(expected)
        self.assertEqual(citations(run(second, second_plan)), expected)
        self.assertEqual(second.calls, 1)

    def test_capability_changes_invalidate_existing_approval(self):
        provider = AlternateOfflineProvider()
        preview = prepare_turn(self.context, provider, REQUEST).preview
        provider.capabilities = frozenset({"preview", "stream"})
        approved = {**REQUEST, "preview_sha256": preview["preview_sha256"]}
        with self.assertRaisesRegex(ContractError, "ASSISTANT_APPROVAL"):
            prepare_turn(self.context, provider, approved, run=True)
        self.assertEqual(provider.calls, 0)

    def test_revocation_before_dispatch_prevents_provider_calls(self):
        provider = AlternateOfflineProvider()
        preview = prepare_turn(self.context, provider, REQUEST).preview
        approved = {**REQUEST, "preview_sha256": preview["preview_sha256"]}
        prepared = prepare_turn(self.context, provider, approved, run=True)
        bindings = read_object(self.config)
        bindings["revoked_sessions"].append(read_object(self.scope)["id"])
        self.config.write_bytes(canonical_json(bindings))
        with self.assertRaisesRegex(ContractError, "SESSION_REVOKED"):
            turn_lines(self.context, provider, prepared)
        self.assertEqual(provider.calls, 0)
