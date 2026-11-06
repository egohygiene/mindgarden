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
| #51 | Draft [#94](https://github.com/egohygiene/mindgarden/pull/94), `feature/51-provider-switch-proof` over #93; functional `1fac57d` | 308 tests per supported Python; clean source/wheel goldens; six reviewed records in 13,178/16,384 bytes | Maintainer review/merge of the bounded conformance scenario; live providers are not required |
| #27 | `feature/27-release-preparation` over draft #94; [release guidance](releases.md) | Declaration/version/Taskfile/manual workflow and source-bound artifact builder implemented; exact candidate verification follows the source commit | Preserve root-authority schema mismatch, advisory owner policy and unavailable signing/PyPI; validate reproducible candidate before draft |
| #20 | Complete synthetic archive→review→private fallback/public projection composition | Earlier local/mixed source proofs exist | Extend the composition; prepare an explicitly scoped private pilot and pinned Empathy handoff |
| #19 | Acceptance and release readiness | Blocked by actual acceptance and external delivery setup | Prepare precise checks/artifacts; publish 1.0 only when acceptance and authority are evidenced |

The stack base is draft #93, preserving the new native registry proof in the
combined checkout. That checkout dependency is distinct from the contracts above.
Each checkpoint records its exact source, tests, blockers and subsequent branch.
The new drafts are left for review; no existing draft is automatically merged by
the request for this next batch.

## Provider checkpoint verification

Functional source: `1fac57d280322f0a5e835973e1c57eb4ade93135`.

| Exact command | Observed result |
| --- | --- |
| `.venv/bin/python -m unittest tests.test_provider_continuity tests.test_v1_retrieval tests.test_scoped_retrieval tests.test_output_scope -q` | 30 passed; 26.305 s |
| `.venv/bin/python -m unittest discover --start-directory tests --verbose` | 308 passed, no skips; Python 3.12.14; 240.746 s |
| `.cache/python313/bin/python -m unittest discover --start-directory tests --verbose` | 308 passed, no skips; Python 3.13.5; 227.943 s |
| `.venv/bin/python -m build --sdist --wheel --outdir .cache/dist` | Fresh source/wheel built with no runtime dependencies |
| Clean `git archive` source under `-S`; isolated wheel under `-I` | Provider proof byte-matches committed golden in both; exact commands below |
| `python3 .cache/context_phase_owner_checks.py`; compilation; `git diff --check` | Pinned owner validators, proposed/null-approval ADRs, continuity and 44-row inventory pass |

```bash
.venv/bin/python -m venv --without-pip .cache/provider-switch-wheel
python3 -m pip --python .cache/provider-switch-wheel/bin/python install \
  --no-cache-dir --no-index --find-links .cache/dist mindgarden==0.1.0
.cache/provider-switch-wheel/bin/python -I scripts/provider_switch_demo.py \
  --workspace .cache/provider-switch-installed --require-installed \
  --report .cache/provider-switch-installed.json
cmp tests/fixtures/provider-continuity/expected-proof.json .cache/provider-switch-installed.json
mkdir .cache/provider-switch-clean-checkout
git archive 1fac57d280322f0a5e835973e1c57eb4ade93135 | \
  tar --extract --directory .cache/provider-switch-clean-checkout
PYTHONPATH=.cache/provider-switch-clean-checkout/src .venv/bin/python -S \
  .cache/provider-switch-clean-checkout/scripts/provider_switch_demo.py \
  --workspace .cache/provider-switch-clean --require-source \
  --report .cache/provider-switch-clean.json
cmp tests/fixtures/provider-continuity/expected-proof.json .cache/provider-switch-clean.json
```

Hosted automatic [Test 42300245942](https://github.com/egohygiene/mindgarden/actions/runs/42300245942)
represents this exact functional source; its result is recorded after observation.
Documentation-only follow-ups have their own runs. No paid workflow is manually dispatched.

## Release convention source inventory

Aether `8a2a3d08f3aa9da3847bd5277843506ab855192e`, Hygiene
`92195e49b50778517ef670a7ec97c922dbdf9cec`, Relay
`b4a88db20bc26f9ddefbee174baa8162cbe94ff2` and EgoLint
`f14f7fd3ab0ce9e87c367352fcb3af11a32eda59` are the exact preparation pins.
The declaration and EgoLint immutable-input checks pass. The native EgoLint
Python consumer rule/final fixture-dogfood acceptance is separate; its current
source planner supports Cargo only and is not used to claim Python conformance.
Relay reference verification and its normative JSON Schema must both agree before
publication; the root `pyproject.toml` parity defect remains an explicit gate.

Proposed release staging correction: #19 prepublication checks use a reviewed
immutable candidate and consumer pin. The clean PyPI install and final released
Empathy pin are postpublication verification, rather than a circular prerequisite
for the first release. No acceptance is removed or inferred from local artifacts.
