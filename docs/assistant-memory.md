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
