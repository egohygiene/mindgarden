"""Reviewed v1 knowledge to a replaceable Quartz projection and local preview."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
import sys

from ..adapters.site_files import read_site, write_site
from ..domain.contracts import ContractRegistry, canonical_json, digest_bytes, read_object, safe_path, strict_json
from ..domain.federation import verify_bundle
from ..domain.site import SITE_MARKER, artifact_manifest, content_files, verify_site
from ..domain.validation import ContractError
from .federation import build_federation, export_destination
from .query import QueryContext, authority_bytes


def configuration_template() -> dict:
    return strict_json(profile_resource("v1.config.json"))


def profile_resource(name) -> bytes:
    for root in (Path(__file__).resolve().parents[3] / "profiles/quartz", Path(sys.prefix) / "share/mindgarden/profiles/quartz"):
        path = root / name
        if path.is_file():
            return path.read_bytes()
    raise ContractError("SITE_ADAPTER: install the complete Quartz profile resources")


@dataclass
class SiteProjection:
    bundle: object
    settings: dict
    configuration: bytes
    files: dict[str, bytes]
    manifest: dict
    profile_path: Path | None
    profile_sha256: str

    def check_live(self, context):
        self.bundle.check_live(context)
        if self.profile_path is not None and digest_bytes(authority_bytes(self.profile_path)) != self.profile_sha256:
            raise ContractError("SITE_PLAN_STALE: reviewed site profile changed")

    def destination(self, context, parent):
        return export_destination(context, parent, self.bundle.output_root)

    def plan(self, context, parent, *, operation="project", engine_directory=None):
        self.check_live(context)
        if engine_directory is not None:
            from ..adapters.federation_files import explicit_directory

            root = context.bindings.garden(self.bundle.garden)["root"]
            try:
                if ".." in engine_directory.parts:
                    raise ValueError()
                engine_directory = explicit_directory(engine_directory)
                cache = safe_path(root, ".cache/mindgarden")
                engine_directory.relative_to(cache)
                if engine_directory == cache:
                    raise ValueError()
                engine_directory = export_destination(context, engine_directory.parent, engine_directory.name)
            except (ContractError, ValueError) as error:
                raise ContractError("SITE_ENGINE: use the selected garden's owned .cache/mindgarden directory") from error
        payload = {"schema": "mindgarden.site-plan/v1", "classification": "machine-local-control",
                   "publication": "never-exportable", "operation": operation,
                   "profile_sha256": self.profile_sha256, "authority_sha256": context.scope_digest(),
                   "destination_sha256": digest_bytes(str(self.destination(context, parent)).encode()),
                   "engine_sha256": digest_bytes(str(engine_directory.absolute()).encode()) if engine_directory is not None else None,
                   "revision": self.manifest["revision"], "renderer": self.settings,
                   "configuration_sha256": digest_bytes(self.configuration),
                   "files": self.manifest["artifacts"]}
        return {**payload, "plan_sha256": digest_bytes(canonical_json(payload))}

    def apply(self, context, parent, digest, *, operation="project", engine_directory=None):
        if self.plan(context, parent, operation=operation, engine_directory=engine_directory)["plan_sha256"] != digest:
            raise ContractError("SITE_PLAN_STALE: exact reviewed inputs, authority and destination are required")
        if context.session["writable"] != self.bundle.garden:
            raise ContractError("WRITE_DENIED: site generation requires an explicitly writable garden")
        destination = self.destination(context, parent)
        expected = {**self.manifest, "kind": "content" if operation == "project" else "site"}
        if destination.exists():
            observed = read_site(destination)
            verify_site(observed, expected=expected)
            if operation == "project" and observed != self.files:
                raise ContractError("SITE_OUTPUT_CONFLICT: existing content differs; choose a fresh destination")
            self.check_live(context)
            return False
        files = self.files
        if operation == "build":
            from ..adapters.quartz import render_public_site

            files = render_public_site(self, engine_directory)
            for name in ("garden.json", "index.json", "graph.json", "llms.txt"):
                files[name] = self.bundle.files[name]
            manifest = artifact_manifest("site", self.manifest["revision"], self.manifest["base_uri"], self.settings,
                                         self.manifest["routes"], files)
            files[SITE_MARKER] = canonical_json(manifest)
        self.check_live(context); context.snapshots()
        return write_site(destination, files, check_live=lambda: self.check_live(context), verify_inputs=context.snapshots)


def build_site(context: QueryContext, profile: dict, *, profile_path: Path | None = None) -> SiteProjection:
    settings = profile.get("x-site")
    if ContractRegistry().errors(settings, "site-adapter"):
        raise ContractError("SITE_PROFILE: supply a supported explicit pinned site adapter")
    raw = authority_bytes(profile_path) if profile_path is not None else canonical_json(profile)
    if strict_json(raw) != profile:
        raise ContractError("SITE_PROFILE: reviewed profile bytes differ")
    bundle = build_federation(context, profile, projection_kind="site")
    descriptor, index, graph = verify_bundle(bundle.files)
    files, routes = content_files(descriptor, index, graph, settings)
    configuration = configuration_template()
    configuration["configuration"].update(pageTitle=settings["title"], baseUrl=descriptor["base_uri"].removeprefix("https://").rstrip("/"))
    configuration = canonical_json(configuration)
    files.update({name: content for name, content in bundle.files.items() if not name.startswith(".")})
    files["quartz.config.yaml"] = configuration
    files["static/mindgarden/graph.js"] = profile_resource("v1.graph.js")
    files["static/mindgarden/site.css"] = profile_resource("v1.css")
    revision = "sha256:" + digest_bytes(canonical_json({"base_uri": descriptor["base_uri"], "renderer": settings,
                 "files": [{"path": name, "sha256": digest_bytes(content)} for name, content in sorted(files.items())]}))
    manifest = artifact_manifest("content", revision, descriptor["base_uri"], settings, routes, files)
    files[SITE_MARKER] = canonical_json(manifest)
    verify_site(files)
    return SiteProjection(bundle, deepcopy(settings), configuration, files, manifest, profile_path, digest_bytes(raw))


def run_site(arguments, *, operation):
    if arguments.local_config is None or arguments.scope is None:
        raise ContractError("SCOPE_REQUIRED: v1 publishing requires explicit local bindings and a query session")
    context = QueryContext.load(arguments.local_config, arguments.scope)
    profile = read_object(arguments.profile)
    projection = build_site(context, profile, profile_path=arguments.profile)
    parent = arguments.output_directory
    parent = (parent if parent.is_absolute() else arguments.repository_root / parent).absolute()
    engine = None
    if operation == "build":
        engine = arguments.engine_directory
        engine = (engine if engine.is_absolute() else arguments.repository_root / engine).absolute()
    plan = projection.plan(context, parent, operation=operation, engine_directory=engine)
    if arguments.check:
        expected = {**projection.manifest, "kind": "content" if operation == "project" else "site"}
        manifest = verify_site(read_site(projection.destination(context, parent)), expected=expected)
        projection.check_live(context)
        print(canonical_json(manifest).decode(), end="")
    elif arguments.apply:
        changed = projection.apply(context, parent, arguments.plan_digest, operation=operation, engine_directory=engine)
        print(canonical_json({"schema": "mindgarden.site-application/v1", "applied": changed,
                              "revision": projection.manifest["revision"]}).decode(), end="")
        if arguments.command == "serve":
            from ..adapters.site_files import preview_server
            from urllib.parse import urlsplit

            if not 1 <= arguments.port <= 65535:
                raise ContractError("SITE_PORT: use a port between 1 and 65535")
            with preview_server(projection.destination(context, parent), projection.manifest["base_uri"], arguments.port,
                                check_live=lambda: projection.check_live(context)) as server:
                print("Preview: http://127.0.0.1:" + str(arguments.port) + urlsplit(projection.manifest["base_uri"]).path, flush=True)
                try:
                    server.serve_forever()
                except KeyboardInterrupt:
                    pass
    else:
        print(canonical_json(plan).decode(), end="")
    return 0
