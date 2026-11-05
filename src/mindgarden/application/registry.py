"""Reviewed, reversible registration over existing local bindings and scopes."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
import stat
import sys

from ..adapters.registry_files import (
    MAX_CONTROL_BYTES, control_path, create_control, history_directory, read_control, read_snapshot,
    registry_writer, replace_registry, require_platform,
)
from ..domain.contracts import ContractRegistry, canonical_json, digest_bytes, safe_path, strict_json
from ..domain.registry import (
    default_registry_path, empty_bindings, empty_metadata, require_registry_runtime,
    validate_registry,
)
from ..domain.scope import local_scope, validate_scope
from ..domain.validation import ContractError
from .bindings import explicit_root


def state(path: Path) -> tuple[bytes | None, dict]:
    raw = read_control(path, missing_ok=True)
    document = strict_json(raw) if raw is not None else empty_bindings()
    validate_registry(document, managed=False)
    protect_location(path, document)
    return raw, document


def protect_location(path: Path, document: dict) -> None:
    for item in document["gardens"] + document["vaults"]:
        root = Path(item["root"])
        if not root.is_absolute() or ".." in root.parts or item["root"].startswith("//"):
            raise ContractError("REGISTRY_PATH: declared bindings require absolute roots without traversal")
        if path == root or root in path.parents:
            raise ContractError("REGISTRY_LOCATION: machine-local control state belongs outside registered garden and vault roots")


def inspect_root(binding: dict, *, expected_owners: list | None = None) -> tuple[dict, dict]:
    # Capability/policy denial precedes even a stat of an unavailable root.
    require_registry_runtime(binding["scope"])
    if binding["root"].startswith("//"):
        raise ContractError("REGISTRY_PATH: use one canonical absolute root spelling")
    try:
        root = explicit_root(binding["root"])
        root_info = root.stat()
        target = safe_path(root, ".garden/garden.json")
        info = target.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > MAX_CONTROL_BYTES:
            raise ContractError("REGISTRY_ROOT: garden manifest must be a bounded ordinary file")
        content = target.read_bytes()
        if len(content) > MAX_CONTROL_BYTES:
            raise ContractError("REGISTRY_BUDGET: garden manifest exceeds the metadata budget")
        manifest = strict_json(content)
        contracts = ContractRegistry()
        if contracts.errors(manifest, "garden"):
            raise ContractError("REGISTRY_CONTRACT: registration requires the supported v1 garden manifest")
        supported = {schema.get("properties", {}).get("schema", {}).get("const") for schema in contracts.schemas.values()}
        supported.add("mindgarden.garden/v0")
        declared = manifest["contracts"]
        if ("mindgarden.garden/v1" not in declared["reads"]
                or not set(declared["reads"] + declared["writes"]) <= supported):
            raise ContractError("REGISTRY_CONTRACT: declared garden contracts are incompatible")
        if binding.get("id") is not None and manifest["id"] != binding["id"]:
            raise ContractError("REGISTRY_IDENTITY: declared and observed garden identities differ")
        validate_scope(binding["scope"], manifest["visibility"])
        if "scope" in manifest and manifest["scope"] != binding["scope"]:
            raise ContractError("REGISTRY_SCOPE: registration cannot override canonical scope")
        if expected_owners and set(expected_owners) != set(manifest["owners"]):
            raise ContractError("REGISTRY_OWNER: registration cannot override canonical owners")
        current = root.stat()
        if (root_info.st_dev, root_info.st_ino) != (current.st_dev, current.st_ino):
            raise ContractError("REGISTRY_PLAN_STALE: explicit root changed while inspecting its manifest")
        metadata = {"garden": manifest["id"], "title": manifest["title"], "owners": sorted(manifest["owners"]),
                    "canonical_uri": manifest["canonical_uri"], "version": manifest["version"],
                    "manifest_sha256": digest_bytes(content)}
        fingerprint = {"kind": "garden-manifest", "path": str(target), "sha256": digest_bytes(content),
                       "device": root_info.st_dev, "inode": root_info.st_ino}
        return metadata, fingerprint
    except ContractError:
        raise
    except (OSError, UnicodeError, ValueError) as error:
        raise ContractError("REGISTRY_ROOT_UNAVAILABLE: explicit root or supported manifest is unavailable") from error


def check_overlaps(document: dict) -> None:
    roots = []
    for item in document["gardens"] + document["vaults"]:
        root = Path(item["root"])
        if not root.is_absolute() or ".." in root.parts or item["root"].startswith("//"):
            raise ContractError("REGISTRY_PATH: declared roots must be absolute without traversal")
        if any(root == other or root in other.parents or other in root.parents for other in roots):
            raise ContractError("REGISTRY_CONFLICT: canonical garden and vault ownership roots overlap")
        roots.append(root)


def next_view(metadata: dict, view_id: str, gardens: list[str]) -> dict:
    epoch = metadata["view_epochs"].get(view_id, 0) + 1
    metadata["view_epochs"][view_id] = epoch
    return {"schema": "mindgarden.registry-view/v1", "id": view_id, "gardens": sorted(gardens), "generation": epoch}


def changes(before: dict, after: dict) -> list[dict]:
    result = []
    if ("registry" in before) != ("registry" in after):
        result.append({"entity": "registry", "id": "registry", "before": {"managed": "registry" in before},
                       "after": {"managed": "registry" in after}})
    def gardens(document):
        registered = {item["garden"]: item for item in document.get("registry", {}).get("registrations", [])}
        return {item["id"]: {**item, "registration": registered.get(item["id"])} for item in document["gardens"]}

    for kind, left, right in (("garden", gardens(before), gardens(after)),
                              ("view", {item["id"]: item for item in before.get("registry", {}).get("views", [])},
                               {item["id"]: item for item in after.get("registry", {}).get("views", [])})):
        for identity in sorted(left.keys() | right.keys()):
            if left.get(identity) != right.get(identity):
                result.append({"entity": kind, "id": identity, "before": left.get(identity), "after": right.get(identity)})
    if before["revoked_sessions"] != after["revoked_sessions"]:
        result.append({"entity": "revocations", "id": "revoked-sessions",
                       "before": {"sessions": before["revoked_sessions"]}, "after": {"sessions": after["revoked_sessions"]}})
    return result


@dataclass
class RegistryPlan:
    path: Path
    operation: str
    request: dict
    before_sha256: str | None
    after: bytes
    inputs: list[dict]
    edits: list[dict]

    def document(self) -> dict:
        value = {"schema": "mindgarden.registry-plan/v1", "classification": "machine-local-control",
                 "publication": "never-exportable", "operation": self.operation, "registry_path": str(self.path),
                 "before_sha256": self.before_sha256, "after_sha256": digest_bytes(self.after),
                 "request": self.request, "inputs": self.inputs, "changes": self.edits}
        return {**value, "plan_sha256": digest_bytes(canonical_json(value))}


def validate_request(path: Path, operation: str, request: dict) -> None:
    example = RegistryPlan(path, operation, request, None, b"", [], []).document()
    if ContractRegistry().errors(example, "registry-plan"):
        raise ContractError("REGISTRY_REQUEST: supply a complete supported registry operation")


def build_registry_plan(path: Path, operation: str, request: dict) -> RegistryPlan:
    require_platform()
    validate_request(path, operation, request)
    path = control_path(path)
    raw, before = state(path)
    after = deepcopy(before)
    inputs = []
    if operation not in {"init", "restore"}:
        validate_registry(before)
    if operation == "init":
        after.setdefault("registry", empty_metadata())
        registrations = []
        for binding in after["gardens"]:
            registration, fingerprint = inspect_root(binding)
            registrations.append(registration); inputs.append(fingerprint)
        after["registry"]["registrations"] = sorted(registrations, key=lambda item: item["garden"])
    elif operation == "register":
        scope = request["scope"]
        require_registry_runtime(scope)
        tentative = {"id": request["expected_garden"], "root": str(Path(request["root"])), "scope": scope}
        registration, fingerprint = inspect_root(tentative, expected_owners=request["expected_owners"])
        inputs.append(fingerprint)
        binding = {**tentative, "id": registration["garden"]}
        previous = next((item for item in before["gardens"] if item["id"] == binding["id"]), None)
        if previous is not None and previous != binding:
            raise ContractError("REGISTRY_CONFLICT: unregister the existing binding before changing its root or scope")
        after["gardens"] = sorted([item for item in after["gardens"] if item["id"] != binding["id"]] + [binding], key=lambda item: item["id"])
        metadata = after["registry"]
        metadata["registrations"] = sorted([item for item in metadata["registrations"] if item["garden"] != binding["id"]] + [registration], key=lambda item: item["garden"])
    elif operation == "unregister":
        identity = request["garden"]
        after["gardens"] = [item for item in after["gardens"] if item["id"] != identity]
        after["registry"]["registrations"] = [item for item in after["registry"]["registrations"] if item["garden"] != identity]
        for position, view in enumerate(after["registry"]["views"]):
            if identity in view["gardens"]:
                after["registry"]["views"][position] = next_view(after["registry"], view["id"], [item for item in view["gardens"] if item != identity])
    elif operation == "set-view":
        metadata = after["registry"]
        if not set(request["gardens"]) <= {item["id"] for item in before["gardens"]}:
            raise ContractError("REGISTRY_VIEW: named views require explicitly registered garden identities")
        previous = next((item for item in metadata["views"] if item["id"] == request["id"]), None)
        if previous is None or set(previous["gardens"]) != set(request["gardens"]):
            metadata["views"] = sorted([item for item in metadata["views"] if item["id"] != request["id"]]
                                       + [next_view(metadata, request["id"], request["gardens"])], key=lambda item: item["id"])
    elif operation == "remove-view":
        metadata = after["registry"]
        if any(item["id"] == request["id"] for item in metadata["views"]):
            metadata["views"] = [item for item in metadata["views"] if item["id"] != request["id"]]
            metadata["view_epochs"][request["id"]] += 1
    elif operation == "restore":
        target, content = read_snapshot(path, request["revision"])
        after = strict_json(content)
        validate_registry(after, managed=False)
        restored = deepcopy(after.get("registry", empty_metadata()))
        current = before.get("registry", empty_metadata())
        epochs = {name: max(current["view_epochs"].get(name, 0), restored["view_epochs"].get(name, 0)) + 1
                  for name in current["view_epochs"].keys() | restored["view_epochs"].keys()}
        registrations = []
        inputs.append({"kind": "registry-snapshot", "path": str(target), "sha256": request["revision"], "device": None, "inode": None})
        for binding in after["gardens"]:
            registration, fingerprint = inspect_root(binding)
            registrations.append(registration); inputs.append(fingerprint)
        restored["registrations"] = sorted(registrations, key=lambda item: item["garden"])
        restored["view_epochs"] = epochs
        for view in restored["views"]:
            view["generation"] = epochs[view["id"]]
        after["registry"] = restored
        after["revoked_sessions"] = sorted(set(after["revoked_sessions"]) | set(before["revoked_sessions"]))
    validate_registry(after)
    check_overlaps(after)
    protect_location(path, after)
    content = canonical_json(after)
    if len(content) > MAX_CONTROL_BYTES:
        raise ContractError("REGISTRY_BUDGET: registry exceeds the metadata byte budget")
    result = RegistryPlan(path, operation, deepcopy(request), digest_bytes(raw) if raw is not None else None,
                          content, sorted(inputs, key=lambda item: (item["kind"], item["path"])), changes(before, after))
    if ContractRegistry().errors(result.document(), "registry-plan"):
        raise ContractError("REGISTRY_BUDGET: registry plan exceeds the supported control contract")
    return result


def semantic_registry(content: bytes) -> dict:
    document = strict_json(content)
    if "registry" in document:
        document["registry"].pop("view_epochs", None)
        for view in document["registry"]["views"]:
            view.pop("generation", None)
    return document


def apply_registry_plan(path: Path, supplied: dict, reviewed_digest: str) -> bool:
    if ContractRegistry().errors(supplied, "registry-plan"):
        raise ContractError("REGISTRY_PLAN_INVALID: supply the complete saved registry preview")
    expected = digest_bytes(canonical_json({key: value for key, value in supplied.items() if key != "plan_sha256"}))
    if supplied["plan_sha256"] != expected or reviewed_digest != expected:
        raise ContractError("REGISTRY_PLAN_STALE: exact reviewed plan digest is required")
    path = control_path(path)
    if str(path) != supplied["registry_path"]:
        raise ContractError("REGISTRY_PLAN_STALE: reviewed registry location differs")

    def prepare():
        raw, _document = state(path)
        current = digest_bytes(raw) if raw is not None else None
        if current not in {supplied["before_sha256"], supplied["after_sha256"]}:
            raise ContractError("REGISTRY_PLAN_STALE: registry changed after preview")
        plan = build_registry_plan(path, supplied["operation"], supplied["request"])
        if current == supplied["after_sha256"]:
            matches = (semantic_registry(plan.after) == semantic_registry(raw) if plan.operation == "restore" else plan.after == raw)
            if not matches or plan.inputs != supplied["inputs"]:
                raise ContractError("REGISTRY_PLAN_STALE: desired registration or represented root changed")
            return plan, True
        if plan.document() != supplied:
            raise ContractError("REGISTRY_PLAN_STALE: represented registry, manifest, scope or effect changed")
        return plan, False

    prepare()  # Stale plans are rejected before creating a writer lease/directory.
    with registry_writer(path):
        plan, unchanged = prepare()
        if unchanged:
            return False
        def verify_inputs():
            if build_registry_plan(path, supplied["operation"], supplied["request"]).document() != supplied:
                raise ContractError("REGISTRY_PLAN_STALE: a represented input changed before commit")
        replace_registry(path, plan.after, expected_sha256=plan.before_sha256, verify_inputs=verify_inputs)
        return True


def registry_report(path: Path, *, garden_id: str | None = None, doctor: bool = False,
                    include_local_paths: bool = False) -> dict:
    _raw, document = state(path)
    validate_registry(document)
    entries = {entry["garden"]: entry for entry in document["registry"]["registrations"]}
    selected = [item for item in document["gardens"] if garden_id is None or item["id"] == garden_id]
    if garden_id is not None and not selected:
        raise ContractError("REGISTRY_UNKNOWN: requested registration is unavailable")
    results = []
    for binding in selected:
        entry = {"id": binding["id"], "scope": binding["scope"], "registration": entries[binding["id"]],
                 "state": "registered", "diagnostics": []}
        if include_local_paths:
            entry["root"] = binding["root"]
        if doctor:
            try:
                metadata, _fingerprint = inspect_root(binding)
                if metadata != entries[binding["id"]]:
                    entry.update(state="stale", diagnostics=["REGISTRY_MANIFEST_CHANGED"])
            except ContractError as error:
                code = str(error).partition(":")[0]
                entry.update(state="unavailable", diagnostics=[code if code.startswith("REGISTRY_") else "REGISTRY_ROOT_INVALID"])
        results.append(entry)
    return {"schema": "mindgarden.registry-report/v1", "classification": "machine-local-control",
            "publication": "never-exportable", "status": "degraded" if any(item["diagnostics"] for item in results) else "ready",
            "gardens": results, "views": document["registry"]["views"], "content_integrity": "not-checked"}


def run_registry(arguments) -> int:
    if arguments.operation == "capabilities":
        value = {"schema": "mindgarden.registry-capabilities/v1", "filesystem": "linux-single-user",
                 "available": sys.platform.startswith("linux"), "restricted_registration": False,
                 "verified_encryption": False, "automatic_discovery": False, "cloud_sync": False,
                 "canonical_writes": False, "query_cache_cleanup": False, "history_restore": True}
        print(canonical_json(value).decode(), end="")
        return 0
    path = arguments.registry or default_registry_path()
    if arguments.operation in {"list", "inspect", "doctor"}:
        result = registry_report(path, garden_id=getattr(arguments, "garden_id", None),
                                 doctor=arguments.operation == "doctor", include_local_paths=arguments.include_local_paths)
        print(canonical_json(result).decode(), end="")
        return 0 if result["status"] == "ready" else 3
    if arguments.operation == "apply":
        supplied = strict_json(read_control(arguments.plan))
        changed = apply_registry_plan(path, supplied, arguments.plan_digest)
        print(canonical_json({"schema": "mindgarden.registry-application/v1", "classification": "machine-local-control",
                              "publication": "never-exportable", "applied": changed, "plan_sha256": supplied["plan_sha256"]}).decode(), end="")
        return 0
    request = {}
    if arguments.operation == "register":
        request = {"root": str(arguments.root), "scope": local_scope(arguments.visibility, persistence=arguments.persistence,
                    execution=arguments.execution, publication=arguments.publication),
                   "expected_garden": arguments.garden_id, "expected_owners": arguments.owner}
    elif arguments.operation == "unregister":
        request = {"garden": arguments.garden_id}
    elif arguments.operation == "set-view":
        request = {"id": arguments.view_id, "gardens": sorted(arguments.garden)}
    elif arguments.operation == "remove-view":
        request = {"id": arguments.view_id}
    elif arguments.operation == "restore":
        request = {"revision": arguments.revision}
    plan = build_registry_plan(path, arguments.operation, request)
    if arguments.output:
        _raw, document = state(path)
        protect_location(arguments.output, document)
        protect_location(arguments.output, strict_json(plan.after))
        history = history_directory(path)
        if arguments.output == path or arguments.output == history or history in arguments.output.parents:
            raise ContractError("REGISTRY_LOCATION: save reviewed plans separately from registry state and owned history")
        create_control(arguments.output, canonical_json(plan.document()))
    print(canonical_json(plan.document()).decode(), end="")
    return 0
