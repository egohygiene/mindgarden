"""Optional FTS parity, owned recovery and authorization before cache access."""

from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from mindgarden.adapters.sqlite_query import SQLiteQueryStore, capabilities
from mindgarden.application.retrieval import build_index, rank
from mindgarden.application.query_store import store_backup
from mindgarden.domain.contracts import canonical_json, digest_bytes
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests import test_v1_retrieval as retrieval_tests


class QueryStoreTests(unittest.TestCase):
    def setUp(self):
        retrieval_tests.RetrievalTests.setUp(self)
        self.index = build_index(self.context)
        self.scope = self.context.scope_digest()
        self.directory = self.root / "query-cache"
        self.store = SQLiteQueryStore(self.directory)

    def build(self):
        plan = self.store.plan(self.index, self.scope)
        result = self.store.build(
            self.index,
            self.scope,
            plan["plan_sha256"],
            check_live=self.context.check_live,
        )
        return plan, result

    def test_fts_matches_reference_scores_reasons_and_exact_evidence(self):
        self.build()
        for query in (
            "prompt",
            "procedure synthetic",
            "NOT OR *",
            "",
            "synthetic-prompt",
        ):
            self.assertEqual(
                self.store.search(self.index, self.scope, query),
                rank(self.index, query),
            )
        self.assertNotIn(
            b"unreviewed-unique-marker", (self.directory / "query.sqlite").read_bytes()
        )
        self.assertFalse(capabilities()["encrypted_storage"])
        self.assertFalse(capabilities()["vectors"])

    def test_unicode_and_hyphen_tokenization_matches_reference(self):
        record = self.index["records"][0]
        for term in ("café", "κόσμος", "long-term", "日本語"):
            record["terms"][term] = 2
        self.build()
        for term in ("café", "κόσμος", "long-term", "日本語"):
            self.assertEqual(
                self.store.search(self.index, self.scope, term), rank(self.index, term)
            )

    def test_rebuild_replay_backup_restore_and_owned_reset_preserve_canonical(self):
        before = {p: p.read_bytes() for p in self.workspace.rglob("*") if p.is_file()}
        plan, result = self.build()
        self.assertEqual(result["status"], "rebuilt")
        self.assertEqual(
            self.store.build(
                self.index,
                self.scope,
                plan["plan_sha256"],
                check_live=self.context.check_live,
            )["status"],
            "verified-no-op",
        )
        backup = self.store.backup(self.index, self.scope)
        self.assertEqual(backup, store_backup(self.index, self.scope))
        restored = SQLiteQueryStore(self.root / "restored-cache")
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
        marker = self.store.inventory()
        self.store.reset(
            digest_bytes(canonical_json(marker)), check_live=self.context.check_live
        )
        self.assertFalse(self.directory.exists())
        self.assertEqual(
            before,
            {p: p.read_bytes() for p in self.workspace.rglob("*") if p.is_file()},
        )

    def test_stale_scope_and_changed_plan_never_return_cached_content(self):
        p = self.store.plan(self.index, self.scope)
        changed = deepcopy(self.index)
        changed["records"][0]["title"] = "changed"
        with self.assertRaisesRegex(ContractError, "QUERY_STORE_STALE"):
            self.store.build(
                changed,
                self.scope,
                p["plan_sha256"],
                check_live=self.context.check_live,
            )
        self.assertFalse(self.directory.exists())
        self.build()
        with self.assertRaisesRegex(ContractError, "QUERY_STORE_STALE"):
            self.store.load(changed, self.scope)
        with self.assertRaisesRegex(ContractError, "QUERY_STORE_STALE"):
            self.store.load(self.index, "0" * 64)

    def test_corruption_unknown_files_and_symlink_are_retained(self):
        self.build()
        database = self.directory / "query.sqlite"
        database.write_bytes(database.read_bytes() + b"corruption")
        with self.assertRaisesRegex(ContractError, "QUERY_STORE_CORRUPT"):
            self.store.load(self.index, self.scope)
        self.assertTrue(database.exists())
        unknown = self.root / "human"
        unknown.mkdir(mode=0o700)
        (unknown / "notes.txt").write_text("retain")
        with self.assertRaisesRegex(ContractError, "QUERY_STORE_UNOWNED"):
            SQLiteQueryStore(unknown).plan(self.index, self.scope)
        link = self.root / "alias"
        link.symlink_to(self.directory, target_is_directory=True)
        with self.assertRaisesRegex(ContractError, "REGISTRY_PATH"):
            SQLiteQueryStore(link)

    def test_typed_traversal_and_backlinks_use_authorized_index_only(self):
        self.build()
        start = "synthetic-garden/synthetic-prompt"
        graph = self.store.traverse(self.index, self.scope, start, 1, 20)
        self.assertTrue(graph["edges"])
        self.assertEqual(
            self.store.backlinks(
                self.index, self.scope, "synthetic-garden/second-note"
            ),
            self.index["backlinks"]["synthetic-garden/second-note"],
        )
        self.assertEqual(
            self.store.traverse(self.index, self.scope, "denied-canary", 10, 20),
            {"nodes": [], "edges": []},
        )

    def test_cli_live_authority_is_checked_before_opening_store(self):
        self.build()
        args = [
            "query-store",
            "--local-config",
            str(self.configuration),
            "--scope",
            str(self.session_path),
            "--cache-directory",
            str(self.directory),
            "--operation",
            "search",
            "--query",
            "prompt",
        ]
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(args), 0)
        self.assertTrue(json.loads(output.getvalue())["results"])
        session = json.loads(self.session_path.read_text())
        session["expires_at"] = "2000-01-01T00:00:00Z"
        self.session_path.write_text(json.dumps(session))
        with (
            patch.object(
                SQLiteQueryStore,
                "inventory",
                side_effect=AssertionError("Cache opened"),
            ),
            redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(main(args), 3)

    def test_failed_replacement_restores_the_prior_owned_store(self):
        self.build()
        previous = (self.directory / "query.sqlite").read_bytes()
        changed = deepcopy(self.index)
        changed["records"][0]["title"] = "refreshed"
        p = self.store.plan(changed, self.scope)
        import os

        replace = os.replace

        def fail_stage(source, target):
            if Path(source).name.startswith(".query-store-stage-"):
                raise OSError("Synthetic replacement failure")
            return replace(source, target)

        with patch(
            "mindgarden.adapters.sqlite_query.os.replace", side_effect=fail_stage
        ):
            with self.assertRaises(OSError):
                self.store.build(
                    changed,
                    self.scope,
                    p["plan_sha256"],
                    check_live=self.context.check_live,
                )
        self.assertEqual((self.directory / "query.sqlite").read_bytes(), previous)
        self.assertEqual(self.store.load(self.index, self.scope), self.index)

    def test_missing_optional_sqlite_preserves_unrelated_cli_and_reports_unavailable(
        self,
    ):
        import subprocess

        source = Path(__file__).parents[1] / "src"
        program = "import sys; sys.path.insert(0, sys.argv[1]); sys.modules['sqlite3']=None; from mindgarden.interfaces.cli import main; assert main(['version']) == 0"
        result = subprocess.run(
            [sys.executable, "-c", program, str(source)],
            capture_output=True,
            text=True,
            check=True,
        )
        from mindgarden import __version__

        self.assertIn("mindgarden " + __version__, result.stdout)
        with patch("mindgarden.adapters.sqlite_query.sqlite3", None):
            self.assertFalse(capabilities()["lexical"])
            with self.assertRaisesRegex(ContractError, "QUERY_STORE_UNAVAILABLE"):
                SQLiteQueryStore(self.root / "unavailable")

    def test_application_accepts_a_conforming_store_factory(self):
        from mindgarden.application.query_store import run_query_store
        from mindgarden.interfaces.cli import build_parser

        self.build()
        calls = []

        class ExtensionStore(SQLiteQueryStore):
            def search(self, index, scope, query):
                calls.append(query)
                return super().search(index, scope, query)

        arguments = build_parser().parse_args(
            [
                "query-store",
                "--local-config",
                str(self.configuration),
                "--scope",
                str(self.session_path),
                "--cache-directory",
                str(self.directory),
                "--operation",
                "search",
                "--query",
                "prompt",
            ]
        )
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(
                run_query_store(arguments, store_factory=ExtensionStore), 0
            )
        self.assertEqual(calls, ["prompt"])
        self.assertEqual(
            json.loads(output.getvalue())["results"], rank(self.index, "prompt")
        )
