"""Portable ownership evidence for one checked public garden in a portal."""

from .. import __version__
from .contracts import canonical_json, digest_bytes, strict_json
from .federation import ARTIFACT_NAMES, OWNER_NAME, file_entry, owner_marker, public_url, verify_bundle
from .site import SITE_MARKER
from .validation import ContractError

PORTAL_MARKER = ".mindgarden-portal.json"
PORTAL_CONTRACTS = ["mindgarden.portal-manifest/v1", "mindgarden.site-manifest/v1",
                    "mindgarden.federation-descriptor/v1", "mindgarden.federation-index/v1", "mindgarden.federation-graph/v1"]


def composition_manifest(request, site, files):
    try:
        descriptor = strict_json(files["garden.json"])
        bundle = {name: files[name] for name in (*ARTIFACT_NAMES, "garden.json")}
        bundle[OWNER_NAME] = canonical_json(owner_marker(descriptor["revision"]))
        descriptor, index, _graph = verify_bundle(bundle)
    except (KeyError, TypeError) as error:
        raise ContractError("PORTAL_SITE: complete verified public discovery artifacts required") from error
    expected_routes = [{"reference": record["reference"], "url": record["canonical_url"],
                        "path": "notes/" + record["reference"]["id"] + "/index.html"} for record in index["records"]]
    if (descriptor["base_uri"] != site["base_uri"]
            or sorted(site["routes"], key=canonical_json) != sorted(expected_routes, key=canonical_json)):
        raise ContractError("PORTAL_SITE: rendered routes must cover the exact public discovery selection")
    portal = request["portal"]
    base = public_url(portal["base_uri"], base=True)
    if base != portal["base_uri"] or base + portal["mount"] + "/" != site["base_uri"]:
        raise ContractError("PORTAL_ROUTE: site base must equal the explicit portal base and mount")
    payload = {"schema": "mindgarden.portal-manifest/v1", "engine_version": __version__, "base_uri": base,
               "mount": portal["mount"], "commit_marker": PORTAL_MARKER, "contracts": PORTAL_CONTRACTS,
               "site": {"revision": site["revision"], "manifest_sha256": digest_bytes(files[SITE_MARKER]),
                        "base_uri": site["base_uri"], "renderer": site["renderer"]},
               "owned": [file_entry(portal["mount"] + "/" + name, content) for name, content in sorted(files.items())]}
    return {**payload, "revision": "sha256:" + digest_bytes(canonical_json(payload))}
