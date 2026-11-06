#!/usr/bin/env python3
"""Prove portable public garden references with authored rendered-site fixtures."""

from argparse import ArgumentParser
import os
from pathlib import Path
import shutil
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
try:
    import mindgarden
except ModuleNotFoundError:
    sys.path.insert(0,str(ROOT / "src"))
    import mindgarden

from mindgarden.adapters.rendered_federation import read_rendered_bundle
from mindgarden.application.federation import build_catalog
from mindgarden.domain.contracts import canonical_json, digest_bytes, strict_json
from mindgarden.domain.site import SITE_MARKER


def run_demo(workspace):
    sys.path.insert(0,str(ROOT))
    from tests.portal_fixture import create_portal_fixture

    if any(path.is_symlink() for path in (workspace,*workspace.parents)) or workspace.exists() and any(workspace.iterdir()):
        raise ValueError("Synthetic proof requires a new or empty ordinary workspace")
    with patch.dict(os.environ,{},clear=True),patch("socket.socket",side_effect=AssertionError("Network attempted")),patch("subprocess.run",side_effect=AssertionError("External process attempted")):
        fixture=create_portal_fixture(workspace)
        revision=strict_json(fixture["files"]["garden.json"])["revision"]
        pin=digest_bytes(fixture["files"][SITE_MARKER])
        bundle,reference=read_rendered_bundle(fixture["source"],pin,revision)
        relocated=workspace / "relocated-public-site";shutil.copytree(fixture["source"],relocated)
        assert read_rendered_bundle(relocated,pin,revision)==(bundle,reference)
        request={"schema":"mindgarden.federation-catalog-request/v1","bundles":[{
            "directory":str(relocated),"format":"rendered-site","expected_revision":revision,"expected_manifest_sha256":pin}]}
        catalog=build_catalog(request)
        refreshed=build_catalog({**request,"previous":catalog})
        assert catalog["status"]=="complete" and refreshed["refresh"][0]["state"]=="unchanged"
        unavailable={**request,"bundles":[{**request["bundles"][0],"directory":str(workspace / "unavailable")}],"previous":catalog}
        partial=build_catalog(unavailable)
        assert partial["records"]==[] and partial["refresh"][0]["state"]=="not-retained"
        return {"schema":"mindgarden.synthetic-garden-reference-proof/v1","status":"passed","package":reference,
            "records":len(catalog["records"]),"catalog_sha256":digest_bytes(canonical_json(catalog)),
            "renderer":"authored-contract-fixture-no-renderer-invocation","refresh":[refreshed["refresh"][0]["state"],partial["refresh"][0]["state"]],
            "checks":["exact-rendered-and-public-revision-pins","exact-canonical-routes","portable-after-relocation",
                      "data-only-no-authority-grant","no-previous-record-fallback","network-and-execution-blocked"]}


if __name__=="__main__":
    parser=ArgumentParser(description=__doc__)
    parser.add_argument("--workspace",type=Path,required=True)
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument("--require-source",action="store_true")
    mode.add_argument("--require-installed",action="store_true")
    args=parser.parse_args();engine=Path(mindgarden.__file__).resolve()
    if args.require_source and not engine.is_relative_to(ROOT / "src"):parser.error("Source engine from this checkout required")
    if args.require_installed and (engine.is_relative_to(ROOT / "src") or not engine.is_relative_to(Path(sys.prefix).resolve())):parser.error("Installed engine in this interpreter prefix required")
    report=run_demo(args.workspace.absolute())
    expected=strict_json((ROOT / "tests/fixtures/federation/expected-garden-reference-proof.json").read_bytes())
    if report!=expected:raise AssertionError("Synthetic garden-reference golden differs")
    print(canonical_json(report).decode(),end="")
