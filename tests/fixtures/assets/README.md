# Synthetic asset and mixed-workflow fixtures

`python3 scripts/generate_media_fixtures.py` deterministically creates a one-pixel
PNG and a short silent WAV with stdlib only. No private images, recordings or
external copyrighted material are used. The opaque adapter never decodes them.

`review-cases.json` lists the supported metadata-only dispositions and explicit
unavailable restricted/copy/deletion boundaries. `pdf-curation-plan.json` is an
authored, approved synthetic human proposal for the exact first PDF page. Source
text remains untrusted and knowledge retains its stated uncertainty.

`expected-proof.json` pins the complete mixed archive/PDF/media result. Its PDF
reader mode is explicitly recorded-synthetic-reader-port: this fixture is not a
claim that a CI host installed Poppler. The actual local 25.03.0 tool proof is
separate, and matches the same golden data while reporting real-local-poppler.
See [the checkpoint](../../../docs/mixed-source-vault.md) for commands and limits.
