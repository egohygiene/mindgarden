"""Compose a pinned supplied public site without touching sibling surfaces."""

from dataclasses import dataclass
from pathlib import Path

from ..adapters.federation_files import explicit_directory
from ..adapters.portal_files import check_receipt, create_receipt
from ..adapters.site_files import read_artifact, read_site, write_site
from ..domain.contracts import ContractRegistry, canonical_json, digest_bytes, read_object, safe_path, strict_json
from ..domain.portal import composition_manifest
from ..domain.site import SITE_MARKER, verify_site
from ..domain.validation import ContractError
from .query import authority_bytes


def absolute_directory(value):
    path = Path(value)
    if not path.is_absolute() or ".." in path.parts:
        raise ContractError("PORTAL_PATH: explicit absolute ordinary directories are required")
    return explicit_directory(path)


@dataclass
class PortalComposition:
    request: dict
    request_path: Path | None
    request_sha256: str
    source: Path
    parent: Path
    destination: Path
    files: dict
    manifest: dict

    def check_live(self):
        if self.request_path is not None and digest_bytes(authority_bytes(self.request_path)) != self.request_sha256:
            raise ContractError("PORTAL_STALE: exact reviewed composition request changed")
        if digest_bytes(read_artifact(safe_path(self.source, SITE_MARKER))) != self.request["source"]["expected_manifest_sha256"]:
            raise ContractError("PORTAL_STALE: source site manifest changed")

    def check_source(self):
        self.check_live()
        if read_site(self.source) != self.files:
            raise ContractError("PORTAL_STALE: source site membership or content changed")

    def plan(self):
        self.check_source()
        payload = {"schema": "mindgarden.portal-plan/v1", "classification": "machine-local-control",
                   "publication": "never-exportable", "request_sha256": self.request_sha256,
                   "source_directory_sha256": digest_bytes(str(self.source).encode()),
                   "destination_sha256": digest_bytes(str(self.destination).encode()), "manifest": self.manifest}
        return {**payload, "plan_sha256": digest_bytes(canonical_json(payload))}

    def verify(self):
        self.check_source()
        if read_site(self.destination) != self.files:
            raise ContractError("PORTAL_INTEGRITY: owned garden output differs from the pinned site")
        check_receipt(self.parent, self.manifest, required=True)
        self.check_live()
        return self.manifest

    def apply(self, digest):
        if digest != self.plan()["plan_sha256"]:
            raise ContractError("PORTAL_STALE: exact reviewed composition plan required")
        check_receipt(self.parent, self.manifest)
        # A complete garden is committed before the final portal receipt. A
        # failed receipt write leaves an inspectable, retryable complete copy.
        changed = write_site(self.destination, self.files, check_live=self.check_live, verify_inputs=self.check_source)
        self.check_source()
        if read_site(self.destination) != self.files:
            raise ContractError("PORTAL_INTEGRITY: owned output changed before receipt creation")
        created = create_receipt(self.parent, self.manifest)
        self.verify()
        return changed or created


def build_portal(request, *, request_path=None):
    if ContractRegistry().errors(request, "portal-request"):
        raise ContractError("PORTAL_REQUEST: supported explicit public composition request required")
    raw = authority_bytes(request_path) if request_path is not None else canonical_json(request)
    if strict_json(raw) != request:
        raise ContractError("PORTAL_REQUEST: reviewed request bytes differ")
    source = absolute_directory(request["source"]["directory"])
    parent = absolute_directory(request["portal"]["directory"])
    if not parent.is_dir():
        raise ContractError("PORTAL_OUTPUT: caller must supply an existing ordinary portal directory")
    destination = safe_path(parent, request["portal"]["mount"])
    if (destination == source or destination in source.parents or source in destination.parents
            or any(part in {".garden", ".git"} for part in Path(request["portal"]["mount"]).parts)):
        raise ContractError("PORTAL_PATH: source and owned garden mount must be separate")
    if not destination.parent.is_dir():
        raise ContractError("PORTAL_OUTPUT: caller must create the mount's existing ordinary parent")
    files = read_site(source)
    site = verify_site(files)
    if site["kind"] != "site":
        raise ContractError("PORTAL_SITE: only a complete rendered site can be composed")
    if (site["revision"] != request["source"]["expected_revision"]
            or digest_bytes(files[SITE_MARKER]) != request["source"]["expected_manifest_sha256"]):
        raise ContractError("PORTAL_STALE: both represented revision and actual site manifest pin must match")
    manifest = composition_manifest(request, site, files)
    composition = PortalComposition(request, request_path, digest_bytes(raw), source, parent, destination, files, manifest)
    composition.check_source()
    return composition


def run_portal(arguments):
    composition = build_portal(read_object(arguments.input), request_path=arguments.input)
    if arguments.check:
        output = composition.verify()
    elif arguments.apply:
        changed = composition.apply(arguments.plan_digest)
        output = {"schema": "mindgarden.portal-application/v1", "applied": changed, "manifest": composition.manifest}
    else:
        output = composition.plan()
    print(canonical_json(output).decode(), end="")
    return 0
