"""Verify supplied rendered sites as public discovery data, without HTML scraping."""

from pathlib import Path

from ..domain.contracts import ContractRegistry, canonical_json, digest_bytes, strict_json
from ..domain.federation import ARTIFACT_NAMES, OWNER_NAME, owner_marker, verify_bundle
from ..domain.site import SITE_MARKER, verify_site
from ..domain.validation import ContractError
from .site_files import read_site


def read_rendered_bundle(directory: Path, expected_manifest_sha256: str, expected_revision: str) -> tuple[dict, dict]:
    try:
        files = read_site(directory)
        if SITE_MARKER not in files or digest_bytes(files[SITE_MARKER]) != expected_manifest_sha256:
            raise ContractError("FEDERATION_STALE: rendered manifest differs from the explicit pin")
        site = verify_site(files)
        if site["kind"] != "site":
            raise ContractError("FEDERATION_INVALID: a completed rendered site is required")
        descriptor = strict_json(files["garden.json"])
        bundle = {name:files[name] for name in (*ARTIFACT_NAMES,"garden.json")}
        # Site ownership already binds every byte. The standalone federation
        # owner marker is intentionally absent from renderer output.
        bundle[OWNER_NAME] = canonical_json(owner_marker(descriptor["revision"]))
        descriptor, index, _graph = verify_bundle(bundle, expected_revision)
        routes = [{"reference":record["reference"], "url":record["canonical_url"],
                   "path":"notes/" + record["reference"]["id"] + "/index.html"} for record in index["records"]]
        if descriptor["base_uri"] != site["base_uri"] or sorted(site["routes"],key=canonical_json) != sorted(routes,key=canonical_json):
            raise ContractError("FEDERATION_INVALID: rendered routes must exactly cover the reviewed discovery selection")
        package = {"schema":"mindgarden.garden-package/v1", "format":"rendered-public-site/v1",
            "publisher":{"garden":descriptor["garden"],"canonical_uri":descriptor["canonical_uri"]},
            "revision":descriptor["revision"], "descriptor_sha256":digest_bytes(bundle["garden.json"]),
            "rendering":{"revision":site["revision"],"manifest_sha256":expected_manifest_sha256},
            "trust":"untrusted-evidence", "authority":"read-only", "execution":"data-only",
            "capabilities":["discovery","canonical-links"]}
        if ContractRegistry().errors(package,"garden-package"):
            raise ContractError("FEDERATION_INVALID: public package reference cannot preserve the supported contract")
        return bundle, package
    except ContractError as error:
        if str(error).startswith("FEDERATION_"): raise
        code = "FEDERATION_UNAVAILABLE" if str(error).startswith("SITE_UNAVAILABLE") else "FEDERATION_INVALID"
        raise ContractError(code + ": supplied rendered discovery could not be verified") from error
    except (KeyError,TypeError,ValueError) as error:
        raise ContractError("FEDERATION_INVALID: rendered discovery artifacts are incomplete") from error
