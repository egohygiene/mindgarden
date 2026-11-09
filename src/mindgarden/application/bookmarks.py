"""Bounded offline private cleanup of captured normalized bookmark metadata."""

from html import escape
import ipaddress
import re
from urllib.parse import urlsplit, parse_qsl

from ..adapters.captured_source import CapturedSourceAdapter
from ..adapters.generated_files import apply_generated, inventory
from ..adapters.registry_files import control_path, private_parent
from ..domain.contracts import (
    ContractRegistry,
    canonical_json,
    digest_bytes,
    read_object,
    strict_json,
)
from ..domain.scope import POLICY_REFERENCE, local_scope
from ..domain.sources import normalize_source
from ..domain.validation import ContractError
from .curation import require_review_authority

SOURCE_PROFILE = "mindcap.chrome-bookmarks.normalized/v0.1"
BUNDLE_PROFILE = "mindcap.captured-source-bundle/v1"
HANDOFF = {
    "schema": "mindgarden.bookmark-handoff-status/v1",
    "state": "unavailable",
    "owner_contract": "https://github.com/egohygiene/akashic/issues/175",
    "reason": "accepted-sanitized-candidate-contract-unavailable",
    "publication": "denied",
}


def require_personal(classification):
    if classification != "personal":
        raise ContractError(
            "BOOKMARK_RUNTIME_UNAVAILABLE: explicit personal classification is required; confidential runtime is unavailable"
        )


def _bookmark_input(path, classification, input_format):
    require_personal(classification)
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise ContractError("BOOKMARK_INPUT: captured metadata must be a regular file")
    if input_format not in {"normalized-json", "captured-source-bundle"}:
        raise ContractError(
            "BOOKMARK_INCOMPATIBLE: select an explicit supported input format"
        )
    maximum = (
        100 * 1024 * 1024 if input_format == "captured-source-bundle" else 2_000_000
    )
    with path.open("rb") as stream:
        captured = stream.read(maximum + 1)
    if len(captured) > maximum:
        raise ContractError(
            "BOOKMARK_BUDGET: captured input exceeds the selected format limit"
        )
    units = None
    if input_format == "captured-source-bundle":
        bundle = normalize_source(CapturedSourceAdapter(), captured, {})
        if bundle.metadata["source_type"] != "bookmark-collection":
            raise ContractError(
                "BOOKMARK_INCOMPATIBLE: explicit bookmark-collection units required"
            )
        units = bundle.units
        if any(
            unit.media_type != "application/json"
            or not {"json:/title", "json:/url"}.issubset(unit.locators)
            for unit in units
        ):
            raise ContractError(
                "BOOKMARK_EVIDENCE: exact JSON title and URL evidence required"
            )
        source = {
            "schema": BUNDLE_PROFILE,
            "capture": bundle.metadata,
            "bookmark_records": [strict_json(unit.content) for unit in units],
        }
    else:
        source = strict_json(captured)
    expected_profile = BUNDLE_PROFILE if units is not None else SOURCE_PROFILE
    if (
        not isinstance(source, dict)
        or source.get("schema") != expected_profile
        or not isinstance(source.get("bookmark_records"), list)
    ):
        raise ContractError(
            "BOOKMARK_INCOMPATIBLE: require the selected tested bookmark metadata profile"
        )
    records = []
    seen = set()
    if len(source["bookmark_records"]) > 10000:
        raise ContractError(
            "BOOKMARK_BUDGET: metadata exceeds the bounded local profile"
        )
    for position, item in enumerate(source["bookmark_records"]):
        if (
            not isinstance(item, dict)
            or item.get("schema_version") != "mindcap.normalized-bookmark/v0.1"
            or item.get("record_type") != "bookmark"
            or item.get("source_provider") != "chrome-bookmarks"
            or not all(
                isinstance(item.get(k), str) and item[k]
                for k in ("profile_id", "title", "url")
            )
            or len(item["title"]) > 8192
            or len(item["url"]) > 8192
            or not isinstance(item.get("folder_path"), list)
            or len(item["folder_path"]) > 16
            or not all(
                isinstance(s, str) and len(s) <= 1000 for s in item["folder_path"]
            )
        ):
            raise ContractError(
                "BOOKMARK_INPUT: incompatible normalized record; originals are retained"
            )
        provider_identity = item.get("source_guid") or item.get("source_node_id")
        if not isinstance(provider_identity, str) or not provider_identity:
            raise ContractError(
                "BOOKMARK_IDENTITY: missing provider identity requires explicit capture reconciliation"
            )
        identity = (
            "bookmark-"
            + digest_bytes(
                canonical_json(
                    [item["source_provider"], item["profile_id"], provider_identity]
                )
            )[:24]
        )
        if units is not None:
            identity = (
                "bookmark-" + digest_bytes(units[position].identity.encode())[:24]
            )
        if identity in seen:
            raise ContractError(
                "BOOKMARK_IDENTITY: conflicting provider identities require review"
            )
        seen.add(identity)
        records.append(
            {
                "id": identity,
                "title": item["title"],
                "url": item["url"],
                "folders": item["folder_path"],
                "source_locator": "json:/bookmark_records/" + str(position),
            }
        )
        if units is not None:
            unit = units[position]
            records[-1].update(
                source_locator="json:/url",
                page_content="not-captured",
                evidence={
                    "source_identity": unit.identity,
                    "sha256": digest_bytes(unit.content),
                    "locators": list(unit.locators),
                    **unit.metadata,
                },
            )
    return source, records, captured


def read_metadata(path, classification, *, input_format="normalized-json"):
    source, records, _captured = _bookmark_input(path, classification, input_format)
    return source, records


def unsafe_url(value):
    try:
        parsed = urlsplit(value)
        host = parsed.hostname
        if parsed.scheme not in {"http", "https"} or not host:
            return "unsupported-url"
        if parsed.username or parsed.password:
            return "credential-url"
        if any(
            k.casefold()
            in {
                "token",
                "access_token",
                "session",
                "sessionid",
                "auth",
                "password",
                "key",
                "api_key",
                "code",
            }
            for k, _ in parse_qsl(parsed.query)
        ):
            return "session-or-credential-query"
        if re.search(
            r"(?:token|password|session|access_token)=", parsed.fragment, re.I
        ):
            return "session-or-credential-fragment"
        try:
            if not ipaddress.ip_address(host).is_global:
                return "private-url"
        except ValueError:
            if "." not in host or host.endswith((".local", ".internal", ".localhost")):
                return "private-url"
        return None
    except ValueError:
        return "invalid-url"


def bookmark_html(records):
    tree = {}
    for record in records:
        branch = tree
        for folder in record["folders"]:
            branch = branch.setdefault(folder, {})
        branch.setdefault(None, []).append(record)

    def render(branch):
        body = "<DL><p>\n"
        for folder, child in sorted(
            ((k, v) for k, v in branch.items() if k is not None), key=lambda p: p[0]
        ):
            body += "<DT><H3>" + escape(folder) + "</H3>\n" + render(child)
        for record in sorted(branch.get(None, []), key=lambda r: r["id"]):
            body += (
                '<DT><A HREF="'
                + escape(record["url"], quote=True)
                + '">'
                + escape(record["title"])
                + "</A>\n"
            )
        return body + "</DL><p>\n"

    return (
        '<!DOCTYPE NETSCAPE-Bookmark-file-1>\n<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">\n<TITLE>Reviewed private bookmarks</TITLE>\n<H1>Reviewed private bookmarks</H1>\n'
        + render(tree)
    ).encode()


def plan_bookmarks(
    source_path,
    catalog_path,
    request,
    *,
    classification="restricted",
    input_format="normalized-json",
    previous=None,
    previous_sha256=None,
):
    require_personal(classification)
    if (
        ContractRegistry().errors(request, "bookmark-review-request")
        or request["policy"] != POLICY_REFERENCE
    ):
        raise ContractError(
            "BOOKMARK_PLAN: explicit compatible local review contract is required"
        )
    source, records, captured = _bookmark_input(
        source_path, classification, input_format
    )
    catalog = read_object(catalog_path)
    if (
        catalog.get("schema") != "mindgarden.local-bookmark-catalog/v1"
        or set(catalog) != {"schema", "urls"}
        or not isinstance(catalog["urls"], list)
        or not all(isinstance(u, str) for u in catalog["urls"])
    ):
        raise ContractError(
            "BOOKMARK_CATALOG: require an explicit local exact-URL comparison selection"
        )
    inputs = {
        "source_sha256": digest_bytes(captured),
        "catalog_sha256": digest_bytes(catalog_path.read_bytes()),
        "policy": POLICY_REFERENCE,
        "source_profile": source["schema"],
    }
    if (
        request["source_sha256"] != inputs["source_sha256"]
        or request["catalog_sha256"] != inputs["catalog_sha256"]
        or request["prior_receipt_sha256"] != previous_sha256
    ):
        raise ContractError(
            "BOOKMARK_STALE: captured input, catalog or prior checkpoint changed"
        )
    offset = request["offset"]
    selected = records[offset : offset + request["limit"]]
    decisions = list(request["decisions"])
    prior = []
    if offset:
        if (
            not isinstance(previous, dict)
            or previous.get("schema") != "mindgarden.bookmark-review-receipt/v1"
            or previous.get("inputs") != inputs
            or previous.get("next_offset") != offset
        ):
            raise ContractError(
                "BOOKMARK_RESUME: prior reviewed batch does not match these exact inputs"
            )
        prior = previous["reviewed_decisions"]
        if {d["id"] for d in prior} != {r["id"] for r in records[:offset]}:
            raise ContractError(
                "BOOKMARK_RESUME: previous dispositions do not cover the exact prefix"
            )
    elif previous is not None:
        raise ContractError(
            "BOOKMARK_RESUME: initial batch must not import an unrelated checkpoint"
        )
    if not selected or {d["id"] for d in decisions} != {r["id"] for r in selected}:
        raise ContractError(
            "BOOKMARK_BATCH: supply one disposition for each item in the bounded batch"
        )
    combined = prior + decisions
    if len({d["id"] for d in combined}) != len(combined) or any(
        ContractRegistry().errors(d, "bookmark-decision") for d in combined
    ):
        raise ContractError(
            "BOOKMARK_CONFLICT: duplicate or incompatible dispositions require review"
        )
    by = {r["id"]: r for r in records}
    actions = {d["id"]: d for d in combined}
    cleaned = []
    quarantine = []
    trail = []
    for decision in combined:
        record = by[decision["id"]]
        action = decision["action"]
        reason = unsafe_url(record["url"])
        state = "retained"
        if reason is not None:
            state = "quarantine"
        elif action in {
            "quarantine",
            "defer",
            "omit",
            "observed-redirect",
            "publish-proposal",
        }:
            state = (
                "deferred"
                if action in {"defer", "observed-redirect", "publish-proposal"}
                else action
            )
            reason = {
                "observed-redirect": "accepted-observation-contract-unavailable",
                "publish-proposal": "accepted-publication-contract-unavailable",
            }.get(action, decision["rationale"])
        elif action == "merge":
            target = by.get(decision["merge_into"])
            if (
                target is None
                or target["url"] != record["url"]
                or target["id"] == record["id"]
                or actions.get(target["id"], {}).get("action")
                not in {"keep", "move", "rename", "private-route"}
            ):
                raise ContractError(
                    "BOOKMARK_MERGE: exact URL and one explicitly retained canonical target are required"
                )
            state = "merged"
            reason = "explicit-exact-url-duplicate"
        if state == "retained":
            item = dict(record)
            if action == "rename":
                if not decision["new_title"]:
                    raise ContractError(
                        "BOOKMARK_RENAME: explicit replacement title is required"
                    )
                item["title"] = decision["new_title"]
            if action == "move":
                if decision["new_folders"] is None:
                    raise ContractError(
                        "BOOKMARK_MOVE: explicit destination folders are required"
                    )
                item["folders"] = decision["new_folders"]
            item["catalog_match"] = item["url"] in catalog["urls"]
            cleaned.append(item)
        else:
            quarantine.append({"record": record, "state": state, "reason": reason})
        trail.append(
            {
                "id": record["id"],
                "action": action,
                "state": state,
                "rationale": decision["rationale"],
                "public_approval": decision["public_approval"],
                "source_locator": record["source_locator"],
            }
        )
        if "evidence" in record:
            trail[-1]["evidence"] = record["evidence"]
    if len({r["url"] for r in cleaned}) != len(cleaned):
        raise ContractError(
            "BOOKMARK_DUPLICATE: exact duplicates need an explicit merge disposition"
        )
    next_offset = (
        offset + len(selected) if offset + len(selected) < len(records) else None
    )
    receipt = {
        "schema": "mindgarden.bookmark-review-receipt/v1",
        "inputs": inputs,
        "prior_receipt_sha256": previous_sha256,
        "next_offset": next_offset,
        "reviewed_decisions": combined,
        "review": request["review"],
        "review_authority": request["review_authority"],
        "classification": "machine-local-control",
        "publication": "never-exportable",
    }
    files = {
        (
            "captured-source.zip"
            if input_format == "captured-source-bundle"
            else "captured-normalized.json"
        ): captured,
        "cleaned-bookmarks.json": canonical_json(
            {
                "schema": "mindgarden.cleaned-bookmarks/v1",
                "records": sorted(cleaned, key=lambda r: r["id"]),
                "complete_review": next_offset is None
                and source.get("capture", {}).get("status", "complete") == "complete",
            }
        ),
        "cleaned-bookmarks.html": bookmark_html(cleaned),
        "review-receipt.json": canonical_json(receipt),
        "quarantine.json": canonical_json({"items": quarantine}),
        "akashic-handoff-status.json": canonical_json(HANDOFF),
    }
    if sum(map(len, files.values())) > 16 * 1024 * 1024:
        raise ContractError(
            "BOOKMARK_BUDGET: private export exceeds the 16 MiB generated-bundle limit"
        )
    value = {
        "schema": "mindgarden.bookmark-review-plan/v1",
        "inputs": inputs,
        "request_sha256": digest_bytes(canonical_json(request)),
        "prior_receipt_sha256": previous_sha256,
        "review": request["review"],
        "scope": local_scope("personal", publication="never-exportable"),
        "decisions": trail,
        "next_offset": next_offset,
        "files": inventory(files),
        "handoff": HANDOFF,
        "capabilities": {
            "raw_capture_verification": False,
            "source_bundle": input_format == "captured-source-bundle",
            "deltas": False,
            "observations": False,
            "url_identity": "exact-string-only",
            "network": False,
            "browser_mutation": False,
            "public_packet": False,
        },
    }
    if input_format == "captured-source-bundle":
        value["capture"] = source["capture"]
        value["capabilities"].update(
            member_checksums=True, producer_authentication=False
        )
    return {**value, "plan_sha256": digest_bytes(canonical_json(value))}, files


def private_write(path, content):
    path = control_path(path)
    private_parent(path)
    if path.exists():
        if not path.is_file() or path.read_bytes() != content:
            raise ContractError(
                "BOOKMARK_OUTPUT: existing private plan differs; choose a fresh file"
            )
        return
    with path.open("xb") as output:
        import os

        os.chmod(output.name, 0o600)
        output.write(content)


def _run_bookmarks(arguments):
    require_personal(arguments.classification)
    if arguments.inspect:
        _source, records, captured = _bookmark_input(
            arguments.input, arguments.classification, arguments.input_format
        )
        document = {
            "schema": "mindgarden.bookmark-private-inventory/v1",
            "records": records,
            "source_sha256": digest_bytes(captured),
            "catalog_sha256": digest_bytes(arguments.catalog.read_bytes()),
            "publication": "never-exportable",
        }
        if arguments.input_format == "captured-source-bundle":
            document["capture"] = _source["capture"]
        private_write(arguments.plan_file, canonical_json(document))
        result = {
            "status": "private-inventory-written",
            "sha256": digest_bytes(canonical_json(document)),
        }
    else:
        if arguments.request is None:
            raise ContractError(
                "BOOKMARK_REQUEST: supply an authored private review request"
            )
        request = read_object(arguments.request)
        previous = (
            read_object(control_path(arguments.previous_receipt))
            if arguments.previous_receipt
            else None
        )
        previous_sha = (
            digest_bytes(arguments.previous_receipt.read_bytes())
            if arguments.previous_receipt
            else None
        )
        preview, files = plan_bookmarks(
            arguments.input,
            arguments.catalog,
            request,
            classification=arguments.classification,
            input_format=arguments.input_format,
            previous=previous,
            previous_sha256=previous_sha,
        )
        if arguments.apply:
            if request["review"]["state"] != "approved":
                raise ContractError(
                    "BOOKMARK_REVIEW: explicit human approval is required"
                )
            require_review_authority(request["review"], request["review_authority"])
            if arguments.output_directory is None:
                raise ContractError(
                    "BOOKMARK_OUTPUT: supply a new private output directory"
                )

            def verify():
                current = read_object(arguments.request)
                prior = (
                    read_object(control_path(arguments.previous_receipt))
                    if arguments.previous_receipt
                    else None
                )
                prior_sha = (
                    digest_bytes(arguments.previous_receipt.read_bytes())
                    if arguments.previous_receipt
                    else None
                )
                if (
                    plan_bookmarks(
                        arguments.input,
                        arguments.catalog,
                        current,
                        classification=arguments.classification,
                        input_format=arguments.input_format,
                        previous=prior,
                        previous_sha256=prior_sha,
                    )[0]
                    != preview
                ):
                    raise ContractError("BOOKMARK_STALE: reviewed inputs changed")

            changed = apply_generated(
                arguments.output_directory,
                files,
                arguments.plan_digest,
                preview["plan_sha256"],
                check_live=lambda: None,
                verify_inputs=verify,
            )
            result = {
                "status": "created" if changed else "verified-no-op",
                "plan_sha256": preview["plan_sha256"],
                "public_handoff": "unavailable",
            }
        else:
            private_write(arguments.plan_file, canonical_json(preview))
            result = {
                "status": "private-plan-written",
                "plan_sha256": preview["plan_sha256"],
                "public_handoff": "unavailable",
            }
    print(canonical_json(result).decode(), end="")
    return 0


def run_bookmarks(arguments):
    try:
        return _run_bookmarks(arguments)
    except ContractError:
        raise
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        AttributeError,
        RecursionError,
    ) as error:
        raise ContractError(
            "BOOKMARK_INVALID: explicit private inputs or output are unavailable or incompatible; no source details emitted"
        ) from error
