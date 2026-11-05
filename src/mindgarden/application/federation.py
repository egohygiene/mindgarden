"""Reviewed public projections and catalogs over explicit, offline inputs."""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from ..adapters.federation_files import explicit_directory, read_bundle, write_bundle
from ..domain.contracts import ContractRegistry, canonical_json, digest_bytes, read_object, safe_path, strict_json
from ..domain.federation import (
    ARTIFACT_NAMES, CAPABILITIES, MAX_BUNDLE_BYTES, MAX_FILE_BYTES, OWNER_NAME, SUPPORTED_CONTRACTS,
    agent_entrypoint, canonical_uri, file_entry, note_url, owner_marker, public_url,
    represented_revision, verify_bundle,
)
from ..domain.publication import permits_publication
from ..domain.scope import inherit_scope, local_scope, validate_scope
from ..domain.validation import ContractError
from .query import QueryContext, authority_bytes
from .retrieval import build_index, record_key


def require_public_scope(scope: dict) -> None:
    validate_scope(scope)
    if scope["visibility"] != "public" or scope["publication"] != "publishable":
        raise ContractError("FEDERATION_SCOPE: public discovery requires publishable public inputs")


def export_destination(context: QueryContext, output_directory: Path, relative: str) -> Path:
    target = safe_path(explicit_directory(output_directory), relative)
    target = explicit_directory(target)
    # Compare declared paths without probing denied roots. Canonical records,
    # private vaults and ancestors of registered roots are never export targets.
    for field in ("gardens", "vaults"):
        for item in context.bindings.document.get(field, []):
            if not isinstance(item, dict) or not isinstance(item.get("root"), str):
                continue
            root = Path(item["root"]).absolute()
            protected = root / ".garden" if field == "gardens" else root
            if target == root or target in root.parents or target == protected or protected in target.parents:
                raise ContractError("FEDERATION_OUTPUT: select an export outside canonical records and private vaults")
    return target


@dataclass
class FederationBundle:
    garden: str
    descriptor: dict
    files: dict[str, bytes]
    reviewed_profile_sha256: str
    output_root: str
    source_checks: tuple[tuple[Path, str], ...] = ()

    def check_live(self, context: QueryContext) -> None:
        context.check_live()
        for path, expected in self.source_checks:
            if digest_bytes(authority_bytes(path)) != expected:
                raise ContractError("PLAN_STALE: reviewed federation profile changed")

    def plan(self, context: QueryContext, output_directory: Path) -> dict:
        self.check_live(context)
        destination = export_destination(context, output_directory, self.output_root)
        payload = {"schema": "mindgarden.federation-plan/v1",
                   "reviewed_profile_sha256": self.reviewed_profile_sha256,
                   "authority_sha256": context.scope_digest(),
                   "destination_sha256": digest_bytes(str(destination).encode("utf8")),
                   "descriptor_revision": self.descriptor["revision"],
                   "files": [file_entry(name, content) for name, content in sorted(self.files.items())]}
        return {**payload, "plan_sha256": digest_bytes(canonical_json(payload))}

    def apply(self, context: QueryContext, output_directory: Path, reviewed_digest: str) -> bool:
        plan = self.plan(context, output_directory)
        if reviewed_digest != plan["plan_sha256"]:
            raise ContractError("PLAN_STALE: federation inputs, authority, destination or outputs changed")
        if context.session["writable"] != self.garden:
            raise ContractError("WRITE_DENIED: the public projection needs an explicitly writable garden")
        return write_bundle(export_destination(context, output_directory, self.output_root), self.files,
                            check_live=lambda: self.check_live(context), verify_inputs=context.snapshots)


def build_federation(context: QueryContext, profile: dict, *, profile_sha256: str | None = None,
                     profile_path: Path | None = None) -> FederationBundle:
    try:
        if profile_path is not None:
            raw = authority_bytes(profile_path)
            actual = digest_bytes(raw)
            if (len(raw) > MAX_FILE_BYTES or strict_json(raw) != profile
                    or profile_sha256 not in {None, actual}):
                raise ContractError("FEDERATION_PROFILE: supplied profile bytes differ from the reviewed control input")
            profile_sha256 = actual
        return _build_federation(context, profile, profile_sha256=profile_sha256, profile_path=profile_path)
    except (OSError, UnicodeError) as error:
        raise ContractError("FEDERATION_UNAVAILABLE: authorized public inputs cannot be verified") from error


def _build_federation(context: QueryContext, profile: dict, *, profile_sha256: str | None = None,
                      profile_path: Path | None = None) -> FederationBundle:
    """Reuse the existing reviewed projection profile and authorized index."""
    registry = ContractRegistry()
    if (registry.errors(profile, "projection") or profile.get("kind") != "federation"
            or profile.get("status") != "planned" or profile.get("visibility") != "public"
            or profile.get("review", {}).get("state") != "approved"):
        raise ContractError("FEDERATION_PROFILE: supply an approved, planned public federation projection")
    if (context.session["allowed_visibilities"] != ["public"]
            or context.session["allowed_review_states"] != ["approved"]
            or context.session.get("request_scope", {}).get("visibility") != "public"
            or context.session["publication_authority"] != "publishable"):
        raise ContractError("FEDERATION_SCOPE: use an explicit public-only reviewed publication session")
    for capability in ("index", "graph", "llms"):
        context.require(capability)
    if "scope" in profile:
        require_public_scope(profile["scope"])
    binding = context.bindings.garden(profile["garden"])
    require_public_scope(binding["scope"])
    base = public_url(profile["base_uri"], base=True)
    index = build_index(context)
    require_public_scope(index["scope"])
    revision = next((item["revision"] for item in index["inputs"] if item["garden"] == profile["garden"]), None)
    if profile["source_revision"] != revision:
        raise ContractError("FEDERATION_REVISION: projection must pin the current authorized public view revision")
    by_key = {record_key(record["reference"]): record for record in index["records"]}
    selected = {}
    policy = {**profile["policy"], "raw_sources": "exclude"}
    for reference in profile["inputs"]:
        key = record_key(reference)
        record = by_key.get(key)
        if (reference["garden"] != profile["garden"] or key in selected or record is None
                or reference != record["reference"] or reference["revision"] is None):
            raise ContractError("FEDERATION_SELECTION: selected reviewed inputs are unavailable, stale or ambiguous")
        if not permits_publication(policy, kind=record["kind"], domains=record["domains"], topics=record["topics"]):
            raise ContractError("FEDERATION_POLICY: selected record is outside the reviewed projection allowlist")
        require_public_scope(record["scope"])
        selected[key] = record
    # Claims may not escape selection of their reviewed subject. Public graph
    # edges are induced only over the explicit selected records.
    snapshots = context.snapshots()
    for record in selected.values():
        if record["record_type"] == "claim":
            original = snapshots[record["garden"]].records[record["id"]]
            if record_key(original["subject"]) not in selected:
                raise ContractError("FEDERATION_SELECTION: selected claim requires its reviewed subject")
    scope = context.output_scope([record["scope"] for record in selected.values()])
    require_public_scope(scope)
    public_records = []
    for key, record in sorted(selected.items()):
        original = snapshots[record["garden"]].records[record["id"]]
        subject = (selected[record_key(original["subject"])]["reference"]
                   if record["record_type"] == "claim" else None)
        qualifications = deepcopy(record["qualifications"])
        qualifications["contradictions"] = [selected[record_key(ref)]["reference"]
                                             for ref in qualifications["contradictions"] if record_key(ref) in selected]
        public_records.append({"reference": record["reference"], "canonical_url": note_url(base, record["id"]),
                               "title": record["title"], "record_type": record["record_type"], "kind": record["kind"],
                               "subject": subject,
                               "review_state": "approved", "scope": record["scope"], "confidence": record["confidence"],
                               "content": record["content"], "sources": record["sources"], "qualifications": qualifications,
                               "domains": record["domains"], "topics": record["topics"], "tags": record["tags"],
                               "selection_reason": "reviewed-profile-include"})
    public_index = {"schema": "mindgarden.federation-index/v1", "garden": profile["garden"],
                    "trust": "untrusted-evidence", "scope": scope, "records": public_records}
    graph = {"schema": "mindgarden.federation-graph/v1", "garden": profile["garden"], "scope": scope,
             "nodes": [record["reference"] for _, record in sorted(selected.items())],
             "edges": [{"source": selected[edge["source"]]["reference"], "target": selected[edge["target"]]["reference"],
                        "type": edge["type"], "directed": edge["directed"], "review_state": "approved"}
                       for edge in index["edges"] if edge["source"] in selected and edge["target"] in selected]}
    files = {"index.json": canonical_json(public_index), "graph.json": canonical_json(graph),
             "llms.txt": agent_entrypoint(base)}
    if len(files["llms.txt"]) > context.session["budgets"]["max_context_bytes"]:
        raise ContractError("FEDERATION_BUDGET: agent entrypoint exceeds the explicit byte budget")
    manifest = read_object(safe_path(binding["root"], ".garden/garden.json"))
    descriptor = {"schema": "mindgarden.federation-descriptor/v1", "garden": profile["garden"],
                  "canonical_uri": canonical_uri(manifest["canonical_uri"], profile["garden"]),
                  "base_uri": base, "scope": scope, "review_state": "approved", "trust": "untrusted-evidence",
                  "freshness": "represented-revision", "capabilities": deepcopy(CAPABILITIES),
                  "contracts": deepcopy(SUPPORTED_CONTRACTS),
                  "artifacts": [file_entry(name, files[name]) for name in ARTIFACT_NAMES]}
    descriptor["revision"] = represented_revision(descriptor)
    files["garden.json"] = canonical_json(descriptor)
    files[OWNER_NAME] = canonical_json(owner_marker(descriptor["revision"]))
    if any(len(value) > MAX_FILE_BYTES for value in files.values()) or sum(map(len, files.values())) > MAX_BUNDLE_BYTES:
        raise ContractError("FEDERATION_BUDGET: public projection exceeds the bounded artifact size")
    verify_bundle(files)
    context.check_live()
    digest = profile_sha256 or digest_bytes(canonical_json(profile))
    return FederationBundle(profile["garden"], descriptor, files, digest, profile["output_root"],
                            ((profile_path, digest),) if profile_path is not None else ())


def build_catalog(request: dict) -> dict:
    """Combine supplied checksum-bound public bundles, never canonical bodies."""
    if ContractRegistry().errors(request, "federation-catalog-request"):
        raise ContractError("FEDERATION_REQUEST: supply a bounded list of explicit public bundles and expected revisions")
    verified = []
    diagnostics = set()
    allowed_codes = {"FEDERATION_UNAVAILABLE", "FEDERATION_INVALID", "FEDERATION_VERSION",
                     "FEDERATION_INTEGRITY", "FEDERATION_STALE", "FEDERATION_BUDGET"}
    for item in request["bundles"]:
        try:
            files = read_bundle(Path(item["directory"]))
            descriptor, index, _graph = verify_bundle(files, item["expected_revision"])
            verified.append((descriptor, index, digest_bytes(files["garden.json"])))
        except ContractError as error:
            code = str(error).partition(":")[0]
            diagnostics.add(code if code in allowed_codes else "FEDERATION_INVALID")
    groups = defaultdict(list)
    homes = defaultdict(list)
    for position, (descriptor, index, _digest) in enumerate(verified):
        groups[descriptor["garden"]].append(position)
        homes[("garden", descriptor["canonical_uri"])].append(position)
        homes[("base", descriptor["base_uri"])].append(position)
        for record in index["records"]:
            homes[("record", record["canonical_url"])].append(position)
    denied = set()
    for group in groups.values():
        if len(group) > 1:
            denied.update(group); diagnostics.add("FEDERATION_DUPLICATE_ID")
    for group in homes.values():
        if len(set(group)) > 1:
            denied.update(group); diagnostics.add("FEDERATION_CANONICAL_CONFLICT")
    gardens = []
    records = []
    scopes = []
    for position, (descriptor, index, digest) in sorted(enumerate(verified), key=lambda item: item[1][0]["garden"]):
        if position in denied:
            continue
        gardens.append({key: descriptor[key] for key in ("garden", "canonical_uri", "base_uri", "revision")}
                       | {"descriptor_sha256": digest})
        scopes.append(descriptor["scope"])
        records += [{key: record[key] for key in ("reference", "canonical_url", "title", "kind", "review_state")}
                    for record in index["records"]]
    if len(records) > 10000:
        raise ContractError("FEDERATION_BUDGET: supplied public catalog exceeds 10000 records")
    result = {"schema": "mindgarden.federation-catalog/v1", "status": "partial" if diagnostics else "complete",
              "trust": "untrusted-evidence", "scope": inherit_scope(scopes) if scopes else local_scope("public", publication="publishable"),
              "gardens": gardens, "records": sorted(records, key=lambda record: record_key(record["reference"])),
              "diagnostics": sorted(diagnostics)}
    if ContractRegistry().errors(result, "federation-catalog"):
        raise ContractError("FEDERATION_INVALID: supplied catalog cannot preserve the supported public contract")
    return result


def run_federation(arguments) -> int:
    try:
        return _run_federation(arguments)
    except (OSError, UnicodeError) as error:
        raise ContractError("FEDERATION_UNAVAILABLE: explicit federation inputs or output are unavailable") from error


def _run_federation(arguments) -> int:
    if arguments.operation == "catalog":
        try:
            request = read_object(arguments.input)
        except (OSError, UnicodeError) as error:
            raise ContractError("FEDERATION_REQUEST: explicit public catalog request is unavailable") from error
        result = build_catalog(request)
        print(canonical_json(result).decode(), end="")
        return 0 if result["status"] == "complete" else 3
    context = QueryContext.load(arguments.local_config, arguments.scope)
    raw_profile = authority_bytes(arguments.profile)
    profile = strict_json(raw_profile)
    bundle = build_federation(context, profile, profile_sha256=digest_bytes(raw_profile), profile_path=arguments.profile)
    plan = bundle.plan(context, arguments.output_directory)
    if arguments.apply:
        bundle.apply(context, arguments.output_directory, arguments.plan_digest)
        print(canonical_json(bundle.descriptor).decode(), end="")
    elif arguments.check:
        files = read_bundle(export_destination(context, arguments.output_directory, bundle.output_root))
        verify_bundle(files, bundle.descriptor["revision"])
        if files != bundle.files:
            raise ContractError("FEDERATION_INTEGRITY: supplied output differs from current reviewed inputs")
        print(canonical_json(bundle.descriptor).decode(), end="")
    else:
        print(canonical_json(plan).decode(), end="")
    context.check_live()
    return 0
