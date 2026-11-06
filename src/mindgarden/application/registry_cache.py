"""Reviewed reversible cache quarantine; canonical garden content is never moved."""

from pathlib import Path
import os
import re

from ..adapters.registry_files import (control_path,create_control,private_parent,read_control,registry_writer)
from ..domain.contracts import ContractRegistry,canonical_json,digest_bytes,read_object,safe_path,strict_json
from ..domain.registry import default_registry_path,require_registry_runtime,validate_registry
from ..domain.validation import ContractError
from .bindings import LocalBindings
from .scope_cache import CACHE_MARKER,verify_cache
from .transactions import atomic_journal

RECOVERY_MARKER = ".mindgarden-cache-recovery.json"


def read_receipt(path):
    receipt = strict_json(read_control(path))
    if (not isinstance(receipt,dict) or receipt.get("schema")!="mindgarden.cache-recovery/v1"
            or receipt.get("state") not in {"prepared-quarantine","prepared-restore","quarantined","restored"}
            or not {"garden","scope_sha256","manifest_sha256","plan_sha256"} <= receipt.keys()):
        raise ContractError("CACHE_INTEGRITY: recovery receipt is not recognized owned state")
    return receipt


def recovery_root(registry: Path) -> Path:
    return registry.parent / (registry.name + ".cache-recovery")


def locations(registry: Path,garden: str,scope: str):
    if not re.fullmatch(r"[0-9a-f]{64}",scope):
        raise ContractError("CACHE_IDENTITY: supply an exact scope digest")
    raw=read_control(registry);document=strict_json(raw);validate_registry(document)
    candidates=[item for item in document["gardens"] if item["id"]==garden]
    if len(candidates)!=1:raise ContractError("CACHE_UNAVAILABLE: explicit registered garden is unavailable")
    require_registry_runtime(candidates[0]["scope"])
    bindings=LocalBindings.load(registry,garden_ids={garden},vault_ids=set())
    root=bindings.garden(garden)["root"]
    manifest=read_object(safe_path(root,".garden/garden.json"))
    generated=safe_path(root/".garden",manifest["roots"]["generated"][0])
    marker=safe_path(generated,".mindgarden-owned.json")
    if not marker.is_file() or read_object(marker)!={"schema":"mindgarden.generated-owner/v1","garden":garden}:
        raise ContractError("CACHE_UNOWNED: generated ownership is unavailable; canonical content is retained")
    source=safe_path(generated,"scopes/"+scope)
    return raw,root,source


def recovery_owner(registry):
    return {"schema":"mindgarden.cache-recovery-owner/v1","registry_location_sha256":digest_bytes(str(registry).encode())}


def check_recovery_root(registry,*,create=False):
    root=recovery_root(registry);marker=root/RECOVERY_MARKER
    if root.exists():
        if strict_json(read_control(marker))!=recovery_owner(registry):
            raise ContractError("CACHE_UNOWNED: recovery directory has another owner")
    elif create:
        create_control(marker,canonical_json(recovery_owner(registry)))
    else:raise ContractError("CACHE_UNAVAILABLE: owned cache recovery state is unavailable")
    return root


def inspect_cache(registry: Path,garden: str,scope: str) -> dict:
    registry=control_path(registry)
    _raw,_root,source=locations(registry,garden,scope)
    manifest=verify_cache(source,garden,scope)
    return {"schema":"mindgarden.cache-inspection/v1","classification":"machine-local-control","publication":"never-exportable",
            "garden":garden,"scope_sha256":scope,"state":"owned" if manifest is not None else "missing",
            "files":len(manifest["files"]) if manifest else 0,
            "bytes":sum(item["size_bytes"] for item in manifest["files"]) if manifest else 0}


def build_cache_plan(registry: Path,request: dict) -> dict:
    registry=control_path(registry)
    if (set(request)!={"id","action","garden","scope_sha256","recovery_id"}
            or request["action"] not in {"quarantine","restore"}
            or request["action"]=="quarantine" and request["recovery_id"] is not None
            or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*",request["id"])):
        raise ContractError("CACHE_REQUEST: supply an explicit operation identity and supported action")
    raw,root,original=locations(registry,request["garden"],request["scope_sha256"])
    if request["action"]=="quarantine":
        manifest=verify_cache(original,request["garden"],request["scope_sha256"])
        if manifest is None:raise ContractError("CACHE_UNAVAILABLE: selected owned cache is unavailable")
        content_sha=digest_bytes((original/CACHE_MARKER).read_bytes())
        token=digest_bytes(canonical_json({"request":request,"manifest_sha256":content_sha,
                                          "registry_location_sha256":digest_bytes(str(registry).encode())}))
        source,destination=original,recovery_root(registry)/token/"payload"
    else:
        token=request["recovery_id"]
        if not isinstance(token,str) or not re.fullmatch(r"[0-9a-f]{64}",token):
            raise ContractError("CACHE_IDENTITY: restore needs an exact recovery identity")
        archive=check_recovery_root(registry)/token
        receipt=read_receipt(archive/"receipt.json")
        if receipt.get("garden")!=request["garden"] or receipt.get("scope_sha256")!=request["scope_sha256"]:
            raise ContractError("CACHE_IDENTITY: recovery identity belongs to another cache")
        source,destination=archive/"payload",original
        observed=source if source.exists() else destination
        manifest=verify_cache(observed,request["garden"],request["scope_sha256"])
        content_sha=receipt["manifest_sha256"]
        if manifest is None or digest_bytes((observed/CACHE_MARKER).read_bytes())!=content_sha:
            raise ContractError("CACHE_INTEGRITY: recovery payload differs")
    payload={"schema":"mindgarden.registry-cache-plan/v1","classification":"machine-local-control","publication":"never-exportable",
        "request":request,"recovery_id":token,"registry_sha256":digest_bytes(raw),
        "garden_manifest_sha256":digest_bytes((root/".garden/garden.json").read_bytes()),
        "source":str(source),"destination":str(destination),"manifest_sha256":content_sha,"inventory":manifest}
    document={**payload,"plan_sha256":digest_bytes(canonical_json(payload))}
    if ContractRegistry().errors(document,"registry-cache-plan"):
        raise ContractError("CACHE_REQUEST: reviewed cache plan is invalid")
    return document


def apply_cache_plan(registry: Path,document: dict,reviewed_digest: str) -> bool:
    registry=control_path(registry)
    if ContractRegistry().errors(document,"registry-cache-plan"):
        raise ContractError("CACHE_REQUEST: saved cache plan is invalid")
    payload={key:value for key,value in document.items() if key!="plan_sha256"}
    digest=digest_bytes(canonical_json(payload))
    if reviewed_digest!=digest or document["plan_sha256"]!=digest:
        raise ContractError("CACHE_PLAN_STALE: reviewed cache plan differs")
    request=document["request"]
    with registry_writer(registry):
        raw,root,original=locations(registry,request["garden"],request["scope_sha256"])
        if digest_bytes(raw)!=document["registry_sha256"] or digest_bytes((root/".garden/garden.json").read_bytes())!=document["garden_manifest_sha256"]:
            raise ContractError("CACHE_PLAN_STALE: registry or garden contract changed")
        token=document["recovery_id"]
        archive=recovery_root(registry)/token
        expected=(original,archive/"payload") if request["action"]=="quarantine" else (archive/"payload",original)
        source,destination=map(Path,(document["source"],document["destination"]))
        if (source,destination)!=expected:
            raise ContractError("CACHE_PATH: saved plan differs from owned cache locations")
        root=check_recovery_root(registry,create=request["action"]=="quarantine")
        receipt_path=archive/"receipt.json"
        previous=read_receipt(receipt_path) if receipt_path.exists() else None
        if previous is not None and (previous.get("manifest_sha256")!=document["manifest_sha256"]
                or previous.get("garden")!=request["garden"] or previous.get("scope_sha256")!=request["scope_sha256"]):
            raise ContractError("CACHE_CONFLICT: recovery state belongs to another reviewed operation")
        final_state="quarantined" if request["action"]=="quarantine" else "restored"
        if request["action"]=="quarantine" and previous is not None and previous.get("state")=="restored":
            raise ContractError("CACHE_PLAN_STALE: a restored cache needs a new reviewed operation identity")
        if source.exists() and destination.exists():
            raise ContractError("CACHE_CONFLICT: both locations exist; retain both for inspection")
        observed=source if source.exists() else destination
        manifest=verify_cache(observed,request["garden"],request["scope_sha256"])
        if manifest!=document["inventory"] or not observed.exists() or digest_bytes((observed/CACHE_MARKER).read_bytes())!=document["manifest_sha256"]:
            raise ContractError("CACHE_PLAN_STALE: owned cache changed or became unavailable")
        private_parent(receipt_path)
        receipt={"schema":"mindgarden.cache-recovery/v1","garden":request["garden"],"scope_sha256":request["scope_sha256"],
                 "manifest_sha256":document["manifest_sha256"],"plan_sha256":digest,"state":"prepared-"+request["action"]}
        if destination.exists():
            if previous is None:raise ContractError("CACHE_CONFLICT: destination has no recovery receipt")
            atomic_journal(receipt_path,{**receipt,"state":final_state})
            return False
        destination.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        if source.stat().st_dev!=destination.parent.stat().st_dev:
            raise ContractError("CACHE_UNSUPPORTED: reversible quarantine requires one filesystem; originals are retained")
        atomic_journal(receipt_path,receipt)
        try:
            os.replace(source,destination)
            if verify_cache(destination,request["garden"],request["scope_sha256"])!=document["inventory"]:
                raise ContractError("CACHE_INTEGRITY: selected cache failed verification")
            atomic_journal(receipt_path,{**receipt,"state":final_state})
        except OSError as error:
            raise ContractError("CACHE_RECOVERY_REQUIRED: repeat the exact reviewed plan; preserve both owned locations") from error
        return True


def run_cache(arguments):
    registry=(arguments.registry or default_registry_path()).absolute()
    if arguments.operation=="cache-inspect":
        result=inspect_cache(registry,arguments.garden_id,arguments.scope_digest)
    elif arguments.operation=="cache-plan":
        result=build_cache_plan(registry,{"id":arguments.operation_id,"action":arguments.action,"garden":arguments.garden_id,
                                         "scope_sha256":arguments.scope_digest,"recovery_id":arguments.recovery_id})
        if arguments.output:create_control(arguments.output.absolute(),canonical_json(result))
    else:
        document=strict_json(read_control(arguments.plan))
        applied=apply_cache_plan(registry,document,arguments.plan_digest)
        result={"schema":"mindgarden.cache-application/v1","classification":"machine-local-control","publication":"never-exportable",
                "recovery_id":document["recovery_id"],"applied":applied,"state":document["request"]["action"]}
    print(canonical_json(result).decode(),end="")
    return 0
