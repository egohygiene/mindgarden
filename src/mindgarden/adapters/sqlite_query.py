"""Optional SQLite FTS5 cache over an already authorized, versioned index."""

from contextlib import closing, contextmanager
from copy import deepcopy
import os
from pathlib import Path
import shutil

try:
    import sqlite3
except ImportError:  # Some minimal Python builds omit the optional extension.
    sqlite3 = None
import tempfile

from .registry_files import control_path, private_parent
from ..application.agent import tokenize
from ..application.retrieval import rank, record_key
from ..domain.contracts import canonical_json, digest_bytes, read_object
from ..domain.validation import ContractError

MARKER = ".mindgarden-query-store.json"
DATABASE = "query.sqlite"
VERSION = "mindgarden.query-store/v1"
DATABASE_VERSION = 2


def capabilities():
    if sqlite3 is None:
        return {
            "schema": VERSION,
            "adapter": "sqlite-fts5",
            "sqlite_version": None,
            "lexical": False,
            "typed_traversal": False,
            "backlinks": False,
            "vectors": False,
            "encrypted_storage": False,
            "canonical_storage": False,
            "incremental_update": False,
            "schema_migration": False,
            "rebuild": False,
        }
    try:
        with closing(sqlite3.connect(":memory:")) as connection, connection:
            connection.execute("CREATE VIRTUAL TABLE probe USING fts5(tokens)")
        available = True
    except sqlite3.Error:
        available = False
    return {
        "schema": VERSION,
        "adapter": "sqlite-fts5",
        "sqlite_version": sqlite3.sqlite_version,
        "lexical": available,
        "typed_traversal": True,
        "backlinks": True,
        "vectors": False,
        "encrypted_storage": False,
        "canonical_storage": False,
        "incremental_update": available,
        "schema_migration": available,
        "database_version": DATABASE_VERSION,
        "migrate_from": [1],
        "rebuild": True,
    }


def encoded_terms(record):
    terms = set(record["terms"])
    for field in (
        "titleTerms",
        "headingTerms",
        "tagTerms",
        "domainTerms",
        "topicTerms",
    ):
        terms.update(record[field])
    # Hex tokens preserve the reference Unicode/hyphen tokenizer exactly even
    # when SQLite's native tokenization differs. BM25 is not an authority.
    return " ".join("t" + term.encode("utf8").hex() for term in sorted(terms))


class SQLiteQueryStore:
    capabilities = staticmethod(capabilities)

    def __init__(self, directory: Path):
        if sqlite3 is None:
            raise ContractError(
                "QUERY_STORE_UNAVAILABLE: this Python build omits optional SQLite support"
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
                "QUERY_STORE_UNOWNED: retain unknown files; choose a clean private cache"
            )
        marker = read_object(control_path(self.directory / MARKER))
        database = control_path(self.directory / DATABASE)
        if (
            marker.get("schema") != VERSION
            or marker.get("adapter") != "sqlite-fts5"
            or type(marker.get("database_version", 1)) is not int
            or marker.get("database_version", 1) not in {1, DATABASE_VERSION}
            or not database.is_file()
            or database.is_symlink()
            or database.stat().st_size > 64 * 1024 * 1024
        ):
            raise ContractError(
                "QUERY_STORE_INCOMPATIBLE: retain the cache and rebuild into a new owned location"
            )
        if digest_bytes(database.read_bytes()) != marker.get("database_sha256"):
            raise ContractError(
                "QUERY_STORE_CORRUPT: checksum differs; retain and rebuild the disposable cache"
            )
        return marker

    def plan(self, index, scope_sha256):
        if (
            index.get("schema") != "mindgarden.index/v1"
            or index.get("scope_sha256") != scope_sha256
        ):
            raise ContractError(
                "QUERY_STORE_INPUT: require the exact authorized v1 index and scope"
            )
        if (
            index.get("scope", {}).get("persistence") == "encrypted-vault"
            or index.get("scope", {}).get("visibility") == "restricted"
        ):
            raise ContractError(
                "QUERY_STORE_UNAVAILABLE: verified encrypted processing is not supported"
            )
        if not capabilities()["lexical"]:
            raise ContractError("QUERY_STORE_UNAVAILABLE: this SQLite build lacks FTS5")
        before = self.inventory()
        value = {
            "schema": "mindgarden.query-store-plan/v1",
            "adapter": "sqlite-fts5",
            "version": VERSION,
            "scope_sha256": scope_sha256,
            "index_sha256": digest_bytes(canonical_json(index)),
            "before": digest_bytes(canonical_json(before)),
            "operation": "rebuild",
        }
        return {**value, "plan_sha256": digest_bytes(canonical_json(value))}

    @contextmanager
    def writer(self):
        lock = self.directory.parent / (self.directory.name + ".query-store.lock")
        private_parent(lock)
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as error:
            raise ContractError(
                "QUERY_STORE_LOCKED: an owned build or recovery is in progress"
            ) from error
        os.close(descriptor)
        try:
            yield
        finally:
            lock.unlink(missing_ok=True)

    def build(self, index, scope_sha256, reviewed_digest, *, check_live):
        return self._apply(index, scope_sha256, reviewed_digest, check_live=check_live)

    def _apply(
        self,
        index,
        scope_sha256,
        reviewed_digest,
        *,
        check_live,
        operation="rebuild",
        source=None,
    ):
        planner = (
            self.plan
            if operation == "rebuild"
            else self.refresh_plan
            if operation == "refresh"
            else lambda i, s: self.migration_plan(source, i, s)
        )
        with self.writer():
            check_live()
            previous = self.inventory()
            desired = digest_bytes(canonical_json(index))
            if (
                previous
                and previous.get("plan_sha256") == reviewed_digest
                and previous.get("index_sha256") == desired
                and previous.get("scope_sha256") == scope_sha256
                and previous.get("database_version", 1) == DATABASE_VERSION
            ):
                if operation == "migrate":
                    source.load(index, scope_sha256)
                    if previous.get("migration_source_sha256") != digest_bytes(
                        canonical_json(source.inventory())
                    ):
                        raise ContractError(
                            "QUERY_STORE_STALE: migration source changed after application"
                        )
                self.load(index, scope_sha256)
                check_live()
                return {"status": "verified-no-op", "index_sha256": desired}
            plan = planner(index, scope_sha256)
            if plan["plan_sha256"] != reviewed_digest:
                raise ContractError(
                    "QUERY_STORE_STALE: review a fresh plan for the current authorized inputs/cache"
                )
            check_live()
            stage = Path(
                tempfile.mkdtemp(
                    prefix=".query-store-stage-", dir=self.directory.parent
                )
            )
            backup = None
            published = False
            try:
                database = stage / DATABASE
                if operation == "refresh":
                    shutil.copyfile(self.directory / DATABASE, database)
                    self._refresh_database(database, index)
                elif operation == "migrate":
                    shutil.copyfile(source.directory / DATABASE, database)
                    self._migrate_database(database, index)
                else:
                    with closing(sqlite3.connect(database)) as connection, connection:
                        connection.executescript(
                            "CREATE TABLE metadata (id TEXT PRIMARY KEY, value BLOB NOT NULL);"
                            "CREATE TABLE records (id TEXT PRIMARY KEY, value BLOB NOT NULL, content_sha256 TEXT NOT NULL);"
                            "CREATE TABLE edges (source TEXT, target TEXT, type TEXT, value BLOB NOT NULL);"
                            "CREATE INDEX outgoing ON edges(source, type); CREATE INDEX incoming ON edges(target, type);"
                            "CREATE VIRTUAL TABLE lexical USING fts5(id UNINDEXED, tokens, tokenize='ascii');"
                        )
                        connection.execute(
                            "INSERT INTO metadata VALUES (?, ?)",
                            ("index", canonical_json(index)),
                        )
                        for record in index["records"]:
                            identity = record_key(record["reference"])
                            connection.execute(
                                "INSERT INTO records VALUES (?, ?, ?)",
                                (
                                    identity,
                                    canonical_json(record),
                                    digest_bytes(canonical_json(record)),
                                ),
                            )
                            connection.execute(
                                "INSERT INTO lexical VALUES (?, ?)",
                                (identity, encoded_terms(record)),
                            )
                        for edge in index["edges"]:
                            connection.execute(
                                "INSERT INTO edges VALUES (?, ?, ?, ?)",
                                (
                                    edge["source"],
                                    edge["target"],
                                    edge["type"],
                                    canonical_json(edge),
                                ),
                            )
                        connection.execute("PRAGMA user_version=2")
                database.chmod(0o600)
                marker = {
                    "schema": VERSION,
                    "database_version": DATABASE_VERSION,
                    "adapter": "sqlite-fts5",
                    "scope_sha256": scope_sha256,
                    "index_sha256": desired,
                    "database_sha256": digest_bytes(database.read_bytes()),
                    "plan_sha256": reviewed_digest,
                    "publication": "never-exportable",
                }
                if operation == "migrate":
                    marker["migration_source_sha256"] = plan["source_before"]
                (stage / MARKER).write_bytes(canonical_json(marker))
                (stage / MARKER).chmod(0o600)
                SQLiteQueryStore(stage).load(index, scope_sha256)
                check_live()
                if planner(index, scope_sha256) != plan:
                    raise ContractError(
                        "QUERY_STORE_STALE: owned cache changed during preparation"
                    )
                if self.directory.exists():
                    backup = Path(
                        tempfile.mkdtemp(
                            prefix=".query-store-prior-", dir=self.directory.parent
                        )
                    )
                    backup.rmdir()
                    os.replace(self.directory, backup)
                try:
                    os.replace(stage, self.directory)
                    published = True
                except BaseException:
                    if backup is not None:
                        try:
                            os.replace(backup, self.directory)
                        except OSError as error:
                            raise ContractError(
                                "QUERY_STORE_RECOVERY: prior owned cache retained beside the destination; local recovery is required"
                            ) from error
                        backup = None
                    raise
                return {
                    "status": {
                        "rebuild": "rebuilt",
                        "refresh": "refreshed",
                        "migrate": "migrated",
                    }[operation],
                    "index_sha256": desired,
                }
            except sqlite3.Error as error:
                raise ContractError(
                    "QUERY_STORE_UNAVAILABLE: SQLite preparation failed; prior state retained"
                ) from error
            finally:
                if stage.exists():
                    shutil.rmtree(stage)
                if published and backup is not None and backup.exists():
                    shutil.rmtree(backup)

    def refresh_plan(self, index, scope_sha256):
        value = self.plan(index, scope_sha256)
        marker = self.inventory()
        if marker is None:
            raise ContractError("QUERY_STORE_MISSING: build the explicit cache first")
        if marker.get("database_version", 1) != DATABASE_VERSION:
            raise ContractError(
                "QUERY_STORE_INCOMPATIBLE: migrate the known older cache before refresh"
            )
        try:
            with closing(
                sqlite3.connect(
                    (self.directory / DATABASE).as_uri() + "?mode=ro&immutable=1",
                    uri=True,
                )
            ) as connection:
                self._validate_layout(connection, DATABASE_VERSION)
        except sqlite3.Error as error:
            raise ContractError(
                "QUERY_STORE_CORRUPT: retain unreadable cache and rebuild separately"
            ) from error
        value.pop("plan_sha256")
        value["operation"] = "refresh"
        return {**value, "plan_sha256": digest_bytes(canonical_json(value))}

    @staticmethod
    def _validate_layout(connection, database_version):
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        expected = {
            "metadata",
            "records",
            "edges",
            "lexical",
            "lexical_data",
            "lexical_idx",
            "lexical_content",
            "lexical_docsize",
            "lexical_config",
        }
        columns = [row[1] for row in connection.execute("PRAGMA table_info(records)")]
        if (
            tables != expected
            or columns
            != [
                "id",
                "value",
                *(["content_sha256"] if database_version == DATABASE_VERSION else []),
            ]
            or connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type IN ('trigger','view')"
            ).fetchone()
            is not None
        ):
            raise ContractError(
                "QUERY_STORE_INCOMPATIBLE: only the known owned SQLite layout is supported"
            )
        if connection.execute("PRAGMA user_version").fetchone() != (database_version,):
            raise ContractError(
                "QUERY_STORE_INCOMPATIBLE: unsupported database schema version"
            )
        if connection.execute("PRAGMA quick_check").fetchone() != ("ok",):
            raise ContractError("QUERY_STORE_CORRUPT: SQLite integrity audit failed")

    def refresh(self, index, scope_sha256, reviewed_digest, *, check_live):
        return self._apply(
            index,
            scope_sha256,
            reviewed_digest,
            check_live=check_live,
            operation="refresh",
        )

    def migration_plan(self, source, index, scope_sha256):
        value = self.plan(index, scope_sha256)
        if self.directory == source.directory:
            raise ContractError(
                "QUERY_STORE_INPUT: migration needs a separate destination"
            )
        source.load(index, scope_sha256)
        marker = source.inventory()
        if marker.get("database_version", 1) != 1:
            raise ContractError(
                "QUERY_STORE_INCOMPATIBLE: only known version 1 migrates to version 2"
            )
        if self.inventory() is not None:
            raise ContractError(
                "QUERY_STORE_CONFLICT: migration destination must be new"
            )
        value.pop("plan_sha256")
        value.update(
            operation="migrate",
            source_before=digest_bytes(canonical_json(marker)),
            from_database_version=1,
            to_database_version=DATABASE_VERSION,
        )
        return {**value, "plan_sha256": digest_bytes(canonical_json(value))}

    def migrate(self, source, index, scope_sha256, reviewed_digest, *, check_live):
        # Both source and destination are single-writer protected; the original
        # remains byte-identical, including after failure or authority loss.
        with source.writer():
            return self._apply(
                index,
                scope_sha256,
                reviewed_digest,
                check_live=check_live,
                operation="migrate",
                source=source,
            )

    @staticmethod
    def _refresh_database(database, index):
        with closing(sqlite3.connect(database)) as connection, connection:
            desired = {
                record_key(record["reference"]): record for record in index["records"]
            }
            connection.execute("CREATE TEMP TABLE desired_ids (id TEXT PRIMARY KEY)")
            connection.executemany(
                "INSERT INTO desired_ids VALUES (?)",
                [(key,) for key in sorted(desired)],
            )
            existing = dict(
                connection.execute(
                    "SELECT id,content_sha256 FROM records WHERE id IN (SELECT id FROM desired_ids)"
                )
            )
            connection.execute(
                "DELETE FROM records WHERE id NOT IN (SELECT id FROM desired_ids)"
            )
            connection.execute(
                "DELETE FROM lexical WHERE id NOT IN (SELECT id FROM desired_ids)"
            )
            for identity, record in sorted(desired.items()):
                content = canonical_json(record)
                digest = digest_bytes(content)
                if existing.get(identity) == digest:
                    continue
                connection.execute(
                    "INSERT INTO records VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET value=excluded.value,content_sha256=excluded.content_sha256",
                    (identity, content, digest),
                )
                connection.execute("DELETE FROM lexical WHERE id=?", (identity,))
                connection.execute(
                    "INSERT INTO lexical VALUES (?,?)",
                    (identity, encoded_terms(record)),
                )
            desired_edges = {canonical_json(edge): edge for edge in index["edges"]}
            connection.execute(
                "CREATE TEMP TABLE desired_edges (value BLOB PRIMARY KEY)"
            )
            connection.executemany(
                "INSERT INTO desired_edges VALUES (?)",
                [(value,) for value in sorted(desired_edges)],
            )
            connection.execute(
                "DELETE FROM edges WHERE value NOT IN (SELECT value FROM desired_edges)"
            )
            for content, edge in sorted(desired_edges.items()):
                connection.execute(
                    "INSERT INTO edges SELECT ?,?,?,? WHERE NOT EXISTS (SELECT 1 FROM edges WHERE value=?)",
                    (edge["source"], edge["target"], edge["type"], content, content),
                )
            connection.execute(
                "UPDATE metadata SET value=? WHERE id='index'", (canonical_json(index),)
            )
            connection.execute("INSERT INTO lexical(lexical) VALUES('optimize')")
        # Compact only the staged copy. Do not leave removed record blobs in
        # free database pages; the separately owned prior cache is never queried.
        with closing(sqlite3.connect(database)) as connection:
            connection.execute("VACUUM")

    @staticmethod
    def _migrate_database(database, index):
        with closing(sqlite3.connect(database)) as connection, connection:
            connection.execute("ALTER TABLE records ADD COLUMN content_sha256 TEXT")
            for record in index["records"]:
                connection.execute(
                    "UPDATE records SET content_sha256=? WHERE id=?",
                    (
                        digest_bytes(canonical_json(record)),
                        record_key(record["reference"]),
                    ),
                )
            connection.execute("PRAGMA user_version=2")

    def load(self, expected_index, scope_sha256):
        marker = self.inventory()
        if marker is None:
            raise ContractError(
                "QUERY_STORE_MISSING: build this explicit private cache first"
            )
        if marker.get("scope_sha256") != scope_sha256 or marker.get(
            "index_sha256"
        ) != digest_bytes(canonical_json(expected_index)):
            raise ContractError(
                "QUERY_STORE_STALE: cache scope or represented inputs changed; review a rebuild"
            )
        try:
            with (
                closing(
                    sqlite3.connect(
                        (self.directory / DATABASE).as_uri() + "?mode=ro&immutable=1",
                        uri=True,
                    )
                ) as connection,
                connection,
            ):
                database_version = marker.get("database_version", 1)
                if connection.execute("PRAGMA user_version").fetchone() != (
                    database_version,
                ):
                    raise ContractError(
                        "QUERY_STORE_INCOMPATIBLE: unsupported store version; rebuild separately"
                    )
                self._validate_layout(connection, database_version)
                if database_version == DATABASE_VERSION:
                    hashes = list(
                        connection.execute(
                            "SELECT id,content_sha256 FROM records ORDER BY id"
                        )
                    )
                    if hashes != [
                        (record_key(r["reference"]), digest_bytes(canonical_json(r)))
                        for r in sorted(
                            expected_index["records"],
                            key=lambda r: record_key(r["reference"]),
                        )
                    ]:
                        raise ContractError(
                            "QUERY_STORE_CORRUPT: stored row digests differ"
                        )
                stored = connection.execute(
                    "SELECT value FROM metadata WHERE id='index'"
                ).fetchone()[0]
                lexical = list(
                    connection.execute("SELECT id,tokens FROM lexical ORDER BY id")
                )
                records = [
                    row[0]
                    for row in connection.execute(
                        "SELECT value FROM records ORDER BY id"
                    )
                ]
                edges = [
                    row[0]
                    for row in connection.execute(
                        "SELECT value FROM edges ORDER BY source,type,target"
                    )
                ]
                if (
                    lexical
                    != [
                        (record_key(r["reference"]), encoded_terms(r))
                        for r in sorted(
                            expected_index["records"],
                            key=lambda r: record_key(r["reference"]),
                        )
                    ]
                    or stored != canonical_json(expected_index)
                    or records
                    != [
                        canonical_json(r)
                        for r in sorted(
                            expected_index["records"],
                            key=lambda r: record_key(r["reference"]),
                        )
                    ]
                    or edges
                    != [
                        canonical_json(e)
                        for e in sorted(
                            expected_index["edges"],
                            key=lambda e: (e["source"], e["type"], e["target"]),
                        )
                    ]
                ):
                    raise ContractError(
                        "QUERY_STORE_CORRUPT: stored projection differs from the authorized input"
                    )
        except sqlite3.Error as error:
            raise ContractError(
                "QUERY_STORE_CORRUPT: retain unreadable cache; rebuild into a fresh location"
            ) from error
        return deepcopy(expected_index)

    def search(self, expected_index, scope_sha256, query):
        if not isinstance(query, str) or len(query.encode("utf8")) > 4096:
            raise ContractError(
                "QUERY_STORE_BUDGET: query exceeds the explicit adapter bound"
            )
        index = self.load(expected_index, scope_sha256)
        terms = sorted(set(tokenize(query)))
        if len(terms) > 64:
            raise ContractError("QUERY_STORE_BUDGET: too many distinct lexical terms")
        if terms:
            expression = " OR ".join(
                '"t' + term.encode("utf8").hex() + '"' for term in terms
            )
            with (
                closing(
                    sqlite3.connect(
                        (self.directory / DATABASE).as_uri() + "?mode=ro&immutable=1",
                        uri=True,
                    )
                ) as connection,
                connection,
            ):
                selected = {
                    row[0]
                    for row in connection.execute(
                        "SELECT id FROM lexical WHERE lexical MATCH ?", (expression,)
                    )
                }
            index["records"] = [
                r for r in index["records"] if record_key(r["reference"]) in selected
            ]
        return rank(index, query)

    def traverse(self, expected_index, scope_sha256, start, depth, limit):
        index = self.load(expected_index, scope_sha256)
        if type(depth) is not int or depth < 0 or type(limit) is not int or limit < 1:
            raise ContractError("QUERY_STORE_BUDGET: invalid traversal bounds")
        available = {record_key(r["reference"]) for r in index["records"]}
        selected = {start} if start in available else set()
        frontier = set(selected)
        for _ in range(depth):
            adjacent = set()
            for edge in index["edges"]:
                if edge["source"] in frontier:
                    adjacent.add(edge["target"])
                if not edge["directed"] and edge["target"] in frontier:
                    adjacent.add(edge["source"])
            frontier = set(sorted(adjacent - selected)[: max(0, limit - len(selected))])
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
        return index["backlinks"].get(target, [])

    def backup(self, expected_index, scope_sha256):
        index = self.load(expected_index, scope_sha256)
        return {
            "schema": "mindgarden.query-store-backup/v1",
            "adapter": "sqlite-fts5",
            "version": VERSION,
            "scope_sha256": scope_sha256,
            "index_sha256": digest_bytes(canonical_json(index)),
            "index": index,
            "publication": "never-exportable",
        }

    def reset(self, expected_before, *, check_live):
        with self.writer():
            marker = self.inventory()
            if (
                marker is None
                or digest_bytes(canonical_json(marker)) != expected_before
            ):
                raise ContractError("QUERY_STORE_STALE: owned reset inventory changed")
            destination = self.directory.with_name(
                self.directory.name + ".retired-" + expected_before[:16]
            )
            if destination.exists():
                raise ContractError(
                    "QUERY_STORE_CONFLICT: prior recovery state already exists; retain both"
                )
            check_live()
            os.rename(self.directory, destination)
            return {"status": "quarantined", "recovery_id": expected_before[:16]}
