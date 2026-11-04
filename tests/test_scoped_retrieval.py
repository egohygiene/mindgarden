"""Adversarial local scope enforcement before bodies, ranking and traversal."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.bindings import LocalBindings
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import (
    backlinks_payload, build_index, graph_payload, projection_directory, render_context, search_payload, write_projection,
)
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.domain.contracts import canonical_json, digest_bytes
from mindgarden.domain.scope import local_scope
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests.support_v1 import FIXTURES, add_knowledge, add_source, create_garden, reference, write_json, write_session
from tests import test_v1_retrieval as retrieval_tests


class ScopedRetrievalTests(unittest.TestCase):
    def setUp(self):
        retrieval_tests.RetrievalTests.setUp(self)
        self.canaries = json.loads((Path(__file__).parent / "fixtures/scoped-retrieval/cases.json").read_text())["canaries"]

    def refresh(self, **updates):
        session = json.loads(self.session_path.read_text()); session.update(updates)
        session = bind_session_revisions(self.configuration, session)
        write_json(self.session_path, session)
        self.context = QueryContext.load(self.configuration, self.session_path)
        return session

    def test_denied_bodies_and_invalid_unreviewed_metadata_are_never_opened(self):
        before = canonical_json(build_index(self.context))
        denied = add_knowledge(self.workspace, "denied-note", body="denied-body-canary\n", reviewed=False)
        denied["content"] = {"path": "../denied-body-canary.md", "sha256": "0" * 64}
        write_json(self.workspace / ".garden/knowledge/denied-note.json", denied)
        restricted = add_knowledge(self.workspace, "restricted-note", body="restricted-source-canary\n")
        restricted["scope"] = local_scope("restricted")
        write_json(self.workspace / ".garden/knowledge/restricted-note.json", restricted)
        forbidden = {self.workspace / ".garden/knowledge/denied-note.md",
                     self.workspace / ".garden/knowledge/restricted-note.md"}
        read_bytes = Path.read_bytes

        def guarded_read(path):
            if path in forbidden:
                raise AssertionError("Denied body opened")
            return read_bytes(path)

        with patch.object(Path, "read_bytes", guarded_read):
            after = canonical_json(build_index(self.context))
        self.assertEqual(before, after)
        for canary in self.canaries:
            self.assertNotIn(canary.encode(), after)

    def test_denied_garden_and_vault_bindings_are_not_probed_or_echoed(self):
        configuration = json.loads(self.configuration.read_text())
        configuration["gardens"].append({"id": "denied-garden", "root": "/missing/denied-body-canary",
                                          "scope": {"visibility": "restricted", "policy": "unknown"}})
        configuration["vaults"].append({"id": "denied-vault", "adapter": "unknown", "root": "/missing/restricted-source-canary"})
        write_json(self.configuration, configuration)
        session = json.loads(self.session_path.read_text())
        session["readable"].append({"garden": "denied-garden", "revision": "sha256:" + "0" * 64})
        write_json(self.session_path, session)
        context = QueryContext.load(self.configuration, self.session_path)
        before = canonical_json(build_index(context))
        configuration["gardens"][-1]["root"] = "/another-missing-denied-location"
        write_json(self.configuration, configuration)
        self.assertEqual(before, canonical_json(build_index(context)))
        self.assertNotIn(b"denied-garden", before)
        self.assertNotIn(b"denied-vault", before)
        self.assertEqual(len(json.loads(before)["inputs"]), 1)

    def test_denied_source_dependency_excludes_reviewed_derivation_before_body_read(self):
        before = canonical_json(build_index(self.context))
        source = add_source(self.workspace, b"restricted-source-canary", record_id="restricted-source")
        source["scope"] = local_scope("restricted")
        write_json(self.workspace / ".garden/sources/restricted-source.json", source)
        evidence = [{"source": reference("synthetic-garden", source["id"], source["artifact"]["sha256"]),
                     "locator": "artifact", "content_sha256": source["artifact"]["sha256"]}]
        note = add_knowledge(self.workspace, "reviewed-but-denied", body="denied-body-canary", sources=evidence)
        note["content"]["path"] = "../must-never-open.md"
        write_json(self.workspace / ".garden/knowledge/reviewed-but-denied.json", note)
        # The path is unsafe, but authorization excludes this whole dependency
        # closure before content/path validation can become a side channel.
        self.assertEqual(before, canonical_json(build_index(self.context)))

    def test_hidden_edges_counts_includes_and_backlinks_do_not_change_visible_revision(self):
        before = canonical_json(build_index(self.context))
        denied = add_knowledge(self.workspace, "hidden-target", body="hidden-backlink-canary", reviewed=False)
        edge = json.loads((FIXTURES / "synapse.json").read_text())
        first = json.loads((self.workspace / ".garden/knowledge/synthetic-prompt.json").read_text())
        edge.update(id="hidden-relationship", garden="synthetic-garden", source=reference("synthetic-garden", first["id"]),
                    target=reference("synthetic-garden", denied["id"]), visibility="private", review=first["review"])
        write_json(self.workspace / ".garden/synapses/hidden-relationship.json", edge)
        first["synapses"].append(reference("synthetic-garden", edge["id"], digest_bytes(canonical_json(edge))))
        write_json(self.workspace / ".garden/knowledge/synthetic-prompt.json", first)
        self.assertEqual(before, canonical_json(build_index(self.context)))
        self.assertEqual(graph_payload(self.context, start="synthetic-garden/hidden-target"),
                         graph_payload(self.context, start="unknown/absent"))
        self.assertEqual(backlinks_payload(self.context, "synthetic-garden/hidden-target"),
                         backlinks_payload(self.context, "unknown/absent"))
        profile = {**self.profile, "include": [reference("synthetic-garden", denied["id"]), reference("unknown", "absent")]}
        content = render_context(self.context, profile, "json")
        self.assertNotIn(b"hidden-target", content)
        self.assertNotIn(b"absent", content)
        self.assertNotIn(b"hidden-relationship", content)

    def test_unknown_policy_records_and_malformed_denied_json_are_silent_denials(self):
        before = canonical_json(search_payload(self.context, "prompt"))
        denied = add_knowledge(self.workspace, "unknown-policy", body="denied-body-canary")
        denied["scope"] = local_scope(); denied["scope"]["policy"]["revision"] = "sha256:" + "f" * 64
        write_json(self.workspace / ".garden/knowledge/unknown-policy.json", denied)
        (self.workspace / ".garden/knowledge/unidentifiable.json").write_text('{"private":"denied-body-canary",')
        self.assertEqual(before, canonical_json(search_payload(self.context, "prompt")))

    def test_mixed_provenance_derivation_is_denied_before_body_verification(self):
        organization = self.root / "source-organization"; create_garden(organization, "source-organization", "internal")
        source = add_source(organization, b"Synthetic organizational evidence.", record_id="organization-source")
        source["visibility"] = "internal"
        write_json(organization / ".garden/sources/organization-source.json", source)
        configuration = json.loads(self.configuration.read_text())
        configuration["gardens"].append({"id": "source-organization", "root": str(organization), "scope": local_scope("organization")})
        write_json(self.configuration, configuration)
        write_session(self.session_path, self.configuration, visibility=["personal", "organization"])
        context = QueryContext.load(self.configuration, self.session_path)
        before = canonical_json(build_index(context))
        evidence = [{"source": reference("source-organization", source["id"], source["artifact"]["sha256"]),
                     "locator": "artifact", "content_sha256": source["artifact"]["sha256"]}]
        add_knowledge(self.workspace, "mixed-derivation", body="denied-body-canary", sources=evidence)
        forbidden = self.workspace / ".garden/knowledge/mixed-derivation.md"
        read_bytes = Path.read_bytes

        def guarded_read(path):
            if path == forbidden:
                raise AssertionError("Mixed derived body opened before classification")
            return read_bytes(path)

        with patch.object(Path, "read_bytes", guarded_read):
            self.assertEqual(before, canonical_json(build_index(context)))

    def test_result_candidate_depth_context_and_exact_revision_budgets(self):
        self.refresh(budgets={"max_results": 1, "max_context_bytes": 3500, "max_depth": 1, "max_candidates": 2})
        self.assertLessEqual(len(build_index(self.context)["records"]), 2)
        self.assertLessEqual(len(search_payload(self.context, "", limit=1000)["results"]), 1)
        self.assertLessEqual(len(graph_payload(self.context, depth=20, limit=1000)["nodes"]), 1)
        content = render_context(self.context, self.profile, "json")
        self.assertLessEqual(len(content), 3500)
        for limit in (0, -1):
            with self.assertRaisesRegex(ContractError, "QUERY_BUDGET"):
                search_payload(self.context, "", limit=limit)
        profile = {**self.profile, "include": [reference("synthetic-garden", "second-note", "0" * 64)]}
        content = json.loads(render_context(self.context, profile, "json"))
        self.assertTrue(any(item["reason"] == "revision-mismatch" for item in content["excluded"]))

    def test_expiration_revocation_and_mid_query_revocation_stop_outputs(self):
        current = [datetime(2026, 11, 4, tzinfo=timezone.utc)]
        session = json.loads(self.session_path.read_text()); session["expires_at"] = "2026-11-04T00:01:00Z"
        write_json(self.session_path, session)
        context = QueryContext.load(self.configuration, self.session_path, clock=lambda: current[0])
        build_index(context)
        current[0] = datetime(2026, 11, 4, 0, 2, tzinfo=timezone.utc)
        with self.assertRaisesRegex(ContractError, "SESSION_EXPIRED"):
            search_payload(context, "prompt")
        self.refresh(expires_at="2099-01-01T00:00:00Z")
        from mindgarden.application.retrieval import score_note

        def revoke_while_scoring(*arguments):
            configuration = json.loads(self.configuration.read_text())
            configuration["revoked_sessions"] = [self.context.session["id"]]
            write_json(self.configuration, configuration)
            return score_note(*arguments)

        with patch("mindgarden.application.retrieval.score_note", side_effect=revoke_while_scoring):
            with self.assertRaisesRegex(ContractError, "SESSION_REVOKED"):
                search_payload(self.context, "prompt")
        with self.assertRaisesRegex(ContractError, "SESSION_REVOKED"):
            write_projection(self.context, self.workspace, "index.json", b"must-not-write")

    def test_caches_are_scope_isolated_and_never_used_as_query_authority(self):
        add_knowledge(self.workspace, "cached-proposal", body="unreviewed-cache-canary", reviewed=False)
        self.refresh(allowed_review_states=["approved", "unreviewed"])
        broad = self.context
        broad_content = canonical_json(build_index(broad, include_unreviewed=True))
        self.assertIn(b"unreviewed-cache-canary", broad_content)
        write_projection(broad, self.workspace, "index.json", broad_content)
        broad_directory = projection_directory(broad, self.workspace)
        self.refresh(allowed_review_states=["approved"])
        narrow_content = canonical_json(build_index(self.context))
        write_projection(self.context, self.workspace, "index.json", narrow_content)
        narrow_directory = projection_directory(self.context, self.workspace)
        self.assertNotEqual(broad_directory, narrow_directory)
        self.assertNotIn(b"unreviewed-cache-canary", (narrow_directory / "index.json").read_bytes())
        (narrow_directory / "index.json").write_text('denied-body-canary')
        self.assertNotIn("denied-body-canary", json.dumps(search_payload(self.context, "prompt")))
        self.assertEqual(narrow_directory.stat().st_mode & 0o777, 0o700)

    def test_mixed_scope_output_and_public_destination_fail_closed(self):
        public_root = self.root / "public-target"; create_garden(public_root, "public-target", "public")
        organization = self.root / "organization"; create_garden(organization, "organization", "internal")
        add_knowledge(organization, "organization-note", visibility="internal")
        configuration = json.loads(self.configuration.read_text())
        configuration["gardens"] += [{"id": "public-target", "root": str(public_root), "scope": local_scope("public")},
                                      {"id": "organization", "root": str(organization), "scope": local_scope("organization")}]
        write_json(self.configuration, configuration)
        write_session(self.session_path, self.configuration, visibility=["personal", "organization", "public"], writable="public-target")
        context = QueryContext.load(self.configuration, self.session_path)
        index = build_index(context)
        self.assertEqual(index["scope"]["visibility"], "restricted")
        self.assertEqual(index["scope"]["publication"], "never-exportable")
        with self.assertRaisesRegex(ContractError, "OUTPUT_SCOPE"):
            write_projection(context, public_root, "index.json", canonical_json(index))
        manifest = json.loads((public_root / ".garden/garden.json").read_text())
        self.assertFalse((public_root / ".garden" / manifest["roots"]["generated"][0] / "scopes").exists())

    def test_public_allowlist_denial_precedes_body_reads_and_candidate_metadata(self):
        root = self.root / "public-policy"; create_garden(root, "public-policy", "public")
        body = "publication-denied-canary\n"
        note = add_knowledge(root, "public-note", body=body, visibility="public"); note["publication"] = "eligible"
        write_json(root / ".garden/knowledge/public-note.json", note)
        configuration = json.loads(self.configuration.read_text())
        configuration["gardens"].append({"id": "public-policy", "root": str(root),
                                          "scope": local_scope("public", publication="publishable")})
        write_json(self.configuration, configuration)
        session = write_session(self.session_path, self.configuration, visibility=["public"], readable_ids=["public-policy"], writable=None)
        session.update(publication_authority="publishable", request_scope=local_scope("public", publication="publishable"))
        write_json(self.session_path, bind_session_revisions(self.configuration, session))
        context = QueryContext.load(self.configuration, self.session_path)
        before = canonical_json(build_index(context))
        self.assertEqual(json.loads(before)["records"], [])
        (root / ".garden/knowledge/public-note.md").write_text("Modified denied body; must not be verified or exported.")
        self.assertEqual(before, canonical_json(build_index(context)))
        self.assertNotIn(b"publication-denied-canary", before)
        (root / ".garden/knowledge/public-note.md").write_text(body)
        manifest_path = root / ".garden/garden.json"; manifest = json.loads(manifest_path.read_text())
        manifest["publication"]["allow"] = {"kinds": ["procedure"], "domains": ["knowledge-systems"], "topics": ["prompt-bank"]}
        write_json(manifest_path, manifest)
        write_json(self.session_path, bind_session_revisions(self.configuration, session))
        allowed = build_index(QueryContext.load(self.configuration, self.session_path))
        self.assertEqual(allowed["records"][0]["reference"]["id"], "public-note")

    def test_authorized_corruption_has_generic_diagnostics_and_no_partial_stdout(self):
        (self.workspace / ".garden/knowledge/synthetic-prompt.md").write_text("denied-body-canary")
        with redirect_stdout(io.StringIO()) as output, redirect_stderr(io.StringIO()) as errors:
            code = main(["search", "--repository-root", str(self.workspace), "--local-config", str(self.configuration),
                         "--scope", str(self.session_path), "--query", "prompt"])
        self.assertEqual(code, 3)
        self.assertEqual(output.getvalue(), "")
        self.assertIn("QUERY_INTEGRITY", errors.getvalue())
        self.assertNotIn(str(self.root), errors.getvalue())
        self.assertNotIn("synthetic-prompt.md", errors.getvalue())
        self.assertNotIn("denied-body-canary", errors.getvalue())

    def test_scope_cli_authors_portable_private_sessions_and_locked_reads_stop(self):
        output_path = self.root / "authored-session.json"
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(["scope", "--local-config", str(self.configuration), "--session-id", "authored-session",
                "--readable-garden", "synthetic-garden", "--writable-garden", "synthetic-garden",
                "--allowed-visibility", "personal", "--expires-at", "2099-01-01T00:00:00Z", "--output", str(output_path)]), 0)
        self.assertNotIn(str(self.root), output.getvalue())
        self.assertEqual(output_path.stat().st_mode & 0o777, 0o600)
        context = QueryContext.load(self.configuration, output_path)
        self.assertTrue(search_payload(context, "prompt")["results"])
        (self.workspace / ".mindgarden-write.lock").write_text("synthetic recovery lock")
        with self.assertRaisesRegex(ContractError, "WRITE_LOCKED"):
            search_payload(context, "prompt")
