"""Synthetic provider layouts and explicit per-file normalization review."""

import hashlib

from mindgarden.application.query import QueryContext
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.domain.contracts import read_object
from mindgarden.domain.scope import local_scope
from tests.consultation_fixture import FIXTURES
from tests.drive_capture_fixture import FixtureDrive, create_capture_fixture
from tests.support_v1 import write_json, write_session

MAPPINGS = FIXTURES / "mappings"


class MappedFixtureDrive(FixtureDrive):
    def __init__(self):
        super().__init__()
        for identity, name in (
            ("file-a", "layout-a.csv"),
            ("file-overlap", "layout-a-overlap.csv"),
            ("file-b", "layout-b.csv"),
        ):
            self.replace(identity, (MAPPINGS / name).read_bytes())

    def replace(self, identity, raw):
        self.data[identity] = raw
        self.items[identity].update(
            size=str(len(raw)),
            md5Checksum=hashlib.md5(raw, usedforsecurity=False).hexdigest(),
        )


def normalization():
    return read_object(MAPPINGS / "drive-normalization.json")


def create_fixture(root):
    fixture = create_capture_fixture(root)
    fixture["provider"] = MappedFixtureDrive()
    fixture["normalization_path"] = root / "reviewed-drive-normalization.json"
    write_json(fixture["normalization_path"], normalization())
    return fixture


def ingest_arguments(fixture, archive):
    root = fixture["root"]
    source = root / "captured-layouts.zip"
    scope = root / "captured-scope.json"
    source.write_bytes(archive)
    write_json(scope, fixture["binding"]["scope"])
    return [
        "ingest",
        "--repository-root",
        str(fixture["garden"]),
        "--local-config",
        str(fixture["configuration"]),
        "--vault-id",
        "synthetic-vault",
        "--input",
        str(source),
        "--source-id",
        "synthetic-mapped-drive",
        "--title",
        "Synthetic selected layouts",
        "--owner",
        "synthetic-owner",
        "--rights",
        "Wholly synthetic provider fixture.",
        "--origin",
        "urn:synthetic:mapped-drive",
        "--captured",
        fixture["binding"]["captured_at"],
        "--media-type",
        "application/vnd.mindgarden.drive-capture+zip",
        "--adapter",
        "drive-capture",
        "--manifest-version",
        "1.0.0",
        "--source-scope",
        str(scope),
        "--drive-normalization",
        str(fixture["normalization_path"]),
    ]


def packet_inputs(fixture, preview):
    request = read_object(
        FIXTURES.parent / "contracts/v1/valid/consultation-request.json"
    )
    request["sources"] = sorted(
        (unit["evidence"][0] for unit in preview["inputs"]["normalized_sources"]),
        key=lambda item: item["source"]["id"],
    )
    session_path = fixture["root"] / "session.json"
    session = write_session(session_path, fixture["configuration"])
    session.update(
        request_scope=local_scope(publication="never-exportable"),
        source_grants=[item["source"] for item in request["sources"]],
    )
    session["projections"].append("source-evidence")
    session["budgets"]["max_context_bytes"] = 262144
    write_json(session_path, bind_session_revisions(fixture["configuration"], session))
    return QueryContext.load(fixture["configuration"], session_path), request
