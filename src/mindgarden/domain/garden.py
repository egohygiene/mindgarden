"""Version-one garden snapshots, integrity and portable diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Callable
from urllib.parse import unquote, urlsplit

from .contracts import (
    ContractRegistry, Diagnostic, digest_bytes, read_object, safe_path, strict_json,
)
from .validation import ContractError


def evidence_bytes(content: bytes, locator: str) -> bytes:
    """Resolve supported exact evidence selectors without evaluating source text."""
    if locator == "artifact":
        return content
    if locator.startswith("json:"):
        pointer = locator[5:]
        value = strict_json(content)
        if not pointer.startswith("/"):
            raise ContractError("EVIDENCE_LOCATOR: JSON selector needs a pointer")
        try:
            for token in pointer[1:].split("/"):
                token = token.replace("~1", "/").replace("~0", "~")
                value = value[int(token)] if isinstance(value, list) else value[token]
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise ContractError("EVIDENCE_LOCATOR: JSON selector does not resolve") from error
        if not isinstance(value, str):
            raise ContractError("EVIDENCE_LOCATOR: JSON evidence must select text")
        return value.encode("utf8")
    match = re.fullmatch(r"(lines|bytes):(\d+)-(\d+)", locator)
    if match:
        kind, first, last = match[1], int(match[2]), int(match[3])
        if kind == "bytes" and 0 <= first <= last <= len(content):
            return content[first:last]
        lines = content.splitlines(keepends=True)
        if kind == "lines" and 1 <= first <= last <= len(lines):
            return b"".join(lines[first - 1:last])
    raise ContractError("EVIDENCE_LOCATOR: unsupported or out-of-range selector")


@dataclass
class GardenSnapshot:
    root: Path
    manifest: dict
    records: dict[str, dict] = field(default_factory=dict)
    locations: dict[str, str] = field(default_factory=dict)
    hashes: dict[str, str] = field(default_factory=dict)
    contents: dict[str, bytes] = field(default_factory=dict)
    diagnostics: list[Diagnostic] = field(default_factory=list)
    metadata_only: bool = False

    @property
    def count(self) -> int:
        return sum(record["schema"] in {"mindgarden.source/v1", "mindgarden.knowledge/v1"}
                   for record in self.records.values())

    def report(self) -> dict:
        errors = sorted(self.diagnostics, key=lambda item: (item.location, item.code, item.message))
        return {"schema": "mindgarden.validation/v1",
                "status": "invalid" if any(item.severity == "error" for item in errors)
                else "incomplete" if errors or self.metadata_only else "valid",
                "coverage": {"contracts": "v1", "provenance": "metadata-only" if self.metadata_only else "hashes-and-lineage"},
                "records": len(self.records), "diagnostics": [item.document() for item in errors]}

    def require_valid(self) -> GardenSnapshot:
        if self.metadata_only:
            raise ContractError("CONTENT_UNVERIFIED: metadata inspection is not content or provenance verification")
        if self.diagnostics:
            item = sorted(self.diagnostics, key=lambda error: (error.location, error.code))[0]
            raise ContractError(f"{item.code}: {item.location}: {item.message}. {item.remediation}")
        return self


def inspect_garden(repository_root: Path, *, content_resolver: Callable[[dict], bytes] | None = None,
                   authorized_gardens: dict[str, GardenSnapshot] | None = None,
                   garden_root: Path | None = None,
                   allow_unavailable_references: bool = False,
                   record_filter: Callable[[dict], bool] | None = None,
                   metadata_only: bool = False) -> GardenSnapshot:
    """Read only the explicitly supplied garden; never discover private overlays."""
    root = garden_root or repository_root.absolute() / ".garden"
    snapshot = GardenSnapshot(root, {}, metadata_only=metadata_only)

    def visibility(record: dict, owner: GardenSnapshot) -> str:
        from .scope import LEGACY_VISIBILITY

        return record.get("visibility") or LEGACY_VISIBILITY.get(record.get("scope", {}).get("visibility"),
                                                                  owner.manifest.get("visibility", "private"))

    def issue(code: str, location: str, message: str, remediation: str,
              severity: str = "error") -> None:
        snapshot.diagnostics.append(Diagnostic(code, location, message, remediation, severity))

    try:
        if repository_root.is_symlink() or root.is_symlink():
            raise ContractError("PATH_SYMLINK: garden roots must not be symlinks")
        manifest_path = safe_path(root, "garden.json")
        snapshot.manifest = read_object(manifest_path)
        registry = ContractRegistry()
        for error in registry.errors(snapshot.manifest, "garden"):
            issue(error.code, "garden.json" + error.location[1:], error.message, error.remediation)
        if snapshot.diagnostics:
            return snapshot
        manifest = snapshot.manifest
        if "scope" in manifest:
            from .scope import validate_scope

            validate_scope(manifest["scope"], manifest["visibility"])
        roots = manifest["roots"]
        declared = [roots[field] for field in ("sources", "knowledge", "provenance", "context_packs")]
        generated = roots["generated"]
        for value in declared + generated:
            safe_path(root, value)
        all_roots = declared + generated
        for index, left in enumerate(all_roots):
            for right in all_roots[index + 1:]:
                if left == right or left.startswith(right + "/") or right.startswith(left + "/"):
                    issue("ROOT_OVERLAP", "garden.json/roots", "Canonical and generated roots overlap",
                          "Declare separate non-nested content and generated roots.")
        for value in declared:
            if not safe_path(root, value).is_dir():
                issue("ROOT_MISSING", "garden.json/roots", "Declared content root is missing",
                      "Restore the declared directory.")
        ambiguous: set[str] = set()
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(root).as_posix()
            if any(relative == value or relative.startswith(value + "/") for value in generated):
                continue
            if path.is_symlink():
                if record_filter is None:
                    issue("PATH_SYMLINK", relative, "Garden contains a symlink", "Use regular contained files.")
                continue
            if not path.is_file() or path.suffix != ".json" or path == manifest_path:
                continue
            permitted = record_filter is None
            try:
                record = read_object(path)
                if record_filter is not None:
                    permitted = record_filter(record)
                    if not permitted:
                        continue
                errors = registry.errors(record, str(record.get("schema", "unknown")))
                if not (metadata_only and record_filter is not None):
                    for error in errors:
                        issue(error.code, relative + error.location[1:], error.message, error.remediation)
                if errors:
                    continue
                record_id = record["id"]
                if record_id in ambiguous:
                    continue
                if record_id in snapshot.records:
                    if metadata_only and record_filter is not None:
                        ambiguous.add(record_id)
                        for table in (snapshot.records, snapshot.locations, snapshot.hashes):
                            table.pop(record_id, None)
                        continue
                    issue("IDENTITY_DUPLICATE", relative, "Artifact identity is duplicated",
                          "Keep one canonical record for each garden/artifact identity.")
                    continue
                if record.get("garden") != manifest["id"]:
                    issue("IDENTITY_GARDEN", relative, "Record belongs to another garden",
                          "Use the owning garden or an explicit cross-garden reference.")
                snapshot.records[record_id] = record
                snapshot.locations[record_id] = relative
                snapshot.hashes[record_id] = digest_bytes(path.read_bytes())
                if "scope" in record:
                    from .scope import validate_scope

                    validate_scope(record["scope"], record.get("visibility"))
                if metadata_only:
                    if record["schema"] in {"mindgarden.knowledge/v1", "mindgarden.source/v1"}:
                        snapshot.hashes[record_id] = record.get("content", record.get("artifact"))["sha256"]
                    continue
                if record.get("updated", "9999") < record.get("created", "0000"):
                    issue("DATE_ORDER", relative, "Updated date precedes creation",
                          "Preserve consistent observed creation/update dates.")
                if manifest["visibility"] == "public" and visibility(record, snapshot) != "public":
                    issue("PUBLIC_PRIVATE_CONTENT", relative, "Public garden contains non-public material",
                          "Move the record and its bytes to an explicitly private storage boundary.")
                if record.get("schema") in {"mindgarden.knowledge/v1", "mindgarden.source/v1"}:
                    artifact = record.get("content", record.get("artifact"))
                    # Preserve the represented content identity when storage is
                    # unavailable; the explicit incomplete diagnostic prevents
                    # this declaration from being mistaken for verification.
                    snapshot.hashes[record_id] = artifact["sha256"]
                    if metadata_only:
                        continue
                    if "path" in artifact:
                        content = safe_path(root, artifact["path"]).read_bytes()
                    elif content_resolver is not None:
                        content = content_resolver(artifact)
                    else:
                        issue("STORAGE_UNAVAILABLE", relative, "Source storage is not configured",
                              "Supply the explicit local vault binding.", "warning")
                        continue
                    snapshot.contents[record_id] = content
                    snapshot.hashes[record_id] = digest_bytes(content)
                    if digest_bytes(content) != artifact["sha256"]:
                        issue("CONTENT_HASH", relative, "Artifact bytes differ from their immutable hash",
                              "Restore the represented bytes or create a reviewed new revision.")
                    if "size_bytes" in artifact and len(content) != artifact["size_bytes"]:
                        issue("CONTENT_SIZE", relative, "Artifact byte size differs from its manifest",
                              "Restore the original artifact and verify its checksum.")
                    if record["schema"] == "mindgarden.knowledge/v1":
                        for match in re.finditer(r"!?\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)",
                                                 content.decode("utf8")):
                            link = urlsplit(match[1])
                            if link.scheme in {"file", "javascript", "data"} or link.username or link.password:
                                issue("LINK_UNSAFE", relative, "Knowledge contains an unsafe active link",
                                      "Use a safe public URI or a contained, authorized evidence reference.")
                            elif not link.scheme and link.path:
                                target = unquote(link.path)
                                # Relative links may navigate between canonical
                                # folders, but must never leave the garden.
                                base = safe_path(root, artifact["path"]).parent
                                candidate = base / target
                                try:
                                    contained = candidate.resolve().relative_to(root.resolve()).as_posix()
                                    checked = safe_path(root, contained)
                                    if not checked.is_file():
                                        raise OSError()
                                    # Check the unresolved chain too: resolve()
                                    # must not conceal a symlink component.
                                    current = candidate
                                    while current != root and current != current.parent:
                                        if current.is_symlink():
                                            raise OSError()
                                        current = current.parent
                                except (ValueError, OSError, ContractError):
                                    issue("LINK_UNAVAILABLE", relative, "Local link is unsafe or unavailable",
                                          "Use a contained regular file within the authorized garden.")
            except (OSError, ContractError, UnicodeError) as error:
                if not permitted:
                    continue
                code = str(error).split(":", 1)[0] if isinstance(error, ContractError) else "CONTENT_MISSING"
                issue(code, relative, "Record or referenced content cannot be verified",
                      "Restore valid records and their contained source bytes.")
    except (OSError, ContractError) as error:
        code = str(error).split(":", 1)[0] if isinstance(error, ContractError) else "GARDEN_UNAVAILABLE"
        issue(code, "garden.json", "Garden manifest cannot be verified", "Supply a valid explicit garden root.")
        return snapshot

    if metadata_only:
        return snapshot

    records_by_location = {snapshot.locations[key]: record for key, record in snapshot.records.items()}
    content_visibility = {record.get("content", record.get("artifact", {})).get("path"): record.get("visibility")
                          for record in snapshot.records.values()}

    def resolve(reference: dict, location: str, expected: str | None = None) -> tuple[GardenSnapshot, dict] | None:
        target_garden = reference["garden"]
        owner = snapshot if target_garden == snapshot.manifest["id"] else (authorized_gardens or {}).get(target_garden)
        if owner is None:
            if not allow_unavailable_references:
                issue("REFERENCE_UNAVAILABLE", location, "Referenced target is unavailable in this validation scope",
                      "Supply an explicitly authorized target or retain incomplete coverage.", "warning")
            return None
        record = owner.records.get(reference["id"])
        if record is None:
            if record_filter is not None and allow_unavailable_references:
                return None
            issue("REFERENCE_DANGLING", location, "Artifact reference does not resolve",
                  "Restore the target or review the relationship.")
            return None
        if expected is not None and record["schema"] != "mindgarden." + expected + "/v1":
            issue("REFERENCE_KIND", location, "Reference has the wrong artifact kind",
                  "Reference an artifact of the declared kind.")
        referring = records_by_location.get(location)
        if (referring and visibility(referring, snapshot) == "public"
                and visibility(record, owner) != "public"):
            issue("PUBLIC_PRIVATE_REFERENCE", location, "Public record refers to non-public evidence",
                  "Keep the source mapping private and create a separately reviewed public derivative.")
        if owner is not snapshot and owner.diagnostics:
            issue("REFERENCE_UNVERIFIED", location, "Referenced garden has unverified integrity",
                  "Validate the explicitly supplied target before relying on its records.",
                  "error" if any(item.severity == "error" for item in owner.diagnostics) else "warning")
        revision = reference.get("revision")
        if revision and revision.startswith("sha256:") and owner.hashes.get(reference["id"]) != revision[7:]:
            issue("REFERENCE_REVISION", location, "Represented immutable revision does not match",
                  "Restore the represented revision or review a new reference.")
        return owner, record

    def evidence(locator: dict, location: str) -> None:
        result = resolve(locator["source"], location, "source")
        if result is None:
            return
        owner, record = result
        content = owner.contents.get(record["id"])
        if content is None:
            return
        try:
            selected = evidence_bytes(content, locator["locator"])
            if digest_bytes(selected) != locator["content_sha256"]:
                issue("EVIDENCE_HASH", location, "Selected source evidence differs from its hash",
                      "Restore the exact evidence or review the changed source.")
        except ContractError:
            issue("EVIDENCE_LOCATOR", location, "Exact source selector cannot be resolved",
                  "Use a supported selector within the represented source revision.")

    edges: set[tuple] = set()
    supersession: dict[str, set[str]] = {}
    for record_id, record in snapshot.records.items():
        location = snapshot.locations[record_id]
        kind = record["schema"].removeprefix("mindgarden.").removesuffix("/v1")
        if kind in {"source", "provenance"} and record.get("origin") is not None:
            from .sources import validate_origin

            try:
                validate_origin(record["origin"])
            except (ContractError, ValueError):
                issue("SOURCE_ORIGIN_UNSAFE", location, "Source origin contains unsupported physical or credential metadata",
                      "Use a credential-free HTTP(S) or URN source identity and keep acquisition locations in private bindings.")
        for reference in record.get("provenance", []) if kind in {"knowledge", "source"} else []:
            resolve(reference, location, "provenance")
        if kind == "knowledge":
            if record["publication"] == "eligible":
                from .publication import permits_publication

                if not permits_publication(snapshot.manifest["publication"], kind=record["kind"],
                                            domains=record["domains"], topics=record["topics"]):
                    issue("PUBLICATION_POLICY", location, "Publication eligibility is outside the explicit garden allowlist",
                          "Review the kind/domain/topic allowlists; empty lists grant no publication.")
            if record["visibility"] == "public" and record_id in snapshot.contents:
                text = snapshot.contents[record_id].decode("utf8", errors="replace")
                for match in re.finditer(r"!?\[[^\]]*\]\(([^\s)]+)", text):
                    link = urlsplit(match[1])
                    if not link.scheme and link.path:
                        target = safe_path(root, record["content"]["path"]).parent / unquote(link.path)
                        try:
                            relative = target.resolve().relative_to(root.resolve()).as_posix()
                        except ValueError:
                            continue
                        if content_visibility.get(relative, "public") != "public":
                            issue("PUBLIC_PRIVATE_LINK", location, "Public content links to non-public material",
                                  "Keep private links outside the public derivative.")
            for field, expected in (("claims", "claim"), ("synapses", "synapse"), ("supersedes", "knowledge")):
                for reference in record[field]:
                    resolve(reference, location, expected)
                    if field == "supersedes" and reference["garden"] == snapshot.manifest["id"]:
                        supersession.setdefault(record_id, set()).add(reference["id"])
            for locator in record["sources"]:
                evidence(locator, location)
        elif kind == "source":
            for reference in record["inputs"]:
                resolve(reference, location, "source")
        elif kind == "claim":
            resolve(record["subject"], location, "knowledge")
            for item in record["evidence"]:
                target = item["target"]
                evidence(target, location) if "source" in target else resolve(target, location)
        elif kind == "synapse":
            resolve(record["source"], location)
            resolve(record["target"], location)
            endpoints = tuple((record[field]["garden"], record[field]["id"]) for field in ("source", "target"))
            if endpoints[0] == endpoints[1]:
                issue("RELATIONSHIP_SELF", location, "Relationship references itself",
                      "Use distinct relationship endpoints.")
            key = (record["type"], endpoints if record["directed"] else tuple(sorted(endpoints)))
            if key in edges:
                issue("RELATIONSHIP_DUPLICATE", location, "Typed relationship is duplicated",
                      "Keep one canonical relationship and preserve its evidence.")
            edges.add(key)
            if record["type"] == "supersedes" and all(item[0] == snapshot.manifest["id"] for item in endpoints):
                supersession.setdefault(endpoints[0][1], set()).add(endpoints[1][1])
            for locator in record["evidence"]:
                evidence(locator, location)
        elif kind == "provenance":
            if "x-routing-transition" in record:
                from .routing_transitions import transition_event

                try:
                    event = transition_event(record)
                    if event is not None:
                        resolve(event["from"], location, "knowledge")
                        resolve(event["to"], location, "knowledge")
                except ContractError:
                    issue("ROUTE_TRANSITION_INVALID", location, "Invalid reviewed canonical transition",
                          "Restore the exact reviewed transition lineage or author a new private plan.")
            target = resolve(record["artifact"], location)
            if target and target[0].hashes.get(target[1]["id"]) != record["artifact_sha256"]:
                issue("PROVENANCE_HASH", location, "Provenance output hash differs from its artifact",
                      "Restore the represented artifact or review a new transformation.")
            orders = [item["order"] for item in record["transformations"]]
            if orders != list(range(1, len(orders) + 1)):
                issue("TRANSFORMATION_ORDER", location, "Transformation order is not consecutive",
                      "Preserve the exact ordered transformation lineage.")
            for item in record["inputs"]:
                reference = item["artifact"]
                if (item["role"] == "configuration" and reference["garden"] == snapshot.manifest["id"]
                        and reference["id"] == snapshot.manifest["id"]):
                    # The shipped migrator pins the preserved v0 manifest under
                    # the garden identity. Resolve only its explicit rollback
                    # location (or the pre-cutover source), never an overlay.
                    candidates = [repository_root / ".garden.v0/garden.yaml",
                                  repository_root / ".garden/garden.yaml"]
                    previous = next((path for path in candidates if path.is_file()
                                     and not path.is_symlink()), None)
                    if previous is None:
                        issue("PROVENANCE_CONFIGURATION_UNAVAILABLE", location,
                              "Pinned migration configuration is unavailable",
                              "Restore the migration rollback manifest.", "warning")
                    elif (digest_bytes(previous.read_bytes()) != item["sha256"]
                          or reference.get("revision") != "sha256:" + item["sha256"]):
                        issue("PROVENANCE_INPUT_HASH", location, "Pinned migration configuration differs",
                              "Restore the exact rollback manifest.")
                    continue
                target = resolve(item["artifact"], location)
                if target and target[0].hashes.get(target[1]["id"]) != item["sha256"]:
                    issue("PROVENANCE_INPUT_HASH", location, "Transformation input hash differs",
                          "Review a new plan against the changed input.")
        elif kind in {"curation-receipt", "routing-receipt"}:
            for decision in record["decisions"]:
                if kind == "curation-receipt":
                    for locator in decision["sources"]:
                        evidence(locator, location)
                    if decision["output"] is not None:
                        resolve(decision["output"], location, "knowledge")
                else:
                    if decision["canonical_home"] is not None:
                        resolve(decision["canonical_home"], location, "knowledge")
                    for reference in decision["references"]:
                        resolve(reference, location, "knowledge")

    # An iterative three-state walk is bounded even for long or adversarial
    # graphs; recursion and enumerating every path would not be.
    state: dict[str, int] = {}
    for node in sorted(supersession):
        if state.get(node) == 2:
            continue
        stack = [(node, False)]
        while stack:
            current, leaving = stack.pop()
            if leaving:
                state[current] = 2
                continue
            if state.get(current) == 1:
                issue("SUPERSESSION_CYCLE", snapshot.locations.get(current, "garden.json"),
                      "Supersession contains a cycle", "Preserve an acyclic replacement chain.")
                continue
            if state.get(current) == 2:
                continue
            state[current] = 1
            stack.append((current, True))
            stack.extend((target, False) for target in sorted(supersession.get(current, set()), reverse=True))
    return snapshot
