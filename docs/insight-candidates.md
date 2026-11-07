# Reviewed infographic candidate handoffs

The `insights` CLI exports a renderer-independent, versioned candidate projection
from explicitly selected, reviewed **public** knowledge and claims. It does not
render images, authenticate to channels, post, fetch artifact URLs or change
canonical knowledge. The maintainer selected this producer checkpoint before a
release; #19 remains deferred and #21's full downstream acceptance remains open.

```sh
mindgarden insights --local-config bindings.json --scope public-session.json \
  --input insight-plan.json
mindgarden insights --local-config bindings.json --scope public-session.json \
  --input insight-plan.json --apply --plan-digest PREVIEW_DIGEST \
  --output-directory /private/staging/insights
```

The public-only session must allow approved records and explicit publication
handoff authority. Existing garden publication allowlists, effective scope,
review status, source verification, expiry/revocation and budgets still apply.
The output remains in a private staging bundle until separately published.
Changed sources, rights, feedback or request content invalidate the digest.
Retry verifies immutable files; no original or earlier bundle is overwritten.

`insight-candidate/v1` carries a user-owned stable ID and canonical garden,
objective, audience/use, claim-level exact references and rights declarations,
uncertainty, review, publication eligibility, proposed visual form/hierarchy,
caption/alt-text inputs, channel metadata, lifecycle and supersession. Rights
are human-reviewed declarations, not automatic license verification. Uncertain,
inferred or contradictory evidence requires qualified teaching claims. Source
caveats and attribution stay attached; quoted claims must match selected content.
Selecting a canonical claim also requires selecting its reviewed subject.

The deterministic batch sorts candidate identities, suppresses exact/content
aliases with an explicit duplicate map and retains ordered series membership.
Conflicting IDs, ambiguous supersession or unavailable series members fail.
Proposed, rejected and superseded entries remain in the preview inspection trail
and are excluded from handoff files. Rejection and rendering failure do not
change knowledge. `insight-artifact-event/v1` accepts reviewed downstream status
and HTTPS artifact/checksum declarations bound to the exact candidate content
revision. Those references remain derived projection metadata; they are marked
`declared-not-fetched`. A claimed published state needs such reviewed feedback;
it grants no publishing authority and proves no remote artifact exists.

Private-to-public redaction is an explicit compatibility gap. This checkpoint
cannot turn a private citation into a public-safe one by relabeling it or hiding
its path. Use a separately approved public derivation whose *entire effective
evidence trail* is exportable, or remain blocked pending the accepted redaction
contract. Full private consumer adoption, RenderFlow/Identity intake approval,
artifact transport and publication integration remain separate. The producer
schema is not a claim of compatibility with an unavailable downstream contract.

The committed [authored plan](../tests/fixtures/insights/authored-plan.json) and
[golden proof](../tests/fixtures/insights/expected-proof.json) are synthetic. Run
`python -m unittest tests.test_insights tests.test_v1_contracts -q` for single,
series, duplicate, superseded, rejected, feedback, policy, rights, stale-plan and
privacy-blocked cases. No model or renderer is required.
