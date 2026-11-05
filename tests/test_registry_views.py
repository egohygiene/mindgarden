"""Named registration selections preserve existing query and publication authority."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import importlib.util
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.federation import build_federation
from mindgarden.application.query import QueryContext
from mindgarden.application.registry import registry_report
from mindgarden.application.retrieval import backlinks_payload, graph_payload, render_context, search_payload, write_projection, projection_directory
from mindgarden.domain.contracts import canonical_json, digest_bytes
from mindgarden.domain.scope import local_scope
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests.registry_fixture import create_roots, mutate, register_roots
from tests.support_v1 import add_knowledge, create_garden


@unittest.skipUnless(sys.platform.startswith("linux"), "registry filesystem checkpoint supports Linux")
class RegistryViewTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.fixture = create_roots(self.root / "gardens")
        self.registry = self.root / "configuration/registry.json"
        register_roots(self.registry, self.fixture)

    def session(self, name, visibilities, *, view="private-view-canary", writable=None):
        path = self.registry.parent / (name + ".json")
        arguments = ["scope", "--local-config", str(self.registry), "--registry-view", view,
                     "--session-id", name, "--expires-at", "2099-01-01T00:00:00Z", "--output", str(path),
                     "--request-visibility", "public" if visibilities == ["public"] else "personal",
                     "--publication-authority", "publishable" if visibilities == ["public"] else "never-exportable"]
        for visibility in visibilities:
            arguments += ["--allowed-visibility", visibility]
        if writable:
            arguments += ["--writable-garden", writable]
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(arguments), 0)
        return QueryContext.load(self.registry, path)

    def test_named_union_retrieves_private_links_without_public_backlinks(self):
        personal = self.session("personal-session", ["public", "personal"])
        public = self.session("public-session", ["public"], writable="repository-garden")
        with patch("socket.socket", side_effect=AssertionError("Network attempted")):
            results = search_payload(personal, "evidence", limit=20)
        self.assertEqual({item["reference"]["garden"] for item in results["results"]}, {"repository-garden", "personal-garden"})
        self.assertEqual(results["scope"]["visibility"], "personal")
        links = backlinks_payload(personal, "repository-garden/reviewed-prompt")["links"]
        self.assertTrue(any(item["from"] == "personal-garden/personal-prompt" for item in links))
        self.assertEqual(backlinks_payload(public, "repository-garden/reviewed-prompt")["links"], [])
        profile = json.loads((self.fixture["personal_root"] / ".garden/context-packs/default.json").read_text())
        context = json.loads(render_context(personal, profile, "json"))
        self.assertEqual(context["scope"]["visibility"], "personal")
        self.assertIn(b"personal-content-canary", canonical_json(context))

    def test_public_artifacts_are_identical_to_explicit_bindings_and_ignore_private_metadata(self):
        context = self.session("public-session", ["public"], writable="repository-garden")
        public = self.fixture["public"]
        self.assertEqual(build_federation(context, public["profile"]).files, public["bundle"].files)
        baseline = canonical_json(search_payload(public["context"], "evidence"))
        self.assertEqual(canonical_json(search_payload(context, "evidence")), baseline)
        graph = canonical_json(graph_payload(context))
        document = json.loads(self.registry.read_text())
        private = next(item for item in document["gardens"] if item["id"] == "personal-garden")
        private["root"] = "/unavailable/personal-content-canary"
        document["registry"]["registrations"][-1]["title"] = "private-registry-path-canary"
        document["registry"]["views"].append({"schema": "unknown-private-view", "id": "unrelated-private-view-canary"})
        self.registry.write_bytes(canonical_json(document))
        from mindgarden.application.bindings import explicit_root

        def guarded(value, **options):
            if "personal-content-canary" in value:
                raise AssertionError("Denied private root was probed")
            return explicit_root(value, **options)

        with patch("mindgarden.application.bindings.explicit_root", side_effect=guarded):
            refreshed = QueryContext.load(self.registry, context.session_path)
            self.assertEqual(canonical_json(search_payload(refreshed, "evidence")), baseline)
            self.assertEqual(canonical_json(graph_payload(refreshed)), graph)
            self.assertEqual(build_federation(refreshed, public["profile"]).files, public["bundle"].files)

    def test_unrelated_registration_keeps_view_grants_but_membership_change_revokes(self):
        context = self.session("public-session", ["public"], writable="repository-garden")
        before = canonical_json(search_payload(context, "evidence"))
        extra = self.root / "additional-garden"; create_garden(extra, "additional-garden")
        mutate(self.registry, "register", {"root": str(extra), "scope": local_scope(), "expected_garden": None, "expected_owners": []})
        self.assertEqual(canonical_json(search_payload(context, "evidence")), before)
        mutate(self.registry, "set-view", {"id": "private-view-canary", "gardens": ["repository-garden"]})
        with self.assertRaisesRegex(ContractError, "SESSION_VIEW_STALE"):
            search_payload(context, "evidence")
        fresh = self.session("fresh-public-session", ["public"], writable="repository-garden")
        self.assertEqual(canonical_json(search_payload(fresh, "evidence")), before)

    def test_unregister_keeps_owned_caches_and_invalidates_old_named_sessions_before_bodies(self):
        context = self.session("personal-session", ["public", "personal"], writable="personal-garden")
        write_projection(context, self.fixture["personal_root"], "index.json", b"private cached synthetic data")
        cache = projection_directory(context, self.fixture["personal_root"]) / "index.json"
        mutate(self.registry, "unregister", {"garden": "personal-garden"})
        with patch("mindgarden.application.query.inspect_garden", side_effect=AssertionError("Old view opened bodies")):
            with self.assertRaisesRegex(ContractError, "SESSION_VIEW_STALE"):
                search_payload(context, "evidence")
            with self.assertRaisesRegex(ContractError, "SESSION_VIEW_STALE"):
                QueryContext.load(self.registry, context.session_path)
        self.assertEqual(cache.read_bytes(), b"private cached synthetic data")
        self.assertTrue((self.fixture["personal_root"] / ".garden/knowledge/personal-prompt.md").is_file())

    def test_removed_and_restored_views_never_revive_old_grants_or_explicit_revocations(self):
        context = self.session("old-session", ["public", "personal"])
        snapshot = digest_bytes(self.registry.read_bytes())
        mutate(self.registry, "remove-view", {"id": "private-view-canary"})
        document = json.loads(self.registry.read_text()); document["revoked_sessions"] = ["old-session"]
        self.registry.write_bytes(canonical_json(document))
        mutate(self.registry, "restore", {"revision": snapshot})
        with self.assertRaisesRegex(ContractError, "SESSION_REVOKED"):
            QueryContext.load(self.registry, context.session_path)
        with self.assertRaisesRegex(ContractError, "SESSION_REVOKED"):
            search_payload(context, "evidence")

    def test_selected_view_is_checked_before_missing_or_restricted_root_probes(self):
        document = json.loads(self.registry.read_text())
        document["gardens"].append({"id": "restricted-root-canary", "root": "/unavailable/restricted-root-canary",
                                    "scope": local_scope("restricted")})
        document["registry"]["registrations"].append({"garden": "restricted-root-canary", "owners": ["synthetic-owner"],
            "title": "Unverified synthetic descriptor", "canonical_uri": "urn:mindgarden:garden:restricted-root-canary",
            "version": "1.0.0", "manifest_sha256": "0" * 64})
        self.registry.write_bytes(canonical_json(document))
        mutate(self.registry, "set-view", {"id": "private-view-canary", "gardens": ["repository-garden", "personal-garden", "restricted-root-canary"]})
        from mindgarden.application.bindings import explicit_root

        def guarded(value, **options):
            if "restricted-root-canary" in value or "personal" in value:
                raise AssertionError("Denied root was probed")
            return explicit_root(value, **options)

        with patch("mindgarden.application.bindings.explicit_root", side_effect=guarded):
            context = self.session("public-session", ["public"], writable="repository-garden")
            self.assertNotIn(b"restricted-root-canary", canonical_json(search_payload(context, "evidence")))
        with patch("mindgarden.application.registry.explicit_root", side_effect=guarded):
            report = registry_report(self.registry, garden_id="restricted-root-canary", doctor=True)
        self.assertEqual(report["gardens"][0]["diagnostics"], ["REGISTRY_RUNTIME"])
        mutate(self.registry, "remove-view", {"id": "private-view-canary"})
        with patch("mindgarden.application.bindings.explicit_root", side_effect=AssertionError("Stale view probed a root")):
            with self.assertRaisesRegex(ContractError, "SESSION_VIEW_STALE"):
                QueryContext.load(self.registry, context.session_path)

    def test_views_do_not_grant_review_publication_or_writable_targets(self):
        mutate(self.registry, "set-view", {"id": "public-only", "gardens": ["repository-garden"]})
        path = self.registry.parent / "denied-write-session.json"
        arguments = ["scope", "--local-config", str(self.registry), "--registry-view", "public-only", "--session-id", "denied-write",
                     "--writable-garden", "personal-garden", "--allowed-visibility", "public", "--expires-at", "2099-01-01T00:00:00Z",
                     "--output", str(path)]
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(main(arguments), 3)
        self.assertFalse(path.exists())
        self.assertIn("SESSION_VIEW_STALE", errors.getvalue())
        context = self.session("personal-session", ["public", "personal"])
        add_knowledge(self.fixture["personal_root"], "pending-note", reviewed=False, body="unreviewed-secret-canary")
        self.assertNotIn(b"unreviewed-secret-canary", canonical_json(search_payload(context, "")))
        with self.assertRaisesRegex(ContractError, "FEDERATION_SCOPE"):
            build_federation(context, self.fixture["public"]["profile"])

    def test_legacy_explicit_session_flow_still_uses_the_registry_bindings(self):
        path = self.registry.parent / "explicit-session.json"
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["scope", "--local-config", str(self.registry), "--readable-garden", "repository-garden",
                                   "--session-id", "explicit-session", "--allowed-visibility", "public", "--request-visibility", "public",
                                   "--publication-authority", "publishable", "--expires-at", "2099-01-01T00:00:00Z", "--output", str(path)]), 0)
        context = QueryContext.load(self.registry, path)
        self.assertNotIn("registry_view", context.session)
        self.assertTrue(search_payload(context, "evidence")["results"])

    def test_cli_demo_matches_committed_proof_and_preserves_existing_workspaces(self):
        specification = importlib.util.spec_from_file_location("synthetic_registry_demo", Path(__file__).parents[1] / "scripts/registry_demo.py")
        demo = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(demo)
        report = demo.run_demo(self.root / "demo")
        expected = json.loads((Path(__file__).parent / "fixtures/registry/expected-proof.json").read_text())
        self.assertEqual(report, expected)
        occupied = self.root / "human-workspace"; occupied.mkdir()
        marker = occupied / "human.txt"; marker.write_text("Keep this synthetic file.\n")
        with self.assertRaisesRegex(ValueError, "new or empty"):
            demo.run_demo(occupied)
        self.assertEqual(marker.read_text(), "Keep this synthetic file.\n")


if __name__ == "__main__":
    unittest.main()
