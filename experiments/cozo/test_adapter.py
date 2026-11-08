"""Explicit optional native suite; excluded from the default dependency-free suite."""

from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from experiments.corpus import create_corpus
from experiments.cozo.adapter import (
    CozoQueryStore,
    CozoDbPy,
    MARKER,
    DATABASE,
    expected_relations,
)
from mindgarden.adapters.sqlite_query import SQLiteQueryStore
from mindgarden.application.query_store import run_query_store
from mindgarden.application.retrieval import rank, build_index
from tests.support_v1 import add_knowledge
from mindgarden.domain.contracts import canonical_json, digest_bytes
from mindgarden.domain.validation import ContractError


class CozoTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.corpus = create_corpus(self.root / "corpus", per_garden=2)
        self.context = self.corpus["context"]
        self.index = self.corpus["index"]
        self.scope = self.context.scope_digest()
        self.store = CozoQueryStore(self.root / "cozo")
        self.plan = self.store.plan(self.index, self.scope)
        self.store.build(
            self.index,
            self.scope,
            self.plan["plan_sha256"],
            check_live=self.context.check_live,
        )

    def test_native_lexical_graph_backlinks_and_factory_parity(self):
        sqlite = SQLiteQueryStore(self.root / "sqlite")
        p = sqlite.plan(self.index, self.scope)
        sqlite.build(
            self.index, self.scope, p["plan_sha256"], check_live=self.context.check_live
        )
        with patch("socket.socket", side_effect=AssertionError("Network attempted")):
            for query in (
                "prompt",
                "retirement café",
                "long-term",
                "NOT OR *",
                "日本語",
                "",
                "' ; :delete records",
            ):
                expected = rank(self.index, query)
                self.assertEqual(
                    self.store.search(self.index, self.scope, query), expected
                )
                self.assertEqual(sqlite.search(self.index, self.scope, query), expected)
            for start in (
                "public-alpha/reviewed-prompt",
                "public-alpha/reviewed-reference",
                "personal-gamma/private-canary",
            ):
                self.assertEqual(
                    self.store.traverse(self.index, self.scope, start, 3, 100),
                    sqlite.traverse(self.index, self.scope, start, 3, 100),
                )
                self.assertEqual(
                    self.store.backlinks(self.index, self.scope, start),
                    sqlite.backlinks(self.index, self.scope, start),
                )
        args = SimpleNamespace(
            local_config=self.corpus["configuration"],
            scope=self.corpus["session"],
            operation="search",
            cache_directory=self.store.directory,
            query="retirement",
            limit=3,
        )
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(run_query_store(args, store_factory=CozoQueryStore), 0)
        self.assertEqual(len(json.loads(output.getvalue())["results"]), 3)

    def test_denied_input_overlay_cache_scope_and_revocation(self):
        self.assertNotIn(
            b"denied-financial-canary", (self.store.directory / DATABASE).read_bytes()
        )
        self.assertFalse(
            self.store.search(self.index, self.scope, "denied-financial-canary")
        )
        add_knowledge(
            self.corpus["private_workspace"],
            "private-canary",
            body="changed-denied-canary\n",
        )
        self.assertEqual(build_index(self.context), self.index)
        self.assertFalse(
            self.store.search(self.index, self.scope, "changed-denied-canary")
        )
        with self.assertRaisesRegex(ContractError, "COZO_STALE"):
            self.store.load(
                self.corpus["personal_index"],
                self.corpus["personal_context"].scope_digest(),
            )
        configuration = json.loads(self.corpus["configuration"].read_text())
        configuration["revoked_sessions"] = [self.context.session["id"]]
        self.corpus["configuration"].write_bytes(canonical_json(configuration))
        args = SimpleNamespace(
            local_config=self.corpus["configuration"],
            scope=self.corpus["session"],
            operation="search",
            cache_directory=self.store.directory,
            query="retirement",
            limit=3,
        )
        with patch.object(
            CozoQueryStore,
            "__init__",
            side_effect=AssertionError("Cache opened before authority"),
        ):
            with self.assertRaises(ContractError):
                run_query_store(args, store_factory=CozoQueryStore)

    def test_portable_backup_restore_rebuild_native_backup_and_quarantine(self):
        backup = self.store.backup(self.index, self.scope)
        restored = CozoQueryStore(self.root / "restored")
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
        native = self.root / "native-backup.sqlite"
        db = CozoDbPy("sqlite", str(self.store.directory / DATABASE), "{}")
        db.backup(str(native))
        db.close()
        db = CozoDbPy("mem", "", "{}")
        db.restore(str(native))
        export = db.export_relations(["records"])
        db.close()
        self.assertEqual(
            export["records"]["rows"], expected_relations(self.index)["records"]["rows"]
        )
        self.assertEqual(
            self.store.build(
                self.index,
                self.scope,
                self.plan["plan_sha256"],
                check_live=self.context.check_live,
            )["status"],
            "verified-no-op",
        )
        marker = self.store.inventory()
        self.store.reset(
            digest_bytes(canonical_json(marker)), check_live=self.context.check_live
        )
        self.assertFalse(self.store.directory.exists())
        self.assertTrue(list(self.root.glob("cozo.retired-*")))

    def test_corrupt_foreign_version_unknown_files_and_partial_build_are_retained(self):
        database = self.store.directory / DATABASE
        before = database.read_bytes()
        database.write_bytes(before + b"corruption")
        with self.assertRaisesRegex(ContractError, "COZO_CORRUPT"):
            self.store.load(self.index, self.scope)
        database.write_bytes(before)
        marker = self.store.directory / MARKER
        document = json.loads(marker.read_text())
        document["native_version"] = "future"
        marker.write_bytes(canonical_json(document))
        with self.assertRaisesRegex(ContractError, "COZO_INCOMPATIBLE"):
            self.store.load(self.index, self.scope)
        document["native_version"] = "0.7.6"
        marker.write_bytes(canonical_json(document))
        unexpected = self.store.directory / "unowned"
        unexpected.write_text("retain")
        with self.assertRaisesRegex(ContractError, "COZO_UNOWNED"):
            self.store.inventory()
        self.assertEqual(unexpected.read_text(), "retain")
        unexpected.unlink()
        fresh = CozoQueryStore(self.root / "failed-build")
        p = fresh.plan(self.index, self.scope)

        calls = []

        def fail():
            calls.append(True)
            if len(calls) > 1:
                raise ContractError("revoked after native preparation")

        with self.assertRaises(ContractError):
            fresh.build(self.index, self.scope, p["plan_sha256"], check_live=fail)
        self.assertFalse(fresh.directory.exists())
        self.assertEqual(self.store.load(self.index, self.scope), self.index)

    def test_input_change_restricted_policy_bounds_and_owned_reset(self):
        changed = deepcopy(self.index)
        changed["records"][0]["title"] = "changed"
        with self.assertRaisesRegex(ContractError, "COZO_STALE"):
            self.store.build(
                changed,
                self.scope,
                self.plan["plan_sha256"],
                check_live=self.context.check_live,
            )
        changed = deepcopy(self.index)
        changed["scope"]["visibility"] = "restricted"
        with self.assertRaisesRegex(ContractError, "COZO_POLICY"):
            self.store.plan(changed, self.scope)
        with self.assertRaisesRegex(ContractError, "COZO_BUDGET"):
            self.store.search(self.index, self.scope, "x" * 4097)
        with self.assertRaises(ContractError):
            self.store.traverse(
                self.index, self.scope, "public-alpha/reviewed-prompt", 101, 10
            )
        self.assertFalse(self.store.capabilities()["vectors"])
        self.assertFalse(self.store.capabilities()["encrypted_storage"])


if __name__ == "__main__":
    unittest.main()
