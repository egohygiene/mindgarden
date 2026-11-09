"""Expiring memory is checked locally before reuse; no canonical deletion or recall."""

from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.memory import plan_memory
from mindgarden.application.query import QueryContext
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.domain.contracts import ContractRegistry, digest_bytes
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests import memory_fixture as fixture
from tests.support_v1 import add_knowledge, write_json

CREATED = "2026-11-06T00:00:00Z"
NOW = datetime(2026, 11, 6, tzinfo=timezone.utc)


class MemoryValidityTests(unittest.TestCase):
    def setUp(self):
        fixture.setup(self)
        self.request_path = self.root / "authored-memory.json"
        write_json(self.request_path, self.request)
        self.output = self.root / "managed-memory"

    def run_cli(self, *options, expected=0):
        with (
            patch(
                "mindgarden.application.memory.QueryContext.load",
                return_value=self.context,
            ),
            redirect_stdout(io.StringIO()) as output,
            redirect_stderr(io.StringIO()) as error,
        ):
            code = main(
                [
                    "memory",
                    "--local-config",
                    str(self.configuration),
                    "--scope",
                    str(self.session_path),
                    "--input",
                    str(self.request_path),
                    "--created-at",
                    CREATED,
                    *options,
                ]
            )
        self.assertEqual(code, expected, error.getvalue())
        return json.loads(output.getvalue()) if code == 0 else error.getvalue()

    def create(self):
        preview = self.run_cli()
        self.run_cli(
            "--apply",
            "--output-directory",
            str(self.output),
            "--plan-digest",
            preview["plan_sha256"],
        )
        return preview

    def test_managed_validity_is_deterministic_schema_checked_and_hash_bound(self):
        preview, files = plan_memory(self.context, self.request, created_at=CREATED)
        self.assertEqual(
            (preview, files),
            plan_memory(self.context, self.request, created_at=CREATED),
        )
        validity = json.loads(files["memory-validity.json"])
        self.assertEqual(ContractRegistry().errors(validity, "memory-validity"), [])
        self.assertEqual(validity["created_at"], CREATED)
        self.assertEqual(validity["expires_at"], "2026-11-06T00:10:00Z")
        self.assertEqual(
            validity["projection_sha256"], digest_bytes(files["memory-projection.json"])
        )
        self.assertEqual(
            validity["markdown_sha256"], digest_bytes(files["memory-snippets.md"])
        )
        validity["publication"] = "publishable"
        self.assertTrue(ContractRegistry().errors(validity, "memory-validity"))
        legacy, original = plan_memory(self.context, self.request)
        self.assertNotIn("memory-validity.json", original)
        self.assertNotEqual(legacy["plan_sha256"], preview["plan_sha256"])

    def test_snippet_expiry_review_half_life_and_session_bound_local_validity(self):
        output = self.request["candidates"][0]["outputs"][0]
        output["stale_after"] = "2026-11-06T00:05:00Z"
        self.assertEqual(
            plan_memory(self.context, self.request, created_at=CREATED)[0]["validity"][
                "expires_at"
            ],
            output["stale_after"],
        )
        output.update(last_reviewed="2026-11-05T00:03:00Z", half_life_days=1)
        self.assertEqual(
            plan_memory(self.context, self.request, created_at=CREATED)[0]["validity"][
                "expires_at"
            ],
            "2026-11-06T00:03:00Z",
        )
        document = json.loads(self.session_path.read_bytes())
        document["expires_at"] = "2026-11-06T00:02:00Z"
        write_json(self.session_path, document)
        context = QueryContext.load(
            self.configuration, self.session_path, clock=lambda: NOW
        )
        self.assertEqual(
            plan_memory(context, self.request, created_at=CREATED)[0]["validity"][
                "expires_at"
            ],
            document["expires_at"],
        )

    def test_expired_future_and_naive_times_deny_before_index_or_bundle_access(self):
        for created, code in (
            ("2026-11-05T00:00:00Z", "MEMORY_EXPIRED"),
            ("2026-11-07T00:00:00Z", "MEMORY_EXPIRED"),
            ("2026-11-06T00:00:00", "MEMORY_TIME"),
            ("PRIVATE_CANARY", "MEMORY_TIME"),
        ):
            with (
                self.subTest(created=created),
                patch(
                    "mindgarden.application.memory.build_index",
                    side_effect=AssertionError("Source body opened"),
                ),
            ):
                with self.assertRaisesRegex(ContractError, code) as error:
                    plan_memory(self.context, self.request, created_at=created)
                self.assertNotIn("PRIVATE_CANARY", str(error.exception))

    def test_check_is_read_only_replayable_and_does_not_create_missing_bundle(self):
        self.create()
        before = {
            p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.output.iterdir()
        }
        self.assertEqual(
            self.run_cli("--check", "--output-directory", str(self.output))["status"],
            "verified-current",
        )
        self.assertEqual(
            before,
            {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.output.iterdir()},
        )
        missing = self.root / "missing"
        self.assertIn(
            "MEMORY_MISSING",
            self.run_cli("--check", "--output-directory", str(missing), expected=3),
        )
        self.assertFalse(missing.exists())

    def test_elapsed_ttl_refuses_reuse_and_retains_bundle_and_canonical_sources(self):
        self.create()
        before = {
            p: p.read_bytes()
            for root in (self.output, self.workspace)
            for p in root.rglob("*")
            if p.is_file()
        }
        self.context.clock = lambda: NOW + timedelta(minutes=10)
        with patch(
            "mindgarden.application.memory.apply_generated",
            side_effect=AssertionError("Expired bundle accessed"),
        ):
            self.assertIn(
                "MEMORY_EXPIRED",
                self.run_cli(
                    "--check", "--output-directory", str(self.output), expected=3
                ),
            )
        for path, content in before.items():
            self.assertEqual(path.read_bytes(), content)

    def test_corrupt_or_unknown_output_is_retained_with_shareable_failure(self):
        self.create()
        markdown = self.output / "memory-snippets.md"
        markdown.write_text("PRIVATE_CANARY changed local copy")
        error = self.run_cli(
            "--check", "--output-directory", str(self.output), expected=3
        )
        self.assertIn("GENERATED_CONFLICT", error)
        self.assertNotIn("PRIVATE_CANARY", error)
        self.assertNotIn(str(self.output), error)
        self.assertEqual(markdown.read_text(), "PRIVATE_CANARY changed local copy")

    def test_source_change_and_revocation_stop_before_old_bundle_access(self):
        self.create()
        original = json.loads(
            (self.workspace / ".garden/knowledge/memory-0.json").read_bytes()
        )
        add_knowledge(
            self.workspace,
            "memory-0",
            body="Reviewed synthetic source correction.\n",
            sources=original["sources"],
        )
        write_json(
            self.session_path,
            bind_session_revisions(
                self.configuration, json.loads(self.session_path.read_bytes())
            ),
        )
        self.context = QueryContext.load(
            self.configuration, self.session_path, clock=lambda: NOW
        )
        with patch(
            "mindgarden.application.memory.apply_generated",
            side_effect=AssertionError("Stale bundle accessed"),
        ):
            self.assertIn(
                "MEMORY_SOURCE_CHANGED",
                self.run_cli(
                    "--check", "--output-directory", str(self.output), expected=3
                ),
            )
        document = json.loads(self.configuration.read_bytes())
        document["revoked_sessions"] = [self.context.session["id"]]
        write_json(self.configuration, document)
        with patch(
            "mindgarden.application.memory.apply_generated",
            side_effect=AssertionError("Revoked bundle accessed"),
        ):
            self.assertIn(
                "SESSION_REVOKED",
                self.run_cli(
                    "--check", "--output-directory", str(self.output), expected=3
                ),
            )
        self.assertTrue((self.output / "memory-projection.json").exists())

    def test_export_cannot_write_inside_source_vault(self):
        preview = self.run_cli()
        destination = (
            Path(self.context.bindings.document["vaults"][0]["root"]) / "context-copy"
        )
        self.assertIn(
            "FEDERATION_OUTPUT",
            self.run_cli(
                "--apply",
                "--output-directory",
                str(destination),
                "--plan-digest",
                preview["plan_sha256"],
                expected=3,
            ),
        )
        self.assertFalse(destination.exists())

    def test_authored_refresh_changes_only_the_affected_snippet_and_keeps_prior_bundle(
        self,
    ):
        preview = self.create()
        before = {s["id"]: s for s in preview["projection"]["snippets"]}
        old_bytes = {p: p.read_bytes() for p in self.output.iterdir()}
        record = json.loads(
            (self.workspace / ".garden/knowledge/memory-0.json").read_bytes()
        )
        updated = add_knowledge(
            self.workspace,
            "memory-0",
            body="Reviewed synthetic citation preference correction.\n",
            sources=record["sources"],
        )
        write_json(
            self.session_path,
            bind_session_revisions(
                self.configuration, json.loads(self.session_path.read_bytes())
            ),
        )
        self.context = QueryContext.load(
            self.configuration, self.session_path, clock=lambda: NOW
        )
        self.request["candidates"][0]["sources"][0]["revision"] = (
            "sha256:" + updated["content"]["sha256"]
        )
        self.request["candidates"][0]["rationale"] = (
            "Authored human review of the changed source; retain the concise preference."
        )
        revised, _ = plan_memory(self.context, self.request, created_at=CREATED)
        after = {s["id"]: s for s in revised["projection"]["snippets"]}
        self.assertNotEqual(before["keep-snippet"], after["keep-snippet"])
        self.assertEqual(
            {k: v for k, v in before.items() if k != "keep-snippet"},
            {k: v for k, v in after.items() if k != "keep-snippet"},
        )
        self.assertEqual(old_bytes, {p: p.read_bytes() for p in self.output.iterdir()})
