"""Page-aware PDF source adapter over an explicitly supplied reader port."""

from ..domain.contracts import ContractRegistry, canonical_json, digest_bytes
from ..domain.sources import NormalizedBundle, NormalizedUnit
from ..domain.validation import ContractError


class PDFSourceAdapter:
    adapter_id = "local-pdf"
    version = "1.0.0"
    supported_inputs = frozenset({("application/pdf", None)})
    limits = {"capture_bytes": 10 * 1024 * 1024, "units": 1001}

    def __init__(self, reader):
        self.reader = reader
        self.bundle = None

    def normalize(self, captured: bytes, metadata: dict) -> NormalizedBundle:
        result = self.reader.read(captured)
        status = result["status"]
        if status != "complete":
            codes = {"ocr-needed": "DOCUMENT_OCR_NEEDED", "partial": "DOCUMENT_PARTIAL",
                     "encrypted": "DOCUMENT_ENCRYPTED", "malformed": "DOCUMENT_MALFORMED",
                     "unsupported": "DOCUMENT_UNSUPPORTED", "unavailable": "DOCUMENT_UNAVAILABLE"}
            raise ContractError(codes.get(status, "DOCUMENT_MALFORMED") + ": no complete document bundle was produced")
        original_sha = digest_bytes(captured)
        parser_sha = digest_bytes(canonical_json(result["parser"]))
        units, pages = [], []
        for page in result["pages"]:
            document = {"schema": "mindgarden.document-page/v1", "original_sha256": original_sha, **page}
            if ContractRegistry().errors(document, "document-page"):
                raise ContractError("DOCUMENT_MALFORMED: page contract is invalid")
            raw_text, previous = page["text"].encode("utf8"), 0
            for word in page["words"]:
                start, end = word["start_byte"], word["end_byte"]
                x0, y0, x1, y1 = word["bbox"]
                if (not previous <= start < end <= len(raw_text) or raw_text[start:end] != word["text"].encode("utf8")
                        or not 0 <= x0 <= x1 <= page["width"] or not 0 <= y0 <= y1 <= page["height"]):
                    raise ContractError("DOCUMENT_MALFORMED: word evidence does not match normalized text")
                previous = end
            content = canonical_json(document)
            pages.append({"page": page["page"], "normalized_sha256": digest_bytes(content),
                          "word_count": len(page["words"])})
            units.append(NormalizedUnit(
                "document:" + original_sha + ":page:" + str(page["page"]), content, "application/json",
                ("json:/text",), {"original_selector": {"sha256": original_sha, "page": page["page"]},
                                   "parser_sha256": parser_sha, "trust": "untrusted-evidence"}))
        bundle = {"schema": "mindgarden.document-bundle/v1", "status": "complete",
                  "original": {"sha256": original_sha, "size_bytes": len(captured), "media_type": "application/pdf"},
                  "scope": metadata["source_scope"], "classification_sha256": metadata["classification_sha256"],
                  "classification": metadata["classification_review"],
                  "parser": result["parser"], "pages": pages,
                  "attachments": "preserved-in-original-only",
                  "losses": ["reading-order-estimated", "formatting-not-preserved", "no-ocr", "no-semantic-outline"],
                  "trust": "untrusted-evidence"}
        if not pages or ContractRegistry().errors(bundle, "document-bundle"):
            raise ContractError("DOCUMENT_MALFORMED: document bundle contract is invalid")
        units.append(NormalizedUnit("document:" + original_sha + ":bundle", canonical_json(bundle), "application/json"))
        self.bundle = bundle
        return NormalizedBundle(tuple(units), ({"name": "pdf-page-layout", "version": self.version,
                                                "parameters": {"parser_sha256": parser_sha,
                                                               "classification_sha256": metadata["classification_sha256"]}},),
                                {"document_bundle": bundle})
