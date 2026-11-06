#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Prepare and verify source-bound Python release evidence; publication is a manual handoff."""

from argparse import ArgumentParser
from datetime import datetime, timezone
from email.parser import Parser
import gzip
import hashlib
import importlib.metadata
import importlib.util
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "egohygiene/mindgarden"


class ReleaseError(ValueError): pass


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf8")


def digest(content): return hashlib.sha256(content).hexdigest()


def run(arguments, *, cwd=None, environment=None):
    result = subprocess.run(arguments, cwd=cwd, env=environment, capture_output=True, check=False)
    if result.returncode:
        raise ReleaseError("RELEASE_COMMAND: required local tool failed; inspect the tool separately")
    return result.stdout


def git(root, *arguments): return run(["git", "-C", str(root), *arguments]).decode().strip()


def owner_sources(root): return json.loads((root / ".egohygiene/release-sources.json").read_bytes())


def bootstrap(root, tools):
    if tools.exists() and tools.is_symlink(): raise ReleaseError("RELEASE_PATH: tools root must be ordinary")
    tools.mkdir(mode=0o700, parents=True, exist_ok=True)
    for name, source in owner_sources(root).items():
        target = tools / name
        if target.exists():
            require_tool(root, tools, name)
            continue
        target.mkdir(mode=0o700)
        run(["git", "init", "--quiet", str(target)])
        run(["git", "-C", str(target), "fetch", "--quiet", "--depth", "1", "https://github.com/" + source["repository"] + ".git", source["revision"]])
        run(["git", "-C", str(target), "checkout", "--quiet", "--detach", "FETCH_HEAD"])
    return {"schema": "mindgarden.release-tools/v1", "state": "qualified", "sources": owner_sources(root)}


def require_tool(root, tools, name):
    target = tools / name
    source = owner_sources(root)[name]
    if target.is_symlink() or not target.is_dir() or git(target, "rev-parse", "HEAD") != source["revision"]:
        raise ReleaseError("RELEASE_OWNER_UNAVAILABLE: bootstrap the exact pinned owner tools")
    if git(target, "status", "--porcelain", "--untracked-files=no"):
        raise ReleaseError("RELEASE_OWNER_DIRTY: pinned owner source has local modifications")
    return target


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec); spec.loader.exec_module(loaded)
    return loaded


def project_version(root):
    project = tomllib.loads((root / "pyproject.toml").read_text())["project"]
    if project["name"] != "mindgarden" or not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", project["version"]):
        raise ReleaseError("RELEASE_VERSION: use the declared exact semantic version")
    return project["version"]


def build_tools(root):
    versions = {}
    for line in (root / "requirements/release.txt").read_text().splitlines():
        if not line.strip() or line.startswith("#"): continue
        if not re.fullmatch(r"[A-Za-z0-9_-]+==[A-Za-z0-9.]+", line):
            raise ReleaseError("RELEASE_BUILD_TOOLS: use exact tool requirements")
        name, expected = line.split("==")
        if importlib.metadata.version(name) != expected:
            raise ReleaseError("RELEASE_BUILD_TOOLS: install requirements/release.txt exactly")
        versions[name] = expected
    return versions


def qualified_plan(root, tools, requested=None, *, revision=None):
    version = project_version(root)
    if requested is not None and requested != "v" + version:
        raise ReleaseError("RELEASE_VERSION_DRIFT: requested tag must match pyproject.toml")
    aether = require_tool(root, tools, "aether")
    hygiene = require_tool(root, tools, "hygiene")
    egolint = require_tool(root, tools, "egolint")
    declaration = module(aether / "library/organization/specs/release/validate.py", "qualified_aether_release")
    declaration.validate_release_declaration(root, Path(".egohygiene/release.json"), "v" + version)
    run([sys.executable, str(egolint / "scripts/validate_repository_release_sources.py")])
    policy = json.loads((hygiene / "catalog/repository-release-policy.json").read_bytes())
    return {"schema": "mindgarden.release-plan/v1", "repository": REPOSITORY, "version": version,
            "tag": "v" + version, "authority": {"kind": "pyproject-project", "path": "pyproject.toml"},
            "source_revision": revision or git(root, "rev-parse", "HEAD"), "owner_sources": owner_sources(root),
            "owner_policy_status": policy["status"], "publication": "not-performed",
            "egolint": "pinned-inputs-qualified; Python consumer conformance remains separate",
            "delivery": json.loads((root / ".egohygiene/release.json").read_bytes())["delivery"]}


def safe_members(archive):
    members = archive.getmembers()
    for member in members:
        path = PurePosixPath(member.name)
        if path.is_absolute() or ".." in path.parts or not (member.isfile() or member.isdir()):
            raise ReleaseError("RELEASE_ARCHIVE: source contains unsupported paths or links")
    return members


def normalize_sdist(path, epoch):
    output = io.BytesIO()
    with tarfile.open(fileobj=io.BytesIO(path.read_bytes()), mode="r:gz") as original:
        members = safe_members(original)
        with gzip.GzipFile(fileobj=output, mode="wb", filename="", mtime=epoch) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as normalized:
                for member in sorted(members, key=lambda value: value.name):
                    clean = tarfile.TarInfo(member.name)
                    clean.size = member.size; clean.mtime = epoch; clean.uid = clean.gid = 0
                    clean.mode = 0o755 if member.isdir() else 0o644
                    clean.type = tarfile.DIRTYPE if member.isdir() else tarfile.REGTYPE
                    normalized.addfile(clean, original.extractfile(member) if member.isfile() else None)
    path.write_bytes(output.getvalue())


def normalize_wheel(path, epoch):
    output = io.BytesIO()
    stamp = datetime.fromtimestamp(max(epoch, 315532800), timezone.utc).timetuple()[:6]
    with zipfile.ZipFile(path) as original, zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as normalized:
        for name in sorted(original.namelist()):
            candidate = PurePosixPath(name)
            if candidate.is_absolute() or ".." in candidate.parts:
                raise ReleaseError("RELEASE_ARCHIVE: wheel paths are unsafe")
            info = zipfile.ZipInfo(name, stamp); info.create_system = 3; info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            normalized.writestr(info, original.read(name))
    path.write_bytes(output.getvalue())


def build_once(source, directory, epoch):
    tree = directory / "source"; tree.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(source), mode="r:") as archive:
        archive.extractall(tree, members=safe_members(archive), filter="data")
    build_tools(tree)
    target = directory / "dist"
    environment = {**os.environ, "SOURCE_DATE_EPOCH": str(epoch), "PYTHONHASHSEED": "0"}
    run([sys.executable, "-m", "build", "--no-isolation", "--sdist", "--wheel", "--outdir", str(target)], cwd=tree, environment=environment)
    for artifact in target.iterdir():
        if artifact.name.endswith(".tar.gz"): normalize_sdist(artifact, epoch)
        elif artifact.suffix == ".whl": normalize_wheel(artifact, epoch)
        else: raise ReleaseError("RELEASE_ARTIFACT: unexpected build output")
    return target


def artifact_facts(directory, version):
    wheels = sorted(directory.glob("*.whl")); sources = sorted(directory.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sources) != 1:
        raise ReleaseError("RELEASE_ARTIFACT: require one wheel and one source distribution")
    with zipfile.ZipFile(wheels[0]) as wheel:
        metadata = Parser().parsestr(wheel.read(f"mindgarden-{version}.dist-info/METADATA").decode())
        if metadata["Name"] != "mindgarden" or metadata["Version"] != version or metadata.get_all("Requires-Dist"):
            raise ReleaseError("RELEASE_METADATA: wheel version or dependency contract differs")
    with tarfile.open(sources[0], "r:gz") as archive:
        names = {member.name for member in safe_members(archive)}
        pyproject = tomllib.loads(archive.extractfile(f"mindgarden-{version}/pyproject.toml").read().decode())
        if pyproject["project"]["version"] != version:
            raise ReleaseError("RELEASE_METADATA: source version differs")
        if any(".cache" in PurePosixPath(name).parts or ".git" in PurePosixPath(name).parts for name in names):
            raise ReleaseError("RELEASE_CONTENT: generated/private control state entered source distribution")
    return sources[0], wheels[0]


def prepare(root, tools, output, requested=None, revision=None):
    if (output.exists() or ".." in output.parts or any(part in {".git", ".garden"} for part in output.parts)
            or any(path.is_symlink() for path in (output, *output.parents))):
        raise ReleaseError("RELEASE_DESTINATION: use a new ordinary output directory")
    if any((parent / ".garden/garden.json").exists() or (parent / ".garden/garden.yaml").exists()
           or (parent / "vault.json").exists() for parent in output.parents):
        raise ReleaseError("RELEASE_DESTINATION: keep candidates outside canonical garden/vault roots")
    build_tools(root)
    revision = revision or git(root, "rev-parse", "HEAD")
    if not re.fullmatch(r"[0-9a-f]{40}", revision): raise ReleaseError("RELEASE_SOURCE: require a full immutable commit")
    source = run(["git", "-C", str(root), "archive", revision])
    epoch = int(git(root, "show", "--no-patch", "--format=%ct", revision))
    output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".release-stage-", dir=output.parent) as temporary:
        stage = Path(temporary)
        first = build_once(source, stage / "first", epoch)
        second = build_once(source, stage / "second", epoch)
        first_hashes = {path.name: digest(path.read_bytes()) for path in first.iterdir()}
        if first_hashes != {path.name: digest(path.read_bytes()) for path in second.iterdir()}:
            raise ReleaseError("RELEASE_REPRODUCIBILITY: independent builds differ")
        checkout = stage / "first/source"
        plan = qualified_plan(checkout, tools, requested, revision=revision)
        version = plan["version"]
        source_path, wheel_path = artifact_facts(first, version)
        bundle = stage / "bundle"; bundle.mkdir(mode=0o700)
        for artifact in (source_path, wheel_path): shutil.copyfile(artifact, bundle / artifact.name)
        created = datetime.fromtimestamp(epoch, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        source_identity = {"repository": REPOSITORY, "revision": revision, "source_date_epoch": epoch}
        python_record = {"$schema": "https://egohygiene.github.io/relay/contracts/python-package-release/v1/schema.json",
            "schema": "egohygiene.relay-python-package-release/v1", "component": {"id": "mindgarden", "distribution": "mindgarden",
            "version": version, "version_authority": plan["authority"]}, "artifacts": {"sdist": {"path": source_path.name,
            "sha256": first_hashes[source_path.name]}, "wheels": [{"path": wheel_path.name, "sha256": first_hashes[wheel_path.name]}]},
            "registry": {"provider": "pypi", "state": "unavailable"}}
        documents = {"python-package.json": python_record,
            "provenance.json": {"schema": "mindgarden.release-provenance/v1", "source": source_identity,
                "builder": {"python": sys.version.split()[0], "tools": build_tools(checkout)}, "artifacts": first_hashes,
                "reproducibility": "two-independent-builds-match", "publication": "not-performed"},
            "signature.json": {"state": "unavailable", "reason": "No owner-managed signing identity or attestation is configured for this local candidate."},
            "sbom.spdx.json": {"spdxVersion": "SPDX-2.3", "dataLicense": "CC0-1.0", "SPDXID": "SPDXRef-DOCUMENT",
                "name": "mindgarden-" + version, "documentNamespace": "https://github.com/egohygiene/mindgarden/sbom/" + revision,
                "creationInfo": {"created": created, "creators": ["Organization: Ego Hygiene"]},
                "packages": [{"name": "mindgarden", "SPDXID": "SPDXRef-Mindgarden", "versionInfo": version,
                    "downloadLocation": "NOASSERTION", "filesAnalyzed": False, "licenseConcluded": "MIT", "licenseDeclared": "MIT"}],
                "relationships": [{"spdxElementId": "SPDXRef-DOCUMENT", "relationshipType": "DESCRIBES", "relatedSpdxElement": "SPDXRef-Mindgarden"}]}}
        for name, value in documents.items(): (bundle / name).write_bytes(encode(value))
        shutil.copyfile(checkout / "CHANGELOG.md", bundle / "CHANGELOG.md")
        (bundle / "ROLLBACK.md").write_text("Preserve immutable tags and assets. Revert affected source, review a corrective successor, and update consumers explicitly. Registry yanks require their separate owner adapter.\n")
        inventory = "".join(digest(path.read_bytes()) + "  " + path.name + "\n" for path in sorted(bundle.iterdir()))
        (bundle / "SHA256SUMS").write_text(inventory)
        if output.exists(): raise ReleaseError("RELEASE_DESTINATION: output appeared during preparation")
        os.rename(bundle, output)
    return verify(root, tools, output, requested, artifact_only=True)


def verify(root, tools, bundle, requested=None, *, artifact_only=False):
    version = project_version(root)
    if requested is not None and requested != "v" + version: raise ReleaseError("RELEASE_VERSION_DRIFT: tag differs from authority")
    relay = require_tool(root, tools, "relay")
    validator = module(relay / "actions/validate-release-bundle/scripts/validate_release_bundle.py", "qualified_relay_bundle")
    validator.safe_regular_files(bundle)
    provenance = json.loads((bundle / "provenance.json").read_bytes())
    evidence = validator.validate_release_bundle(bundle_directory=bundle, profiles_path=relay / "release-profiles.json",
        profile_id="python-package", release_version="v" + version, source_revision=provenance["source"]["revision"])
    artifact_facts(bundle, version)
    from jsonschema import Draft202012Validator
    schema = json.loads((relay / "schemas/python-package-release.schema.json").read_bytes())
    findings = sorted("/" + "/".join(map(str, error.absolute_path)) for error in Draft202012Validator(schema).iter_errors(json.loads((bundle / "python-package.json").read_bytes())))
    gates = ([{"code": "RELEASE_UPSTREAM_SCHEMA_PARITY", "state": "blocked", "paths": findings,
               "owner": "egohygiene/relay", "revision": owner_sources(root)["relay"]["revision"]}] if findings else [])
    gates += [{"code": "RELEASE_REVIEW_REQUIRED", "state": "external", "required_for": "manual-publication"},
              {"code": "RELEASE_PYPI_OIDC", "state": "unavailable", "required_for": "pypi-1.0"}]
    result = {"schema": "mindgarden.release-verification/v1", "source_revision": provenance["source"]["revision"],
        "tag": "v" + version, "artifact_checks": "passed", "relay_evidence": evidence,
        "upstream_schema": "invalid" if findings else "valid", "publication_performed": False,
        "handoff_ready": not findings, "releasable": False, "gates": gates}
    if findings and not artifact_only:
        raise ReleaseError("RELEASE_UPSTREAM_SCHEMA_PARITY: candidate is blocked by the pinned Relay root-pyproject schema mismatch")
    return result


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("bootstrap", "plan", "prepare", "verify"))
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    parser.add_argument("--owner-tools", type=Path, default=ROOT / ".cache/release-tools")
    parser.add_argument("--release-version")
    parser.add_argument("--source-revision")
    parser.add_argument("--output-directory", type=Path)
    parser.add_argument("--artifact-only", action="store_true", help="Verify local artifacts; still report releasable=false and every external gate")
    args = parser.parse_args()
    root, tools = args.repository_root.resolve(), args.owner_tools.resolve()
    try:
        if args.operation == "bootstrap": result = bootstrap(root, tools)
        elif args.operation == "plan": result = qualified_plan(root, tools, args.release_version)
        else:
            if args.output_directory is None: parser.error("--output-directory is required")
            output = args.output_directory.absolute()
            result = (prepare(root, tools, output, args.release_version, args.source_revision) if args.operation == "prepare"
                      else verify(root, tools, output, args.release_version, artifact_only=args.artifact_only))
    except (ReleaseError, OSError, ValueError, KeyError, importlib.metadata.PackageNotFoundError) as error:
        print("release: " + str(error), file=sys.stderr); return 2
    print(encode(result).decode(), end=""); return 0


if __name__ == "__main__": raise SystemExit(main())
