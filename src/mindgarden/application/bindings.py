"""Explicit machine-local bindings; never a discovery or content database."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..domain.contracts import ContractRegistry, canonical_json, digest_bytes, read_object, safe_path
from ..domain.scope import validate_scope
from ..domain.validation import ContractError


def explicit_root(value: str, *, must_exist: bool = True) -> Path:
    path = Path(value)
    if not path.is_absolute() or ".." in path.parts:
        raise ContractError("BINDING_PATH: supply an explicit absolute root")
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ContractError("BINDING_SYMLINK: roots must not cross symlinks")
    if path.exists() and not path.is_dir():
        raise ContractError("BINDING_ROOT: root must be a directory")
    if must_exist and not path.is_dir():
        raise ContractError("BINDING_MISSING: explicit root is unavailable")
    return path


def garden_fingerprint(root: Path, *, garden_root: Path | None = None) -> str:
    garden = garden_root or safe_path(explicit_root(str(root)), ".garden")
    manifest = read_object(safe_path(garden, "garden.json"))
    generated = manifest["roots"]["generated"]
    records = []
    for path in sorted(garden.rglob("*")):
        relative = path.relative_to(garden).as_posix()
        if path.is_symlink():
            raise ContractError("PATH_SYMLINK: garden contains a symlink")
        if any(relative == item or relative.startswith(item + "/") for item in generated):
            continue
        if path.is_file():
            records.append({"path": relative, "sha256": digest_bytes(path.read_bytes())})
    return "sha256:" + digest_bytes(canonical_json(records))


@dataclass(frozen=True)
class LocalBindings:
    """Physical roots never leave this nonportable runtime value."""

    path: Path
    document: dict
    gardens: dict[str, dict]
    vaults: dict[str, dict]

    @classmethod
    def load(cls, path: Path, *, garden_ids: set[str] | None = None,
             vault_ids: set[str] | None = None, allow_interrupted: bool = False) -> LocalBindings:
        if path.is_symlink():
            raise ContractError("BINDING_SYMLINK: configuration must be a regular file")
        document = read_object(path)
        checked = dict(document)
        for field, selected in (("gardens", garden_ids), ("vaults", vault_ids)):
            if selected is not None:
                checked[field] = [item for item in document.get(field, [])
                                  if isinstance(item, dict) and item.get("id") in selected]
        if ContractRegistry().errors(checked, "local-bindings"):
            raise ContractError("BINDINGS_INVALID: use the supported local-bindings contract")
        gardens: dict[str, dict] = {}
        vaults: dict[str, dict] = {}
        roots: list[Path] = []
        for field, table in (("gardens", gardens), ("vaults", vaults)):
            for item in checked[field]:
                selected = garden_ids if field == "gardens" else vault_ids
                if selected is not None and item["id"] not in selected:
                    continue
                if item["id"] in table:
                    raise ContractError("BINDING_DUPLICATE: logical identity is already registered")
                root = explicit_root(item["root"], must_exist=field == "gardens")
                for existing in roots:
                    if root == existing or root in existing.parents or existing in root.parents:
                        raise ContractError("BINDING_OVERLAP: registered ownership roots must not overlap")
                roots.append(root)
                if field == "gardens":
                    if (allow_interrupted and not (root / ".garden").exists()
                            and safe_path(root, ".mindgarden-write.lock").is_file()):
                        validate_scope(item["scope"])
                        table[item["id"]] = {**item, "root": root}
                        continue
                    manifest = read_object(safe_path(root, ".garden/garden.json"))
                    if manifest.get("id") != item["id"]:
                        raise ContractError("BINDING_IDENTITY: configured and observed garden identities differ")
                    validate_scope(item["scope"], manifest.get("visibility"))
                    if "scope" in manifest and manifest["scope"] != item["scope"]:
                        raise ContractError("BINDING_SCOPE: configured and canonical scope disagree")
                    try:
                        path.absolute().relative_to(root / ".garden")
                    except ValueError:
                        pass
                    else:
                        raise ContractError("BINDING_LOCATION: machine bindings belong outside canonical records")
                table[item["id"]] = {**item, "root": root}
        return cls(path.absolute(), document, gardens, vaults)

    def garden(self, garden_id: str) -> dict:
        if garden_id not in self.gardens:
            raise ContractError("TARGET_UNAVAILABLE: explicit target binding is unavailable")
        return self.gardens[garden_id]

    def vault(self, vault_id: str) -> dict:
        if vault_id not in self.vaults:
            items = [item for item in self.document.get("vaults", []) if isinstance(item, dict) and item.get("id") == vault_id]
            if not items:
                raise ContractError("STORAGE_UNAVAILABLE: explicit vault binding is unavailable")
            if len(items) != 1 or ContractRegistry().errors({"schema": "mindgarden.local-bindings/v1", "gardens": [],
                                                           "vaults": items, "revoked_sessions": []}, "local-bindings"):
                raise ContractError("STORAGE_UNAVAILABLE: explicit vault binding is invalid")
            item = items[0]
            root = explicit_root(item["root"], must_exist=False)
            for garden in self.gardens.values():
                existing = garden["root"]
                if root == existing or root in existing.parents or existing in root.parents:
                    raise ContractError("BINDING_OVERLAP: source storage overlaps canonical ownership")
            self.vaults[vault_id] = {**item, "root": root}
        return self.vaults[vault_id]
