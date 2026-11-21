"""Materialize the shipped fictional garden for the offline browser visit."""

from __future__ import annotations

import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

from ..adapters.registry_files import control_path, create_control
from ..application.pilot import private_control, private_root
from ..application.sessions import bind_session_revisions
from ..domain.contracts import canonical_json, read_object, strict_json
from ..domain.scope import local_scope
from ..domain.validation import ContractError
from ..domain.zip_package import read_zip, verify_inventory


def shipped_demo() -> dict[str, bytes]:
    """Read the same bounded, checksummed example from source, wheel or sdist."""
    roots = (
        Path(__file__).resolve().parents[3] / "examples/mock-garden",
        Path(sys.prefix) / "share/mindgarden/examples/mock-garden",
    )
    for root in roots:
        archive = root / "visit.zip"
        if archive.is_file():
            limit = 512 * 1024
            with archive.open("rb") as source:
                members = read_zip(source.read(limit + 1), captured_limit=limit, expanded_limit=2 * limit)
            inventory = verify_inventory(members)
            if (
                not {"scope.json", "garden/.garden/garden.json", "vault/vault.json"} <= inventory.keys()
                or any(
                    name != "scope.json" and not name.startswith(("garden/.garden/", "vault/"))
                    for name in inventory
                )
            ):
                raise ContractError("VISIT_DEMO_INVALID: shipped fictional fixture has unexpected members")
            return {name: members[name] for name in inventory}
    raise ContractError("VISIT_DEMO_UNAVAILABLE: install Mindgarden with its example assets")


def demo_bindings(state: Path) -> dict:
    return {
        "schema": "mindgarden.local-bindings/v1",
        "gardens": [{"id": "synthetic-garden", "root": str(state / "garden"), "scope": local_scope()}],
        "vaults": [{"id": "synthetic-vault", "root": str(state / "vault"), "adapter": "filesystem"}],
        "revoked_sessions": [],
    }


def _fixture_assistant_scope(config: Path, base: dict, citations: list[dict]) -> Path:
    """Grant the fixed booklet's normalized rows without broadening the pinned view."""
    session = bind_session_revisions(config, {
        **base,
        "projections": [*base["projections"], "source-evidence"],
        "source_grants": [citation["source"] for citation in citations],
    })
    if session["readable"] != base["readable"]:
        raise ContractError("SESSION_REVISION: start the fictional assistant in an unchanged demo workspace")
    target = config.with_name("assistant-scope.json")
    create_control(target, canonical_json(session))
    return target


def prepare_demo(workspace: Path, *, assistant: bool = False) -> tuple[Path, Path]:
    """Install once, then return only the existing owned fixture's bindings and scope."""
    workspace = workspace.expanduser().absolute()
    state = workspace / ".mindgarden-visit"
    config, scope = state / "bindings.json", state / "scope.json"
    control_path(config)
    seed = shipped_demo()
    bindings = demo_bindings(state)
    base = strict_json(seed["scope.json"])
    citations = None
    if assistant:
        from ..application.booklet import read_booklet_request

        citations = read_booklet_request()["sources"]
    if state.exists():
        private_root(workspace)
        private_root(state)
        existing = read_object(private_control(config))
        # Session revocation remains live, even for the fictional browser session.
        if (
            {**existing, "revoked_sessions": []} != bindings
            or read_object(private_control(scope)) != base
        ):
            raise ContractError("VISIT_DEMO_BINDINGS: use explicit private mode for edited demo authority")
    elif workspace.exists() and (not workspace.is_dir() or any(workspace.iterdir())):
        raise ContractError("VISIT_DEMO_WORKSPACE: choose a new or empty private directory")
    else:
        workspace.mkdir(mode=0o700, parents=True, exist_ok=True)
        private_root(workspace)
        with TemporaryDirectory(prefix=".mindgarden-visit-stage-", dir=workspace) as temporary:
            stage = Path(temporary)
            for name, content in {**seed, "bindings.json": canonical_json(bindings)}.items():
                destination = stage / name
                destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                descriptor = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                with os.fdopen(descriptor, "wb") as output:
                    output.write(content)
            try:
                stage.rename(state)
            except OSError as error:
                if state.exists():
                    raise ContractError("VISIT_DEMO_WORKSPACE: another process selected this directory") from error
                raise
    if citations is not None:
        scope = _fixture_assistant_scope(config, base, citations)
    return config, scope
