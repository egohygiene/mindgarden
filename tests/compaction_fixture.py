"""Synthetic archive, reviewed evidence anchors and authored compaction fixtures."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path

from mindgarden.application.query import QueryContext
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.domain.scope import local_scope
from mindgarden.interfaces.cli import main
from tests.archive_fixture import package_bytes, package_members
from tests.support_v1 import TIME, create_garden, write_json, write_session

FIXTURES = Path(__file__).parent / "fixtures/compaction"


def cli(arguments):
    with redirect_stdout(io.StringIO()) as output:
        status = main(arguments)
    if status:
        raise AssertionError("Synthetic compaction command failed")
    return json.loads(output.getvalue())


def capture_fixture(root):
    root.mkdir(parents=True, exist_ok=True)
    garden = root / "garden"; create_garden(garden)
    configuration = root / "bindings.json"
    write_json(configuration, {"schema": "mindgarden.local-bindings/v1", "gardens": [
        {"id": "synthetic-garden", "root": str(garden), "scope": local_scope()}],
        "vaults": [{"id": "synthetic-vault", "root": str(root / "vault"), "adapter": "filesystem"}], "revoked_sessions": []})
    initialize = ["vault", "init", "--local-config", str(configuration), "--vault-id", "synthetic-vault"]
    plan = cli(initialize); cli([*initialize, "--apply", "--plan-digest", plan["plan_sha256"]])
    archive = root / "synthetic-archive.zip"; archive.write_bytes(package_bytes(package_members()))
    arguments = ["ingest", "--repository-root", str(garden), "--local-config", str(configuration), "--vault-id", "synthetic-vault",
                 "--input", str(archive), "--source-id", "synthetic-archive", "--title", "Synthetic conversation archive",
                 "--origin", "urn:synthetic:conversation", "--captured", TIME, "--owner", "synthetic-owner",
                 "--rights", "Authored synthetic fixtures only.", "--media-type", "application/zip", "--adapter", "conversation-archive", "--manifest-version", "3.2.3"]
    imported = cli(arguments); cli([*arguments, "--apply", "--plan-digest", imported["plan_sha256"]])
    return {"root": root, "garden": garden, "configuration": configuration, "archive": archive, "imported": imported}


def create_fixture(root):
    fixture = capture_fixture(root)
    configuration = fixture["configuration"]
    seed = FIXTURES / "seed-curation.json"
    plan = cli(["gardenize", "--local-config", str(configuration), "--plan", str(seed)])
    cli(["gardenize", "--local-config", str(configuration), "--apply", str(seed), "--plan-digest", plan["plan_sha256"]])
    session_path = root / "session.json"; session = write_session(session_path, configuration)
    session["budgets"]["max_context_bytes"] = 32768
    write_json(session_path, bind_session_revisions(configuration, session))
    fixture.update(session_path=session_path, context=QueryContext.load(configuration, session_path),
                   plan=json.loads((FIXTURES / "authored-plan.json").read_text()),
                   curation=json.loads((FIXTURES / "curation.json").read_text()))
    return fixture
