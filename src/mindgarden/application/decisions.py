"""Read-only metadata projection of an explicitly supplied public ADR read model."""

from datetime import date
import re
from urllib.parse import urlsplit

from ..domain.contracts import (
    ContractRegistry,
    canonical_json,
    digest_bytes,
    strict_json,
)
from ..domain.sources import validate_origin
from ..domain.validation import ContractError
from .ingestion import captured_bytes

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
RELATED_KINDS = {
    "repository",
    "roadmap_step",
    "issue",
    "pull_request",
    "commit",
    "check",
    "release",
    "deployment",
}
# Supported subset of Hygiene's versioned Repository Intelligence vocabulary.
RELATED_TYPES = {
    "blocks",
    "depends-on",
    "evidences",
    "implements",
    "informs",
    "tracks",
    "verifies",
}


def public_url(value):
    if not isinstance(value, str):
        return False
    try:
        validate_origin(value)
        parsed = urlsplit(value)
    except (ContractError, ValueError):
        return False
    return (
        parsed.scheme == "https"
        and bool(parsed.hostname)
        and not parsed.username
        and not parsed.password
        and not parsed.query
    )


def public_sources(graph):
    sources = {}
    for source in graph["sources"]:
        if (
            source.get("visibility") != "public"
            or source.get("freshness") not in {"current", "not_applicable"}
            or source.get("assertion") not in {"authoritative", "inferred"}
            or not public_url(source.get("url"))
        ):
            continue
        if source.get("revision") is not None and (
            not isinstance(source["revision"], str)
            or not re.fullmatch(r"[0-9a-f]{40}", source["revision"])
        ):
            continue
        path = urlsplit(source["url"]).path
        if any(part in path for part in ("/blob/", "/commit/", "/tree/")):
            pin = re.search(r"/(?:blob|commit|tree)/([0-9a-f]{40})(?:/|$)", path)
            if pin is None or pin[1] != source.get("revision"):
                continue
        if source["id"] in sources:
            raise ValueError()
        sources[source["id"]] = source
    return sources


def canonical_sources(item, sources):
    canonical = item.get("canonical_url")
    if (
        not public_url(canonical)
        or not item.get("provenance")
        or not set(item["provenance"]) <= sources.keys()
    ):
        return []
    return [
        sources[key]
        for key in item["provenance"]
        if sources[key].get("repository") == item.get("repository")
        and sources[key]["url"].split("#")[0] == canonical.split("#")[0]
    ]


def provenance_refs(sources):
    values = [
        {
            "source": source["url"],
            "revision": source.get("revision"),
            "observed_at": source["observed_at"],
            "assertion": source["assertion"],
            "freshness": source["freshness"],
        }
        for source in sources
    ]
    return sorted(
        {canonical_json(value): value for value in values}.values(), key=canonical_json
    )


def related_artifacts(graph, nodes, sources, represented_commit, selected):
    """One-hop public source metadata, never a new graph owner or access grant."""
    candidates = {}
    for item in graph["entities"]:
        if (
            item.get("kind") not in RELATED_KINDS
            or item.get("visibility") != "public"
            or item.get("freshness") not in {"current", "not_applicable"}
            or item.get("state", {}).get("assertion")
            not in {"authoritative", "inferred"}
        ):
            continue
        evidence = canonical_sources(item, sources)
        if not evidence:
            continue
        if item["id"] in candidates or item["id"] in nodes:
            raise ValueError()
        candidates[item["id"]] = {
            "id": item["id"],
            "key": item["key"],
            "kind": item["kind"],
            "title": item["title"],
            "repository": item["repository"],
            "source": item["canonical_url"],
            "state": item["state"]["value"],
            "assertion": item["state"]["assertion"],
            "visibility": "public",
            "observed_in_commit": represented_commit,
            "provenance": provenance_refs(evidence),
        }
    edges, retained = [], set()
    for item in graph["relationships"]:
        kind = item["type"].replace("_", "-")
        source, target = item["source"], item["target"]
        if (
            kind not in RELATED_TYPES
            or item.get("direction") != "directed"
            or item.get("assertion") not in {"authoritative", "inferred"}
            or item.get("freshness") != "current"
            or not item.get("provenance")
            or not set(item["provenance"]) <= sources.keys()
        ):
            continue
        if source in nodes and target in candidates:
            retained.add(target)
        elif target in nodes and source in candidates:
            retained.add(source)
        else:
            continue
        edges.append(
            {
                "source": source,
                "target": target,
                "type": kind,
                "assertion": item["assertion"],
                "provenance": provenance_refs(
                    [sources[key] for key in item["provenance"]]
                ),
            }
        )
    context = []
    for edge in sorted(
        {canonical_json(e): e for e in edges}.values(), key=canonical_json
    ):
        decision = (
            edge["source"]
            if edge["source"] in selected
            else edge["target"]
            if edge["target"] in selected
            else None
        )
        if decision is None:
            continue
        artifact = candidates[
            edge["target"] if edge["source"] == decision else edge["source"]
        ]
        context.append(
            {
                "reference": artifact["source"],
                "title": artifact["title"],
                "status": artifact["state"],
                "reason": "related-to-selected-decision",
                "untrusted": True,
                "decision": nodes[decision]["source"],
                "relationship": edge["type"],
                "assertion": edge["assertion"],
            }
        )
    return [candidates[key] for key in sorted(retained)], edges, context


def project_decisions(
    snapshot,
    *,
    represented_commit,
    include_proposed=False,
    include_related=False,
    max_bytes=65536,
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
        or snapshot.get("contract_version") not in {"1.0.0-alpha.1", "1.0.0-alpha.2"}
        or not re.fullmatch(r"[0-9a-f]{40}", represented_commit)
        or snapshot.get("represented_commit") != represented_commit
    ):
        raise ContractError(
            "DECISIONS_INPUT: require a public commit-matched owner read model"
        )
    try:
        graph = snapshot["graph"]
        if any(
            not isinstance(graph.get(key), list) or len(graph[key]) > 10000
            for key in ("sources", "entities", "relationships")
        ):
            raise ValueError()
        sources = public_sources(graph)
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
            evidence = canonical_sources(item, sources)
            revisions = {
                source.get("revision")
                for source in evidence
                if source["assertion"] == "authoritative"
                and source["freshness"] == "current"
                and isinstance(source.get("revision"), str)
                and re.fullmatch(r"[0-9a-f]{40}", source["revision"])
                and "/blob/" + source["revision"] + "/" in canonical
            }
            if len(revisions) != 1:
                continue
            revision = next(iter(revisions))
            if (
                item.get("repository") == snapshot["repository"]["repository"]
                and revision != represented_commit
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
                "represented_commit": revision,
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
            if include_related:
                nodes[identity]["repository"] = item["repository"]
                nodes[identity]["authority_scope"] = (
                    "repository-local"
                    if item["repository"] == snapshot["repository"]["repository"]
                    else "organization-scope-reference"
                    if attributes.get("decision_scope") == "organization"
                    else "cross-repository-reference"
                )
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
                        **(
                            {
                                "provenance": provenance_refs(
                                    [sources[key] for key in item["provenance"]]
                                )
                            }
                            if include_related
                            else {}
                        ),
                    }
                )
        selected = {
            identity
            for identity, node in nodes.items()
            if node["status"] == "accepted"
            or include_proposed
            and node["status"] == "proposed"
        }
        artifacts, related_context = [], []
        if include_related:
            artifacts, related_edges, related_context = related_artifacts(
                graph, nodes, sources, represented_commit, selected
            )
            edges.extend(related_edges)
        edges = sorted(
            {canonical_json(e): e for e in edges}.values(), key=canonical_json
        )
        backlinks = {
            identity: [e for e in edges if e["target"] == identity]
            for identity in sorted(
                set(nodes) | {artifact["id"] for artifact in artifacts}
            )
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
            "context": sorted(
                {
                    canonical_json(item): item for item in context + related_context
                }.values(),
                key=canonical_json,
            )
            if include_related
            else context,
        }
        if include_related:
            result["artifacts"] = artifacts
            result["coverage"] = "selected-current-public-inputs-only"
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
    content = captured_bytes(arguments.input, 2_000_000)
    if digest_bytes(content) != arguments.input_sha256:
        raise ContractError("DECISIONS_STALE: supplied read-model digest differs")
    snapshot = strict_json(content)
    result = project_decisions(
        snapshot,
        represented_commit=arguments.represented_commit,
        include_proposed=arguments.include_proposed,
        include_related=arguments.include_related,
        max_bytes=arguments.max_bytes,
    )
    print(canonical_json(result).decode(), end="")
    return 0
