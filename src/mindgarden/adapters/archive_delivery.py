"""Bounded delivery facts; arbitrary producer runtime metadata stays in the ZIP.

These are the adapter's supported descriptive labels, not an exhaustive upstream
enum. Unknown labels are withheld rather than guessed or treated as execution
authority. This does not redact the private original or certify its producer.
"""

from ..domain.validation import ContractError
from .archive_preservation import require_array, require_object

LABELS = {
    "status": {"validated", "incomplete", "failed", "unavailable", "not-run"},
    "method": {
        "primary-file-runtime",
        "primary-local-packager",
        "fallback-local-packager",
        "local-packager",
        "rebuilt-local-packager",
        "synthetic-local-packager",
    },
    "path_id": {
        "primary-file-runtime",
        "fallback-local-filesystem",
        "primary-local-packager",
        "fallback-local-packager",
        "local-filesystem",
        "shell-filesystem",
        "product-native-artifact-writer",
    },
    "result": {
        "success",
        "available",
        "failed-transient",
        "failed-deterministic",
        "unavailable",
        "not-tested",
    },
    "error_class": {
        "transport-or-wrapper-error",
        "content-or-validation-error",
        "packager-error",
        "filesystem-error",
        "capability-unavailable",
    },
}
MAX_ATTEMPTS = 64


def delivery_metadata(value: object) -> dict:
    delivery = require_object(
        value, {"type", "status", "limitations"}, "ARCHIVE_DELIVERY"
    )
    if delivery["type"] != "zip":
        raise ContractError("ARCHIVE_DELIVERY: this adapter requires actual ZIP bytes")
    withheld = set()

    def label(item, key):
        if item is None and key == "error_class":
            return None
        if not isinstance(item, str) or not item or len(item) > 512:
            raise ContractError(
                "ARCHIVE_DELIVERY: delivery labels must be bounded strings"
            )
        if item not in LABELS[key]:
            withheld.add(key)
            return "withheld"
        return item

    limitations = require_array(delivery["limitations"], "ARCHIVE_DELIVERY")
    if len(limitations) > 64 or any(not isinstance(item, str) for item in limitations):
        raise ContractError(
            "ARCHIVE_DELIVERY: delivery limitations must be bounded text records"
        )
    result = {
        "type": "zip",
        "status": label(delivery["status"], "status"),
        "limitations": [],
    }
    if limitations:
        withheld.add("limitations")
        result["limitations"] = [
            "Producer delivery limitations remain in the private original."
        ]
    if "method" in delivery:
        result["method"] = label(delivery["method"], "method")
    if "attempts" in delivery:
        attempts = require_array(delivery["attempts"], "ARCHIVE_DELIVERY")
        if len(attempts) > MAX_ATTEMPTS:
            raise ContractError(
                "ARCHIVE_DELIVERY_LIMIT: at most 64 delivery attempts are supported"
            )
        result["attempts"] = []
        fields = {"path_id", "result", "error_class", "archive_created"}
        for attempt in attempts:
            require_object(attempt, fields, "ARCHIVE_DELIVERY")
            if type(attempt["archive_created"]) is not bool:
                raise ContractError(
                    "ARCHIVE_DELIVERY: attempts require observed creation state"
                )
            result["attempts"].append(
                {
                    "path_id": label(attempt["path_id"], "path_id"),
                    "result": label(attempt["result"], "result"),
                    "error_class": label(attempt["error_class"], "error_class"),
                    "archive_created": attempt["archive_created"],
                }
            )
            if attempt.keys() - fields:
                withheld.add("attempt_extensions")
    if delivery.keys() - {"type", "status", "method", "attempts", "limitations"}:
        withheld.add("delivery_extensions")
    if withheld:
        result["metadata_withheld"] = sorted(withheld)
    return result
