# Authored curation plans

The #13 local checkpoint implements `mindgarden.curation-plan/v1`, readonly
preview and deterministic application. Model-assisted proposal production is
optional and is not implemented by this service.

## Reviewable input

A plan identifies one bound garden, creation time, producer, nullable human review
authority and candidates. Each candidate has an exact source selector/hash,
immutable represented revision, rationale and an explicit disposition: `keep`,
`summarize`, `merge`, `reference`, `defer`, or `exclude`.

Kept outputs declare identity, body, kind, authors, lifecycle, review, confidence,
epistemic state, attribution, domains/topics, caveats, uncertainty, contradictions,
claims and typed relationships. These axes remain independent. A reviewed
assistant suggestion can remain epistemically proposed; review does not turn it
into an earlier user decision or verified fact. Retrieval/context preserve those
qualifications alongside exact source references.

`reference` requires a reference-kind output. `merge` binds at least two exact
existing knowledge revisions and retains all their evidence without modifying
them. Merge does not imply supersession; an optional explicit `supersedes` list
records that separately. `defer` and `exclude` forbid output bodies and retain a
private disposition/rationale rather than deleting source material.

## Human authority

Approved or rejected items require a separate top-level human `review_authority`
matching the per-item reviewer, with an explicit review time and rationale.
Agent-produced proposals without that assertion remain proposed/unreviewed.
Permission to apply writes does not supply knowledge review. The authority is a
trusted local operator assertion, not an authenticated identity-provider claim.

A normal flow is: author proposed candidates, preview them, inspect exact evidence,
edit the plan with explicit per-item review and lifecycle decisions, preview the
changed plan, then apply its exact new digest. Applying a previously stored
proposal does not silently approve it. Changed or conflicting canonical artifacts
require another reviewed artifact/revision; no original is overwritten.

## CLI

```bash
mindgarden gardenize --local-config "/private/bindings.json" \
  --plan "/private/candidate-plan.json"
mindgarden gardenize --local-config "/private/bindings.json" \
  --apply "/private/candidate-plan.json" --plan-digest "REVIEWED_SHA256"
```

The preview is a `mindgarden.change-plan/v1` with the complete authored proposal,
output checksums, source/configuration digests and target revision. It contains
private review material and belongs within the input scope. The canonical
curation receipt's `plan_sha256` identifies the authored proposal file; a routed
public derivative instead binds a canonical public-only selection, with its raw
private request digest retained in the personal controller. The CLI
apply digest identifies the complete preview. Neither is a self-hash.

Preview validates schemas, exact evidence, identities, human authority and target
conflicts before writes. Apply repeats checks, validates the staged complete
garden and uses the shared non-overwriting cutover. Changed sources/proposals
invalidate review. Raw originals and existing note bytes remain intact.

## Reproducible checkpoint

`tests/fixtures/curation/` contains synthetic source text and an authored plan.
`tests/test_curation.py` prepares its exact source and merge inputs, previews and
applies all dispositions, verifies uncertainty/contradiction retention and proves
that agent proposals stay unreviewed. No model service is used.

The checkpoint has one explicit local target. Cross-garden routing is #14;
optional extraction producers, broader attachment/infographic selection and the
full multi-route acceptance scope of #13 remain open. Publication is excluded
for these derived private records and requires an independent reviewed handoff.

## Transformation follow-up checkpoint

Merges retain prior authors, caveats, uncertainty and contradiction references.
The derivative records each prior attribution and epistemic state; differing
attributions become `mixed`. Duplicate references to one merge input do not count
as two knowledge inputs. Existing relationship and supersession targets require
an exact represented revision. Logical references between outputs created in the
same digest-bound plan remain supported.

Claims may use only source selectors retained in the candidate's evidence set.
Optional authored `redactions` identify an exact selected source and rationale;
they are recorded in derivative qualifications and transformation provenance.
The service applies the supplied derivative text, without rewriting originals or
claiming to detect or perform automatic redaction. Sensitivity inheritance still
applies after redaction; it does not grant public-release authority.

`tests/test_curation_transformations.py` covers these cases alongside the six
existing dispositions. Optional entity/triple producers, batch resumption and
model evaluation remain separate parent scope.
