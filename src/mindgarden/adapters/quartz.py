#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT
# pylint: disable=too-many-arguments,too-many-locals
# ruff: noqa: PLR0913, T201, TRY003

"""Render a Mindgarden projection with an immutable Quartz checkout."""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
import json
from pathlib import Path
import shutil
import subprocess  # nosec B404
import sys
from typing import Any

# Commands use validated argument vectors and never invoke a shell.

from .publishing import (
    DEFAULT_OUTPUT_PATH,
    DEFAULT_PROFILE_PATH,
    load_publish_profile,
    project_garden,
)
from ..domain.validation import ContractError


DEFAULT_ENGINE_PATH = Path(".cache/mindgarden/quartz")
DEFAULT_SITE_PATH = Path(".cache/mindgarden/site")
ENGINE_MARKER = Path(".mindgarden-quartz-cache.json")
DISTINCT_CACHE_DIRECTORY_COUNT = 3
MAXIMUM_PORT = 65_535


def accessible_navigation(html: str) -> str:
    """Keep Quartz's article hooks while adding a main landmark and skip target."""
    import re

    html, articles = re.subn(
        r"<article(?=[ >])",
        '<article role="main" id="mindgarden-main" tabindex="-1"',
        html,
        count=1,
    )
    html, bodies = re.subn(
        r"(<body(?: [^>]*)?>)",
        r'\1<a class="mindgarden-skip-link" href="#mindgarden-main">Skip to garden content</a>',
        html,
        count=1,
    )
    if articles != 1 or bodies != 1:
        raise ContractError("SITE_RENDERER: pinned page lacks the expected article/body landmarks")
    pending, replacements = None, []
    for match in re.finditer(r"<(?:button|ul)\b[^>]*>", html):
        classes = re.search(r'class="([^"]*)"', match[0])
        names = classes[1].split() if classes else []
        if "toc-header" in names:
            pending = match
        elif "toc-content" in names and pending is not None:
            target = re.search(r'\bid="([^"]+)"', match[0])
            if target:
                fixed = re.sub(r'aria-controls="[^"]*"', 'aria-controls="' + target[1] + '"', pending[0])
                replacements.append((pending.start(), pending.end(), fixed))
            pending = None
    for start, end, fixed in reversed(replacements):
        html = html[:start] + fixed + html[end:]
    return html


def canonical_navigation(html: str, path: str, base_path: str) -> str:
    """Make native Quartz links work on ordinary static servers without rewrites."""
    from html import escape, unescape
    import re
    from urllib.parse import urljoin, urlsplit, urlunsplit

    def replace(match):
        raw = unescape(match[1])
        if raw.startswith("#"):
            return match[0]
        parts = urlsplit(raw)
        if parts.scheme or parts.netloc:
            return match[0]
        target = urlsplit(urljoin(base_path + path, raw))
        if not target.path.startswith(base_path):
            return match[0]
        route = target.path
        if route.endswith(("/index", "/index.html")):
            route = route.rsplit("/", 1)[0] + "/"
        elif route == base_path + "relationships":
            route += ".html"
        if route == target.path:
            return match[0]
        return 'href="' + escape(urlunsplit(("", "", route, target.query, target.fragment)), quote=True) + '"'

    return re.sub(r'href="([^"]*)"', replace, html)


def render_public_site(projection, engine_root: Path) -> dict[str, bytes]:
    """Render only generated reviewed content; keep subprocess logs private."""
    from html import escape
    import os
    import re
    import stat
    import tempfile

    from ..domain.contracts import canonical_json, strict_json
    from ..domain.site import SITE_MARKER
    from .site_files import read_site

    settings = projection.settings
    profile = {"quartz_repository": settings["repository"], "quartz_commit": settings["commit"]}
    for executable in ("git", "node", "npm"):
        require_executable(executable)
    if node_major_version() != settings["node_major"]:
        raise ContractError("SITE_RENDERER: selected renderer requires its declared Node major")
    engine_root.parent.mkdir(parents=True, exist_ok=True)
    log_path = engine_root.parent / ".mindgarden-renderer.log"
    from ..domain.contracts import safe_path
    safe_path(engine_root.parent, "npm")
    if log_path.is_symlink():
        raise ContractError("SITE_PATH: renderer logs must not cross symlinks")
    if log_path.exists() and (not stat.S_ISREG(log_path.stat().st_mode) or log_path.stat().st_nlink != 1):
        raise ContractError("SITE_PATH: renderer logs must be ordinary owned files")

    def quiet_command(arguments, *, cwd=None):
        try:
            descriptor = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)
            with os.fdopen(descriptor, "ab") as log:
                info = os.fstat(log.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    raise ContractError("SITE_PATH: renderer logs must be ordinary owned files")
                subprocess.run(arguments, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, check=True,
                               env={**os.environ, "npm_config_offline": "true", "npm_config_audit": "false"})
        except (OSError, subprocess.CalledProcessError) as error:
            raise ContractError("SITE_RENDERER: prepared offline renderer failed; inspect the private owned renderer log") from error

    try:
        observed = subprocess.run(["git", "rev-parse", "HEAD"], cwd=engine_root, check=True, capture_output=True, text=True).stdout.strip()
        clean = subprocess.run(["git", "diff", "--quiet", "HEAD"], cwd=engine_root, capture_output=True).returncode == 0
        tracked = subprocess.run(["git", "ls-files", "-z"], cwd=engine_root, check=True, capture_output=True).stdout.decode().split("\x00")
        if observed != profile["quartz_commit"] or not clean:
            raise ContractError("SITE_RENDERER: prepared renderer must match the exact clean reviewed commit")
    except (OSError, subprocess.CalledProcessError) as error:
        raise ContractError("SITE_RENDERER: prepare the pinned renderer and offline package cache separately") from error
    # Quartz honors ancestor .gitignore files. Put its scratch inputs outside
    # ignored repository caches so a valid projection is not silently empty.
    with tempfile.TemporaryDirectory(prefix="mindgarden-render-") as temporary:
        from ..domain.contracts import safe_path

        root = Path(temporary)
        engine = root / "engine"; engine.mkdir()
        for name in tracked:
            if not name:
                continue
            source = safe_path(engine_root, name)
            if not source.is_file() or source.stat().st_nlink != 1:
                raise ContractError("SITE_RENDERER: prepared renderer files must be ordinary immutable inputs")
            target = safe_path(engine, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        (engine / "quartz.config.yaml").write_bytes(projection.configuration)
        content = root / "content"; content.mkdir()
        for name, data in projection.files.items():
            if name in {SITE_MARKER, "quartz.config.yaml"} or not name.endswith(".md"):
                continue
            target = content / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
        output = root / "site"
        quiet_command(["npm", "ci", "--offline", "--ignore-scripts", "--no-audit", "--no-fund", "--cache", str(engine_root.parent / "npm")], cwd=engine)
        quiet_command(["node", "quartz/bootstrap-cli.mjs", "build", "--directory", str(content), "--output", str(output)], cwd=engine)
        files = read_site(output)
    from urllib.parse import urlsplit
    base_path = urlsplit(projection.manifest["base_uri"]).path
    for name, content in projection.files.items():
        if name.startswith("static/mindgarden/"):
            files[name] = content
    for name in list(files):
        if name.endswith(".html"):
            html = canonical_navigation(accessible_navigation(files[name].decode("utf8")), name, base_path)
            html = html.replace('<link rel="preconnect" href="https://cdnjs.cloudflare.com" crossorigin="anonymous"/>', "")
            html = html.replace("</head>", '<link rel="stylesheet" href="' + base_path + 'static/mindgarden/site.css"/>'
                + ('<link rel="stylesheet" href="' + base_path + 'static/mindgarden/theme.css"/>' if "static/mindgarden/theme.css" in files else '')
                + '<script id="mindgarden-graph-script" defer src="' + base_path + 'static/mindgarden/graph.js"></script></head>')
            files[name] = html.encode("utf8")
    canonical = {"index.html": projection.manifest["base_uri"], "relationships.html": projection.manifest["base_uri"] + "relationships.html",
                 **{item["path"]: item["url"] for item in projection.manifest["routes"]}}
    for name, url in canonical.items():
        if name not in files:
            raise ContractError("SITE_RENDERER: renderer did not produce every selected canonical route")
        html = files[name].decode("utf8")
        html = re.sub(r'(<meta property="(?:og:url|twitter:url)" content=")[^"]*(")', lambda match: match[1] + escape(url, quote=True) + match[2], html)
        html = html.replace("</head>", '<link rel="canonical" href="' + escape(url, quote=True) + '"/></head>')
        files[name] = html.encode("utf8")
    # Quartz's index supplies an invented current date when no date transformer
    # exists. Omit that generated field instead of manufacturing source history.
    index_path = "static/contentIndex.json"
    if index_path in files:
        index = strict_json(files[index_path])
        for item in index.values():
            item.pop("date", None)
        files[index_path] = canonical_json(index)
    urls = [canonical[name] for name in sorted(canonical)]
    files["sitemap.xml"] = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join("<url><loc>" + escape(url) + "</loc></url>\n" for url in urls) + "</urlset>\n").encode()
    files["robots.txt"] = ("User-agent: *\nAllow: /\nSitemap: " + projection.manifest["base_uri"] + "sitemap.xml\n").encode()
    return files


def run_command(arguments: list[str], *, cwd: Path | None = None) -> None:
    """Run one external command without a shell."""
    print("$ " + " ".join(arguments))
    subprocess.run(arguments, cwd=cwd, check=True)  # noqa: S603  # nosec B603


def require_executable(name: str) -> None:
    """Require one executable used by the adapter."""
    if shutil.which(name) is None:
        raise ContractError(f"required executable is unavailable: {name}")


def node_major_version() -> int:
    """Read the active Node.js major version."""
    node_path = shutil.which("node")
    if node_path is None:
        raise ContractError("required executable is unavailable: node")
    result = subprocess.run(  # noqa: S603  # nosec B603
        [node_path, "--version"],
        check=True,
        capture_output=True,
        encoding="utf8",
    )
    match = result.stdout.strip().removeprefix("v").split(".", maxsplit=1)[0]
    if not match.isdecimal():
        raise ContractError(f"could not parse Node.js version: {result.stdout.strip()}")
    return int(match)


def cache_path(repository_root: Path, value: Path, label: str) -> Path:
    """Resolve an adapter cache path beneath `.cache/mindgarden/`."""
    repository = repository_root.resolve()
    candidate = value if value.is_absolute() else repository / value
    resolved = candidate.resolve()
    cache_root = (repository / ".cache" / "mindgarden").resolve()
    try:
        resolved.relative_to(cache_root)
    except ValueError as error:
        raise ContractError(f"{label} must stay beneath {cache_root}: {resolved}") from error
    if resolved == cache_root:
        raise ContractError(f"{label} must not be the shared cache root")
    return resolved


def expected_engine_marker(profile: dict[str, Any]) -> dict[str, str]:
    """Return the ownership metadata for the Quartz cache."""
    return {
        "schema": "mindgarden.quartz-cache/v0",
        "repository": str(profile["quartz_repository"]),
        "commit": str(profile["quartz_commit"]),
    }


def prepare_engine(engine_root: Path, profile: dict[str, Any]) -> None:
    """Prepare a clean, detached Quartz checkout at the configured commit."""
    expected_marker = expected_engine_marker(profile)
    marker_path = engine_root / ENGINE_MARKER
    if engine_root.exists():
        if engine_root.is_symlink() or not marker_path.is_file():
            raise ContractError(
                f"refusing to reuse unowned Quartz cache without {ENGINE_MARKER}: {engine_root}"
            )
        observed = json.loads(marker_path.read_text(encoding="utf8"))
        if observed != expected_marker:
            raise ContractError(
                "Quartz cache pin differs from the publishing profile; remove the "
                f"owned cache and retry: {engine_root}"
            )
    else:
        engine_root.parent.mkdir(parents=True, exist_ok=True)
        run_command(
            [
                "git",
                "clone",
                "--filter=blob:none",
                "--no-checkout",
                str(profile["quartz_repository"]),
                str(engine_root),
            ]
        )

    run_command(
        [
            "git",
            "fetch",
            "--depth=1",
            "origin",
            str(profile["quartz_commit"]),
        ],
        cwd=engine_root,
    )
    run_command(["git", "checkout", "--detach", "--force", "FETCH_HEAD"], cwd=engine_root)
    run_command(["git", "clean", "-ffdx"], cwd=engine_root)
    marker_path.write_text(
        json.dumps(expected_marker, indent=2, sort_keys=True) + "\n",
        encoding="utf8",
        newline="\n",
    )


def render_site(
    repository_root: Path,
    *,
    profile_path: Path,
    content_directory: Path,
    engine_directory: Path,
    output_directory: Path,
    serve: bool,
    port: int,
) -> None:
    """Project canonical notes and invoke the pinned Quartz renderer."""
    repository = repository_root.resolve()
    resolved_profile, profile = load_publish_profile(repository, profile_path)
    for executable in ("git", "node", "npm"):
        require_executable(executable)
    expected_node_major = profile["node_major"]
    observed_node_major = node_major_version()
    if observed_node_major != expected_node_major:
        raise ContractError(
            f"Quartz profile requires Node.js {expected_node_major}; observed {observed_node_major}"
        )

    content_root = cache_path(repository, content_directory, "content directory")
    engine_root = cache_path(repository, engine_directory, "engine directory")
    output_root = cache_path(repository, output_directory, "output directory")
    if len({content_root, engine_root, output_root}) != DISTINCT_CACHE_DIRECTORY_COUNT:
        raise ContractError("content, engine, and output directories must be distinct")

    project_garden(repository, content_root, profile_path)
    prepare_engine(engine_root, profile)
    configuration_path = resolved_profile.parent / "quartz.config.yaml"
    if not configuration_path.is_file() or configuration_path.is_symlink():
        raise ContractError(f"Quartz configuration must be a regular file: {configuration_path}")
    shutil.copyfile(configuration_path, engine_root / "quartz.config.yaml")

    engine_content = engine_root / "content"
    if engine_content.is_symlink():
        raise ContractError(f"Quartz content directory must not be a symlink: {engine_content}")
    if engine_content.exists():
        shutil.rmtree(engine_content)
    shutil.copytree(content_root, engine_content)

    npm_cache = repository / ".cache" / "npm"
    npm_cache.mkdir(parents=True, exist_ok=True)
    run_command(
        ["npm", "ci", "--cache", str(npm_cache), "--prefer-offline"],
        cwd=engine_root,
    )
    command = [
        "node",
        "quartz/bootstrap-cli.mjs",
        "build",
        "--directory",
        "content",
        "--output",
        str(output_root),
        "--verbose",
    ]
    if serve:
        command.extend(["--serve", "--port", str(port)])
    run_command(command, cwd=engine_root)


def build_parser() -> ArgumentParser:
    """Build the Quartz adapter command-line contract."""
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE_PATH)
    parser.add_argument("--content-directory", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--engine-directory", type=Path, default=DEFAULT_ENGINE_PATH)
    parser.add_argument("--output-directory", type=Path, default=DEFAULT_SITE_PATH)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("build", help="Build the static Quartz site")
    serve = commands.add_parser("serve", help="Build and serve the local Quartz preview")
    serve.add_argument("--port", type=int, default=8080)
    return parser


def run(arguments: Namespace) -> int:
    """Execute a parsed Quartz command."""
    port = arguments.port if arguments.command == "serve" else 8080
    if not 1 <= port <= MAXIMUM_PORT:
        raise ContractError("preview port must be between 1 and 65535")
    render_site(
        arguments.repository_root,
        profile_path=arguments.profile,
        content_directory=arguments.content_directory,
        engine_directory=arguments.engine_directory,
        output_directory=arguments.output_directory,
        serve=arguments.command == "serve",
        port=port,
    )
    return 0


def main() -> int:
    """Run the CLI with stable diagnostics."""
    arguments = build_parser().parse_args()
    try:
        return run(arguments)
    except (
        ContractError,
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"Quartz rendering failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
