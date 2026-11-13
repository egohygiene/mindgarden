"""Bounded source selection, version/checksum integrity, recovery and no credentials."""

from io import BytesIO
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.drive_source import DriveCaptureAdapter
from mindgarden.adapters.google_drive import GoogleDriveProvider
from mindgarden.application.drive_capture import collect
from mindgarden.application.bindings import LocalBindings
from mindgarden.application.storage import open_vault
from mindgarden.domain.contracts import digest_bytes
from mindgarden.domain.scope import local_scope
from mindgarden.domain.validation import ContractError
from tests.consultation_fixture import cli
from tests.drive_capture_fixture import create_capture_fixture


class Response(BytesIO):
    status = 200


class DriveTransportTests(unittest.TestCase):
    def setUp(self):
        self.limits = {
            "max_requests": 10,
            "max_seconds": 60,
            "timeout_seconds": 5,
            "max_files": 10,
            "max_file_bytes": 1000,
        }

    def test_exact_read_only_metadata_media_export_wire_and_no_token_in_urls(self):
        calls = []

        def open_request(request, timeout):
            calls.append((request, timeout))
            return (
                Response(b'{"id":"file-one"}')
                if "fields" in request.full_url
                else Response(b"synthetic")
            )

        provider = GoogleDriveProvider(
            self.limits, token="synthetic-secret", opener=open_request
        )
        provider.stat("file-one")
        provider.read({"id": "file-one", "mimeType": "text/plain"}, "text/plain")
        provider.read(
            {"id": "native-one", "mimeType": "application/vnd.google-apps.document"},
            "text/plain",
        )
        self.assertTrue(
            all(
                request.get_method() == "GET"
                and urlsplit(request.full_url).netloc == "www.googleapis.com"
                for request, _ in calls
            )
        )
        self.assertTrue(
            all("synthetic-secret" not in request.full_url for request, _ in calls)
        )
        self.assertEqual(
            parse_qs(urlsplit(calls[1][0].full_url).query), {"alt": ["media"]}
        )
        self.assertTrue(urlsplit(calls[2][0].full_url).path.endswith("/export"))
        self.assertEqual(
            calls[0][0].get_header("Authorization"), "Bearer synthetic-secret"
        )
        self.assertTrue(all(timeout <= 5 for _, timeout in calls))

    def test_pagination_is_complete_parent_bounded_and_rejects_incomplete_search(self):
        calls = []
        pages = [
            b'{"files":[],"nextPageToken":"next"}',
            b'{"files":[],"incompleteSearch":false}',
        ]

        def open_request(request, timeout):
            calls.append(request.full_url)
            return Response(pages.pop(0))

        self.assertEqual(
            GoogleDriveProvider(
                self.limits, token="synthetic", opener=open_request
            ).children("selected-folder"),
            [],
        )
        self.assertIn("parents", parse_qs(urlsplit(calls[0]).query)["q"][0])
        self.assertEqual(parse_qs(urlsplit(calls[1]).query)["pageToken"], ["next"])
        provider = GoogleDriveProvider(
            self.limits,
            token="synthetic",
            opener=lambda *_args, **_kwargs: Response(
                b'{"files":[],"incompleteSearch":true}'
            ),
        )
        with self.assertRaisesRegex(ContractError, "CAPTURE_INCOMPLETE"):
            provider.children("selected-folder")

    def test_credential_absence_http_failures_and_time_request_byte_limits(self):
        with (
            patch.dict("os.environ", {}, clear=True),
            self.assertRaisesRegex(ContractError, "CAPTURE_AUTH"),
        ):
            GoogleDriveProvider(self.limits)

        def denied(request, timeout):
            raise HTTPError(
                request.full_url,
                403,
                "synthetic-secret-sensitive-filename",
                {},
                BytesIO(),
            )

        with self.assertRaisesRegex(ContractError, "CAPTURE_DENIED") as error:
            GoogleDriveProvider(
                self.limits, token="synthetic-secret", opener=denied
            ).stat("file-one")
        self.assertNotIn("sensitive", str(error.exception))
        provider = GoogleDriveProvider(
            {**self.limits, "max_requests": 1, "max_file_bytes": 2},
            token="synthetic",
            opener=lambda *_args, **_kwargs: Response(b"too many bytes"),
        )
        with self.assertRaisesRegex(ContractError, "CAPTURE_BUDGET"):
            provider.read({"id": "file-one", "mimeType": "text/plain"}, "text/plain")
        with self.assertRaisesRegex(ContractError, "CAPTURE_BUDGET"):
            provider.stat("file-one")

    def test_partial_encoded_or_expired_http_reads_never_return_complete_content(self):
        response = Response(b"short")
        response.headers = {"Content-Length": "10"}
        provider = GoogleDriveProvider(
            self.limits, token="synthetic", opener=lambda *_a, **_k: response
        )
        with self.assertRaisesRegex(ContractError, "CAPTURE_CORRUPTED"):
            provider.read({"id": "file-one", "mimeType": "text/plain"}, "text/plain")
        response = Response(b"encoded")
        response.headers = {"Content-Encoding": "gzip"}
        provider = GoogleDriveProvider(
            self.limits, token="synthetic", opener=lambda *_a, **_k: response
        )
        with self.assertRaisesRegex(ContractError, "CAPTURE_FORMAT"):
            provider.stat("file-one")
        times = iter([0, 61])
        provider = GoogleDriveProvider(
            self.limits,
            token="synthetic",
            opener=lambda *_a, **_k: self.fail("Expired request sent"),
            clock=lambda: next(times),
        )
        with self.assertRaisesRegex(ContractError, "CAPTURE_BUDGET"):
            provider.stat("file-one")


class DriveCaptureTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.fixture = create_capture_fixture(Path(temporary.name))
        self.binding, self.provider, self.vault = (
            self.fixture[key] for key in ("binding", "provider", "vault")
        )
        self.checkpoint = self.fixture["root"] / "capture-checkpoint.json"

    def capture(self, **kwargs):
        return collect(
            self.binding, self.provider, self.vault, self.checkpoint, **kwargs
        )

    def normalize(self, content):
        return DriveCaptureAdapter().normalize(
            content, {"source_scope": self.binding["scope"]}
        )

    def test_repeat_overlap_normalization_and_moved_vault_resolve_same_evidence(self):
        before, manifest = self.capture()
        units = self.normalize(before).units
        self.assertEqual(len(units), 8)
        self.assertEqual(self.capture()[0], before)
        self.assertEqual(len(self.provider.reads), 3)
        self.assertEqual({item["version"] for item in manifest["files"]}, {"1"})
        for unit in units:
            self.assertIn("original_utf8_span", unit.metadata)
            self.assertIn("provider_file_id", unit.metadata)
        self.assertEqual(self.checkpoint.stat().st_mode & 0o777, 0o600)
        args = [
            "vault",
            "relocate",
            "--local-config",
            str(self.fixture["configuration"]),
            "--vault-id",
            "synthetic-vault",
            "--destination",
            str(self.fixture["root"] / "relocated-vault"),
        ]
        planned = cli(args)
        cli(args + ["--apply", "--plan-digest", planned["plan_sha256"]])
        self.vault = open_vault(
            LocalBindings.load(self.fixture["configuration"]), "synthetic-vault"
        )
        self.assertEqual(self.capture()[0], before)
        self.assertEqual(len(self.provider.reads), 3)

    def test_partial_failure_resumes_verified_objects_without_redownloading(self):
        self.provider.fail = "file-b"
        with self.assertRaisesRegex(ContractError, "CAPTURE_UNAVAILABLE"):
            self.capture()
        self.assertTrue(self.checkpoint.is_file())
        self.assertEqual(self.provider.reads.count("file-a"), 1)
        self.provider.fail = None
        complete, _ = self.capture()
        self.assertEqual(self.provider.reads.count("file-a"), 1)
        self.assertEqual(len(self.normalize(complete).units), 8)

    def test_metadata_change_download_denial_and_corruption_fail_safely(self):
        self.provider.change_on_read = True
        with self.assertRaisesRegex(ContractError, "CAPTURE_CHANGED"):
            self.capture()
        self.provider.change_on_read = False
        self.provider.items["file-a"]["capabilities"]["canDownload"] = False
        with self.assertRaisesRegex(ContractError, "CAPTURE_DENIED"):
            self.capture()
        self.provider.items["file-a"]["capabilities"]["canDownload"] = True
        self.provider.data["file-a"] = b"corrupted"
        with self.assertRaisesRegex(ContractError, "CAPTURE_CORRUPTED"):
            self.capture()

    def test_refresh_preserves_old_capture_marks_unlisted_and_rejects_changed_selection(
        self,
    ):
        before, _ = self.capture()
        self.provider.items.pop("file-b")
        self.binding["captured_at"] = "2026-11-05T00:00:00Z"
        updated, manifest = self.capture()
        self.assertIn("file-b", manifest["unavailable_previous"])
        self.assertNotEqual(updated, before)
        self.assertEqual(len(self.normalize(before).units), 8)
        self.binding["folders"] = ["another-folder"]
        with self.assertRaisesRegex(ContractError, "CAPTURE_CHECKPOINT"):
            self.capture()

    def test_initial_scope_gate_precedes_provider_access_and_never_approves_knowledge(
        self,
    ):
        self.binding["scope"] = local_scope(
            "restricted", publication="never-exportable"
        )
        with self.assertRaisesRegex(ContractError, "CAPTURE_RUNTIME_UNVERIFIED"):
            self.capture()
        self.assertEqual(self.provider.calls, [])

    def test_native_exports_preserve_explicit_loss_and_malformed_packages_are_denied(
        self,
    ):
        self.binding["exports"] = [
            {
                "source_type": "application/vnd.google-apps.spreadsheet",
                "export_type": "text/csv",
            }
        ]
        self.provider.items["file-a"]["mimeType"] = (
            "application/vnd.google-apps.spreadsheet"
        )
        snapshot, manifest = self.capture()
        self.assertEqual(
            next(item for item in manifest["files"] if item["file_id"] == "file-a")[
                "losses"
            ],
            ["first-sheet-only"],
        )
        with self.assertRaisesRegex(ContractError, "CAPTURE_PACKAGE"):
            self.normalize(snapshot[:-40])
        with self.assertRaisesRegex(ContractError, "CAPTURE_SCOPE"):
            DriveCaptureAdapter().normalize(snapshot, {})

    def test_cli_network_review_gates_and_supplied_capture_ingestion(self):
        output = self.fixture["root"] / "captured"
        args = [
            "capture",
            "drive",
            "--input",
            str(self.fixture["binding_path"]),
            "--local-config",
            str(self.fixture["configuration"]),
            "--vault-id",
            "synthetic-vault",
            "--output-directory",
            str(output),
        ]
        planned = cli(args)
        from mindgarden.interfaces.cli import main

        with patch("sys.stderr"):
            self.assertEqual(
                main(args + ["--apply", "--plan-digest", planned["plan_sha256"]]), 3
            )
        with patch(
            "mindgarden.application.drive_capture.GoogleDriveProvider",
            return_value=self.provider,
        ):
            self.assertEqual(
                cli(
                    args
                    + [
                        "--apply",
                        "--allow-network",
                        "--plan-digest",
                        planned["plan_sha256"],
                    ]
                )["status"],
                "created",
            )
        ingest = [
            "ingest",
            "--repository-root",
            str(self.fixture["garden"]),
            "--local-config",
            str(self.fixture["configuration"]),
            "--vault-id",
            "synthetic-vault",
            "--input",
            str(output / "capture.zip"),
            "--source-id",
            "selected-drive-capture",
            "--title",
            "Synthetic selected capture",
            "--owner",
            "synthetic-owner",
            "--rights",
            "Wholly synthetic fixture.",
            "--origin",
            "urn:synthetic:drive-capture",
            "--captured",
            self.binding["captured_at"],
            "--media-type",
            "application/vnd.mindgarden.drive-capture+zip",
            "--adapter",
            "drive-capture",
            "--manifest-version",
            "1.0.0",
            "--source-scope",
            str(output / "source-scope.json"),
        ]
        plan = cli(ingest)
        self.assertEqual(len(plan["inputs"]["normalized_sources"]), 8)
        self.assertTrue(
            cli(ingest + ["--apply", "--plan-digest", plan["plan_sha256"]])["applied"]
        )
        again = cli(ingest)
        self.assertFalse(
            cli(ingest + ["--apply", "--plan-digest", again["plan_sha256"]])["applied"]
        )
        self.assertEqual(output.stat().st_mode & 0o777, 0o700)
        self.assertNotIn(
            "MINDGARDEN_DRIVE_ACCESS_TOKEN", (output / "manifest.json").read_text()
        )

    def test_recursive_depth_and_live_configuration_limits_stop_further_reads(self):
        self.provider.items["child"] = {
            "id": "child",
            "name": "Synthetic child",
            "mimeType": "application/vnd.google-apps.folder",
            "version": "1",
            "parents": ["selected-folder"],
        }
        self.binding["recursive"] = True
        self.binding["limits"]["max_depth"] = 0
        with self.assertRaisesRegex(ContractError, "CAPTURE_BUDGET"):
            self.capture()
        self.assertEqual(self.provider.reads, [])
        self.binding["recursive"] = False
        calls = 0

        def check():
            nonlocal calls
            calls += 1
            if calls > 3:
                raise ContractError("CAPTURE_PLAN_STALE: synthetic permission revoked")

        with self.assertRaisesRegex(ContractError, "CAPTURE_PLAN_STALE"):
            self.capture(check_live=check)
        self.assertEqual(self.provider.reads, ["file-a"])

    def test_binary_documents_are_preserved_without_claiming_text_extraction(self):
        raw = b"%PDF-synthetic-preservation-only"
        self.provider.data["document"] = raw
        self.provider.items["document"] = {
            "id": "document",
            "name": "Synthetic document",
            "mimeType": "application/pdf",
            "version": "1",
            "parents": ["selected-folder"],
            "size": str(len(raw)),
            "sha256Checksum": digest_bytes(raw),
            "capabilities": {"canDownload": True},
        }
        self.binding["media_types"].append("application/pdf")
        snapshot, _ = self.capture()
        normalized = self.normalize(snapshot)
        self.assertEqual(len(normalized.units), 8)
        state = next(
            item
            for item in normalized.metadata["normalization_states"]
            if item["file_id"] == "document"
        )
        self.assertEqual(state["state"], "preserved-only")

    def test_offline_capture_scope_cannot_be_overridden_by_a_network_flag(self):
        self.binding["scope"] = local_scope(publication="never-exportable")
        with self.assertRaisesRegex(ContractError, "CAPTURE_EXECUTION"):
            self.capture()
        self.assertEqual(self.provider.calls, [])

    def test_new_capture_reuses_previous_checkpoint_without_overwriting_history(self):
        before, _ = self.capture()
        previous = self.checkpoint.read_bytes()
        self.binding["captured_at"] = "2026-11-05T00:00:00Z"
        self.checkpoint = self.fixture["root"] / "new-checkpoint.json"
        updated, _ = self.capture(
            previous=self.fixture["root"] / "capture-checkpoint.json"
        )
        self.assertEqual(len(self.provider.reads), 3)
        self.assertNotEqual(before, updated)
        self.assertEqual(
            (self.fixture["root"] / "capture-checkpoint.json").read_bytes(), previous
        )
        self.assertEqual(
            [(unit.identity, unit.content) for unit in self.normalize(before).units],
            [(unit.identity, unit.content) for unit in self.normalize(updated).units],
        )
