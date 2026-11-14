"""Real CLI currentness, correction/review, missing evidence and denied metadata."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.consultation import plan_packet
from mindgarden.application.query import QueryContext
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.application.storage import open_vault
from mindgarden.domain.contracts import canonical_json, digest_bytes, read_object
from mindgarden.domain.packet_dependencies import (
    reconcile_packet,
    validate_dependencies,
)
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests.consultation_fixture import cli, create_fixture
from tests.packet_freshness_fixture import correct_fixture
from tests.support_v1 import TIME, write_json


class PacketFreshnessTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.fixture = create_fixture(self.root)
        self.target = self.root / "packet-before"
        self.arguments = [
            "packet",
            "--local-config",
            str(self.fixture["configuration"]),
            "--scope",
            str(self.fixture["session_path"]),
            "--input",
            str(self.fixture["request_path"]),
        ]
        preview = cli(self.arguments + ["--output-directory", str(self.target)])
        self.digest = preview["plan_sha256"]
        cli(
            self.arguments
            + [
                "--output-directory",
                str(self.target),
                "--apply",
                "--plan-digest",
                preview["plan_sha256"],
            ]
        )
        self.previous = self.target / "packet-dependencies.json"

    def compare(self):
        return cli(self.arguments + ["--previous-manifest", str(self.previous)])

    def failure(self, arguments):
        with (
            redirect_stderr(io.StringIO()) as error,
            redirect_stdout(io.StringIO()) as output,
        ):
            status = main(arguments)
        self.assertEqual(status, 3)
        self.assertEqual(output.getvalue(), "")
        return error.getvalue()

    def test_same_explicit_inputs_are_current_and_comparison_never_writes(self):
        before = {
            path: (path.read_bytes(), path.stat().st_mode)
            for path in self.root.rglob("*")
            if path.is_file()
        }
        with (
            patch("socket.socket", side_effect=AssertionError("Network attempted")),
            patch("subprocess.Popen", side_effect=AssertionError("Process attempted")),
            patch(
                "mindgarden.application.consultation.apply_generated",
                side_effect=AssertionError("Write attempted"),
            ),
        ):
            result = self.compare()
        self.assertEqual(result["state"], "current")
        self.assertEqual(result["reasons"], ["explicit-inputs-unchanged"])
        self.assertEqual(result["coverage"], "explicit-current-request-only")
        after = {
            path: (path.read_bytes(), path.stat().st_mode)
            for path in self.root.rglob("*")
            if path.is_file()
        }
        self.assertEqual(before, after)

    def test_corrected_selected_source_requires_new_review_and_preserves_prior_packet(
        self,
    ):
        original = {path.name: path.read_bytes() for path in self.target.iterdir()}
        vault = open_vault(self.fixture["context"].bindings, "synthetic-vault")
        objects = vault.audit()["objects"]
        self.fixture = correct_fixture(self.fixture)
        result = self.compare()
        self.assertEqual(result["state"], "stale")
        self.assertIn("selected-evidence-changed", result["reasons"])
        self.assertEqual(result["action"], "review-and-build-new-packet")
        self.assertNotIn("Synthetic payroll", json.dumps(result))
        self.failure(
            self.arguments + ["--output-directory", str(self.target), "--check"]
        )
        self.assertIn(
            "GENERATED_PLAN_STALE",
            self.failure(
                self.arguments
                + [
                    "--output-directory",
                    str(self.root / "unapproved-old-plan"),
                    "--apply",
                    "--plan-digest",
                    self.digest,
                ]
            ),
        )
        target = self.root / "packet-after"
        preview = cli(self.arguments + ["--output-directory", str(target)])
        cli(
            self.arguments
            + [
                "--output-directory",
                str(target),
                "--apply",
                "--plan-digest",
                preview["plan_sha256"],
            ]
        )
        self.assertEqual(
            read_object(target / "packet.json")["totals"][0]["net_movement"], "2159.76"
        )
        self.assertEqual(
            {path.name: path.read_bytes() for path in self.target.iterdir()}, original
        )
        self.assertTrue(all(item in vault.audit()["objects"] for item in objects))
        self.previous = target / "packet-dependencies.json"
        self.assertEqual(self.compare()["state"], "current")

    def test_review_change_is_distinct_from_selected_evidence_change(self):
        request = deepcopy(self.fixture["request"])
        request["questions"].append("A separately reviewed follow-up question")
        write_json(self.fixture["request_path"], request)
        result = self.compare()
        self.assertEqual(result["state"], "stale")
        self.assertIn("review-or-request-changed", result["reasons"])
        self.assertNotIn("selected-evidence-changed", result["reasons"])

    def test_revoked_or_missing_grant_fails_before_prior_manifest_read(self):
        request = deepcopy(self.fixture["request"])
        request["sources"][0]["source"]["id"] = "denied-current-source-canary"
        write_json(self.fixture["request_path"], request)
        with patch(
            "mindgarden.application.consultation.read_control",
            side_effect=AssertionError("Prior read"),
        ):
            message = self.failure(
                self.arguments + ["--previous-manifest", str(self.previous)]
            )
        self.assertIn("SOURCE_GRANT", message)
        self.assertNotIn("canary", message)
        configuration = read_object(self.fixture["configuration"])
        configuration["revoked_sessions"] = [self.fixture["context"].session["id"]]
        write_json(self.fixture["configuration"], configuration)
        self.assertIn(
            "SESSION_REVOKED",
            self.failure(self.arguments + ["--previous-manifest", str(self.previous)]),
        )

    def test_missing_or_corrupted_current_evidence_blocks_reuse_and_preserves_bundle(
        self,
    ):
        before = self.previous.read_bytes()
        source = self.fixture["request"]["sources"][0]
        vault = open_vault(self.fixture["context"].bindings, "synthetic-vault")
        path = vault._object_path("sha256:" + source["content_sha256"])
        original = path.read_bytes()
        retained = self.root / "retained-missing-fixture"
        path.rename(retained)
        message = self.failure(
            self.arguments + ["--previous-manifest", str(self.previous)]
        )
        self.assertIn("QUERY_INTEGRITY", message)
        path.write_bytes(b"corrupted synthetic row")
        path.chmod(0o600)
        message = self.failure(
            self.arguments + ["--previous-manifest", str(self.previous)]
        )
        self.assertIn("QUERY_INTEGRITY", message)
        path.write_bytes(original)
        self.assertEqual(self.previous.read_bytes(), before)
        self.assertEqual(self.compare()["state"], "current")

    def test_prior_only_id_is_not_echoed_and_invalid_metadata_cannot_claim_current(
        self,
    ):
        prior = read_object(self.previous)
        prior["id"] = "private-historical-only-canary"
        prior["fingerprint"] = digest_bytes(
            canonical_json(
                {key: value for key, value in prior.items() if key != "fingerprint"}
            )
        )
        self.previous.write_bytes(canonical_json(prior))
        result = self.compare()
        self.assertEqual(result["state"], "stale")
        self.assertNotIn("canary", json.dumps(result))
        prior["inputs_sha256"] = "0" * 64
        self.previous.write_bytes(canonical_json(prior))
        self.assertIn(
            "PACKET_DEPENDENCIES",
            self.failure(self.arguments + ["--previous-manifest", str(self.previous)]),
        )

    def test_revocation_during_comparison_stops_output(self):
        from mindgarden.application.consultation import reconcile_packet as reconcile

        def revoke(*args):
            result = reconcile(*args)
            configuration = read_object(self.fixture["configuration"])
            configuration["revoked_sessions"] = [self.fixture["context"].session["id"]]
            write_json(self.fixture["configuration"], configuration)
            return result

        with patch(
            "mindgarden.application.consultation.reconcile_packet", side_effect=revoke
        ):
            message = self.failure(
                self.arguments + ["--previous-manifest", str(self.previous)]
            )
        self.assertIn("SESSION_REVOKED", message)

    def test_fingerprints_survive_authority_renewal_and_reject_wrong_scope(self):
        session = read_object(self.fixture["session_path"])
        session["id"] = "renewed-synthetic-authority"
        write_json(self.fixture["session_path"], session)
        context = QueryContext.load(
            self.fixture["configuration"], self.fixture["session_path"]
        )
        _, files = plan_packet(context, self.fixture["request"])
        manifest = validate_dependencies(json.loads(files["packet-dependencies.json"]))
        self.assertEqual(
            reconcile_packet(manifest, read_object(self.previous))["state"], "current"
        )
        prior = deepcopy(manifest)
        prior["scope"]["publication"] = "review-required"
        prior["fingerprint"] = digest_bytes(
            canonical_json(
                {key: value for key, value in prior.items() if key != "fingerprint"}
            )
        )
        with self.assertRaisesRegex(ContractError, "PACKET_SCOPE"):
            reconcile_packet(manifest, prior)

    def test_unrelated_import_leaves_selected_packet_current_and_identical(self):
        before = plan_packet(self.fixture["context"], self.fixture["request"])[1]
        unrelated = self.root / "unrelated.csv"
        unrelated.write_bytes(
            b"transaction_id,account_id,date,amount,currency,description\n"
            b"unrelated,another-account,2026-01-01,1.00,USD,Unrelated private canary\n"
        )
        arguments = list(self.fixture["imports"][0]["arguments"])
        for flag, value in (
            ("--input", str(unrelated)),
            ("--source-id", "unrelated-export"),
            ("--origin", "urn:synthetic:unrelated-export"),
        ):
            arguments[arguments.index(flag) + 1] = value
        preview = cli(arguments)
        cli(arguments + ["--apply", "--plan-digest", preview["plan_sha256"]])
        self.assertEqual(self.compare()["state"], "current")
        context = QueryContext.load(
            self.fixture["configuration"], self.fixture["session_path"]
        )
        self.assertEqual(plan_packet(context, self.fixture["request"])[1], before)

    def test_comparison_requires_review_and_rejects_write_options(self):
        self.assertIn(
            "PACKET_OPTIONS",
            self.failure(
                self.arguments
                + [
                    "--previous-manifest",
                    str(self.previous),
                    "--plan-digest",
                    self.digest,
                ]
            ),
        )
        request = deepcopy(self.fixture["request"])
        request["review"].update(state="in-review")
        write_json(self.fixture["request_path"], request)
        self.assertIn(
            "PACKET_REVIEW",
            self.failure(self.arguments + ["--previous-manifest", str(self.previous)]),
        )

    def test_source_review_metadata_change_stales_even_identical_evidence_bytes(self):
        source = self.fixture["request"]["sources"][0]["source"]
        path = self.fixture["garden"] / ".garden/sources" / (source["id"] + ".json")
        record = read_object(path)
        record["review"] = {
            "state": "approved",
            "reviewers": ["synthetic-reviewer"],
            "reviewed_at": TIME,
            "rationale": "Separate authored source review.",
        }
        write_json(path, record)
        session = read_object(self.fixture["session_path"])
        write_json(
            self.fixture["session_path"],
            bind_session_revisions(self.fixture["configuration"], session),
        )
        result = self.compare()
        self.assertEqual(result["reasons"], ["selected-evidence-changed"])
