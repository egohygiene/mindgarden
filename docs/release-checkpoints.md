# Provider, consumer and release checkpoints

The maintainer authorized #51 → #27 → #20 → #19. The live refresh found #93 open
and draft, no published GitHub releases, and main at
`d5edb13de1b65871ec85e7a25af035228a1d756d`. This batch leaves small drafts for
review and preserves the existing Python engine, canonical contracts and v0
compatibility. Deferred #86–#91 remain deferred.

## Dependency reconciliation

- #51 is a deterministic recovery proof over existing scoped context/evidence
  services. Broader #49 memory and #47 application work are related integration
  proofs, not prerequisites for two local fixture adapters.
- #27 preparation can advance independently of the complete #20 pilot. Aether
  #61, Hygiene #27 and Relay #46/#47 are closed, but the published Hygiene release
  policy and ADR still say proposed/null approval. Preserve that distinction.
  EgoLint #29 remains open, with current-v1 validators available; do not claim its
  broader fixture/dogfood acceptance is complete.
- #20 synthetic composition can advance on current source interfaces. Aether #51,
  Relay #40 and Empathy #65 remain open. An approved private archive/workspace and
  actual consumer evidence are required for their respective acceptance; public
  synthetic tests cannot replace them. Avoid the old circular dependency on the
  Mindgarden #1 umbrella, as Empathy #65's reconciliation explicitly requires.
- #19 follows actual #20 acceptance, released-version Empathy consumption and
  configured protected OIDC publication. A useful candidate bundle does not mean
  1.0 has shipped. No tag, package, site or release is published by PR validation.

These are proposed bounded dependency corrections. They do not close parents,
ratify ADRs, invent missing contracts or authorize reading private consumer data.

## Checkpoint stack and exact next action

| Issue | Bounded checkpoint / branch | State and evidence | Remaining / next action |
| --- | --- | --- | --- |
| #51 | `feature/51-provider-switch-proof` over #93 | Source demo matches the committed provider recovery golden; focused tests running | Finish compatibility/clean-engine evidence; open the first coherent draft |
| #27 | Release declaration, authoritative version, reproducible artifacts and pinned shared tooling | Contract/owner inventory complete; no implementation in this checkpoint yet | Prepare a reviewable release flow; record external PyPI/signing states honestly |
| #20 | Complete synthetic archive→review→private fallback/public projection composition | Earlier local/mixed source proofs exist | Extend the composition; prepare an explicitly scoped private pilot and pinned Empathy handoff |
| #19 | Acceptance and release readiness | Blocked by actual acceptance and external delivery setup | Prepare precise checks/artifacts; publish 1.0 only when acceptance and authority are evidenced |

The stack base is draft #93, preserving the new native registry proof in the
combined checkout. That checkout dependency is distinct from the contracts above.
Each checkpoint records its exact source, tests, blockers and subsequent branch.
The new drafts are left for review; no existing draft is automatically merged by
the request for this next batch.
