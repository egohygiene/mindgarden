"""Explicit initial classification and ordinary PDF plan/apply application service."""

from pathlib import Path

from ..adapters.pdf_source import PDFSourceAdapter
from ..adapters.pdf_tools import LocalPDFReader
from ..domain.contracts import ContractRegistry, canonical_json, digest_bytes
from ..domain.scope import inherit_scope, validate_scope
from ..domain.sources import AdapterRegistry
from ..domain.validation import ContractError
from .bindings import LocalBindings
from .ingestion import apply_ingestion, build_ingestion_plan, captured_bytes
from .storage import open_vault


def classification_review(path: Path | None, garden_scope: dict) -> tuple[dict, str]:
    # Confidential is the default; unavailable assurance is checked before input/tool/temp access.
    if path is None:
        raise ContractError("RUNTIME_UNVERIFIED: restricted PDF processing requires unavailable confidential storage/runtime")
    content = captured_bytes(path, 65536)
    from ..domain.contracts import strict_json

    review = strict_json(content)
    if ContractRegistry().errors(review, "document-classification"):
        raise ContractError("DOCUMENT_CLASSIFICATION: supply an approved human initial-classification record")
    scope = inherit_scope([validate_scope(garden_scope), validate_scope(review["scope"])])
    if scope["visibility"] in {"public", "restricted"} or scope["persistence"] == "encrypted-vault":
        raise ContractError("RUNTIME_UNVERIFIED: this reader has no verified confidential-runtime capability")
    if scope["visibility"] != garden_scope["visibility"]:
        raise ContractError("DOCUMENT_CLASSIFICATION: explicit source classification conflicts with destination")
    return review, digest_bytes(content)


def build_document_plan(bindings: LocalBindings, garden_id: str, vault_id: str, input_path: Path,
                        metadata: dict, classification: Path | None, *, tool_directory: Path | None = None,
                        reader=None):
    review, review_sha = classification_review(classification, bindings.garden(garden_id)["scope"])
    original = captured_bytes(input_path, 10 * 1024 * 1024)
    if digest_bytes(original) != review["source_sha256"]:
        raise ContractError("DOCUMENT_CHANGED: initial classification names different captured bytes")
    vault = open_vault(bindings, vault_id)
    # A filesystem flag never grants encryption or confidential execution.
    if not hasattr(vault, "_check_root"):
        raise ContractError("DOCUMENT_UNAVAILABLE: selected adapter supplies no verified local workspace")
    vault._check_root()
    if reader is None:
        if tool_directory is None:
            raise ContractError("DOCUMENT_UNAVAILABLE: select an explicit optional local tool directory")
        reader = LocalPDFReader(tool_directory, vault.root)
    adapter = PDFSourceAdapter(reader)
    supplied = {**metadata, "media_type": "application/pdf",
                "source_scope": inherit_scope([bindings.garden(garden_id)["scope"], review["scope"]]),
                "classification_review": review, "classification_sha256": review_sha}
    plan = build_ingestion_plan(bindings, garden_id, vault_id, input_path, supplied,
                                registry=AdapterRegistry((adapter,)), adapter_id=adapter.adapter_id)
    plan.source_checks.append((classification.absolute(), review_sha))
    plan.source_checks.extend(getattr(reader, "source_checks", []))
    return plan


def run_document(arguments):
    bindings = LocalBindings.load(arguments.local_config, garden_ids={arguments.garden_id}, vault_ids={arguments.vault_id})
    metadata = {"source_id": arguments.source_id, "title": arguments.title, "origin": arguments.origin,
                "owner": arguments.owner, "rights": arguments.rights, "captured_at": arguments.captured}
    plan = build_document_plan(bindings, arguments.garden_id, arguments.vault_id, arguments.input,
                               metadata, arguments.classification_review, tool_directory=arguments.tool_directory)
    result = plan.document()
    if arguments.apply:
        if not arguments.plan_digest:
            raise ContractError("PLAN_DIGEST: --plan-digest is required with --apply")
        result["applied"] = apply_ingestion(plan, arguments.plan_digest, bindings, arguments.vault_id)
    print(canonical_json(result).decode(), end="")
    return 0
