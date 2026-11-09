"""Private metadata discovery, exact progressive reads and fail-closed local recovery."""

from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from mindgarden.application.local_federation import discover_local, query_local
from mindgarden.application.query import QueryContext
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.domain.contracts import ContractRegistry
from mindgarden.domain.scope import local_scope
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests import test_projection_selection as fixtures
from tests.support_v1 import add_knowledge, create_garden, write_json, write_session


class LocalFederationTests(unittest.TestCase):
    def refresh(self):
        fixtures.ProjectionSelectionTests.refresh(self)

    def setUp(self):
        fixtures.ProjectionSelectionTests.setUp(self)
        self.session = json.loads(self.context.session_path.read_text())
        self.session["request_scope"] = local_scope(publication="never-exportable")
        write_json(
            self.context.session_path,
            bind_session_revisions(self.context.bindings.path, self.session),
        )
        self.context = QueryContext.load(
            self.context.bindings.path, self.context.session_path
        )

    def request(self, catalog, operation="search", garden="synthetic-garden", **fields):
        selected = next(
            entry for entry in catalog["gardens"] if entry["garden"] == garden
        )
        return {
            "schema": "mindgarden.local-federation-query/v1",
            "gardens": [{"garden": garden, "revision": selected["revision"]}],
            "operation": operation,
            **({"query": "needle00000", "limit": 10} if operation == "search" else {}),
            **fields,
        }

    def test_discovery_has_no_bodies_paths_or_unreviewed_counts(self):
        original_read = Path.read_bytes

        def guard(path):
            if path.is_relative_to(self.root) and path.suffix not in {".json"}:
                raise AssertionError("Body opened during metadata discovery")
            return original_read(path)

        with (
            patch.object(Path, "read_bytes", guard),
            patch("socket.socket", side_effect=AssertionError("Network")),
        ):
            catalog = discover_local(self.context)
        self.assertEqual(
            ContractRegistry().errors(catalog, "local-federation-catalog"), []
        )
        self.assertEqual([g["records_available"] for g in catalog["gardens"]], [1, 9])
        self.assertEqual(catalog["publication"], "never-exportable")
        self.assertNotIn(str(self.root), json.dumps(catalog))
        self.assertNotIn("needle00000", json.dumps(catalog))
        self.assertTrue(
            all(g["body_verification"] == "not-performed" for g in catalog["gardens"])
        )
        self.assertFalse(catalog["capabilities"]["remote_fetch"])
        self.assertFalse(catalog["capabilities"]["package_installation"])
        self.assertEqual(
            catalog,
            discover_local(
                QueryContext.load(self.context.bindings.path, self.context.session_path)
            ),
        )
        self.assertTrue(discover_local(self.context, max_gardens=1)["truncated"])

    def test_progressive_search_graph_links_and_bounded_context_use_only_selected_garden(
        self,
    ):
        catalog = discover_local(self.context)
        operations = [
            self.request(catalog),
            self.request(
                catalog,
                "graph",
                start="synthetic-garden/corpus-00000",
                depth=1,
                limit=10,
            ),
            self.request(
                catalog, "backlinks", artifact="synthetic-garden/corpus-00001"
            ),
            self.request(catalog, "outbound", artifact="synthetic-garden/corpus-00000"),
            self.request(catalog, "context", profile=self.profile, format="json"),
            self.request(catalog, "context", profile=self.profile, format="markdown"),
        ]
        original_read = Path.read_bytes

        def guard(path):
            if path.is_relative_to(self.other / ".garden") and path.suffix != ".json":
                raise AssertionError("Unselected garden body opened")
            return original_read(path)

        with (
            patch.object(Path, "read_bytes", guard),
            patch("socket.socket", side_effect=AssertionError("Network")),
        ):
            results = [query_local(self.context, request) for request in operations]
        search = json.loads(results[0])
        self.assertEqual(search["results"][0]["reference"]["id"], "corpus-00000")
        self.assertTrue(search["results"][0]["sources"][0]["content_sha256"])
        self.assertTrue(json.loads(results[1])["edges"])
        self.assertTrue(json.loads(results[2])["links"])
        self.assertTrue(json.loads(results[3])["links"])
        for content in results[4:]:
            self.assertLessEqual(len(content), self.profile["max_bytes"])
        for content in results:
            self.assertNotIn(b"other-garden", content)

    def test_stale_selection_and_unsupported_operations_fail_before_bodies(self):
        catalog = discover_local(self.context)
        invalid = self.request(catalog)
        invalid["gardens"][0]["revision"] = "sha256:" + "0" * 64
        original_read = Path.read_bytes

        def guard(path):
            if path.is_relative_to(self.root) and path.suffix != ".json":
                raise AssertionError("Body opened before pin validation")
            return original_read(path)

        with (
            patch.object(Path, "read_bytes", guard),
            self.assertRaisesRegex(ContractError, "SESSION_REVISION"),
        ):
            query_local(self.context, invalid)
        for operation in ("publish", "execute", "install", "grant-source"):
            invalid = self.request(catalog)
            invalid["operation"] = operation
            with self.assertRaisesRegex(ContractError, "LOCAL_QUERY_INVALID"):
                query_local(self.context, invalid)
        invalid = self.request(catalog)
        invalid["gardens"][0]["garden"] = "denied-canary"
        with self.assertRaisesRegex(ContractError, "QUERY_SELECTION"):
            query_local(self.context, invalid)

    def test_corrupted_or_unavailable_peer_does_not_break_explicit_healthy_selection(
        self,
    ):
        catalog = discover_local(self.context)
        path = self.other / ".garden/knowledge/other-note.md"
        path.write_text("SYNTHETIC_CORRUPTION_CANARY\n")
        self.assertEqual(
            discover_local(self.context), catalog
        )  # explicitly metadata-only, no body-health claim
        with self.assertRaisesRegex(ContractError, "QUERY_INTEGRITY"):
            query_local(
                self.context,
                self.request(catalog, garden="other-garden", query="independent"),
            )
        context = QueryContext.load(
            self.context.bindings.path,
            self.context.session_path,
            garden_ids={"synthetic-garden"},
        )
        self.assertTrue(
            json.loads(query_local(context, self.request(catalog)))["results"]
        )
        config = json.loads(self.context.bindings.path.read_text())
        config["gardens"][1]["root"] = str(self.root / "unavailable-peer")
        write_json(self.context.bindings.path, config)
        context = QueryContext.load(
            self.context.bindings.path,
            self.context.session_path,
            garden_ids={"synthetic-garden"},
        )
        self.assertTrue(
            json.loads(query_local(context, self.request(catalog)))["results"]
        )

    def test_private_bundle_check_revocation_and_collision_preserve_owned_outputs(self):
        destination = self.root / "private-local-catalog"
        args = [
            "federation",
            "local-discover",
            "--local-config",
            str(self.context.bindings.path),
            "--scope",
            str(self.context.session_path),
            "--output-directory",
            str(destination),
        ]

        def run(arguments):
            with redirect_stdout(io.StringIO()) as capture:
                self.assertEqual(main(arguments), 0)
            return json.loads(capture.getvalue())

        preview = run(args)
        run([*args, "--apply", "--plan-digest", preview["plan_sha256"]])
        run([*args, "--check"])
        self.assertEqual((destination / "catalog.json").stat().st_mode & 0o777, 0o600)
        original = (destination / "catalog.json").read_bytes()
        config = json.loads(self.context.bindings.path.read_text())
        config["revoked_sessions"] = [self.context.session["id"]]
        write_json(self.context.bindings.path, config)
        with (
            redirect_stdout(io.StringIO()) as stdout,
            redirect_stderr(io.StringIO()) as stderr,
        ):
            self.assertNotEqual(
                main([*args, "--check", "--diagnostic-format", "json"]), 0
            )
        self.assertEqual(stdout.getvalue(), "")
        self.assertNotIn(str(self.root), stderr.getvalue())
        self.assertEqual((destination / "catalog.json").read_bytes(), original)

    def test_expired_and_public_authority_cannot_discover_private_catalog(self):
        self.context.clock = lambda: datetime(2100, 1, 1, tzinfo=timezone.utc)
        with self.assertRaisesRegex(ContractError, "SESSION_EXPIRED"):
            discover_local(self.context)
        self.session["publication_authority"] = "publishable"
        write_json(
            self.context.session_path,
            bind_session_revisions(self.context.bindings.path, self.session),
        )
        context = QueryContext.load(
            self.context.bindings.path, self.context.session_path
        )
        with self.assertRaisesRegex(ContractError, "LOCAL_FEDERATION_SCOPE"):
            discover_local(context)

    def test_local_organization_scope_and_mixed_policy_are_explicit(self):
        org = self.root / "organization"
        create_garden(org, "organization-garden", "internal")
        manifest = json.loads((org / ".garden/garden.json").read_text())
        manifest["kind"] = "organization"
        write_json(org / ".garden/garden.json", manifest)
        add_knowledge(
            org,
            "org-note",
            body="Synthetic internal engineering context.\n",
            visibility="internal",
        )
        config = json.loads(self.context.bindings.path.read_text())
        config["gardens"].append(
            {
                "id": "organization-garden",
                "root": str(org),
                "scope": local_scope("organization"),
            }
        )
        write_json(self.context.bindings.path, config)
        session = write_session(
            self.context.session_path,
            self.context.bindings.path,
            readable_ids=["organization-garden"],
            visibility=["organization"],
        )
        session["request_scope"] = local_scope(
            "organization", publication="never-exportable"
        )
        write_json(
            self.context.session_path,
            bind_session_revisions(self.context.bindings.path, session),
        )
        context = QueryContext.load(
            self.context.bindings.path, self.context.session_path
        )
        catalog = discover_local(context)
        self.assertEqual(catalog["scope"]["visibility"], "organization")
        self.assertEqual(catalog["gardens"][0]["records_available"], 1)
        self.assertEqual(
            catalog["capabilities"]["organization_assurance"], "draft-local-policy-only"
        )
        session = write_session(
            self.context.session_path,
            self.context.bindings.path,
            visibility=["personal", "organization"],
        )
        session["request_scope"] = local_scope(publication="never-exportable")
        write_json(
            self.context.session_path,
            bind_session_revisions(self.context.bindings.path, session),
        )
        with self.assertRaisesRegex(ContractError, "OUTPUT_SCOPE|RUNTIME_UNVERIFIED"):
            discover_local(
                QueryContext.load(self.context.bindings.path, self.context.session_path)
            )

    def test_cli_query_uses_exact_private_request_without_public_catalog(self):
        catalog = discover_local(self.context)
        request = self.request(catalog)
        path = self.root / "selected-query.json"
        write_json(path, request)
        with redirect_stdout(io.StringIO()) as capture:
            self.assertEqual(
                main(
                    [
                        "federation",
                        "local-query",
                        "--local-config",
                        str(self.context.bindings.path),
                        "--scope",
                        str(self.context.session_path),
                        "--input",
                        str(path),
                    ]
                ),
                0,
            )
        payload = json.loads(capture.getvalue())
        self.assertEqual(payload["results"][0]["reference"]["id"], "corpus-00000")
        self.assertEqual(payload["scope"]["publication"], "never-exportable")
