"""Full relation vocabulary, cross-garden suppression and authority-preserving selection."""

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import (
    backlinks_payload,
    build_index,
    graph_payload,
    outbound_payload,
    projection_directory,
    render_context,
    search_payload,
)
from mindgarden.domain.contracts import ContractRegistry, canonical_json
from mindgarden.domain.scope import local_scope
from mindgarden.domain.validation import ContractError
from tests.projection_corpus import create_corpus
from tests.support_v1 import (
    FIXTURES,
    add_knowledge,
    add_source,
    create_garden,
    reference,
    write_json,
    write_session,
)

RELATIONS = {
    "related",
    "supports",
    "contradicts",
    "supersedes",
    "derived-from",
    "part-of",
    "depends-on",
    "references",
}


class ProjectionSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.context, self.profile = create_corpus(self.root / "first", 8)
        self.garden = self.context.bindings.garden("synthetic-garden")["root"]
        self.other = self.root / "other"
        create_garden(self.other, "other-garden")
        source = add_source(self.other, b"Synthetic independent second source.\n")
        self.other_note = add_knowledge(
            self.other,
            "other-note",
            body="Independent second-garden needle.\n",
            sources=[
                {
                    "source": reference(
                        "other-garden", source["id"], source["artifact"]["sha256"]
                    ),
                    "locator": "artifact",
                    "content_sha256": source["artifact"]["sha256"],
                }
            ],
        )
        config = json.loads(self.context.bindings.path.read_text())
        config["gardens"].append(
            {"id": "other-garden", "root": str(self.other), "scope": local_scope()}
        )
        write_json(self.context.bindings.path, config)
        self.refresh()

    def refresh(self):
        write_session(self.context.session_path, self.context.bindings.path)
        self.context = QueryContext.load(
            self.context.bindings.path, self.context.session_path
        )

    def note(self, identity):
        return json.loads(
            (self.garden / ".garden/knowledge" / (identity + ".json")).read_text()
        )

    def edge(self, kind, target, identity=None, directed=True):
        original = self.note("corpus-00000")
        source = reference(
            "synthetic-garden", original["id"], original["content"]["sha256"]
        )
        edge = json.loads((FIXTURES / "synapse.json").read_text())
        edge.update(
            id=identity or "matrix-" + kind,
            garden="synthetic-garden",
            type=kind,
            directed=directed,
            source=source,
            target=target,
            review=original["review"],
            status="active",
            visibility="private",
            scope=local_scope(),
            evidence=original["sources"],
        )
        write_json(self.garden / ".garden/synapses" / (edge["id"] + ".json"), edge)

    def test_all_typed_relations_cross_garden_backlinks_and_exact_claim_sources(self):
        target = self.note("corpus-00001")
        ref = reference("synthetic-garden", target["id"], target["content"]["sha256"])
        for kind in RELATIONS - {"supports"}:
            self.edge(kind, ref, directed=kind != "related")
        self.edge(
            "references",
            reference(
                "other-garden",
                self.other_note["id"],
                self.other_note["content"]["sha256"],
            ),
            identity="cross-garden-reference",
        )
        self.refresh()
        index = build_index(self.context)
        self.assertEqual({edge["type"] for edge in index["edges"]}, RELATIONS)
        self.assertEqual(len(index["edges"]), 9)
        backlinks = backlinks_payload(self.context, "synthetic-garden/corpus-00001")
        self.assertEqual({edge["type"] for edge in backlinks["links"]}, RELATIONS)
        reciprocal = backlinks_payload(self.context, "synthetic-garden/corpus-00000")
        self.assertEqual([edge["type"] for edge in reciprocal["links"]], ["related"])
        outbound = outbound_payload(self.context, "synthetic-garden/corpus-00000")
        self.assertEqual(len(outbound["links"]), 9)
        graph = graph_payload(
            self.context, start="synthetic-garden/corpus-00000", depth=1
        )
        self.assertTrue(
            any(n["reference"]["garden"] == "other-garden" for n in graph["nodes"])
        )
        claim = search_payload(self.context, "claimneedle")["results"][0]
        self.assertEqual(claim["reference"]["id"], "corpus-claim")
        self.assertEqual(claim["sources"], self.note("corpus-00000")["sources"])
        for format in ("json", "markdown"):
            self.assertLessEqual(
                len(render_context(self.context, self.profile, format)),
                self.profile["max_bytes"],
            )
        for value, name in (
            (index, "index"),
            (graph, "graph"),
            (backlinks, "backlinks"),
            (outbound, "outbound-links"),
        ):
            self.assertEqual(ContractRegistry().errors(value, name), [])

    def test_unavailable_and_denied_targets_do_not_change_any_projection(self):
        def outputs():
            return [
                canonical_json(build_index(self.context)),
                canonical_json(search_payload(self.context, "needle")),
                canonical_json(graph_payload(self.context)),
                canonical_json(
                    backlinks_payload(self.context, "synthetic-garden/corpus-00000")
                ),
                canonical_json(
                    outbound_payload(self.context, "synthetic-garden/corpus-00000")
                ),
                render_context(self.context, self.profile, "json"),
                render_context(self.context, self.profile, "markdown"),
            ]

        before = outputs()
        self.edge(
            "references",
            reference("unavailable-garden", "missing-canary", "0" * 64),
            identity="unavailable-canary",
        )
        denied = add_knowledge(
            self.garden,
            "denied-canary",
            body="DENIED_PROJECTION_CANARY\n",
            reviewed=False,
        )
        denied["content"]["path"] = "../unsafe-canary.txt"
        write_json(self.garden / ".garden/knowledge/denied-canary.json", denied)
        self.edge(
            "references",
            reference("synthetic-garden", denied["id"], denied["content"]["sha256"]),
            identity="denied-edge-canary",
        )
        self.assertEqual(before, outputs())
        self.assertNotIn(b"canary", b"".join(outputs()))

    def test_selection_never_opens_unselected_bodies_and_uses_distinct_cache_identity(
        self,
    ):
        session_bytes = self.context.session_path.read_bytes()
        original_read = Path.read_bytes

        def guard(path):
            if path.is_relative_to(self.other / ".garden") and path.suffix != ".json":
                raise AssertionError("Unselected authorized body opened")
            return original_read(path)

        with patch.object(Path, "read_bytes", guard):
            selected = self.context.select_gardens({"synthetic-garden"})
            index = build_index(selected)
            self.assertTrue(index["records"])
            self.assertEqual(
                [item["garden"] for item in index["inputs"]], ["synthetic-garden"]
            )
            self.assertEqual(search_payload(selected, "independent")["results"], [])
        self.assertEqual(self.context.session_path.read_bytes(), session_bytes)
        self.assertEqual(selected.session, self.context.session)
        self.assertNotEqual(selected.scope_digest(), self.context.scope_digest())
        self.assertNotEqual(
            projection_directory(selected, self.garden),
            projection_directory(self.context, self.garden),
        )
        self.assertEqual(
            build_index(selected),
            build_index(self.context.select_gardens({"synthetic-garden"})),
        )

    def test_loading_selection_avoids_unavailable_unselected_root(self):
        config = json.loads(self.context.bindings.path.read_text())
        missing = str(self.root / "unavailable-peer")
        config["gardens"][1]["root"] = missing
        write_json(self.context.bindings.path, config)
        from mindgarden.application.bindings import explicit_root

        def guard(value, **options):
            if value == missing:
                raise AssertionError("Unselected unavailable root probed")
            return explicit_root(value, **options)

        with patch("mindgarden.application.bindings.explicit_root", side_effect=guard):
            selected = QueryContext.load(
                self.context.bindings.path,
                self.context.session_path,
                garden_ids={"synthetic-garden"},
            )
            self.assertTrue(search_payload(selected, "needle00000")["results"])
        with self.assertRaisesRegex(ContractError, "QUERY_SELECTION"):
            QueryContext.load(
                self.context.bindings.path,
                self.context.session_path,
                garden_ids={"not-authorized"},
            )

    def test_selection_cannot_widen_expire_or_survive_revocation(self):
        child = self.context.select_gardens({"synthetic-garden"})
        for ids in (set(), {"unavailable-garden"}, {"other-garden"}):
            with self.assertRaisesRegex(ContractError, "QUERY_SELECTION"):
                child.select_gardens(ids)
        child.clock = lambda: datetime(2100, 1, 1, tzinfo=timezone.utc)
        with self.assertRaisesRegex(ContractError, "SESSION_EXPIRED"):
            search_payload(child, "needle")
        child = self.context.select_gardens({"synthetic-garden"})
        config = json.loads(self.context.bindings.path.read_text())
        config["revoked_sessions"] = [self.context.session["id"]]
        write_json(self.context.bindings.path, config)
        with self.assertRaisesRegex(ContractError, "SESSION_REVOKED"):
            build_index(child)

    def test_omitted_cross_garden_dependencies_require_explicit_revision_refresh(self):
        self.edge(
            "references",
            reference(
                "other-garden",
                self.other_note["id"],
                self.other_note["content"]["sha256"],
            ),
        )
        self.refresh()
        with self.assertRaisesRegex(ContractError, "SESSION_REVISION"):
            build_index(self.context.select_gardens({"synthetic-garden"}))
        self.assertEqual(
            len(
                build_index(
                    self.context.select_gardens(set(self.context.bindings.gardens))
                )["inputs"]
            ),
            2,
        )
