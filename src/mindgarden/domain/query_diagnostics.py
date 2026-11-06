"""Shareable query failures contain stable codes, never supplied exception text."""

from .contracts import Diagnostic

QUERY_CODES = frozenset({
    "DOCUMENT_LIMIT","DOCUMENT_UNAVAILABLE","DOCUMENT_MALFORMED","DOCUMENT_CHANGED",
    "DOCUMENT_CLASSIFICATION","DOCUMENT_PARTIAL","DOCUMENT_ENCRYPTED","DOCUMENT_UNSUPPORTED","DOCUMENT_OCR_NEEDED",
    "SCOPE_REQUIRED","SCOPE_INVALID","SCOPE_MISSING","SCOPE_CONFLICT","POLICY_UNSUPPORTED",
    "SESSION_INVALID","SESSION_UNAVAILABLE","SESSION_STALE","SESSION_EXPIRED","SESSION_REVOKED",
    "SESSION_CONFIGURATION","SESSION_REVISION","SESSION_VIEW_STALE","PROJECTION_DENIED","QUERY_INTEGRITY",
    "QUERY_BUDGET","CONTEXT_BUDGET","CONTEXT_PROFILE","EVIDENCE_UNAVAILABLE","EVIDENCE_FORMAT",
    "WRITE_DENIED","WRITE_LOCKED","OUTPUT_SCOPE","PUBLICATION_DENIED","EXECUTION_DENIED",
    "RUNTIME_UNVERIFIED","PROJECTION_STALE","PROJECTION_DRIFT","TARGET_UNAVAILABLE",
    "CACHE_INTEGRITY","CACHE_UNOWNED","CACHE_PATH","CACHE_BUDGET","GENERATED_UNOWNED",
})


def query_failure(error: Exception) -> dict:
    candidate = str(error).partition(":")[0]
    code = candidate if candidate in QUERY_CODES else "QUERY_UNAVAILABLE"
    diagnostic = Diagnostic(code,"query","Scoped output was denied",
        "Refresh explicit authority and verify owned inputs locally; do not broaden denied scope.")
    return {"schema":"mindgarden.query-diagnostic/v1", "status":"denied",
            "classification":"shareable-diagnostic", "diagnostics":[diagnostic.document()]}
