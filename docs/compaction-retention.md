# Authored compaction and retention v1 checkpoint

The three versioned contracts are
[compaction-plan](../contracts/v1/compaction-plan.schema.json),
[retention-policy](../contracts/v1/retention-policy.schema.json) and
[compaction-manifest](../contracts/v1/compaction-manifest.schema.json).
The supported reader/evaluator is implemented on this draft. Retention policy and
the broader lifecycle remain proposals under ADR-0019; organization policy,
private-pilot acceptance and destructive operation are not ratified here.

## Hierarchy and evidence

An authored hierarchy represents immutable source citations → normalized segments
→ source summaries → durable knowledge → cross-source synthesis → bounded context
or publication proposals. Nodes are derived control/projection artifacts, not a
competing Garden model. Durable outputs use existing knowledge/provenance/curation
contracts; source bytes, logical identity and physical vault location remain separate.

Every statement requires exact source identity/revision, locator and selected-byte
hash, attribution, epistemic state, uncertainty, contradiction notes and explicit
fact-validity state/dates/reason. A normalized segment quotes its exact selection.
Later layers retain contributing citations and qualifications. Missing evidence,
cycles, dangling references, duplicate IDs, weakened attribution, silent promotion
of inference, lost uncertainty/contradictions and falsely current expired facts
fail closed. Cross-source synthesis requires two represented source identities.
Authored annotations are reviewable claims; checks do not adjudicate factual truth.

Actions are keep, merge, summarize, reference, defer, discard-proposed and supersede.
Discard-proposed means omit a proposed output; it never deletes evidence.
Supersession names retained exact knowledge references. Deferred/discard-proposed
nodes cannot be selected outputs. Exact text groups and bounded token-Jaccard
near-duplicate pairs are recommendations requiring review; identities, evidence
and conflicting qualifications are never silently merged.

## Scoped read-only evaluator and curation handoff

```sh
mindgarden compaction preview --input authored-plan.json \
  --local-config explicit-bindings.json --scope explicit-session.json \
  --curation-plan authored-curation.json
```

The evaluator reuses existing scoped retrieval and exact-evidence services. It
requires context/evidence capabilities and a permitted Garden. The first checkpoint
consumes citations already visible in the authorized reviewed-knowledge closure;
it does not grant an agent new raw-archive access. A first-pass raw-only compactor
needs an explicit source-access contract and is outside this reader's scope.
The synthetic archive fixture establishes reviewed evidence anchors through the
existing authored curation path before evaluating additional layers.

Scope inherits every source/parent restriction under the existing local policy.
Unknown policy, unavailable restricted assurance and a public budget applied to
private knowledge fail closed. There is no public aggregate report: proof and
dependency manifests are `machine-local-control` / `never-exportable`, including
IDs, counts, source metadata and authority digests. Shareable error diagnostics
omit payloads and paths. Source instructions remain untrusted evidence.

The optional handoff pins a canonical existing `curation-plan/v1` document and
binds each candidate to one node. Action, rationale, body, exact evidence,
attribution, uncertainty, caveats and supersession must agree. This initial bridge
supports knowledge outputs; embedded claim/synapse generation remains separate.
Approved output requires the existing explicit human review record. Unreviewed
output remains unreviewed. Preview performs no writes or review promotion.

Apply that separately reviewed proposal through existing `gardenize --plan` /
`gardenize --apply ... --plan-digest ...`. A preview digest is not an apply token.
The ordinary curation digest binds exact current inputs and never overwrites
originals. Retain the authored hierarchy, curation proposal and generated manifest
together. Canonical curation provenance records the proposal digest/candidate and
exact evidence; automatic manifest discovery/storage is future #37/#46 integration.

## Separate retention classes and budgets

| Class | Supported contract | Remaining operation |
| --- | --- | --- |
| Archival/source | Preserve originals; deletion unsupported | Provider/backups/hold/deletion policy and approved destructive proof |
| Durable knowledge | Explicit review; superseded knowledge retained with lineage | Human lifecycle disposition and approved pilot |
| Model context | Ephemeral declaration, byte cap and bounded TTL | Actual persistence/expiry jobs and consumer enforcement |
| Publication | Separate review, declared TTL, revoke by invalidation/rebuild | Deployed revocation/expiry and host acceptance |

Repository, organization, personal, agent and publishing detail profiles have
explicit statement/byte budgets. Complete preview/provenance also fits the
session and model-context byte ceilings. Retention TTLs are validated declarations
in this checkpoint; no scheduler, deletion, memory store or deployed expiry service
is implemented. Existing session expiration/revocation still gates every read.
Context expiration cannot authorize source deletion. Publication-candidate nodes
remain private proposals until an independent reviewed public flow permits them.

## Determinism and incremental invalidation

Node revisions bind authored content, exact evidence, input-node revisions,
effective scope and the applicable retention class. Unchanged inputs produce
identical manifests. Changed source evidence invalidates its branch and descendants;
unrelated branches retain their revisions. A model-context TTL change affects its
context/publication descendants without changing upstream summaries.

`invalidated_nodes(previous, current)` compares complete, matching-scope private
manifests. Callers must already hold authority for both; it is not a public
discovery endpoint. These manifests prove a bounded hierarchy, not #37's complete
dependency scheduler, cache invalidation or fleet reconciliation.

## Synthetic proof and quality limits

[Committed fixtures](../tests/fixtures/compaction/README.md) contain an authored
13-node hierarchy, retention policy, reviewed evidence anchors, curation proposal
and deterministic expected proof. They use the existing tested v3.2.3 synthetic
conversation package, including alternate-branch attribution and inert malicious
instructions. The proof produces a reviewed prompt, retrieves both exact message
citations and emits a bounded context pack without changing originals.

```sh
python -S scripts/compaction_demo.py --require-source --workspace new-proof --report proof.json
python -m unittest tests.test_compaction --verbose
```

Measures include 17 statements with verified evidence, two distinct exact citations,
84 selected source bytes, 75 selected derived-text bytes (ratio 0.893), two authored
fixture fact bindings represented, retrieval inclusion and privacy negatives.
These are structural/provenance and authored-fixture measures, not automatic
factual verification or a general summary-quality score. Model proposal quality,
large-archive scaling, full raw-only compaction, retention execution and the
explicitly approved private pilot remain open #46 scope. #20 gates that full pilot,
not this early non-destructive contract checkpoint.

This is additional bounded synthetic evidence for #20 through draft #73; its
broader publication and consumer acceptance criteria remain open.
