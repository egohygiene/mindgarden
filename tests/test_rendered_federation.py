"""Pinned data-only rendered discovery and explicit catalog refresh regressions."""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.rendered_federation import read_rendered_bundle
from mindgarden.application.federation import build_catalog
from mindgarden.domain.contracts import ContractRegistry, canonical_json, digest_bytes
from mindgarden.domain.federation import verify_bundle
from mindgarden.domain.site import SITE_MARKER
from mindgarden.domain.validation import ContractError
from tests.portal_fixture import create_portal_fixture
from tests.federation_fixture import create_fixture
from tests.support_v1 import write_json


class RenderedFederationTests(unittest.TestCase):
    def setUp(self):
        temporary=TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name)
        self.fixture=create_portal_fixture(self.root)
        self.revision=json.loads(self.fixture["files"]["garden.json"])["revision"]
        self.pin=digest_bytes(self.fixture["files"][SITE_MARKER])
        self.item={"directory":str(self.fixture["source"]),"format":"rendered-site",
                   "expected_revision":self.revision,"expected_manifest_sha256":self.pin}
        self.request={"schema":"mindgarden.federation-catalog-request/v1","bundles":[self.item]}

    def test_pinned_rendered_package_is_portable_data_without_authority(self):
        with patch("socket.socket",side_effect=AssertionError("Network attempted")),patch("subprocess.run",side_effect=AssertionError("Content executed")):
            bundle,package=read_rendered_bundle(self.fixture["source"],self.pin,self.revision)
            descriptor,index,graph=verify_bundle(bundle,self.revision)
            self.assertEqual(package["publisher"]["garden"],descriptor["garden"])
            self.assertEqual(package["authority"],"read-only")
            self.assertEqual(package["execution"],"data-only")
            self.assertEqual(ContractRegistry().errors(package,"garden-package"),[])
            relocated=self.root / "relocated";shutil.copytree(self.fixture["source"],relocated)
            self.assertEqual(read_rendered_bundle(relocated,self.pin,self.revision),(bundle,package))
            catalog=build_catalog(self.request)
        self.assertEqual(catalog["status"],"complete")
        self.assertEqual(catalog["gardens"][0]["package"],package)
        self.assertNotIn(str(self.root),json.dumps(catalog))
        self.assertNotIn('"content"',json.dumps(catalog))
        self.assertTrue(all(record["canonical_url"].startswith(descriptor["base_uri"]) for record in catalog["records"]))

    def test_refresh_never_reuses_unavailable_or_stale_previous_records(self):
        previous=build_catalog(self.request)
        unchanged=build_catalog({**self.request,"previous":previous})
        self.assertEqual(unchanged["refresh"][0]["state"],"unchanged")
        missing={**deepcopy(self.request),"previous":previous}
        missing["bundles"][0]["directory"]=str(self.root / "unavailable")
        result=build_catalog(missing)
        self.assertEqual(result["status"],"partial")
        self.assertEqual(result["records"],[])
        self.assertEqual(result["refresh"][0]["state"],"not-retained")
        self.assertEqual(result["diagnostics"],["FEDERATION_UNAVAILABLE"])
        stale={**deepcopy(self.request),"previous":previous}
        stale["bundles"][0]["expected_manifest_sha256"]="0" * 64
        result=build_catalog(stale)
        self.assertEqual(result["diagnostics"],["FEDERATION_STALE"])
        self.assertEqual(result["records"],[])

    def test_changed_rendering_is_an_explicit_update_and_conflicts_fail_closed(self):
        previous=build_catalog(self.request)
        # An independently pinned renderer configuration can change without
        # changing the represented reviewed knowledge revision.
        changed=deepcopy(self.fixture["files"])
        manifest=json.loads(changed[SITE_MARKER]);manifest["renderer"]["title"]="Synthetic updated rendering metadata"
        changed[SITE_MARKER]=canonical_json(manifest)
        write_json(self.fixture["source"] / SITE_MARKER,manifest)
        item={**self.item,"expected_manifest_sha256":digest_bytes(changed[SITE_MARKER])}
        result=build_catalog({**self.request,"bundles":[item],"previous":previous})
        self.assertEqual(result["refresh"][0]["state"],"updated")
        self.assertEqual(result["refresh"][0]["previous_revision"],result["refresh"][0]["current_revision"])
        conflict=build_catalog({**self.request,"bundles":[item,item]})
        self.assertEqual(conflict["records"],[])
        self.assertIn("FEDERATION_DUPLICATE_ID",conflict["diagnostics"])

    def test_tampered_routes_and_symlinks_fail_without_exposing_paths(self):
        route=json.loads(self.fixture["files"][SITE_MARKER])["routes"][0]["path"]
        (self.fixture["source"] / route).write_text("Tampered synthetic page")
        result=build_catalog(self.request)
        self.assertEqual(result["status"],"partial")
        self.assertEqual(result["records"],[])
        self.assertNotIn(str(self.root),json.dumps(result))
        (self.fixture["source"] / route).write_bytes(self.fixture["files"][route])
        manifest=json.loads(self.fixture["files"][SITE_MARKER]);manifest["routes"].pop()
        write_json(self.fixture["source"] / SITE_MARKER,manifest)
        item={**self.item,"expected_manifest_sha256":digest_bytes(canonical_json(manifest))}
        self.assertEqual(build_catalog({**self.request,"bundles":[item]})["records"],[])
        (self.fixture["source"] / SITE_MARKER).write_bytes(self.fixture["files"][SITE_MARKER])
        outside=self.root / "synthetic-outside";outside.write_text("synthetic-outside-canary")
        (self.fixture["source"] / route).unlink();(self.fixture["source"] / route).symlink_to(outside)
        result=build_catalog(self.request)
        self.assertEqual(result["records"],[])
        self.assertNotIn("synthetic-outside-canary",json.dumps(result))
        with self.assertRaisesRegex(ContractError,"FEDERATION_REQUEST"):
            build_catalog({**self.request,"bundles":[{k:v for k,v in self.item.items() if k!="expected_manifest_sha256"}]})
