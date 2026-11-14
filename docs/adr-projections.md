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

## Explicit public artifact relationships

Add `--include-related` to include one-hop artifacts around the admitted decision
nodes. This opt-in extends the same v1 output with `artifacts`, typed `edges`,
backlinks and explained context entries; ordinary existing output stays compact.
Supported artifact kinds are repository, roadmap step, issue, pull request, commit,
check, release and deployment. Relationships use the actual Hygiene vocabulary
subset: blocks, depends-on, evidences, implements, informs, tracks and verifies.
Existing decision lineage types remain supported. Inferred links remain labeled.

Only current, public, source-backed targets enter the graph. Immutable Git evidence
may explicitly have `not_applicable` freshness. Context adds artifacts only when
linked directly to an explicitly selected accepted decision (or an explicitly
included proposal). Provider state such as merged/closed/success is an observation,
not knowledge approval. Related context stays untrusted and identifies the selected
decision, relationship and assertion. Whole-output byte overflow rejects the result.

Every artifact preserves its canonical owner URL, repository, source revision when
available, observation time and the snapshot commit in which it was represented.
An issue observation with no immutable revision stays null; a commit keeps its own
commit hash instead of being relabeled with the snapshot's commit. Cross-repository
decisions retain their own exact canonical blob/revision. Organization-scoped
references are labeled `organization-scope-reference`; this is **not** a grant of
inherited policy or a conclusion that a decision applies to this consumer.

Private/stale/unknown/unavailable targets are withheld before generated identities,
titles, context, backlinks or counts. Coverage always says
`selected-current-public-inputs-only`; raw producer counts are never copied. Unknown
source revisions, mutable Git source URLs, credential/query URLs, duplicate eligible
source IDs, unsupported read-model versions and malformed metadata fail closed or
are withheld. The adapter does not fetch targets or infer new canonical nodes.

Claims, architecture-component/projection kinds and a private/inherited authority
interface need actual owning contracts; this checkpoint does not invent those
Repository Intelligence kinds. Full ADR narratives stay in canonical source files.
Private federation and real consumer acceptance remain parent #44 scope.

## Supported owner composition proof

The refreshed Relay #115 tracker is closed/delivered, with its real Identity
collector evidence; the earlier blanket missing-collector assumption is superseded.
The existing #41 historical/human disposition gate remains independent. This batch
uses current supported public source contracts, not another renderer or normalizer.

The synthetic `relationships-projection.json` passes the pinned Hygiene schema and
semantic validator; Observatory normalizes it byte-equivalently into
`relationships-snapshot.json`; Mindgarden emits the exact relationship golden;
Relay's native snapshot validator and Decisions renderer consume **the same**
machine-readable snapshot with all three decision source URLs preserved. No
rendered HTML is reverse-parsed into knowledge. No consumer site is deployed.

[Owner revisions and file hashes](../tests/fixtures/decisions/owner-inputs.json) bind
Hygiene `d51043f`, Observatory `7f399a0` and Relay `5de7083`. The
[receipt](../tests/fixtures/decisions/owner-proof.json) records three decision nodes,
six related artifacts, eight typed edges/context entries and exact input/output
digests. All disposition/collection claims in this fixture are synthetic, not
proof of human acceptance or complete canonical ADR-source conformance.

Acquire these recorded **public** revisions separately and unpack the manifest's
paths under `hygiene/`, `observatory/` and `relay/` in an explicit owner-source
folder. Then, with development test dependencies available:

```bash
python3 scripts/verify_decision_relationships.py \
  --owner-sources /explicit/pinned-owner-sources --require-source
```

The executable proof verifies every pinned source file before import and blocks
network/process calls during processing. Its engine-origin guard supports an
installed engine with `--require-installed`. This is process-level test evidence,
not a confidential-host isolation certificate. The ordinary engine remains
standard-library-only and does not install owner runtimes or development tools.
