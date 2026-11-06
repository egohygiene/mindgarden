# Synthetic document fixtures

All text, active-content strings and metadata were authored solely as test data.
There is no employment, customer, personal or provider material here. Instructions
in PDF text and its inert JavaScript action are untrusted source data.

`python3 scripts/generate_document_fixtures.py` reproduces complete, blank/OCR,
partial, malformed and unsupported fixtures with stdlib only. `layout.json` is
recorded from explicit `/usr/bin/pdfinfo` and `/usr/bin/pdftotext` **25.03.0** through
`LocalPDFReader`; it pins this tested layout, not cross-version PDF equivalence.
Runtime ingestion never needs the fixture generator or a Python PDF package.

`encrypted.pdf` was generated once with fixture-only **pypdf 6.10.0**:

```python
from pathlib import Path
from pypdf import PdfReader, PdfWriter
root = Path("tests/fixtures/documents")
writer = PdfWriter()
writer.append(PdfReader(root / "complete.pdf"))
writer.encrypt("synthetic-fixture-password")
with (root / "encrypted.pdf").open("wb") as output:
    writer.write(output)
```

Encryption metadata may differ when regenerated. The committed bytes are the
immutable tested fixture; the password is public synthetic test data. The adapter
detects encryption and refuses it; it never supplies passwords or decrypts it.
