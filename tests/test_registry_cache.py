"""Owned cache quarantine/restore, uncertain commits and canonical preservation."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).parents[1] / "src"))

from mindgarden.application.bindings import garden_fingerprint
from mindgarden.application.query import QueryContext
from mindgarden.application.registry import build_registry_plan,apply_registry_plan
from mindgarden.application.registry_cache import build_cache_plan,apply_cache_plan,inspect_cache,recovery_root
from mindgarden.application.retrieval import build_index,projection_directory,write_projection
from mindgarden.domain.contracts import ContractRegistry,canonical_json
from mindgarden.domain.registry import registry_platforms
from mindgarden.domain.scope import local_scope
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests import test_registry as fixtures
from tests.support_v1 import write_json,write_session


class RegistryCacheTests(unittest.TestCase):
    def setUp(self):
        fixtures.RegistryTests.setUp(self)
        for operation,request in [("init",{}),("register",{"root":str(self.garden),"scope":local_scope(),"expected_garden":None,"expected_owners":[]})]:
            plan=build_registry_plan(self.registry,operation,request)
            apply_registry_plan(self.registry,plan.document(),plan.document()["plan_sha256"])
        self.session_path=self.root/"session.json";write_session(self.session_path,self.registry)
        self.context=QueryContext.load(self.registry,self.session_path)
        self.content=canonical_json(build_index(self.context))
        write_projection(self.context,self.garden,"index.json",self.content)
        self.cache=projection_directory(self.context,self.garden)
        self.request={"id":"synthetic-quarantine","action":"quarantine","garden":"synthetic-garden",
                      "scope_sha256":self.context.scope_digest(),"recovery_id":None}

    def test_quarantine_restore_repeat_and_revocation_preserve_canonical_bytes(self):
        before=garden_fingerprint(self.garden)
        plan=build_cache_plan(self.registry,self.request)
        self.assertEqual(ContractRegistry().errors(plan,"registry-cache-plan"),[])
        self.assertTrue(self.cache.exists())
        self.assertTrue(apply_cache_plan(self.registry,plan,plan["plan_sha256"]))
        self.assertFalse(apply_cache_plan(self.registry,plan,plan["plan_sha256"]))
        self.assertFalse(self.cache.exists())
        archive=Path(plan["destination"])
        self.assertEqual((archive/"index.json").read_bytes(),self.content)
        document=json.loads(self.registry.read_text());document["revoked_sessions"]=[self.context.session["id"]];write_json(self.registry,document)
        self.registry.chmod(0o600)
        restore=build_cache_plan(self.registry,{**self.request,"id":"synthetic-restore","action":"restore","recovery_id":plan["recovery_id"]})
        self.assertTrue(apply_cache_plan(self.registry,restore,restore["plan_sha256"]))
        self.assertFalse(apply_cache_plan(self.registry,restore,restore["plan_sha256"]))
        self.assertEqual((self.cache/"index.json").read_bytes(),self.content)
        self.assertEqual(garden_fingerprint(self.garden),before)
        with self.assertRaisesRegex(ContractError,"SESSION_REVOKED"):
            build_index(self.context)

    def test_changed_cache_registry_or_review_digest_is_refused(self):
        plan=build_cache_plan(self.registry,self.request)
        with self.assertRaisesRegex(ContractError,"CACHE_PLAN_STALE"):
            apply_cache_plan(self.registry,plan,"0"*64)
        (self.cache/"index.json").write_text("changed synthetic cache")
        with self.assertRaisesRegex(ContractError,"CACHE_INTEGRITY"):
            apply_cache_plan(self.registry,plan,plan["plan_sha256"])
        self.assertTrue(self.cache.exists())

    def test_unknown_files_legacy_caches_and_symlinks_are_retained(self):
        unknown=self.cache/"human-file.txt";unknown.write_text("Synthetic retained human file")
        with self.assertRaisesRegex(ContractError,"CACHE_INTEGRITY"):
            build_cache_plan(self.registry,self.request)
        self.assertEqual(unknown.read_text(),"Synthetic retained human file")
        unknown.unlink()
        alias=self.cache/"external-link";alias.symlink_to(self.garden)
        with self.assertRaisesRegex(ContractError,"PATH_SYMLINK|CACHE_"):
            build_cache_plan(self.registry,self.request)
        self.assertTrue(alias.is_symlink())
        alias.unlink()
        marker=self.cache/".mindgarden-scope-cache.json";marker.unlink()
        with self.assertRaisesRegex(ContractError,"CACHE_UNOWNED"):
            build_cache_plan(self.registry,self.request)
        self.assertTrue((self.cache/"index.json").exists())

    def test_failed_receipt_commit_reconciles_by_repeating_exact_plan(self):
        plan=build_cache_plan(self.registry,self.request)
        from mindgarden.application.registry_cache import atomic_journal
        calls=0
        def fail(path,document):
            nonlocal calls
            calls+=1
            if calls==2:raise OSError("Synthetic receipt commit failure")
            return atomic_journal(path,document)
        with patch("mindgarden.application.registry_cache.atomic_journal",side_effect=fail):
            with self.assertRaisesRegex(ContractError,"CACHE_RECOVERY_REQUIRED"):
                apply_cache_plan(self.registry,plan,plan["plan_sha256"])
        self.assertFalse(self.cache.exists())
        self.assertTrue(Path(plan["destination"]).exists())
        self.assertFalse(apply_cache_plan(self.registry,plan,plan["plan_sha256"]))
        self.assertEqual(inspect_cache(self.registry,"synthetic-garden",self.context.scope_digest())["state"],"missing")

    def test_platform_capabilities_and_cli_are_explicit_private_control(self):
        platforms=registry_platforms()
        self.assertIn("unsupported",platforms["win32"]["mutation"])
        self.assertIn("unsupported",platforms["darwin"]["mutation"])
        self.assertEqual(platforms["dev-container"]["host_mount_assurance"],"not-claimed")
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(["registry","cache-inspect","--registry",str(self.registry),"--garden-id","synthetic-garden","--scope-digest",self.context.scope_digest()]),0)
        report=json.loads(output.getvalue())
        self.assertEqual(report["classification"],"machine-local-control")
        self.assertEqual(report["publication"],"never-exportable")
        self.assertNotIn(str(self.root),output.getvalue())

    def test_old_quarantine_cannot_undo_an_interrupted_reviewed_restore(self):
        plan=build_cache_plan(self.registry,self.request)
        apply_cache_plan(self.registry,plan,plan["plan_sha256"])
        restore=build_cache_plan(self.registry,{**self.request,"id":"synthetic-restore","action":"restore","recovery_id":plan["recovery_id"]})
        from mindgarden.application.registry_cache import atomic_journal
        calls=0
        def fail(path,document):
            nonlocal calls
            calls+=1
            if calls==2:raise OSError("Synthetic restore receipt failure")
            return atomic_journal(path,document)
        with patch("mindgarden.application.registry_cache.atomic_journal",side_effect=fail):
            with self.assertRaisesRegex(ContractError,"CACHE_RECOVERY_REQUIRED"):
                apply_cache_plan(self.registry,restore,restore["plan_sha256"])
        with self.assertRaisesRegex(ContractError,"CACHE_PLAN_STALE"):
            apply_cache_plan(self.registry,plan,plan["plan_sha256"])
        self.assertFalse(apply_cache_plan(self.registry,restore,restore["plan_sha256"]))
        self.assertEqual((self.cache/"index.json").read_bytes(),self.content)
