# Publication and preview conformance

This reusable synthetic pack exercises the existing v0 publication gates, v1
record/provenance validation, scoped retrieval, public federation and the v1 site
adapter. It is a bounded reference implementation, not a claim of complete media,
restricted-runtime or real-consumer acceptance for #10.

Install `requirements/test.txt` in a development environment, then run:

```sh
python scripts/publication_conformance.py --require-source --report proof.json
```

Consumer CI can use this checkout's committed fixture pack with its installed
engine, without selecting the engine from this checkout:

```sh
python -I /path/to/mindgarden/scripts/publication_conformance.py --require-installed --report proof.json
```

The script uses disposable synthetic gardens and loopback HTTP only. It never
opens the user's registry or gardens, fetches a renderer, or calls a model.
`proof.json` must be a new file. It contains stable suite names/results and
coverage limits; raw failure tracebacks, control paths and renderer strings are
not included. A failed test or skip reports incomplete coverage and exits nonzero.
Detailed debugging can use ordinary unittest commands in a private development
log. Automatic test discovery includes these fixtures; no paid workflow dispatch
is required.

The [surface matrix](../tests/fixtures/publication-conformance/cases.json) assigns
synthetic canaries to frontmatter, Markdown bodies, attachments, links, indexes,
errors, build logs and metadata. Tests verify field allowlists, denial before body
reads, exact citations, safe canonical routes, immutable output, rollback/retry,
missing/incomplete/budget diagnostics, links/hardlinks, and per-request authority
and byte verification. Existing suites retain relationship, modified-source,
transformation, revocation, expiration and v0 compatibility negatives.

V1 `publish`/`site` commands accept `--diagnostic-format text|json`. Failure output
contains a stable code, severity, generic logical location, remediation and
failed/incomplete status. It omits raw OS messages, source text, absolute paths
and subprocess arguments/logs. Success outputs retain their existing JSON forms.
The human form carries the same code and remediation. V0 dispatch is preserved.

The renderer's complete owned sibling cache/log subtree must be disjoint from
all declared vaults and canonical records, including denied locations. Guards
compare declarations before probing roots. Directory/file/total-byte budgets and
complete manifest checks are mandatory. Preview GET/HEAD responses and errors
use `no-store`; only original manifest members may be served. Checksums establish
integrity, not producer authenticity. Authority remains an explicit local session.

Remaining #10 work includes external normative policy/runtime assurance, approved
consumer conformance and media-specific adapters. No secret-scanning, source-rights
adjudication or sensitivity-classification claim is made by this pack.
