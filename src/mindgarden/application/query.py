"""Explicit local query authority shared by CLI and future interfaces."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from ..domain.contracts import ContractRegistry, canonical_json, digest_bytes, read_object
from ..domain.garden import GardenSnapshot, inspect_garden
from ..domain.scope import POLICY_REFERENCE, inherit_scope, local_scope, record_scope, validate_scope
from ..domain.validation import ContractError
from .bindings import LocalBindings
from .query_view import metadata_view
from .storage import content_resolver


def authority_bytes(path: Path) -> bytes:
    try:
        if path.is_symlink():
            raise OSError()
        return path.read_bytes()
    except OSError as error:
        raise ContractError("SESSION_UNAVAILABLE: explicit local authority is unavailable") from error


def authority_object(path: Path) -> dict:
    try:
        return read_object(path)
    except (OSError, UnicodeError) as error:
        raise ContractError("SESSION_UNAVAILABLE: explicit local authority cannot be read") from error


@dataclass
class QueryContext:
    session_path: Path
    session: dict
    bindings: LocalBindings
    clock: Callable[[], datetime]
    session_digest: str
    last_view_revisions: dict = field(default_factory=dict)
    effective_scopes: dict = field(default_factory=dict)

    @classmethod
    def load(cls, local_config: Path, session_path: Path, *,
             clock: Callable[[], datetime] | None = None) -> QueryContext:
        try:
            return cls._load(local_config, session_path, clock=clock)
        except ContractError:
            raise
        except (OSError, UnicodeError, KeyError, TypeError, ValueError) as error:
            raise ContractError("SESSION_UNAVAILABLE: explicit authorized inputs cannot be verified") from error

    @classmethod
    def _load(cls, local_config: Path, session_path: Path, *,
              clock: Callable[[], datetime] | None = None) -> QueryContext:
        if session_path.is_symlink():
            raise ContractError("SESSION_INVALID: session must be an explicit regular file")
        session = read_object(session_path)
        if ContractRegistry().errors(session, "session") or session["policy"] != POLICY_REFERENCE:
            raise ContractError("SESSION_INVALID: session or policy revision is unsupported")
        readable = {item["garden"] for item in session["readable"]}
        if len(readable) != len(session["readable"]):
            raise ContractError("SESSION_INVALID: duplicate readable garden identity")
        selected_clock = clock or (lambda: datetime.now(timezone.utc))
        if selected_clock() >= datetime.fromisoformat(session["expires_at"].replace("Z", "+00:00")):
            raise ContractError("SESSION_EXPIRED: query authority expired")
        raw_bindings = authority_object(local_config)
        if session["id"] in raw_bindings.get("revoked_sessions", []):
            raise ContractError("SESSION_REVOKED: query authority was revoked")
        selected = {item["id"] for item in raw_bindings.get("gardens", [])
                    if isinstance(item, dict) and item.get("id") in readable
                    and isinstance(item.get("scope"), dict) and item["scope"].get("visibility")
                    in session["allowed_visibilities"]}
        bindings = LocalBindings.load(local_config, garden_ids=selected, vault_ids=set())
        context = cls(session_path.absolute(), session, bindings,
                      selected_clock, digest_bytes(session_path.read_bytes()))
        context.check_live()
        return context

    def check_live(self) -> None:
        if digest_bytes(authority_bytes(self.session_path)) != self.session_digest:
            raise ContractError("SESSION_STALE: explicit query authority changed")
        if authority_object(self.session_path) != self.session:
            raise ContractError("SESSION_STALE: in-memory query authority changed")
        expiry = datetime.fromisoformat(self.session["expires_at"].replace("Z", "+00:00"))
        if self.clock() >= expiry:
            raise ContractError("SESSION_EXPIRED: query authority expired")
        current = authority_object(self.bindings.path)
        if not isinstance(current.get("revoked_sessions"), list):
            raise ContractError("SESSION_CONFIGURATION: revocation authority is unavailable")
        if self.session["id"] in current["revoked_sessions"]:
            raise ContractError("SESSION_REVOKED: query authority was revoked")
        def relevant(document):
            return {field: [item for item in document.get(field, []) if isinstance(item, dict) and item.get("id") in selected]
                    for field, selected in (("gardens", self.bindings.gardens), ("vaults", self.bindings.vaults))}

        if relevant(current) != relevant(self.bindings.document):
            raise ContractError("SESSION_CONFIGURATION: explicit local authority changed")
        if any((item["root"] / ".mindgarden-write.lock").exists() for item in self.bindings.gardens.values()):
            raise ContractError("WRITE_LOCKED: authorized input is awaiting write recovery")
        if self.last_view_revisions:
            current_views = metadata_view(self)
            if {garden: item["revision"] for garden, item in current_views.items()} != self.last_view_revisions:
                raise ContractError("SESSION_REVISION: authorized represented records changed")

    def require(self, projection: str) -> None:
        self.check_live()
        if projection not in self.session["projections"]:
            raise ContractError("PROJECTION_DENIED: this session does not permit the requested projection")

    def snapshots(self) -> dict[str, GardenSnapshot]:
        self.check_live()
        resolver = content_resolver(self.bindings)
        snapshots = {}
        revisions = {item["garden"]: item["revision"] for item in self.session["readable"]}
        views = metadata_view(self)
        self.effective_scopes = {(garden, record_id): scope for garden, view in views.items()
                                 for record_id, scope in view["scopes"].items()}
        for garden_id, binding in sorted(self.bindings.gardens.items()):
            scope = binding["scope"]
            if scope["persistence"] == "encrypted-vault":
                raise ContractError("RUNTIME_UNVERIFIED: encrypted processing assurance is unavailable")
            if self.session["execution"] != scope["execution"]:
                raise ContractError("EXECUTION_DENIED: session and garden execution boundaries differ")
            if views[garden_id]["revision"] != revisions[garden_id]:
                raise ContractError("SESSION_REVISION: authorized view revision changed; refresh the explicit session")
            def selected(record):
                return record.get("id") in views[garden_id]["records"] and record == views[garden_id]["records"][record["id"]]

            snapshots[garden_id] = inspect_garden(binding["root"], content_resolver=resolver,
                                                  allow_unavailable_references=True, record_filter=selected)
        for garden_id, binding in sorted(self.bindings.gardens.items()):
            def selected(record):
                return record.get("id") in views[garden_id]["records"] and record == views[garden_id]["records"][record["id"]]

            snapshots[garden_id] = inspect_garden(binding["root"], content_resolver=resolver,
                                                  authorized_gardens=snapshots,
                                                  allow_unavailable_references=True, record_filter=selected)
            if snapshots[garden_id].diagnostics:
                raise ContractError("QUERY_INTEGRITY: authorized content or evidence failed verification; run owner validation locally")
        self.last_view_revisions = {garden: item["revision"] for garden, item in views.items()}
        self.check_live()
        return snapshots

    def scope_for(self, garden: str, record: dict) -> dict:
        return self.effective_scopes.get((garden, record.get("id"))) or self.declared_scope_for(garden, record)

    def declared_scope_for(self, garden: str, record: dict) -> dict:
        binding_scope = self.bindings.garden(garden)["scope"]
        if binding_scope["visibility"] == "public" and record.get("visibility", "public") != "public":
            raise ContractError("SCOPE_CONFLICT: public storage cannot contain private records")
        if "visibility" not in record and record.get("schema") == "mindgarden.provenance/v1":
            return inherit_scope([binding_scope, record.get("scope", binding_scope)])
        return record_scope(record, binding_scope)

    def allows_scope(self, scope: dict) -> bool:
        return (scope["visibility"] in self.session["allowed_visibilities"]
                and scope["persistence"] != "encrypted-vault" and scope["execution"] == self.session["execution"])

    def allowed(self, garden: str, record: dict, *, review: bool = True) -> bool:
        try:
            scope = self.declared_scope_for(garden, record)
        except (ContractError, TypeError, ValueError, AttributeError):
            return False
        if not self.allows_scope(scope):
            return False
        state = record.get("review")
        return not review or isinstance(state, dict) and state.get("state") in self.session["allowed_review_states"]

    def output_scope(self, contributing: list[dict]) -> dict:
        request = self.session.get("request_scope", local_scope())
        validate_scope(request)
        authority = local_scope(request["visibility"], persistence=request["persistence"],
                                execution=self.session["execution"],
                                publication=self.session["publication_authority"])
        return inherit_scope([request, authority, *contributing])

    def scope_digest(self) -> str:
        return digest_bytes(canonical_json(self.session))
