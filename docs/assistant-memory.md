# Reviewed assistant-memory snippets

`memory` creates a disposable projection of reviewed durable knowledge. Canonical
knowledge, source originals and the #46 retention hierarchy remain unchanged.
The versioned `memory-plan` and `memory-projection` schemas are provider neutral.
No model, external account or automatic memory installation is required.

```bash
mindgarden memory --local-config "/private/bindings.json" \
  --scope "/private/session.json" --input "/private/authored-memory-plan.json"
```

Inspect the proposed snippets, exact references, transformation trail, metrics,
violations and `plan_sha256`. Export with `--apply --output-directory
"/private/new-memory-export" --plan-digest "<reviewed-exact-digest>"`. Explicit
approved human review is required; changed sources, wording, authority or validity
invalidate application. Repeat application verifies the immutable bundle. Prior
exports remain available rather than being overwritten.

Actions are keep, merge, rewrite, demote, expire, split and pin. Merge preserves
all exact source references; split is explicit; demote/expire remove an item only
from this proposed memory view. They never delete canonical detail. Each source
has one explicit action, avoiding contradictory dispositions. Snippets preserve
category, sensitivity, durability/half-life, confidence, source revision and
qualifications, inclusion/transformation rationale, supersedes/merges links,
last-review time and optional expiry.

Preferences, identity, recurring workflows and long-lived project direction are
favored. Temporary, historical, one-off and sensitive categories require explicit
pinning or a different reviewed disposition. Pins cannot override inherited
sensitivity, expired review or unsupported confidential processing. Specific dates
and amounts without expiry/pinning generate review findings; this conservative
syntactic aid does not claim semantic understanding.

Budgets cover the total JSON+Markdown bytes, snippet count, category quotas,
minimum priority, provider body-byte limits and optional exact token limits.
Overflow retains every proposed snippet in the preview and blocks export; it does
not silently discard context. The core has no provider tokenizer. Requesting a
token ceiling without its exact registered adapter fails explicitly. A synthetic
whitespace counter proves that adapter boundary; it is not a model-token claim.

Outputs are `memory-projection.json` and copyable `memory-snippets.md` inside a
private owned bundle. The JSON keeps the complete source trail; each Markdown
block has a short body and source references. Raw-source, knowledge, active model-
context and publication retention remain separate. Export does not install memory
or extend session authority. A manual copy outside Mindgarden requires the
consumer to refresh/revoke it; automatic provider revocation is not claimed.

Eight focused cases pass on both supported Pythons, plus contract checks. The
committed synthetic plan covers all seven actions: eight verbose canonical items
become six snippets, with body bytes reduced from 11,416 to 187. The full cited
bundle is 20,699/32,768 bytes; this is body compaction, not a claim that the entire
provenance bundle is smaller than the source prose. Identical inputs within the
same validity window reproduce exactly. Crossing expiry/half-life produces an
explicit renewed-review finding. A changed source revision requires a refreshed
authored plan; it never freezes stale wording silently.

Richer interactive review, provider-specific adapters and automatic refresh remain
follow-up scope. ADR impact: this projection follows existing human-review,
source/projection and retention boundaries; no provider or canonical store is
selected or ratified.


## Expiring local bundles and current-state checks

Pass an explicit timestamp to opt into a managed local export:

```bash
mindgarden memory --local-config "/private/bindings.json" \
  --scope "/private/session.json" --input "/private/authored-memory-plan.json" \
  --created-at "2026-11-09T00:00:00Z"
```

Review that preview, then use the same arguments with `--apply`,
`--output-directory` and its exact `--plan-digest`. The additional private
`memory-validity.json` binds creation/expiration, authority, exact authored request,
retention policy and both content checksums. Its bytes count toward the existing
complete-bundle limits. Expiration is the earliest of model-context TTL, session
expiry, snippet stale-after or review half-life. Creation must not be in the
future; an ended window fails before source bodies/index access.

Before reuse, supply the same plan, creation timestamp and directory with
`--check` instead of `--apply`. The check recomputes current authorized sources
and validity, verifies every immutable bundle member and returns only a small
status. Missing bundles are never created by checks. Changed/denied sources,
revocation, expiration, altered content and unknown files fail; prior output and
canonical records stay intact. Outputs cannot overlap a declared source vault.
A new timestamp changes the reviewed digest and cannot renew an existing bundle
in place. Review a new bundle at a fresh private location.

Legacy JSON/Markdown exports without `--created-at` retain their original format
and command behavior. They have no managed validity receipt and cannot use this
check. Migrate by reviewing a newly managed export. Copied snippets and external
providers remain outside local enforcement; refresh/remove those copies in the
consumer. A checksum is integrity evidence, not encryption or producer identity.
No automatic deletion, silent rewrite, provider permission or recall is claimed.

Incremental refresh is authored: use current exact references for changed
candidates, review their wording/rationale, and generate a fresh projection.
Unchanged source/snippet records retain their bytes; old bundles remain available
for inspection. The synthetic refresh test updates one source/candidate, keeps
all five unaffected snippets identical and preserves the prior private bundle.
No model has to infer or approve the new preference.

## Listed #49 acceptance and deliverables

| Listed requirement | Implemented evidence |
| --- | --- |
| Disposable projection; every snippet traces to reviewed sources (AC 1–2) | Versioned memory plan/projection and exact evidence/qualification records; existing memory tests |
| Transient expiry, explicit duplicate merge, bounded size/count (AC 3–5) | Seven reviewed actions, category quotas, exact tokenizer adapter, byte/count ceilings; managed TTL/half-life checks |
| Copyable blocks; deterministic rebuild; no implicit sensitivity lowering (AC 6–8) | JSON/Markdown golden metrics, scoped source selection, unchanged-input byte checks and privacy negatives |
| Memory removal differs from source deletion; providers remain adapters (AC 9–10) | Demote/expire preserve canonical detail; generic profile and explicit tokenizers; external copies require consumer refresh |
| All ten deliverables | Schemas/taxonomy/actions/budgets, provenance/rendering, authored refresh rules, synthetic compaction, digest-bound CLI review and [generic unpublished outline/brief](memory-hygiene-publication-draft.md) |

These satisfy the issue's listed local projection scope. Richer UI, native
provider installation and automatic remote revocation are optional integrations,
not added closure gates. Proposed architecture/retention ADRs remain proposed.
