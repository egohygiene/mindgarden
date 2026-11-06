# Reviewed projection dependency builds

`build-projections` plans deterministic artifacts over explicit, authorized,
reviewed v1 knowledge/claims. It reuses canonical source/evidence, review and scope
contracts. Authored `mindgarden.observation/v1` interpretations are separate
reviewed proposal inputs; they never become canonical claims or evidence merely
because a projection exists.

A `mindgarden.dependency-build-request/v1` declares output identity/version,
explicit record selectors and required kinds, minimum confidence/review, inherited
scope, redaction policy, renderer/output contract, observations and byte budget.
Only the explicit `none` redaction policy is supported; it cannot declassify.
JSON and Markdown record views are small replaceable renderers, not a built-in
résumé model. Changing renderer bytes changes the build fingerprint.

```bash
mindgarden build-projections --local-config "/private/bindings.json" \
  --scope "/private/session.json" --input "/private/authored-build.json"
```

Review the complete dependency/file inventory and `plan_sha256`. Apply with
`--apply --output-directory "/private/new-build" --plan-digest "<exact-digest>"`.
The request must carry explicit approved human review. Inputs and live authority
are rechecked before writes and each artifact; existing bundles are create-or-
verify and never overwrite prior outputs. Partial attempts remain inspectable.

`projection-dependencies.json` declares exact record revisions, source evidence,
reviewed observations, uncertainty/contradiction/refinement/supersession links,
effective restrictions, renderer/version, output hashes and dependency fingerprints.
The record digest includes review, provenance, scope and qualifications. A whole-
garden/session revision guards application but does not invalidate every output
when only an unrelated record changes.

Supply `--previous-manifest "/private/previous/projection-dependencies.json"` for
full reconciliation. It recomputes canonical dependencies and explains current or
stale state for current authorized outputs only. No event stream is required for
correctness; unknown/denied old output identities are not copied to diagnostics.
This checkpoint identifies affected outputs; it does not run background hooks or
silently overwrite/rebuild prior immutable bundles.

The committed [authored request](../tests/fixtures/dependency-builds/authored-request.json)
and [reconciliation golden](../tests/fixtures/dependency-builds/expected-reconciliation.json)
exercise synthetic GitHub activity → normalized immutable source → reviewed
observation/claim → generic professional-profile and agent-context views → new
source revision → only those two consumers stale. The unrelated view remains
byte-identical and old source objects remain present. Seven focused cases cover
this loop, renderer replacement, deterministic rebuild, exact evidence, review,
expiry, inherited sensitivity, denied diagnostics and digest-bound CLI apply.

Full #37 still owns broader canonical observation integration, additional claim
validity/history cases, event-driven targeted execution, domain consumer renderers,
Mindcap #33 integration and a separately approved private pilot. The observation
contract here is an additive reviewed input, not a second Garden model. No real
private data or expertise inference is used. ADR impact: existing canonical/
projection and human-review boundaries apply; their proposed statuses are unchanged.
