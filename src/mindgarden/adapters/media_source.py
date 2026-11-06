"""Opaque media preservation; no thumbnail, OCR, codec, model or content execution."""

from ..domain.contracts import digest_bytes
from ..domain.sources import NormalizedBundle, NormalizedUnit


class OpaqueMediaAdapter:
    adapter_id = "opaque-media"
    version = "1.0.0"
    supported_inputs = frozenset((media, None) for media in
        ("image/png", "image/jpeg", "audio/wav", "video/mp4", "application/octet-stream"))

    def normalize(self, captured: bytes, metadata: dict) -> NormalizedBundle:
        digest = digest_bytes(captured)
        media_type = metadata["media_type"]
        unit = NormalizedUnit("opaque-media:" + digest, captured, media_type, ("artifact",),
                              {"sha256": digest, "interpretation": "opaque", "copy_policy": "reference-only",
                               "media_type_authority": "supplied-unverified", "trust": "untrusted-evidence"})
        return NormalizedBundle((unit,), ({"name": "preserve-opaque-media", "version": "1.0.0", "parameters": {}},),
                                {"interpretation": "opaque", "previews": "unavailable"})
