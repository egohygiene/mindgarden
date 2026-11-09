"""Exact private source grants extend sessions without promoting knowledge review."""

from .scope import local_scope
from .validation import ContractError


def source_grants(session):
    grants = session.get("source_grants", [])
    enabled = "source-evidence" in session["projections"]
    if not grants and not enabled:
        return {}
    readable = {item["garden"] for item in session["readable"]}
    if (
        not enabled
        or not grants
        or session.get("request_scope") != local_scope(publication="never-exportable")
        or session["execution"] != "offline"
        or session["publication_authority"] != "never-exportable"
        or any(
            item["garden"] not in readable or item["revision"] is None
            for item in grants
        )
    ):
        raise ContractError(
            "SOURCE_GRANT: exact source grants require an explicit personal, machine-local, offline, never-exportable session"
        )
    result = {(item["garden"], item["id"]): item["revision"] for item in grants}
    if len(result) != len(grants):
        raise ContractError("SOURCE_GRANT: grant each source identity once")
    return result
