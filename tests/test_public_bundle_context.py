"""Progressive public reading uses exact supplied revisions and live authority."""

from contextlib import redirect_stdout
from copy import deepcopy
from datetime import datetime, timezone
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.federation import build_catalog
from mindgarden.application.public_bundle_context import public_bundle_context
from mindgarden.application.query import QueryContext
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.domain.contracts import ContractRegistry, read_object, strict_json
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests import test_federation as fixture
from tests.federation_fixture import create_fixture
from tests.support_v1 import write_json


class PublicBundleContextTests(unittest.TestCase):
    materialize = fixture.FederationTests.materialize

    def setUp(self):
        fixture.FederationTests.setUp(self)
        self.directory = self.materialize()
        descriptor = self.bundle.descriptor
        self.request = {
            "schema": "mindgarden.federation-context-request/v1",
            "id": "synthetic-context",
            "catalog": build_catalog(
                {
                    "schema": "mindgarden.federation-catalog-request/v1",
                    "bundles": [
                        {
                            "directory": str(self.directory),
                            "expected_revision": descriptor["revision"],
                        }
                    ],
                }
            ),
            "bundles": [
                {
                    "garden": descriptor["garden"],
                    "directory": str(self.directory),
                    "expected_revision": descriptor["revision"],
                }
            ],
            "query": "evidence",
            "max_items": 3,
            "max_bytes": 8192,
        }

    def test_catalog_selection_to_explainable_exact_context_without_canonical_bodies(
        self,
    ):
        with (
            patch("socket.socket", side_effect=AssertionError("Network attempted")),
            patch(
                "mindgarden.application.query.content_resolver",
                side_effect=AssertionError("Canonical bodies opened"),
            ),
        ):
            first = public_bundle_context(self.context, self.request)
            self.assertEqual(first, public_bundle_context(self.context, self.request))
        result = strict_json(first)
        self.assertEqual(ContractRegistry().errors(result, "federation-context"), [])
        self.assertLessEqual(len(first), 8192)
        self.assertEqual(
            result["inputs"][0]["revision"], self.bundle.descriptor["revision"]
        )
        prompt = next(
            item
            for item in result["included"]
            if item["record"]["reference"]["id"] == "reviewed-prompt"
        )
        self.assertEqual(prompt["record"]["sources"], self.fixture["evidence"])
        self.assertEqual(
            prompt["record"]["qualifications"]["epistemic_state"], "proposed"
        )
        self.assertTrue(prompt["selection_reasons"])
        self.assertNotIn(str(self.root).encode(), first)
        self.assertNotIn(self.context.session["id"].encode(), first)
        markdown = public_bundle_context(self.context, self.request, "markdown")
        self.assertLessEqual(len(markdown), 8192)
        self.assertIn(b"Untrusted evidence", markdown)

    def test_catalog_cannot_authorize_another_garden_or_read_its_index(self):
        other = create_fixture(self.root / "other", "other-garden")
        directory = self.materialize(other)
        request = deepcopy(self.request)
        request["bundles"] = [
            {
                "garden": "other-garden",
                "directory": str(directory),
                "expected_revision": other["bundle"].descriptor["revision"],
            }
        ]
        request["catalog"] = build_catalog(
            {
                "schema": "mindgarden.federation-catalog-request/v1",
                "bundles": [
                    {
                        "directory": str(directory),
                        "expected_revision": other["bundle"].descriptor["revision"],
                    }
                ],
            }
        )
        with patch(
            "mindgarden.application.public_bundle_context.read_bundle",
            side_effect=AssertionError("Denied bundle opened"),
        ):
            with self.assertRaisesRegex(ContractError, "QUERY_SELECTION"):
                public_bundle_context(self.context, request)

    def test_changed_descriptor_or_corrupted_index_is_rejected(self):
        self.request["bundles"][0]["expected_revision"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ContractError, "FEDERATION_STALE"):
            public_bundle_context(self.context, self.request)
        self.request["bundles"][0]["expected_revision"] = self.bundle.descriptor[
            "revision"
        ]
        path = self.directory / "index.json"
        path.write_bytes(path.read_bytes() + b"corrupt")
        with self.assertRaisesRegex(ContractError, "FEDERATION_INVALID"):
            public_bundle_context(self.context, self.request)

    def test_current_review_revocation_filters_before_ranking_and_counts(self):
        path = self.fixture["workspace"] / ".garden/knowledge/reviewed-prompt.json"
        record = read_object(path)
        record["review"].update(
            state="unreviewed", reviewers=[], reviewed_at=None, rationale=None
        )
        write_json(path, record)
        session = read_object(self.fixture["session_path"])
        write_json(
            self.fixture["session_path"],
            bind_session_revisions(self.fixture["configuration"], session),
        )
        context = QueryContext.load(
            self.fixture["configuration"], self.fixture["session_path"]
        )
        observed = []
        from mindgarden.application.retrieval import rank

        def check_rank(index, query):
            observed.extend(item["reference"]["id"] for item in index["records"])
            return rank(index, query)

        with patch(
            "mindgarden.application.public_bundle_context.rank", side_effect=check_rank
        ):
            result = public_bundle_context(context, self.request)
        self.assertNotIn("reviewed-prompt", observed)
        self.assertNotIn("reviewed-claim", observed)
        self.assertNotIn(b"reviewed-prompt", result)
        self.assertNotIn(b"reviewed-claim", result)

    def test_live_expiration_revocation_and_byte_limits(self):
        self.context.clock = lambda: datetime(2100, 1, 1, tzinfo=timezone.utc)
        with self.assertRaisesRegex(ContractError, "SESSION_EXPIRED"):
            public_bundle_context(self.context, self.request)
        self.context.clock = lambda: datetime.now(timezone.utc)
        self.request["max_bytes"] = 256
        with self.assertRaisesRegex(ContractError, "CONTEXT_BUDGET"):
            public_bundle_context(self.context, self.request)
        self.request["max_bytes"] = 8192
        config = read_object(self.fixture["configuration"])
        config["revoked_sessions"] = [self.context.session["id"]]
        write_json(self.fixture["configuration"], config)
        with self.assertRaisesRegex(ContractError, "SESSION_REVOKED"):
            public_bundle_context(self.context, self.request)

    def test_cli_reads_only_selected_supplied_bundle_and_remains_read_only(self):
        path = self.root / "query.json"
        write_json(path, self.request)
        with redirect_stdout(io.StringIO()) as output:
            result = main(
                [
                    "federation",
                    "query",
                    "--local-config",
                    str(self.fixture["configuration"]),
                    "--scope",
                    str(self.fixture["session_path"]),
                    "--input",
                    str(path),
                ]
            )
        self.assertEqual(result, 0)
        self.assertEqual(
            strict_json(output.getvalue())["schema"], "mindgarden.federation-context/v1"
        )

    def test_duplicate_selection_is_rejected_without_opening_bundle(self):
        self.request["bundles"] *= 2
        with patch(
            "mindgarden.application.public_bundle_context.read_bundle",
            side_effect=AssertionError("Bundle opened"),
        ):
            with self.assertRaisesRegex(ContractError, "FEDERATION_SELECTION"):
                public_bundle_context(self.context, self.request)

    def test_revocation_during_selected_read_cannot_emit_context(self):
        from mindgarden.adapters.federation_files import read_bundle

        def revoke_after_read(directory):
            files = read_bundle(directory)
            config = read_object(self.fixture["configuration"])
            config["revoked_sessions"] = [self.context.session["id"]]
            write_json(self.fixture["configuration"], config)
            return files

        with patch(
            "mindgarden.application.public_bundle_context.read_bundle",
            side_effect=revoke_after_read,
        ):
            with self.assertRaisesRegex(ContractError, "SESSION_REVOKED"):
                public_bundle_context(self.context, self.request)
