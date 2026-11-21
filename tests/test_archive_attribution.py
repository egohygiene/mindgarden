"""Authored semantic cases prove archive evidence survives extraction and review.

The fixture supplies interpretations; this is not a model accuracy evaluation.
"""

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.application.bindings import garden_fingerprint
from mindgarden.application.curation import apply_curation, build_curation_plan
from mindgarden.application.extraction import produce_batch
from mindgarden.application.ingestion import apply_ingestion, build_ingestion_plan
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import graph_payload, search_payload
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.application.source_evidence import resolve_source_evidence
from mindgarden.domain.contracts import ContractRegistry, canonical_json, digest_bytes
from mindgarden.domain.scope import local_scope
from tests.archive_fixture import FIXTURE_ROOT, package_bytes, v2_members
from tests.support_v1 import TIME, write_json, write_session
from tests import test_source_adapters as source_fixtures

CASES = json.loads((FIXTURE_ROOT / "attribution-cases.json").read_bytes())


def archive_members(archive_id, cases, revision=1):
    """Use the existing tested v2 envelope and preservation message shape."""
    members = v2_members(revision=revision)
    members.pop("assets/attachment.txt")
    for name in ("ARCHIVE-MANIFEST.json", "VALIDATION.json", "ASSET-MANIFEST.json"):
        document = json.loads(members[name])
        document["archive_id"] = archive_id
        if name == "ASSET-MANIFEST.json":
            document["assets"] = []
        members[name] = canonical_json(document)
    conversation = json.loads(members["CONVERSATION.json"])
    template = conversation["messages"][0]
    messages = []
    for index, case in enumerate(cases):
        message = deepcopy(template)
        message.update(
            id=case["id"],
            index=index + 1,
            role=case["speaker"],
            role_raw=case["speaker"],
            source_message_id="native-" + case["id"],
            source_locator="synthetic-turn:" + case["id"],
            timestamp=case["timestamp"],
            timestamp_raw=case["timestamp"],
            parent_ids=[cases[index - 1]["id"]] if index else [],
            branch_id="branch-main",
            content=[{"type": "text", "text": case["text"]}],
        )
        messages.append(message)
    branch = deepcopy(conversation["branches"][0])
    branch["message_ids"] = [m["id"] for m in messages]
    conversation.update(archive_id=archive_id, messages=messages, branches=[branch])
    conversation["primary_view"]["message_ids"] = branch["message_ids"]
    members["CONVERSATION.json"] = canonical_json(conversation)
    return members


def authored_response(case):
    """Explicit labels exercise the existing producer boundary, without a model."""
    entities = [
        {
            "id": "project",
            "label": "Project Cedar",
            "quote": "Project Cedar",
            "aliases": [],
            "resolution": "new",
            "rationale": "Proposed local identity, not a cross-conversation merge.",
        },
        {
            "id": "schedule",
            "label": case["object"],
            "quote": case["object"],
            "aliases": [],
            "resolution": "new",
            "rationale": "Proposed schedule retains the original message context.",
        },
    ]
    if case["id"] == "quotation":
        entities.append(
            {
                "id": "alex",
                "label": "Alex",
                "quote": "Alex",
                "aliases": [],
                "resolution": "ambiguous",
                "rationale": "No evidence establishes which Alex or a shared identity.",
            }
        )
    return {
        "schema": "mindgarden.extraction-output/v1",
        "status": "success",
        "diagnostics": ["ambiguous-entity"] if case["id"] == "quotation" else [],
        "entities": entities,
        "assertions": [
            {
                "id": "schedule-statement",
                "subject": "project",
                "predicate": "related",
                "object": "schedule",
                "statement": case["text"],
                "quote": case["text"],
                "polarity": "positive",
                "stance": case["stance"],
                "context": case["context"],
                "temporal": case["timestamp"],
                "contradicts": [],
                "uncertainty": [
                    "Authored interpretation; no independent verification."
                ],
            }
        ],
    }


class ArchiveAttributionTests(unittest.TestCase):
    def setUp(self):
        source_fixtures.SourceAdapterTests.setUp(self)
        self.units = {}
        self.members = archive_members("synthetic-attribution", CASES)
        self.ingest("synthetic-attribution", self.members)
        self.other = archive_members("synthetic-other", [CASES[2]])
        self.ingest("synthetic-other", self.other)

    def ingest(self, identity, members):
        path = self.root / (identity + ".zip")
        path.write_bytes(package_bytes(members))
        plan = build_ingestion_plan(
            self.bindings,
            "synthetic-garden",
            "synthetic-vault",
            path,
            {
                **self.metadata,
                "source_id": identity,
                "origin": "urn:synthetic:" + identity,
                "media_type": "application/zip",
            },
            adapter_id="conversation-archive",
            manifest_version="2.0.2",
        )
        changed = apply_ingestion(plan, plan.digest, self.bindings, "synthetic-vault")
        for unit in plan.inputs["normalized_sources"]:
            if "message_id" in unit["metadata"]:
                self.units[(identity, unit["metadata"]["message_id"])] = unit
        return changed

    def context(self):
        path = self.root / "source-session.json"
        session = write_session(path, self.configuration)
        session.update(
            request_scope=local_scope(publication="never-exportable"),
            source_grants=[u["source"] for u in self.units.values()],
        )
        session["projections"].append("source-evidence")
        session["budgets"].update(max_context_bytes=262144, max_candidates=1000)
        write_json(path, bind_session_revisions(self.configuration, session))
        return QueryContext.load(self.configuration, path)

    def produce(self, context):
        descriptor = {
            "id": "authored-attribution",
            "version": "1.0.0",
            "model": "authored-fixture-no-model",
            "prompt_revision": digest_bytes(b"authored-attribution/v1"),
            "schema_revision": "mindgarden.extraction-output/v1",
        }
        request = {
            "schema": "mindgarden.extraction-request/v1",
            "id": "synthetic-attribution",
            "garden": "synthetic-garden",
            "created_at": TIME,
            "domains": ["knowledge-systems"],
            "topics": ["review"],
            "producer": descriptor,
            "sources": [u["evidence"][0] for u in self.units.values()],
            "limits": {"max_input_bytes": 65536, "max_output_bytes": 32768},
        }
        cases = {case["text"]: case for case in CASES}

        class AuthoredProducer:
            execution = "offline"

            def __init__(self):
                self.descriptor = descriptor

            def extract(self, item):
                return authored_response(cases[item["text"]])

        return produce_batch(context, request, AuthoredProducer())

    def test_archive_to_review_retains_distinct_semantics_exact_evidence_and_conflict(
        self,
    ):
        context = self.context()
        before = garden_fingerprint(self.workspace)
        originals = self.vault.export_bundle()
        with (
            patch("socket.socket", side_effect=AssertionError("Network")),
            patch("subprocess.run", side_effect=AssertionError("Source executed")),
        ):
            batch = self.produce(context)
        self.assertEqual(batch["status"], "complete")
        self.assertEqual(garden_fingerprint(self.workspace), before)
        proposal = batch["proposal"]
        self.assertIsNone(proposal["review_authority"])
        self.assertEqual(ContractRegistry().errors(proposal, "curation-plan"), [])
        assertions = {}
        for candidate in proposal["candidates"]:
            output = candidate["output"]
            self.assertEqual(output["review"]["state"], "unreviewed")
            self.assertNotEqual(output["title"], "Alex")
            if output["claims"]:
                assertions[canonical_json(candidate["sources"][0])] = candidate
        for index, case in enumerate(CASES):
            unit = self.units[("synthetic-attribution", case["id"])]
            citation = unit["evidence"][0]
            evidence = resolve_source_evidence(context, **citation)
            self.assertEqual(evidence["text"], case["text"])
            self.assertEqual(evidence["origin"]["speaker"], case["speaker"])
            self.assertEqual(evidence["origin"]["timestamp"], case["timestamp"])
            self.assertEqual(evidence["origin"]["branch_id"], "branch-main")
            selector = evidence["origin"]["original_selector"]
            self.assertEqual(selector["json_pointer"], "/messages/" + str(index))
            self.assertEqual(
                selector["member_sha256"],
                digest_bytes(self.members["CONVERSATION.json"]),
            )
            message = json.loads(self.vault.get(unit["source"]["revision"]))
            self.assertEqual(
                message["parent_ids"], [CASES[index - 1]["id"]] if index else []
            )
            self.assertEqual(citation["locator"], "json:/content/0/text")
            self.assertEqual(
                citation["content_sha256"], digest_bytes(case["text"].encode())
            )
            candidate = assertions[canonical_json(citation)]
            output = candidate["output"]
            self.assertIn("Proposed " + case["stance"], output["body"])
            self.assertIn("Context: " + case["context"], output["caveats"])
            self.assertEqual(
                output["attribution"],
                "assistant-suggestion"
                if case["speaker"] == "assistant"
                else "user-report",
            )
            if case["stance"] == "question":
                self.assertEqual(
                    output["claims"][0]["epistemic_state"], "open-question"
                )

        def selected(case_id):
            return assertions[
                canonical_json(
                    self.units[("synthetic-attribution", case_id)]["evidence"][0]
                )
            ]

        # A human explicitly links the separate messages. The adapter/producer
        # does not infer cross-message contradictions or grant itself approval.
        decision, correction = selected("decision"), selected("correction")
        for candidate, other in ((decision, correction), (correction, decision)):
            target = {"garden": "synthetic-garden", "id": other["id"], "revision": None}
            candidate["output"]["contradictions"].append(target)
            candidate["output"]["synapses"].append(
                {
                    "id": candidate["id"] + "-reviewed-conflict",
                    "type": "contradicts",
                    "target": target,
                    "directed": True,
                    "review": deepcopy(candidate["output"]["review"]),
                    "rationale": "Human retains the incompatible monthly/weekly decisions with separate evidence.",
                }
            )
        review = {
            "state": "approved",
            "reviewers": ["synthetic-reviewer"],
            "reviewed_at": TIME,
            "rationale": "Authored review preserves attribution and disagreement, not verified truth.",
        }
        proposal["review_authority"] = {"kind": "human", "id": "synthetic-reviewer"}
        for candidate in proposal["candidates"]:
            candidate["output"].update(review=review, status="active")
            for record in (
                candidate["output"]["claims"] + candidate["output"]["synapses"]
            ):
                record["review"] = review
        path = self.root / "reviewed-attribution.json"
        write_json(path, proposal)
        plan = build_curation_plan(self.bindings, path)
        self.assertTrue(apply_curation(plan, plan.digest, self.bindings))
        self.assertFalse(apply_curation(plan, plan.digest, self.bindings))
        path = self.root / "reviewed-session.json"
        session = write_session(path, self.configuration)
        session["budgets"]["max_context_bytes"] = 262144
        write_json(path, session)
        reviewed = QueryContext.load(self.configuration, path)
        results = search_payload(reviewed, "Project Cedar", limit=100)
        result_citations = {
            canonical_json(e)
            for result in results["results"]
            for e in result["sources"]
        }
        self.assertTrue(
            {canonical_json(u["evidence"][0]) for u in self.units.values()}
            <= result_citations
        )
        self.assertTrue(
            any(e["type"] == "contradicts" for e in graph_payload(reviewed)["edges"])
        )
        self.assertEqual(self.vault.export_bundle(), originals)

    def test_overlaps_reuse_evidence_and_identical_names_in_other_conversations_stay_separate(
        self,
    ):
        original_units = deepcopy(self.units)
        self.assertFalse(self.ingest("synthetic-attribution", self.members))
        self.assertEqual(self.units, original_units)
        revised = archive_members("synthetic-attribution", CASES, revision=2)
        self.assertTrue(self.ingest("synthetic-attribution", revised))
        for key, unit in original_units.items():
            self.assertEqual(self.units[key]["source"], unit["source"])
            self.assertEqual(self.units[key]["evidence"], unit["evidence"])
        first = self.units[("synthetic-attribution", "quotation")]
        other = self.units[("synthetic-other", "quotation")]
        self.assertEqual(
            first["evidence"][0]["content_sha256"],
            other["evidence"][0]["content_sha256"],
        )
        self.assertNotEqual(first["source"]["id"], other["source"]["id"])
        batch = self.produce(self.context())
        self.assertEqual(len(batch["records"]), 6)
        candidates = batch["proposal"]["candidates"]
        self.assertEqual(len(candidates), 18)
        self.assertEqual(len({c["id"] for c in candidates}), len(candidates))
        self.assertFalse(any(c["output"]["title"] == "Alex" for c in candidates))
        self.assertTrue(all(len(c["sources"]) == 1 for c in candidates))


if __name__ == "__main__":
    unittest.main()
