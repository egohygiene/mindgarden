"""Explicit local query authority shared by CLI and future interfaces."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from ..domain.contracts import ContractRegistry, canonical_json, digest_bytes, read_object
from ..domain.garden import GardenSnapshot, inspect_garden
from ..domain.scope import POLICY_REFERENCE, inherit_scope, local_scope, record_scope, validate_scope
from ..domain.validation import ContractError
from .bindings import LocalBindings, garden_fingerprint
from .storage import content_resolver


@dataclass
class QueryContext:
    session_path: Path
    session: dict
    bindings: LocalBindings
    clock: Callable[[], datetime]
    session_digest: str

    @classmethod
    def load(cls, local_config: Path, session_path: Path, *,
             clock: Callable[[], datetime] | None = None) -> QueryContext:
        if session_path.is_symlink():
            raise ContractError("SESSION_INVALID: session must be an explicit regular file")
        session = read_object(session_path)
        if ContractRegistry().errors(session, "session") or session["policy"] != POLICY_REFERENCE:
            raise ContractError("SESSION_INVALID: session or policy revision is unsupported")
        readable = {item["garden"] for item in session["readable"]}
        if len(readable) != len(session["readable"]):
            raise ContractError("SESSION_INVALID: duplicate readable garden identity")
        raw_bindings = read_object(local_config)
        selected = {item["id"] for item in raw_bindings.get("gardens", [])
                    if item["id"] in readable and item.get("scope", {}).get("visibility")
                    in session["allowed_visibilities"]}
        bindings = LocalBindings.load(local_config, garden_ids=selected, vault_ids=set())
        context = cls(session_path.absolute(), session, bindings,
                      clock or (lambda: datetime.now(timezone.utc)), digest_bytes(session_path.read_bytes()))
        context.check_live()
        return context

    def check_live(self) -> None:
        if digest_bytes(self.session_path.read_bytes()) != self.session_digest:
            raise ContractError("SESSION_STALE: explicit query authority changed")
        if read_object(self.session_path) != self.session:
            raise ContractError("SESSION_STALE: in-memory query authority changed")
        expiry = datetime.fromisoformat(self.session["expires_at"].replace("Z", "+00:00"))
        if self.clock() >= expiry:
            raise ContractError("SESSION_EXPIRED: query authority expired")
        current = read_object(self.bindings.path)
        if self.session["id"] in current["revoked_sessions"]:
            raise ContractError("SESSION_REVOKED: query authority was revoked")
        if current != self.bindings.document:
            raise ContractError("SESSION_CONFIGURATION: explicit local authority changed")

    def require(self, projection: str) -> None:
        self.check_live()
        if projection not in self.session["projections"]:
            raise ContractError("PROJECTION_DENIED: this session does not permit the requested projection")

    def snapshots(self) -> dict[str, GardenSnapshot]:
        self.check_live()
        resolver = content_resolver(self.bindings)
        snapshots = {}
        revisions = {item["garden"]: item["revision"] for item in self.session["readable"]}
        for garden_id, binding in sorted(self.bindings.gardens.items()):
            scope = binding["scope"]
            if scope["persistence"] == "encrypted-vault":
                raise ContractError("RUNTIME_UNVERIFIED: encrypted processing assurance is unavailable")
            if self.session["execution"] != scope["execution"]:
                raise ContractError("EXECUTION_DENIED: session and garden execution boundaries differ")
            if garden_fingerprint(binding["root"]) != revisions[garden_id]:
                raise ContractError("SESSION_REVISION: authorized garden revision changed")
            snapshots[garden_id] = inspect_garden(binding["root"], content_resolver=resolver,
                                                  allow_unavailable_references=True)
        for garden_id, binding in sorted(self.bindings.gardens.items()):
            snapshots[garden_id] = inspect_garden(binding["root"], content_resolver=resolver,
                                                  authorized_gardens=snapshots,
                                                  allow_unavailable_references=True).require_valid()
        self.check_live()
        return snapshots

    def scope_for(self, garden: str, record: dict) -> dict:
        return record_scope(record, self.bindings.garden(garden)["scope"])

    def allowed(self, garden: str, record: dict, *, review: bool = True) -> bool:
        try:
            scope = self.scope_for(garden, record)
        except ContractError:
            return False
        if scope["visibility"] not in self.session["allowed_visibilities"]:
            return False
        return not review or record.get("review", {}).get("state") in self.session["allowed_review_states"]

    def output_scope(self, contributing: list[dict]) -> dict:
        request = self.session.get("request_scope", local_scope())
        validate_scope(request)
        authority = local_scope(request["visibility"], persistence=request["persistence"],
                                execution=self.session["execution"],
                                publication=self.session["publication_authority"])
        return inherit_scope([request, authority, *contributing])

    def scope_digest(self) -> str:
        return digest_bytes(canonical_json(self.session))
