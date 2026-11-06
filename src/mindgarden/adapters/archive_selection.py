"""Explicit normalization selection; the original ZIP always remains immutable."""

from ..domain.validation import ContractError


def attachment_selection(metadata: dict, available: set[str]) -> tuple[str, set[str]]:
    selection = metadata.get("attachment_selection", {"mode": "all", "asset_ids": []})
    if (not isinstance(selection, dict) or set(selection) != {"mode", "asset_ids"}
            or selection["mode"] not in {"all", "catalog-only", "selected"}
            or not isinstance(selection["asset_ids"], list)
            or any(not isinstance(value, str) for value in selection["asset_ids"])
            or len(set(selection["asset_ids"])) != len(selection["asset_ids"])
            or not set(selection["asset_ids"]) <= available
            or selection["mode"] != "selected" and selection["asset_ids"]):
        raise ContractError("ARCHIVE_SELECTION: select known asset identities with an explicit attachment mode")
    return selection["mode"], (available if selection["mode"] == "all" else set(selection["asset_ids"]))
