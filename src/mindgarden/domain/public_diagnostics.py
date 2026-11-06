"""Shareable publication diagnostics never echo source/control/process strings."""

import re

from .contracts import Diagnostic


def publication_failure(error):
    candidate = str(error).partition(":")[0]
    code = candidate if re.fullmatch(r"[A-Z][A-Z0-9_]{2,63}", candidate) else "SITE_UNAVAILABLE"
    incomplete = any(word in code for word in ("UNAVAILABLE", "INCOMPLETE", "BUDGET"))
    remediation = "Refresh the explicit reviewed profile, session and inputs; retry in a fresh owned output."
    if code.startswith("SESSION") or code == "SCOPE_REQUIRED":
        remediation = "Supply a current explicit reviewed-public session and local bindings; do not expand denied scope."
    elif code in {"SITE_PATH", "SITE_ENGINE", "FEDERATION_OUTPUT"}:
        remediation = "Choose separate ordinary output/cache directories outside canonical records and all declared vaults."
    elif code in {"SITE_INTEGRITY", "SITE_OUTPUT_CONFLICT", "SITE_STALE", "SITE_INCOMPLETE"}:
        remediation = "Preserve the conflicting output for inspection; verify complete checksums or select a fresh destination."
    elif code.startswith("COMPACTION"):
        remediation = "Refresh the authored hierarchy, exact permitted evidence and curation pin; preserve qualifications and explicit review."
    diagnostic = Diagnostic(code, "publication", "Public output verification is incomplete" if incomplete
                            else "Public output was denied", remediation)
    return {"schema": "mindgarden.publication-validation/v1", "status": "incomplete" if incomplete else "failed",
            "diagnostics": [diagnostic.document()]}
