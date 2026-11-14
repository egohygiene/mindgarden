"""Reviewed cache updates, known schema migration and retained recovery state."""

from contextlib import closing, redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import sqlite3
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.sqlite_query import (
    DATABASE,
    MARKER,
    VERSION,
    SQLiteQueryStore,
    encoded_terms,
)
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import build_index, rank, record_key
from mindgarden.domain.contracts import (
    ContractRegistry,
    canonical_json,
    digest_bytes,
    read_object,
)
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests import test_query_store as fixtures
from tests.support_v1 import add_knowledge, write_session

ROOT = Path(__file__).parents[1]


def legacy_store(directory, index, scope):
    directory.mkdir(mode=0o700)
    database = directory / DATABASE
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.executescript(
            (ROOT / "tests/fixtures/query-store/legacy-v1.sql.txt").read_text()
        )
        connection.execute(
            "INSERT INTO metadata VALUES (?,?)", ("index", canonical_json(index))
        )
        for record in index["records"]:
            identity = record_key(record["reference"])
            connection.execute(
                "INSERT INTO records VALUES (?,?)", (identity, canonical_json(record))
            )
            connection.execute(
                "INSERT INTO lexical VALUES (?,?)", (identity, encoded_terms(record))
            )
        for edge in index["edges"]:
            connection.execute(
                "INSERT INTO edges VALUES (?,?,?,?)",
                (edge["source"], edge["target"], edge["type"], canonical_json(edge)),
            )
    database.chmod(0o600)
    (directory / MARKER).write_bytes(
        canonical_json(
            {
                "schema": VERSION,
                "adapter": "sqlite-fts5",
                "scope_sha256": scope,
                "index_sha256": digest_bytes(canonical_json(index)),
                "database_sha256": digest_bytes(database.read_bytes()),
                "plan_sha256": "0" * 64,
                "publication": "never-exportable",
            }
        )
    )
    (directory / MARKER).chmod(0o600)
    return SQLiteQueryStore(directory)


def inventory(directory):
    return {
        path.name: path.read_bytes() for path in directory.iterdir() if path.is_file()
    }


class QueryStoreEvolutionTests(unittest.TestCase):
    def setUp(self):
        fixtures.QueryStoreTests.setUp(self)

    def build(self):
        return fixtures.QueryStoreTests.build(self)

    def cli(self, operation, *extra):
        args = [
            "query-store",
            "--local-config",
            str(self.configuration),
            "--scope",
            str(self.session_path),
            "--cache-directory",
            str(self.directory),
            "--operation",
            operation,
            *extra,
        ]
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(args), 0)
        return json.loads(output.getvalue())

    def test_actual_canonical_change_and_renewed_authority_refresh_through_cli(self):
        self.build()
        added = add_knowledge(
            self.workspace,
            "fresh-note",
            body="Fresh renewal procedure.\n",
            sources=self.index["records"][0]["sources"],
        )
        write_session(self.session_path, self.configuration)
        current = QueryContext.load(self.configuration, self.session_path)
        index = build_index(current)
        self.assertNotEqual(current.scope_digest(), self.scope)
        with patch("socket.socket", side_effect=AssertionError("Network attempted")):
            plan = self.cli("refresh-plan")
            self.assertEqual(ContractRegistry().errors(plan, "query-store-plan"), [])
            self.assertEqual(
                self.cli("refresh", "--plan-digest", plan["plan_sha256"])["status"],
                "refreshed",
            )
            self.assertEqual(
                self.cli("search", "--query", "fresh")["results"], rank(index, "fresh")
            )
            self.assertEqual(
                self.cli("refresh", "--plan-digest", plan["plan_sha256"])["status"],
                "verified-no-op",
            )
        self.assertEqual(
            read_object(self.workspace / ".garden/knowledge/fresh-note.json"), added
        )
        self.assertEqual(self.store.load(index, current.scope_digest()), index)

    def test_delta_add_update_remove_typed_edges_and_reference_parity(self):
        old = deepcopy(self.index)
        old["records"][0]["content"] = "RETIRED-CACHE-CANARY"
        p = self.store.plan(old, self.scope)
        self.store.build(
            old, self.scope, p["plan_sha256"], check_live=self.context.check_live
        )
        changed = deepcopy(self.index)
        changed["records"][0]["title"] = "Updated prompt"
        changed["edges"] = []
        changed["backlinks"] = {key: [] for key in changed["backlinks"]}
        p = self.store.refresh_plan(changed, self.scope)
        self.assertNotIn(b"CANARY", canonical_json(p))
        self.store.refresh(
            changed, self.scope, p["plan_sha256"], check_live=self.context.check_live
        )
        for query in ("prompt", "procedure", "NOT OR *", ""):
            self.assertEqual(
                self.store.search(changed, self.scope, query), rank(changed, query)
            )
        self.assertEqual(
            self.store.backlinks(changed, self.scope, "synthetic-garden/second-note"),
            [],
        )
        self.assertNotIn(
            b"RETIRED-CACHE-CANARY", (self.directory / DATABASE).read_bytes()
        )
        smaller = deepcopy(changed)
        removed = smaller["records"].pop(0)
        smaller["backlinks"].pop(record_key(removed["reference"]), None)
        p = self.store.refresh_plan(smaller, self.scope)
        self.store.refresh(
            smaller, self.scope, p["plan_sha256"], check_live=self.context.check_live
        )
        self.assertEqual(self.store.load(smaller, self.scope), smaller)
        self.assertNotIn(removed, self.store.search(smaller, self.scope, ""))

    def test_refresh_is_stale_after_review_and_interrupted_replacement_keeps_old_bytes(
        self,
    ):
        self.build()
        before = inventory(self.directory)
        changed = deepcopy(self.index)
        changed["records"][0]["title"] = "changed"
        p = self.store.refresh_plan(changed, self.scope)
        with self.assertRaisesRegex(ContractError, "QUERY_STORE_STALE"):
            self.store.refresh(
                self.index,
                self.scope,
                p["plan_sha256"],
                check_live=self.context.check_live,
            )
        replace = os.replace

        def interrupted(source, target):
            if Path(source).name.startswith(".query-store-stage-"):
                raise OSError("Synthetic replacement interruption")
            return replace(source, target)

        with (
            patch(
                "mindgarden.adapters.sqlite_query.os.replace", side_effect=interrupted
            ),
            self.assertRaises(OSError),
        ):
            self.store.refresh(
                changed,
                self.scope,
                p["plan_sha256"],
                check_live=self.context.check_live,
            )
        self.assertEqual(inventory(self.directory), before)
        self.store.refresh(
            changed, self.scope, p["plan_sha256"], check_live=self.context.check_live
        )
        self.assertEqual(self.store.load(changed, self.scope), changed)

    def test_failed_rollback_retains_prior_cache_for_explicit_recovery(self):
        self.build()
        before = inventory(self.directory)
        changed = deepcopy(self.index)
        changed["records"][0]["title"] = "changed"
        p = self.store.refresh_plan(changed, self.scope)
        replace = os.replace

        def interrupted(source, target):
            if Path(source).name.startswith(
                (".query-store-stage-", ".query-store-prior-")
            ):
                raise OSError("Synthetic replacement and rollback interruption")
            return replace(source, target)

        with (
            patch(
                "mindgarden.adapters.sqlite_query.os.replace", side_effect=interrupted
            ),
            self.assertRaisesRegex(ContractError, "QUERY_STORE_RECOVERY"),
        ):
            self.store.refresh(
                changed,
                self.scope,
                p["plan_sha256"],
                check_live=self.context.check_live,
            )
        (prior,) = self.root.glob(".query-store-prior-*")
        self.assertEqual(inventory(prior), before)
        self.assertEqual(
            SQLiteQueryStore(prior).load(self.index, self.scope), self.index
        )
        self.assertFalse(self.directory.exists())

    def test_legacy_migration_replay_backup_restore_and_original_retention(self):
        source = legacy_store(self.root / "legacy", self.index, self.scope)
        before = inventory(source.directory)
        p = self.store.migration_plan(source, self.index, self.scope)
        self.assertEqual(ContractRegistry().errors(p, "query-store-plan"), [])
        self.assertNotIn(str(self.root), json.dumps(p))
        self.assertEqual(
            self.store.migrate(
                source,
                self.index,
                self.scope,
                p["plan_sha256"],
                check_live=self.context.check_live,
            )["status"],
            "migrated",
        )
        self.assertEqual(
            self.store.migrate(
                source,
                self.index,
                self.scope,
                p["plan_sha256"],
                check_live=self.context.check_live,
            )["status"],
            "verified-no-op",
        )
        self.assertEqual(inventory(source.directory), before)
        self.assertEqual(self.store.inventory()["database_version"], 2)
        backup = self.store.backup(self.index, self.scope)
        restored = SQLiteQueryStore(self.root / "restored")
        p = restored.plan(backup["index"], self.scope)
        restored.build(
            backup["index"],
            self.scope,
            p["plan_sha256"],
            check_live=self.context.check_live,
        )
        self.assertEqual(
            restored.search(self.index, self.scope, "prompt"),
            self.store.search(self.index, self.scope, "prompt"),
        )

    def test_migration_interruption_and_authority_loss_leave_both_inputs_untouched(
        self,
    ):
        source = legacy_store(self.root / "legacy", self.index, self.scope)
        before = inventory(source.directory)
        p = self.store.migration_plan(source, self.index, self.scope)
        with (
            patch.object(
                SQLiteQueryStore,
                "_migrate_database",
                side_effect=sqlite3.OperationalError("Synthetic failure"),
            ),
            self.assertRaisesRegex(ContractError, "QUERY_STORE_UNAVAILABLE"),
        ):
            self.store.migrate(
                source,
                self.index,
                self.scope,
                p["plan_sha256"],
                check_live=self.context.check_live,
            )
        self.assertFalse(self.directory.exists())
        calls = []

        def expire():
            calls.append(True)
            if len(calls) == 3:
                raise ContractError("SESSION_EXPIRED: synthetic expiry")

        with self.assertRaisesRegex(ContractError, "SESSION_EXPIRED"):
            self.store.migrate(
                source, self.index, self.scope, p["plan_sha256"], check_live=expire
            )
        self.assertEqual(inventory(source.directory), before)
        self.assertFalse(self.directory.exists())
        self.store.migrate(
            source,
            self.index,
            self.scope,
            p["plan_sha256"],
            check_live=self.context.check_live,
        )

    def test_unknown_version_corruption_and_unknown_files_are_not_migrated(self):
        source = legacy_store(self.root / "legacy", self.index, self.scope)
        marker = read_object(source.directory / MARKER)
        for version in (99, True):
            (source.directory / MARKER).write_bytes(
                canonical_json({**marker, "database_version": version})
            )
            with self.assertRaisesRegex(ContractError, "QUERY_STORE_INCOMPATIBLE"):
                self.store.migration_plan(source, self.index, self.scope)
        (source.directory / MARKER).write_bytes(canonical_json(marker))
        (source.directory / DATABASE).write_bytes(
            (source.directory / DATABASE).read_bytes() + b"corrupt"
        )
        with self.assertRaisesRegex(ContractError, "QUERY_STORE_CORRUPT"):
            self.store.migration_plan(source, self.index, self.scope)
        (source.directory / "human.txt").write_text("Retain this synthetic file")
        with self.assertRaisesRegex(ContractError, "QUERY_STORE_UNOWNED"):
            self.store.migration_plan(source, self.index, self.scope)
        self.assertFalse(self.directory.exists())

    def test_cli_migrates_an_explicit_known_source_without_modifying_original(self):
        source = legacy_store(self.root / "legacy", self.index, self.scope)
        args = ["--previous-cache-directory", str(source.directory)]
        plan = self.cli("migration-plan", *args)
        before = inventory(source.directory)
        self.assertEqual(
            self.cli("migrate", *args, "--plan-digest", plan["plan_sha256"])["status"],
            "migrated",
        )
        self.assertEqual(inventory(source.directory), before)
        self.assertEqual(self.cli("audit")["status"], "verified")

    def test_plan_schema_rejects_unknown_operations_and_private_extension_fields(self):
        self.build()
        plan = self.store.refresh_plan(self.index, self.scope)
        registry = ContractRegistry()
        for change in (
            {"operation": "execute"},
            {"private_path": "/synthetic/private"},
            {"source_before": "0" * 64},
            {"operation": "migrate"},
        ):
            self.assertTrue(registry.errors({**plan, **change}, "query-store-plan"))

    def test_expired_cli_authority_never_opens_refresh_or_migration_cache(
        self,
    ):
        self.build()
        session = read_object(self.session_path)
        session["expires_at"] = "2000-01-01T00:00:00Z"
        self.session_path.write_bytes(canonical_json(session))
        for operation in ("refresh-plan", "refresh", "migration-plan", "migrate"):
            with (
                patch.object(
                    SQLiteQueryStore,
                    "inventory",
                    side_effect=AssertionError("Cache accessed"),
                ),
                redirect_stderr(io.StringIO()),
            ):
                args = [
                    "query-store",
                    "--local-config",
                    str(self.configuration),
                    "--scope",
                    str(self.session_path),
                    "--cache-directory",
                    str(self.directory),
                    "--operation",
                    operation,
                ]
                self.assertEqual(main(args), 3)

    def test_revoked_cli_authority_never_opens_refresh_or_migration_cache(self):
        self.build()
        session = read_object(self.session_path)
        bindings = read_object(self.configuration)
        bindings["revoked_sessions"] = [session["id"]]
        self.configuration.write_bytes(canonical_json(bindings))
        for operation in ("refresh-plan", "refresh", "migration-plan", "migrate"):
            with (
                patch.object(
                    SQLiteQueryStore,
                    "inventory",
                    side_effect=AssertionError("Cache accessed"),
                ),
                redirect_stderr(io.StringIO()),
            ):
                args = [
                    "query-store",
                    "--local-config",
                    str(self.configuration),
                    "--scope",
                    str(self.session_path),
                    "--cache-directory",
                    str(self.directory),
                    "--operation",
                    operation,
                ]
                self.assertEqual(main(args), 3)
