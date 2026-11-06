"""Synthetic reference-capture/1 example, not the unpublished Mindcap handoff."""

from mindgarden.domain.contracts import canonical_json, strict_json
from mindgarden.domain.sources import NormalizedBundle, NormalizedUnit
from mindgarden.domain.validation import ContractError


class ReferenceCaptureAdapter:
    adapter_id = "example-reference-capture"
    version = "1.0.0"
    supported_inputs = frozenset({("application/vnd.example.references+json", "1")})
    limits = {"capture_bytes": 2_000_000, "unit_bytes": 2_000_000, "units": 1000}

    def normalize(self, captured, metadata):
        document = strict_json(captured)
        if (not isinstance(document, dict) or set(document) != {"schema", "id", "records"}
                or document["schema"] != "example.reference-capture/1"
                or not isinstance(document["id"], str) or not document["id"]
                or not isinstance(document["records"], list)):
            raise ContractError("REFERENCE_FORMAT: expected the explicit synthetic example contract")
        units = []
        for record in document["records"]:
            if (not isinstance(record, dict) or set(record) != {"id", "title", "url", "notes"}
                    or any(not isinstance(value, str) for value in record.values()) or not record["id"]):
                raise ContractError("REFERENCE_FORMAT: expected stable identity and retained reference metadata")
            # Even bookmarklets are source data; no URL is dereferenced or executed.
            units.append(NormalizedUnit("reference:" + document["id"] + ":" + record["id"],
                                        canonical_json(record), "application/json", ("json:/notes",),
                                        {"page_content": "not-captured", "bundle_id": document["id"]}))
        return NormalizedBundle(tuple(units), ({"name": "retain-reference-metadata", "version": self.version,
                                               "parameters": {"page_content": "not-captured"}},))
