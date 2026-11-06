"""One supplied public site and three caller-owned synthetic portal surfaces."""

from pathlib import Path
import shutil
from unittest.mock import patch

from mindgarden.adapters.site_files import read_site
from mindgarden.application.site import build_site
from mindgarden.domain.contracts import digest_bytes
from mindgarden.domain.site import SITE_MARKER, verify_site
from tests.site_fixture import create_fixture
from tests.support_v1 import write_json


def create_portal_fixture(root, *, base_uri=None):
    fixture = create_fixture(root / "source")
    if base_uri is not None:
        fixture["profile"]["base_uri"] = base_uri
        write_json(fixture["profile_path"], fixture["profile"])
    projection = build_site(fixture["context"], fixture["profile"], profile_path=fixture["profile_path"])
    plan = projection.plan(fixture["context"], fixture["export"], operation="build", engine_directory=fixture["engine"])
    rendered = {"index.html": b"<!doctype html><title>Synthetic garden</title>"}
    rendered.update({route["path"]: b"<!doctype html><title>Reviewed public note</title>" for route in projection.manifest["routes"]})
    with patch("mindgarden.adapters.quartz.render_public_site", return_value=rendered):
        projection.apply(fixture["context"], fixture["export"], plan["plan_sha256"], operation="build", engine_directory=fixture["engine"])
    source = fixture["export"] / "garden"
    files = read_site(source); manifest = verify_site(files)
    portal = root / "portal"
    shutil.copytree(Path(__file__).parent / "fixtures/portal-composition", portal)
    request = {"schema": "mindgarden.portal-request/v1", "classification": "machine-local-control", "publication": "never-exportable",
               "source": {"directory": str(source), "expected_revision": manifest["revision"], "expected_manifest_sha256": digest_bytes(files[SITE_MARKER])},
               "portal": {"directory": str(portal), "base_uri": manifest["base_uri"].removesuffix("garden/"), "mount": "garden"}}
    return {"request": request, "source": source, "portal": portal, "files": files}
