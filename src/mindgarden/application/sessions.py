"""Explicit local session authoring and authorized-view revision refresh."""

from argparse import Namespace
from copy import deepcopy
from datetime import datetime, timezone
import os
from pathlib import Path

from ..domain.contracts import ContractRegistry, canonical_json, read_object
from ..domain.scope import POLICY_REFERENCE, local_scope
from ..domain.registry import selected_view, verify_session_view, view_reference
from ..domain.validation import ContractError
from ..adapters.registry_files import control_path
from .bindings import LocalBindings
from .query import QueryContext, selected_garden_ids
from .query_view import metadata_view


def bind_session_revisions(local_config: Path, supplied: dict) -> dict:
    session = deepcopy(supplied)
    if ContractRegistry().errors(session, "session") or session["policy"] != POLICY_REFERENCE:
        raise ContractError("SESSION_INVALID: explicit session authoring fields are invalid")
    readable = {item["garden"] for item in session["readable"]}
    if len(readable) != len(session["readable"]):
        raise ContractError("SESSION_INVALID: duplicate readable identities")
    document = read_object(local_config)
    verify_session_view(document, session)
    selected = selected_garden_ids(document, session)
    if session["id"] in document.get("revoked_sessions", []):
        raise ContractError("SESSION_REVOKED: choose a new explicitly authorized session identity")
    bindings = LocalBindings.load(local_config, garden_ids=selected, vault_ids=set())
    for binding in bindings.gardens.values():
        if binding["scope"]["persistence"] == "encrypted-vault":
            raise ContractError("RUNTIME_UNVERIFIED: encrypted query assurance is unavailable")
        if binding["scope"]["execution"] != session["execution"]:
            raise ContractError("EXECUTION_DENIED: explicit runtime and garden policies differ")
    context = QueryContext(Path(), session, bindings, lambda: datetime.now(timezone.utc), "")
    views = metadata_view(context)
    for item in session["readable"]:
        # Denied/unavailable identities are not probed. A future grant requires
        # an explicit refresh before it can match a nonempty authorized view.
        item["revision"] = views[item["garden"]]["revision"] if item["garden"] in views else "sha256:" + "0" * 64
    return session


def run_scope(arguments: Namespace) -> int:
    session = {"schema": "mindgarden.session/v1", "id": arguments.session_id,
               "readable": [{"garden": identity, "revision": "sha256:" + "0" * 64} for identity in (arguments.readable_garden or [])],
               "writable": arguments.writable_garden, "allowed_visibilities": arguments.allowed_visibility,
               "allowed_review_states": arguments.allowed_review_state or ["approved"],
               "execution": arguments.execution, "publication_authority": arguments.publication_authority,
               "projections": arguments.projection or ["index", "search", "graph", "backlinks", "context", "llms", "evidence"],
               "budgets": {"max_results": arguments.max_results, "max_context_bytes": arguments.max_context_bytes,
                           "max_depth": arguments.max_depth, "max_candidates": arguments.max_candidates},
               "policy": dict(POLICY_REFERENCE), "expires_at": arguments.expires_at}
    if getattr(arguments,"max_output_bytes",None) is not None:
        session["budgets"]["max_output_bytes"] = arguments.max_output_bytes
    if getattr(arguments, "registry_view", None) is not None:
        view = selected_view(read_object(arguments.local_config), arguments.registry_view)
        session["readable"] = [{"garden": identity, "revision": "sha256:" + "0" * 64} for identity in view["gardens"]]
        session["registry_view"] = view_reference(view)
    session["request_scope"] = local_scope(arguments.request_visibility, execution=arguments.execution,
                                            publication=arguments.publication_authority)
    if getattr(arguments, "source_grants", None) is not None:
        document = read_object(control_path(arguments.source_grants.absolute()))
        if set(document) != {"source_grants"}:
            raise ContractError("SOURCE_GRANT: supply a private source_grants wrapper only")
        session["source_grants"] = document["source_grants"]
    session = bind_session_revisions(arguments.local_config, session)
    if datetime.fromisoformat(session["expires_at"].replace("Z", "+00:00")) <= datetime.now(timezone.utc):
        raise ContractError("SESSION_EXPIRED: supply a future expiration with an explicit offset")
    content = canonical_json(session)
    if arguments.output:
        output = arguments.output.absolute()
        if any(path.is_symlink() for path in (output, *output.parents)):
            raise ContractError("SESSION_PATH: output must not cross symlinks")
        document = read_object(arguments.local_config)
        for binding in document.get("gardens", []):
            if not isinstance(binding, dict) or not isinstance(binding.get("root"), str):
                continue
            try:
                output.relative_to(Path(binding["root"]) / ".garden")
            except ValueError:
                continue
            raise ContractError("SESSION_PATH: machine-local session authority belongs outside portable garden records")
        if output.exists() and output.read_bytes() != content:
            raise ContractError("SESSION_EXISTS: use a new explicit session file after refreshing authority")
        if not output.exists():
            descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(content)
    print(content.decode(), end="")
    return 0
