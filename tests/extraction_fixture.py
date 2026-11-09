"""Synthetic archive/bookmarks/page extraction inputs using the real ingestion path."""

from copy import deepcopy
import json
from pathlib import Path

from mindgarden.application.ingestion import apply_ingestion, build_ingestion_plan
from mindgarden.application.query import QueryContext
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.domain.contracts import canonical_json, digest_bytes
from mindgarden.domain.scope import local_scope
from tests.archive_fixture import package_bytes
from tests.support_v1 import TIME, write_json, write_session
from tests.test_archive_v2 import v2_members

FIXTURES = Path(__file__).parent / "fixtures/extraction"


def initialize(test):
    inputs = []
    for name, captured, media, adapter, version in (
        (
            "archive",
            package_bytes(v2_members()),
            "application/zip",
            "conversation-archive",
            "2.0.2",
        ),
        (
            "bookmarks",
            (FIXTURES.parent / "captured-source/synthetic-source.zip").read_bytes(),
            "application/vnd.mindcap.captured-source+zip",
            "captured-source-bundle",
            "1",
        ),
        (
            "page",
            (FIXTURES / "page.txt").read_bytes(),
            "text/plain",
            "plain-text",
            None,
        ),
    ):
        path = test.root / (name + ".capture")
        path.write_bytes(captured)
        metadata = {
            **test.metadata,
            "source_id": "synthetic-" + name,
            "media_type": media,
        }
        plan = build_ingestion_plan(
            test.bindings,
            "synthetic-garden",
            "synthetic-vault",
            path,
            metadata,
            adapter_id=adapter,
            manifest_version=version,
        )
        apply_ingestion(plan, plan.digest, test.bindings, "synthetic-vault")
        for source in plan.inputs["normalized_sources"]:
            label = None
            if (
                name == "archive"
                and source["metadata"].get("message_id") == "message-prompt"
            ):
                label = "assistant"
            if name == "bookmarks":
                label = (
                    "inert"
                    if b"inert-bookmarklet"
                    in test.vault.get(source["source"]["revision"])
                    else "bookmark"
                )
            if name == "page":
                label = "page"
            if label:
                evidence = source["evidence"][0]
                if name == "bookmarks":
                    evidence = {
                        "source": source["source"],
                        "locator": "artifact",
                        "content_sha256": source["source"]["revision"][7:],
                    }
                inputs.append((label, evidence))
    session_path = test.root / "extraction-session.json"
    session = write_session(session_path, test.configuration)
    session.update(
        request_scope=local_scope(publication="never-exportable"),
        source_grants=[e["source"] for _, e in inputs],
    )
    session["projections"].append("source-evidence")
    session["budgets"].update(
        max_context_bytes=65536, max_candidates=1000, max_results=1000
    )
    write_json(session_path, bind_session_revisions(test.configuration, session))
    context = QueryContext.load(test.configuration, session_path)
    descriptor = {
        "id": "authored-extraction",
        "version": "1.0.0",
        "model": "authored-fixture-no-model",
        "prompt_revision": digest_bytes(b"synthetic-extraction-prompt/v1"),
        "schema_revision": "mindgarden.extraction-output/v1",
    }
    request = {
        "schema": "mindgarden.extraction-request/v1",
        "id": "synthetic-extraction",
        "garden": "synthetic-garden",
        "created_at": TIME,
        "domains": ["knowledge-systems"],
        "topics": ["prompt-bank"],
        "producer": descriptor,
        "sources": [e for _, e in inputs],
        "limits": {"max_input_bytes": 65536, "max_output_bytes": 32768},
    }
    responses = json.loads((FIXTURES / "responses.json").read_text())
    labels = {canonical_json(e): label for label, e in inputs}

    class Producer:
        execution = "offline"

        def __init__(self):
            self.descriptor = deepcopy(descriptor)
            self.calls = []

        def extract(self, item):
            self.calls.append(deepcopy(item))
            return deepcopy(responses[labels[canonical_json(item["evidence"])]])

    return context, request, Producer(), responses
