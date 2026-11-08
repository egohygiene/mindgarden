# Public ADR metadata projection

`mindgarden decisions` consumes an explicitly supplied
`egohygiene.observatory.repository-intelligence-read-model/v1` with an exact input
SHA-256 and represented Git commit. It emits `mindgarden.adr-projection/v1` JSON
to stdout. It reads no repository history, garden registry, HTML, source body or
private decision. Canonical ADR bodies remain in their owning repositories.

```bash
mindgarden decisions --input "/explicit/public/read-model.json" \
  --input-sha256 "<reviewed-exact-input-sha256>" \
  --represented-commit "<represented-full-git-commit>" --max-bytes 65536
```

Nodes preserve canonical source URLs, exact revision, owner/date when supplied,
lifecycle, implementation status and upstream human disposition independently.
Missing non-proposed approval, unknown/inferred lifecycle, private evidence and
stale records are withheld before edges, backlinks and context are generated.
Superseded/rejected history remains metadata when its disposition is supplied.
Context selects accepted records; `--include-proposed` explicitly includes labeled
proposals as untrusted context. It never changes their status or review authority.

The adapter supports supersedes, superseded-by, amends, depends-on, conflicts-with
and related-to between authorized nodes. Authoritative and inferred edges remain
distinct. Unknown relationship kinds are not projected. Byte overflow rejects the
whole output instead of silently omitting decisions. Identical inputs rebuild
identically and contain no machine paths or denied-record counts.

This is a public-only metadata adapter, not an alternative ADR validator or a
private session interface. The producer must run the pinned Hygiene/EgoLint/Relay
validation; caller-supplied JSON cannot establish real approval merely by carrying
an assertion. The output explicitly preserves upstream assertions only. Existing
source citations expose the full context, constraints, alternatives and
consequences; those narratives are not extracted or copied into `.garden` here.
Private/inherited cross-garden projections, federation composition and accepted
UI integration remain parent #44 scope. #41 backfill is still gated.

Synthetic input provenance is recorded beside the fixture. Six focused tests cover
repeatability, provenance, lifecycle, lineage/inference, private canaries, changed
commits, budgets and CLI digest binding. ADR impact: this read-only adapter applies
existing ownership; it does not ratify any Mindgarden proposal.
