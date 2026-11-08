"""Removable Cozo 0.7.6 experiment over already-authorized Garden indexes.

Not a default adapter. No source discovery, policy authority or native vectors.
"""

from contextlib import closing
from copy import deepcopy
import importlib.metadata
import os
from pathlib import Path
import shutil
import tempfile

from mindgarden.adapters.registry_files import control_path
from mindgarden.adapters.sqlite_query import SQLiteQueryStore
from mindgarden.application.agent import tokenize
from mindgarden.application.retrieval import rank, record_key
from mindgarden.domain.contracts import canonical_json, digest_bytes, read_object
from mindgarden.domain.validation import ContractError

try:
    from cozo_embedded import CozoDbPy
except ImportError:
    CozoDbPy = None

VERSION = "mindgarden.cozo-experiment/v1"
MARKER = ".mindgarden-cozo.json"
DATABASE = "cozo.sqlite"
NATIVE_VERSION = "0.7.6"


def capabilities():
    available = (
        CozoDbPy is not None
        and importlib.metadata.version("cozo-embedded") == NATIVE_VERSION
    )
    return {
        "schema": VERSION,
        "adapter": "cozo-embedded",
        "native_version": NATIVE_VERSION,
        "available": available,
        "lexical": available,
        "typed_traversal": available,
        "backlinks": available,
        "vectors": False,
        "native_fts": False,
        "encrypted_storage": False,
        "canonical_storage": False,
        "incremental_update": False,
        "rebuild": available,
        "multi_writer": False,
    }


def expected_relations(index):
    records = sorted(index["records"], key=lambda r: record_key(r["reference"]))
    postings = []
    for record in records:
        terms = set(record["terms"])
        for field in (
            "titleTerms",
            "headingTerms",
            "tagTerms",
            "domainTerms",
            "topicTerms",
        ):
            terms.update(record[field])
        postings += [[term, record_key(record["reference"])] for term in sorted(terms)]
    return {
        "metadata": {
            "headers": ["id", "payload"],
            "rows": [["index", canonical_json(index).decode()]],
        },
        "records": {
            "headers": ["id", "payload"],
            "rows": [
                [record_key(r["reference"]), canonical_json(r).decode()]
                for r in records
            ],
        },
        "postings": {"headers": ["term", "id"], "rows": sorted(postings)},
        "edges": {
            "headers": [
                "position",
                "source",
                "target",
                "edge_type",
                "directed",
                "payload",
            ],
            "rows": [
                [
                    n,
                    e["source"],
                    e["target"],
                    e["type"],
                    e["directed"],
                    canonical_json(e).decode(),
                ]
                for n, e in enumerate(index["edges"])
            ],
        },
        "links": {
            "headers": ["target", "position", "payload"],
            "rows": [
                [target, n, canonical_json(link).decode()]
                for target, links in sorted(index["backlinks"].items())
                for n, link in enumerate(links)
            ],
        },
    }


class CozoQueryStore(SQLiteQueryStore):
    """Reuses only the core owned writer lock and quarantine-reset protocol."""

    capabilities = staticmethod(capabilities)

    def __init__(self, directory: Path):
        if not capabilities()["available"]:
            raise ContractError(
                "COZO_UNAVAILABLE: install the pinned optional experiment separately"
            )
        self.directory = directory
        control_path(directory / MARKER)

    def inventory(self):
        if not self.directory.exists():
            return None
        if not self.directory.is_dir() or set(
            p.name for p in self.directory.iterdir()
        ) != {MARKER, DATABASE}:
            raise ContractError(
                "COZO_UNOWNED: unknown files are retained; select a fresh cache"
            )
        marker = read_object(control_path(self.directory / MARKER))
        path = control_path(self.directory / DATABASE)
        if (
            marker.get("schema") != VERSION
            or marker.get("native_version") != NATIVE_VERSION
            or not path.is_file()
            or path.stat().st_size > 64 * 1024 * 1024
        ):
            raise ContractError(
                "COZO_INCOMPATIBLE: retain prior state and rebuild separately"
            )
        if digest_bytes(path.read_bytes()) != marker.get("database_sha256"):
            raise ContractError(
                "COZO_CORRUPT: checksum failed; retain cache and rebuild separately"
            )
        return marker

    def plan(self, index, scope_sha256):
        if (
            index.get("schema") != "mindgarden.index/v1"
            or index.get("scope_sha256") != scope_sha256
            or len(index["records"]) > 10000
        ):
            raise ContractError(
                "COZO_INPUT: require the bounded exact authorized projection and scope"
            )
        if (
            index["scope"]["visibility"] == "restricted"
            or index["scope"]["persistence"] == "encrypted-vault"
        ):
            raise ContractError(
                "COZO_POLICY: confidential processing is not supported by this experiment"
            )
        value = {
            "schema": VERSION,
            "scope_sha256": scope_sha256,
            "index_sha256": digest_bytes(canonical_json(index)),
            "before": digest_bytes(canonical_json(self.inventory())),
            "operation": "rebuild",
        }
        return {**value, "plan_sha256": digest_bytes(canonical_json(value))}

    def build(self, index, scope_sha256, reviewed_digest, *, check_live):
        with self.writer():
            plan = self.plan(index, scope_sha256)
            previous = self.inventory()
            if (
                previous
                and previous.get("plan_sha256") == reviewed_digest
                and previous.get("index_sha256") == plan["index_sha256"]
                and previous.get("scope_sha256") == scope_sha256
            ):
                self.load(index, scope_sha256)
                check_live()
                return {"status": "verified-no-op"}
            if plan["plan_sha256"] != reviewed_digest:
                raise ContractError("COZO_STALE: review current inputs and cache")
            check_live()
            stage = Path(
                tempfile.mkdtemp(prefix=".cozo-stage-", dir=self.directory.parent)
            )
            prior = None
            try:
                with closing(CozoDbPy("sqlite", str(stage / DATABASE), "{}")) as db:
                    for script in (
                        ":create metadata {id: String => payload: String}",
                        ":create records {id: String => payload: String}",
                        ":create postings {term: String, id: String}",
                        ":create edges {position: Int => source: String, target: String, edge_type: String, directed: Bool, payload: String}",
                        ":create links {target: String, position: Int => payload: String}",
                    ):
                        db.run_script(script, {}, False)
                    db.import_relations(expected_relations(index))
                (stage / DATABASE).chmod(0o600)
                marker = {
                    "schema": VERSION,
                    "adapter": "cozo-embedded",
                    "native_version": NATIVE_VERSION,
                    "scope_sha256": scope_sha256,
                    "index_sha256": plan["index_sha256"],
                    "plan_sha256": reviewed_digest,
                    "database_sha256": digest_bytes((stage / DATABASE).read_bytes()),
                    "publication": "never-exportable",
                }
                (stage / MARKER).write_bytes(canonical_json(marker))
                (stage / MARKER).chmod(0o600)
                check_live()
                if self.plan(index, scope_sha256) != plan:
                    raise ContractError("COZO_STALE: cache changed during preparation")
                if self.directory.exists():
                    prior = Path(
                        tempfile.mkdtemp(
                            prefix=".cozo-prior-", dir=self.directory.parent
                        )
                    )
                    prior.rmdir()
                    os.replace(self.directory, prior)
                try:
                    os.replace(stage, self.directory)
                except BaseException:
                    if prior:
                        os.replace(prior, self.directory)
                        prior = None
                    raise
                return {"status": "rebuilt"}
            except ContractError:
                raise
            except Exception as error:
                raise ContractError(
                    "COZO_UNAVAILABLE: native preparation failed; prior state retained"
                ) from error
            finally:
                if stage.exists():
                    shutil.rmtree(stage)
                if prior and prior.exists():
                    shutil.rmtree(prior)

    def load(self, expected_index, scope_sha256):
        marker = self.inventory()
        if marker is None:
            raise ContractError("COZO_MISSING: build an explicit owned cache first")
        if marker["scope_sha256"] != scope_sha256 or marker[
            "index_sha256"
        ] != digest_bytes(canonical_json(expected_index)):
            raise ContractError("COZO_STALE: represented scope or inputs differ")
        try:
            with closing(
                CozoDbPy("sqlite", str(self.directory / DATABASE), "{}")
            ) as db:
                actual = db.export_relations(list(expected_relations(expected_index)))
            if any(v.get("next") is not None for v in actual.values()) or {
                name: {k: v[k] for k in ("headers", "rows")}
                for name, v in actual.items()
            } != expected_relations(expected_index):
                raise ContractError(
                    "COZO_CORRUPT: native relations differ from the authorized input"
                )
        except ContractError:
            raise
        except Exception as error:
            raise ContractError(
                "COZO_CORRUPT: retain unreadable cache; rebuild separately"
            ) from error
        return deepcopy(expected_index)

    def search(self, expected_index, scope_sha256, query):
        if not isinstance(query, str) or len(query.encode()) > 4096:
            raise ContractError("COZO_BUDGET: query exceeds the experiment bound")
        terms = sorted(set(tokenize(query)))
        if len(terms) > 64:
            raise ContractError("COZO_BUDGET: too many lexical terms")
        index = self.load(expected_index, scope_sha256)
        if terms:
            selected = set()
            with closing(
                CozoDbPy("sqlite", str(self.directory / DATABASE), "{}")
            ) as db:
                for term in terms:
                    selected.update(
                        row[0]
                        for row in db.run_script(
                            "?[id] := *postings{term: $term, id}", {"term": term}, True
                        )["rows"]
                    )
            index["records"] = [
                r for r in index["records"] if record_key(r["reference"]) in selected
            ]
        return rank(index, query)

    def traverse(self, expected_index, scope_sha256, start, depth, limit):
        index = self.load(expected_index, scope_sha256)
        if (
            type(depth) is not int
            or not 0 <= depth <= 100
            or type(limit) is not int
            or not 1 <= limit <= 10000
        ):
            raise ContractError("COZO_BUDGET: unsupported traversal bound")
        available = {record_key(r["reference"]) for r in index["records"]}
        selected = {start} if start in available else set()
        frontier = set(selected)
        with closing(CozoDbPy("sqlite", str(self.directory / DATABASE), "{}")) as db:
            for _ in range(depth):
                adjacent = set()
                for node in frontier:
                    adjacent.update(
                        row[0]
                        for row in db.run_script(
                            "?[target] := *edges{source: $node, target}",
                            {"node": node},
                            True,
                        )["rows"]
                    )
                    adjacent.update(
                        row[0]
                        for row in db.run_script(
                            "?[source] := *edges{source, target: $node, directed: false}",
                            {"node": node},
                            True,
                        )["rows"]
                    )
                frontier = set(
                    sorted((adjacent & available) - selected)[
                        : max(0, limit - len(selected))
                    ]
                )
                selected |= frontier
        return {
            "nodes": [
                r for r in index["records"] if record_key(r["reference"]) in selected
            ],
            "edges": [
                e
                for e in index["edges"]
                if e["source"] in selected and e["target"] in selected
            ],
        }

    def backlinks(self, expected_index, scope_sha256, target):
        index = self.load(expected_index, scope_sha256)
        from mindgarden.domain.contracts import strict_json

        with closing(CozoDbPy("sqlite", str(self.directory / DATABASE), "{}")) as db:
            rows = db.run_script(
                "?[position, payload] := *links{target: $target, position, payload}",
                {"target": target},
                True,
            )["rows"]
        result = [strict_json(payload) for _, payload in rows]
        if result != index["backlinks"].get(target, []):
            raise ContractError("COZO_STALE: cache changed during native lookup")
        return result

    def backup(self, expected_index, scope_sha256):
        index = self.load(expected_index, scope_sha256)
        return {
            "schema": "mindgarden.query-store-backup/v1",
            "adapter": "cozo-embedded",
            "version": VERSION,
            "scope_sha256": scope_sha256,
            "index_sha256": digest_bytes(canonical_json(index)),
            "index": index,
            "publication": "never-exportable",
        }
