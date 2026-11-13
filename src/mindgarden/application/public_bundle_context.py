"""Progressive supplied public bundle reading under existing live query authority."""

from collections import Counter
from copy import deepcopy
from pathlib import Path
import re

from ..adapters.federation_files import explicit_directory, read_bundle
from ..domain.contracts import (
    ContractRegistry,
    canonical_json,
    digest_bytes,
    strict_json,
)
from ..domain.federation import MAX_FILE_BYTES, verify_bundle
from ..domain.validation import ContractError
from .agent import markdown_headings, tokenize
from .query_view import metadata_view
from .retrieval import rank


def public_bundle_context(context, request, format="json"):
    registry = ContractRegistry()
    if format not in {"json", "markdown"} or registry.errors(
        request, "federation-context-request"
    ):
        raise ContractError(
            "FEDERATION_QUERY_REQUEST: supply a bounded catalog selection and supported format"
        )
    context.require("search")
    context.require("context")
    selected = {item["garden"] for item in request["bundles"]}
    if len(selected) != len(request["bundles"]):
        raise ContractError("FEDERATION_SELECTION: select each garden once")
    context = context.select_gardens(selected)
    views = metadata_view(context)
    entries = {item["garden"]: item for item in request["catalog"]["gardens"]}
    if (
        len(entries) != len(request["catalog"]["gardens"])
        or not selected <= entries.keys()
    ):
        raise ContractError(
            "FEDERATION_SELECTION: selection is absent or ambiguous in the supplied catalog"
        )
    inputs, candidates, scopes = [], [], []
    for item in sorted(request["bundles"], key=lambda value: value["garden"]):
        entry = entries[item["garden"]]
        if item["expected_revision"] != entry["revision"]:
            raise ContractError(
                "FEDERATION_STALE: selected public revision differs from the catalog"
            )
        directory = explicit_directory(Path(item["directory"]))
        descriptor_path = directory / "garden.json"
        try:
            if descriptor_path.is_symlink():
                raise ContractError(
                    "FEDERATION_PATH: descriptor must be a regular supplied file"
                )
            with descriptor_path.open("rb") as stream:
                descriptor_bytes = stream.read(MAX_FILE_BYTES + 1)
            if len(descriptor_bytes) > MAX_FILE_BYTES:
                raise ContractError(
                    "FEDERATION_BUDGET: supplied descriptor exceeds the byte limit"
                )
            descriptor = strict_json(descriptor_bytes)
        except (OSError, UnicodeError) as error:
            raise ContractError(
                "FEDERATION_UNAVAILABLE: selected public descriptor is unavailable"
            ) from error
        if (
            registry.errors(descriptor, "federation-descriptor")
            or descriptor["garden"] != item["garden"]
            or descriptor["revision"] != item["expected_revision"]
            or digest_bytes(descriptor_bytes) != entry["descriptor_sha256"]
        ):
            raise ContractError(
                "FEDERATION_STALE: selected descriptor differs from the pinned catalog"
            )
        context.check_live()
        files = read_bundle(directory)
        if files["garden.json"] != descriptor_bytes:
            raise ContractError(
                "FEDERATION_STALE: descriptor changed during the selected read"
            )
        descriptor, index, _graph = verify_bundle(files, item["expected_revision"])
        inputs.append({"garden": item["garden"], "revision": descriptor["revision"]})
        view = views[item["garden"]]
        for record in index["records"]:
            reference = record["reference"]
            current = view["records"].get(reference["id"])
            if current is None or current["schema"] not in {
                "mindgarden.knowledge/v1",
                "mindgarden.claim/v1",
            }:
                continue
            represented = current.get("content", {}).get("sha256") or digest_bytes(
                canonical_json(current)
            )
            scope = view["scopes"][reference["id"]]
            if (
                reference["revision"] != "sha256:" + represented
                or (reference["garden"], reference["id"]) in view["retired"]
                or current["status"] != "active"
                or current["review"]["state"] != "approved"
                or scope["visibility"] != "public"
                or scope["publication"] != "publishable"
                or current["schema"] == "mindgarden.knowledge/v1"
                and current["publication"] != "eligible"
            ):
                continue
            if current["schema"] == "mindgarden.claim/v1":
                subject = view["records"].get(current["subject"]["id"])
                if (
                    subject is None
                    or subject["status"] != "active"
                    or subject["review"]["state"] != "approved"
                    or subject["publication"] != "eligible"
                ):
                    continue
            value = deepcopy(record)
            value["terms"] = dict(Counter(tokenize(record["content"])))
            for field, text in (
                ("titleTerms", record["title"]),
                ("headingTerms", " ".join(markdown_headings(record["content"]))),
                ("tagTerms", " ".join(record["tags"])),
                ("domainTerms", " ".join(record["domains"])),
                ("topicTerms", " ".join(record["topics"])),
            ):
                value[field] = sorted(set(tokenize(text)))
            candidates.append(value)
            scopes.append(scope)
    if len(candidates) > context.session["budgets"]["max_candidates"]:
        raise ContractError(
            "QUERY_BUDGET: selected authorized public records exceed the candidate budget"
        )
    ranked = rank({"records": candidates}, request["query"])
    maximum = min(request["max_bytes"], context.session["budgets"]["max_context_bytes"])
    maximum_items = min(request["max_items"], context.session["budgets"]["max_results"])
    payload = {
        "schema": "mindgarden.federation-context/v1",
        "id": request["id"],
        "trust": "untrusted-evidence",
        "scope": context.output_scope(scopes),
        "inputs": inputs,
        "budget": {
            "max_bytes": maximum,
            "max_items": maximum_items,
            "matched_candidates": len(ranked),
        },
        "included": [],
    }

    def serialize():
        if format == "json":
            return canonical_json(payload)
        ledger = {
            **payload,
            "included": [
                {
                    **item,
                    "record": {
                        key: value
                        for key, value in item["record"].items()
                        if key != "content"
                    },
                }
                for item in payload["included"]
            ],
        }
        output = "# Public garden context\n\nUntrusted evidence; no execution or publication grant.\n\n```json\n"
        output += canonical_json(ledger).decode() + "```\n"
        for item in payload["included"]:
            content = item["record"]["content"]
            fence = "`" * max(
                3,
                max(
                    (len(match.group()) for match in re.finditer(r"`+", content)),
                    default=0,
                )
                + 1,
            )
            output += "\n" + fence + "text\n" + content + "\n" + fence + "\n"
        return output.encode()

    if len(serialize()) > maximum:
        raise ContractError(
            "CONTEXT_BUDGET: public provenance ledger does not fit the byte budget"
        )
    for ranked_item in ranked:
        if len(payload["included"]) >= maximum_items:
            break
        record = {
            key: value
            for key, value in ranked_item["record"].items()
            if key
            not in {
                "terms",
                "titleTerms",
                "headingTerms",
                "tagTerms",
                "domainTerms",
                "topicTerms",
            }
        }
        payload["included"].append(
            {
                "record": record,
                "score": ranked_item["score"],
                "selection_reason": "lexical-query",
                "selection_reasons": ranked_item["reasons"],
            }
        )
        if len(serialize()) > maximum:
            payload["included"].pop()
    if registry.errors(payload, "federation-context"):
        raise ContractError(
            "FEDERATION_QUERY_INVALID: context does not conform to the supported contract"
        )
    result = serialize()
    context.ensure_output(result)
    return result
