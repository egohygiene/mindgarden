"""The first supplied-byte adapter; no acquisition, interpretation or model calls."""

from ..domain.sources import NormalizedBundle, NormalizedUnit, normalize_text
from ..domain.validation import ContractError


class TextSourceAdapter:
    adapter_id = "plain-text"
    version = "1.0.0"
    supported_inputs = frozenset({("text/plain", None), ("text/markdown", None)})

    def normalize(self, captured: bytes, metadata: dict) -> NormalizedBundle:
        if len(captured) > 2_000_000:
            raise ContractError("SOURCE_OVERSIZED: text input exceeds 2000000 bytes")
        try:
            content = normalize_text(captured.decode("utf8")).encode("utf8")
        except UnicodeError as error:
            raise ContractError("SOURCE_ENCODING: plain text must be UTF-8") from error
        unit = NormalizedUnit("supplied-text:" + metadata["source_id"], content,
                              metadata["media_type"])
        return NormalizedBundle((unit,), (
            {"name": "decode-utf8", "version": "1.0.0", "parameters": {}},
            {"name": "normalize-newlines", "version": "1.0.0",
             "parameters": {"remove_initial_bom": True, "terminal_newline": "one"}},
        ))
