# Bounded research for a calling assistant

The #89 checkpoint exposes `mindgarden research` through the same application
services as ordinary CLI reads. Codex or another caller supplies a bounded tool
plan, inspects the observations and can submit a fresh refined plan. No planner
or generative model runs inside the engine. A separate research model is optional,
not a prerequisite; model-disabled direct search/context remains useful.

## Request and result

The [request schema](../contracts/v1/research-request.schema.json) selects exact
authorized garden revisions, exact source citations, allowed tools, expiration
and cumulative step/result/byte/cooperative-time budgets. Engine model calls are
fixed at zero. The caller's planner identifier is attribution, not certification
of a particular model or semantic quality.

Search, graph, backlinks, outbound links and JSON context consume the existing
`local-federation-query/v1` request unchanged. Exact `evidence` requires an already
permitted reviewed citation; `source-evidence` requires the existing private
session grant and exact revision. They do not promote source review. All steps,
tools, projections and first-pass grants are checked before opening any body.
The existing private local scope contract applies; no new session or permission
model is introduced. Conflicting/unknown/confidential policy fails closed.

```sh
mindgarden research --local-config /private/bindings.json \
  --scope /private/read-session.json --input /private/research-request.json \
  --diagnostic-format json
```

The [synthetic search-first](../tests/fixtures/research/search-first.json) and
[graph-first](../tests/fixtures/research/graph-first.json) plans show complete
shapes. Replace their synthetic identities, pinned revisions, citations and
expiration with explicitly authorized local values. A client can issue one search
first, inspect its citations, then issue another exact request; plans cannot
generate executable code or name an arbitrary handler.

The [result](../contracts/v1/research-result.schema.json) keeps observations and
their native provenance/review/selection reasons, represented input revisions,
contributing scope, expiration, request/authority digests and usage. Interpretations
are empty. A calling model may propose prose separately, with uncertainty and
citations; this result does not claim the question is answered or evidence is
complete. No matching authorized record returns `insufficient-evidence` without
enumerating denied records or implying their absence. Stale/unavailable/conflicting
evidence errors fail the whole plan; refresh/review is explicit.

Every read and final output rechecks live policy/revisions. Cumulative result and
byte bounds include result metadata; existing session ceilings remain stronger
limits. Request-file changes, expiry or revocation invalidate output. No partial
observations are printed on failure and shareable diagnostics omit private text,
paths and counts. Elapsed-time checks occur between synchronous local operations;
they are not a hard OS deadline or a certified CPU/memory isolation boundary.

## Codex and privacy

Review the [workspace profile](../profiles/agent/codex.md) with the operator and
use it as local task instructions in the chosen workspace. It is packaged with
the Python distribution. Nothing edits global Codex settings, launches a model
or connects the user's account. An assistant can use the ordinary installed CLI
without a new server. Its actual filesystem, execution and network permissions
remain the caller/Aether/Realm responsibility.

The current reference research session is private, offline and never-exportable.
That session authorizes local engine reads; **it does not authorize forwarding
private outputs to a hosted model or external consumer**. The profile is not a
sandbox. A real private assistant integration needs actual runtime and consumer
authority, especially for restricted content. The deterministic packet path works
with no model. Do not change source classification just to satisfy a tool flag.

There are no persisted research traces/caches. Caller-saved outputs inherit their
scope/lifetime, and must be revalidated after revision/authority changes or
revocation. No static copy is claimed to revoke itself. Durable summaries and
packet exports use the existing explicit review and fresh plan/apply workflows.

## Evidence and remaining parent scope

Offline tests exercise two distinguishable data-only caller plans, removal of
the planner dependency/direct search, all seven tools, exact source grants,
untrusted instructions, denied body/snippet/count exclusion, malformed later
tools, cumulative limits, interruption, stale inputs, expiry/revocation and
complete session output ceilings. These are software tests, not model accuracy.

`scripts/research_demo.py` composes the complete synthetic Drive/ledger/reviewed
packet/recovery proof with both CLI caller plans, a direct-search fallback and
metadata-only local pilot readiness. Its [complete golden](../tests/fixtures/research/expected-proof.json)
retains exact report and research hashes. No real Drive, Codex model or private
pilot runs. The [pilot guide](private-pilot.md) records the remaining operator
configuration and execution steps.

Live/local-model adapter acceptance, semantic/lexical/graph quality comparisons,
actual consumer execution assurance, broader original formats and the rest of
#89 stay open. These changes neither require #88/#91 nor ratify proposed ADRs.
