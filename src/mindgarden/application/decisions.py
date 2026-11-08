"""Read-only metadata projection of an explicitly supplied public ADR read model."""

from datetime import date
import re
from urllib.parse import urlsplit

from ..domain.contracts import (
    ContractRegistry,
    canonical_json,
    digest_bytes,
    read_object,
)
from ..domain.validation import ContractError

READ_MODEL = "egohygiene.observatory.repository-intelligence-read-model/v1"
RELATIONSHIPS = {
    "supersedes",
    "superseded-by",
    "amends",
    "depends-on",
    "conflicts-with",
    "related-to",
}
STATUSES = {"proposed", "accepted", "rejected", "deprecated", "superseded"}


def public_url(value):
    if not isinstance(value, str):
        return False
    parsed = urlsplit(value)
    return (
        parsed.scheme == "https"
        and bool(parsed.hostname)
        and not parsed.username
        and not parsed.password
    )


def project_decisions(
    snapshot, *, represented_commit, include_proposed=False, max_bytes=65536
):
    """Consume the owner read model, never a raw private ADR corpus or rendered HTML.

    This adapter preserves upstream assertions; it cannot establish approval or
    whole-repository conformance. Unknown/private evidence is withheld before
    titles, edges, backlinks, selection, counts or snippets are generated.
    """
    if (
        not isinstance(snapshot, dict)
        or snapshot.get("schema") != READ_MODEL
        or snapshot.get("visibility") != "public"
        or not re.fullmatch(r"[0-9a-f]{40}", represented_commit)
        or snapshot.get("represented_commit") != represented_commit
    ):
        raise ContractError(
            "DECISIONS_INPUT: require a public commit-matched owner read model"
        )
    try:
        graph = snapshot["graph"]
        sources = {
            s["id"]: s
            for s in graph["sources"]
            if s.get("visibility") == "public"
            and s.get("revision") == represented_commit
            and public_url(s.get("url"))
        }
        nodes = {}
        for item in graph["entities"]:
            if (
                item.get("kind") != "architecture_decision"
                or item.get("visibility") != "public"
                or item.get("freshness") != "current"
                or not item.get("provenance")
                or not set(item["provenance"]) <= sources.keys()
            ):
                continue
            state, attributes = item["state"], item["attributes"]
            status = state["value"]
            if status not in STATUSES or state.get("assertion") != "authoritative":
                continue
            approval = attributes.get("approval")
            if status != "proposed":
                if not isinstance(approval, dict) or set(approval) != {
                    "by",
                    "date",
                    "evidence",
                }:
                    continue
                if not approval["by"] or not public_url(approval["evidence"]):
                    continue
                date.fromisoformat(approval["date"])
            elif approval is not None:
                continue
            canonical = item["canonical_url"]
            if (
                not public_url(canonical)
                or "/blob/" + represented_commit + "/" not in canonical
            ):
                continue
            identity = item["id"]
            if identity in nodes:
                raise ValueError()
            nodes[identity] = {
                "id": identity,
                "key": item["key"],
                "title": item["title"],
                "source": canonical,
                "represented_commit": represented_commit,
                "status": status,
                "decision_scope": attributes.get("decision_scope", "unknown"),
                "implementation_status": attributes.get(
                    "implementation_status", "unknown"
                ),
                "owners": attributes.get("owners", []),
                "date": attributes.get("date"),
                "approval": approval,
                "assertion": state["assertion"],
                "visibility": "public",
                "review": "proposal-only"
                if status == "proposed"
                else "upstream-human-disposition",
                "narrative": "canonical-source-required",
            }
        edges = []
        for item in graph["relationships"]:
            relationship = item["type"].replace("_", "-")
            if (
                relationship in RELATIONSHIPS
                and item["source"] in nodes
                and item["target"] in nodes
                and item.get("assertion") in {"authoritative", "inferred"}
                and item.get("freshness") == "current"
                and item.get("provenance")
                and set(item["provenance"]) <= sources.keys()
            ):
                edges.append(
                    {
                        "source": item["source"],
                        "target": item["target"],
                        "type": relationship,
                        "assertion": item["assertion"],
                    }
                )
        edges = sorted(
            {canonical_json(e): e for e in edges}.values(), key=canonical_json
        )
        backlinks = {
            identity: [e for e in edges if e["target"] == identity]
            for identity in sorted(nodes)
        }
        context = [
            {
                "reference": n["source"],
                "title": n["title"],
                "status": n["status"],
                "reason": "explicit-proposal-selection"
                if n["status"] == "proposed"
                else "human-disposition",
                "untrusted": True,
            }
            for _, n in sorted(nodes.items())
            if n["status"] == "accepted"
            or include_proposed
            and n["status"] == "proposed"
        ]
        result = {
            "schema": "mindgarden.adr-projection/v1",
            "visibility": "public",
            "represented_commit": represented_commit,
            "source_contract": READ_MODEL,
            "authority": "upstream-assertions-only",
            "nodes": [nodes[k] for k in sorted(nodes)],
            "edges": edges,
            "backlinks": backlinks,
            "context": context,
        }
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        raise ContractError(
            "DECISIONS_INPUT: incompatible owner metadata; no partial projection emitted"
        ) from error
    if ContractRegistry().errors(result, "adr-projection"):
        raise ContractError(
            "DECISIONS_INPUT: projected metadata violates the supported adapter contract"
        )
    if (
        isinstance(max_bytes, bool)
        or not isinstance(max_bytes, int)
        or max_bytes < 1
        or len(canonical_json(result)) > max_bytes
    ):
        raise ContractError(
            "DECISIONS_BUDGET: reviewed output exceeds its explicit byte ceiling"
        )
    return result


def run_decisions(arguments):
    if (
        arguments.input.is_symlink()
        or digest_bytes(arguments.input.read_bytes()) != arguments.input_sha256
    ):
        raise ContractError("DECISIONS_STALE: supplied read-model digest differs")
    snapshot = read_object(arguments.input)
    result = project_decisions(
        snapshot,
        represented_commit=arguments.represented_commit,
        include_proposed=arguments.include_proposed,
        max_bytes=arguments.max_bytes,
    )
    print(canonical_json(result).decode(), end="")
    return 0
