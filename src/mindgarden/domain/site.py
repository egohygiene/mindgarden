"""Portable, public site artifacts and explicit renderer capabilities."""

from __future__ import annotations

import json
from pathlib import PurePosixPath
import re

from .contracts import ContractRegistry, canonical_json, digest_bytes, strict_json
from .federation import file_entry, public_url
from .validation import ContractError

SITE_MARKER = ".mindgarden-site.json"
QUARTZ_COMMIT = "075afd3f712da0088a07f5284a7b3aba37dd61b6"
QUARTZ_REPOSITORY = "https://github.com/jackyzha0/quartz.git"
MAX_SITE_BYTES = 64_000_000
MAX_SITE_FILE_BYTES = 16_000_000
MAX_SITE_FILES = 3000


def literal(value: str) -> str:
    """Keep reviewed Markdown, HTML and instruction-bearing text as inert data."""
    runs = [len(match.group()) for match in re.finditer(r"`+", value)]
    fence = "`" * max(3, max(runs, default=0) + 1)
    return fence + "text\n" + value.rstrip() + "\n" + fence + "\n"


def label(value: str) -> str:
    return re.sub(r"([\\`*_{}\[\]()#+.!|<>~])", r"\\\1", value.replace("\n", " ").replace("\r", " "))


def frontmatter(title: str, *, tags: list[str], description: str) -> str:
    # JSON scalar/list syntax is a deterministic subset of YAML.
    return "---\n" + "\n".join(name + ": " + json.dumps(value, ensure_ascii=False)
        for name, value in (("title", title), ("description", description), ("tags", tags),
                            ("draft", False), ("review", "approved"))) + "\n---\n\n"


def content_files(descriptor: dict, index: dict, graph: dict, settings: dict) -> tuple[dict[str, bytes], list[dict]]:
    base = public_url(descriptor["base_uri"], base=True)
    records = {item["reference"]["id"]: item for item in index["records"]}
    routes = []
    files = {}
    home = frontmatter(settings["title"], tags=[], description=settings["description"])
    home += "# Reviewed knowledge\n\n" + label(settings["description"]) + "\n\n"
    home += "[[relationships|Explore typed relationships]]\n\n"
    if not records:
        home += "No reviewed notes have been selected yet. Add public knowledge, review it, and select it in a site profile.\n"
    for identity, record in sorted(records.items()):
        tags = record["tags"] + ["domain/" + value for value in record["domains"]] + ["topic/" + value for value in record["topics"]]
        if any(not re.fullmatch(r"[a-z0-9]+(?:[-/][a-z0-9]+)*", tag) for tag in tags):
            raise ContractError("SITE_TAG: use portable lowercase tag segments for this adapter")
        path = "notes/" + identity + "/index.md"
        title = label(record["title"])
        home += f"- [[notes/{identity}/index|{label(identity)}]] — {title}\n"
        page = frontmatter(record["title"], tags=sorted(set(tags)), description="Reviewed " + record["kind"] + " with exact evidence.")
        page += "Reviewed · " + label(record["kind"]) + " · confidence " + str(record["confidence"]) + "\n\n"
        page += "## Content\n\n" + literal(record["content"])
        page += "\n## Relationships\n\n"
        relations = []
        for edge in graph["edges"]:
            source, target = edge["source"]["id"], edge["target"]["id"]
            if source == identity:
                relations.append((edge["type"], target, "outbound"))
            if target == identity:
                relations.append((edge["type"], source, "backlink"))
        if record["subject"] is not None:
            relations.append(("subject", record["subject"]["id"], "outbound"))
        page += "".join(f"- {direction} · {kind}: [[notes/{other}/index|{other}]]\n"
                        for kind, other, direction in sorted(set(relations))) or "No selected relationships.\n"
        page += "\n## Exact evidence\n\n"
        for source in record["sources"]:
            page += literal(json.dumps(source, ensure_ascii=False, sort_keys=True)) + "\n"
        if not record["sources"]:
            page += "No source citation is declared for this selected record.\n"
        page += "\n## Review qualifications\n\n" + literal(json.dumps(record["qualifications"], ensure_ascii=False, sort_keys=True))
        page += "\n## Represented record\n\n" + literal(json.dumps(record["reference"], sort_keys=True))
        files[path] = page.encode("utf8")
        routes.append({"reference": record["reference"], "url": record["canonical_url"], "path": "notes/" + identity + "/index.html"})
    files["index.md"] = home.encode("utf8")
    if records:
        files["notes/index.md"] = (frontmatter("Selected notes", tags=[], description="Reviewed public notes.")
            + "\n".join(f"- [[notes/{identity}/index|{label(record['title'])}]]" for identity, record in sorted(records.items())) + "\n").encode("utf8")
    relationships = frontmatter("Relationships", tags=[], description="Selected reviewed knowledge and typed connections.")
    relationships += ('<section id="mindgarden-graph" aria-label="Interactive relationships">\n'
        '<div class="mindgarden-controls"><button type="button" data-zoom="in">Zoom in</button>'
        '<button type="button" data-zoom="out">Zoom out</button><button type="button" data-zoom="reset">Reset zoom</button></div>\n'
        '<p role="status">Loading the selected public graph. The complete relationship list is below.</p>\n'
        '<svg viewBox="0 0 800 520" role="group" aria-label="Reviewed knowledge nodes and relationships"></svg>\n</section>\n\n')
    relationships += "## Complete relationship list\n\n"
    for identity, record in sorted(records.items()):
        relationships += f"- [[notes/{identity}/index|{identity}]] — {label(record['title'])}\n"
    for edge in graph["edges"]:
        source, target = edge["source"]["id"], edge["target"]["id"]
        relationships += f"- [[notes/{source}/index|{source}]] {edge['type']} [[notes/{target}/index|{target}]]\n"
    if not records:
        relationships += "No reviewed relationships are selected yet.\n"
    files["relationships.md"] = relationships.encode("utf8")
    return files, routes


def artifact_manifest(kind: str, revision: str, base_uri: str, renderer: dict, routes: list[dict], files: dict[str, bytes]) -> dict:
    return {"schema": "mindgarden.site-manifest/v1", "kind": kind, "revision": revision,
            "base_uri": base_uri, "renderer": renderer, "routes": routes,
            "artifacts": [file_entry(path, content) for path, content in sorted(files.items())]}


def verify_site(files: dict[str, bytes], *, expected: dict | None = None) -> dict:
    try:
        if SITE_MARKER not in files or len(files) > MAX_SITE_FILES or sum(map(len, files.values())) > MAX_SITE_BYTES:
            raise ContractError("SITE_BUDGET: site membership or total bytes exceed the supported budget")
        for name, content in files.items():
            path = PurePosixPath(name)
            if (not name or path.is_absolute() or str(path) != name or ".." in path.parts
                    or any(part in {".garden", ".git"} for part in path.parts)
                    or ":" in name or "\\" in name or len(content) > MAX_SITE_FILE_BYTES):
                raise ContractError("SITE_PATH: artifact paths and sizes must be portable and bounded")
        manifest = strict_json(files[SITE_MARKER])
        if ContractRegistry().errors(manifest, "site-manifest"):
            raise ContractError("SITE_INVALID: supported public site manifest required")
        if files[SITE_MARKER] != canonical_json(manifest):
            raise ContractError("SITE_INTEGRITY: manifest serialization differs")
        if manifest["artifacts"] != [file_entry(name, content) for name, content in sorted(files.items()) if name != SITE_MARKER]:
            raise ContractError("SITE_INTEGRITY: complete site membership or checksums differ")
        if public_url(manifest["base_uri"], base=True) != manifest["base_uri"]:
            raise ContractError("SITE_ROUTE: canonical public base URL required")
        for route in manifest["routes"]:
            if route["url"] != manifest["base_uri"] + "notes/" + route["reference"]["id"] + "/":
                raise ContractError("SITE_ROUTE: canonical note route differs")
            target = route["path"].removesuffix(".html") + ".md" if manifest["kind"] == "content" else route["path"]
            if target not in files:
                raise ContractError("SITE_ROUTE: represented note page is missing")
        if expected is not None and any(manifest[field] != expected[field] for field in ("kind", "revision", "base_uri", "renderer", "routes")):
            raise ContractError("SITE_STALE: represented site inputs or renderer differ")
        return manifest
    except ContractError:
        raise
    except (KeyError, TypeError, ValueError, UnicodeError) as error:
        raise ContractError("SITE_INVALID: supplied site is invalid") from error
