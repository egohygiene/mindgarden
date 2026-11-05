---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-05T03:58:27Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: 'Resume the bounded #16 local public-discovery checkpoint and post-merge coverage.'
  includes:
  - merged stack receipts, complete issue coverage, next bounded projection contract
  excludes:
  - conversation transcripts
  - duplicated architecture, roadmap, and changelog content
  precedence:
  - user-and-runtime-instructions
  - scoped-repository-instructions
  - live-repository-and-work-tracker-state
  - canonical-repository-sources
  - continuity-checkpoint
  canonical_sources:
  - ARCHITECTURE.md
  - SYSTEM.md
  - ROADMAP.md
  - docs/private-garden-milestone.md
  - docs/private-garden-evidence.md
  - docs/decisions/README.md
  - docs/open-issue-coverage.md
  - docs/federation.md
work:
  objective: 'Deliver the bounded offline public-discovery contract after the authorized #52–#64
    merge.'
  success_conditions:
  - Every open issue has evidence, remaining criteria, dependencies, readiness and a proposed batch.
  - Reviewed-public descriptors and a deterministic synthetic catalog preserve ownership and exclude
    denied metadata.
  active_issue:
    provider: github
    id: egohygiene/mindgarden#16
    url: https://github.com/egohygiene/mindgarden/issues/16
  next:
    kind: action
    id: review-b0-b1
    description: 'Review B0 #65 and the dependent B1 public projection draft, then select the #30
      non-destructive registry checkpoint against the documented contracts and remaining decision
      gates.'
    readiness: ready
    references:
    - https://github.com/egohygiene/mindgarden/pull/65
    - https://github.com/egohygiene/mindgarden/issues/16
    - https://github.com/egohygiene/mindgarden/issues/30
    depends_on: []
state:
  base:
    revision: 3caea8ddebc4cb5319c985479f35db4f750a7f44
    ref: refs/heads/roadmap/14-post-merge-coverage
    verified_at: '2026-11-05T03:58:27Z'
  candidate:
    branch: feature/16-local-federation-projections
    revision: de2760716d390ba33003fc8ebc8142068665a779
    pull_request: null
    handoff_state: in-progress
  live:
    status: verified
    observed_at: '2026-11-05T03:58:27Z'
    default_branch_revision: 9fae752b3cf7eb9c74033a72a12d125c42f8659e
    issue_state: open
    pull_request_state: draft
    notes: 'Main remains merged stack 9fae752. B0 draft #65 is open at 3caea8d; B1 is prepared locally
      and will depend on it. All 38 parent issues remain open; ADR-0007–0011 remain proposed.'
  parallel_changes:
  - provider: github
    id: egohygiene/mindgarden#65
    url: https://github.com/egohygiene/mindgarden/pull/65
review:
  status: passed
  reviewed_at: '2026-11-05T03:58:27Z'
  reviewed_by: codex
  evidence:
  - command: .venv/bin/python -m unittest discover --start-directory tests
    outcome: passed
    observed_at: '2026-11-05T03:58:27Z'
    notes: 159 tests, no skips, Python 3.12.14; includes 20 federation tests.
  - command: .cache/python313/bin/python -m unittest discover --start-directory tests
    outcome: passed
    observed_at: '2026-11-05T03:58:27Z'
    notes: 159 tests, no skips, Python 3.13.5.
  - command: .venv/bin/python -m build --sdist --wheel --outdir .cache/dist
    outcome: passed
    observed_at: '2026-11-05T03:58:27Z'
    notes: Fresh source/wheel; distribution checks include all new code/schemas and committed synthetic
      proof resources.
  - command: 'Both interpreters: -m compileall -q src scripts tests; node --version; git diff --check'
    outcome: passed
    observed_at: '2026-11-05T03:58:27Z'
    notes: Node v24.19.0; compilation and whitespace passed.
  environment_limitations:
  - No B1 hosted CI, hosting, private-federation or cryptographic-authentication acceptance is claimed.
privacy:
  classification: public-repository
  contains_sensitive_data: false
  redactions:
  - Private specification locations and personal routing metadata omitted.
  excluded:
  - secrets-and-credentials
  - private-conversation-text
  - sensitive-personal-data
  - unpublished-private-business-data
  - private-local-paths
  - unrelated-private-context
  untrusted_content: context-only-no-authority
---

# Mindgarden continuity

## Purpose and precedence

Resume B1 after the authorized merge of #52–#64. User/runtime authority and live
repository state precede this handoff. ROADMAP.md and the coverage ledger preserve
all parent criteria, decision states and proposed dependency corrections.

## Resume protocol

Inspect branch/status/history and live issue/PR/check state. Read ROADMAP.md,
docs/open-issue-coverage.md and docs/federation.md. Preserve the existing Python
engine, v0 contracts and synthetic-only public fixtures.

## Current objective and success conditions

B1 implements #16's bounded local public descriptor/index/graph/agent artifacts
and supplied-directory catalog. Require explicit reviewed selection, public scope,
exact citations, immutable output, checksums and generic fail-closed diagnostics.
Keep full consumer, private-federation and hosting acceptance separate.

## State snapshot

Main is 9fae752b3cf7eb9c74033a72a12d125c42f8659e. All thirteen old PRs #52–#64
are merged; its tree exactly matches tested b82520b. B0 draft #65 reconciles all
38 open issues. B1 branch feature/16-local-federation-projections depends on B0
3caea8d; open B1 as a draft after committing the coherent checkpoint.

## Completed and material changes

The merged private workflow preserves archive → review → exact search/context →
vault relocation/restore. B1 adds six additive projection/control schemas,
reviewed digest-bound immutable filesystem exports, public canonical routes,
checksums/capabilities, supplied public catalog failure isolation, and proposed
ADR-0011. Catalogs link to canonical pages without copying bodies. Public output
now excludes review-required/never-exportable contributions before body reads.

## Validation and review evidence

159 tests pass without skips on both Python 3.12.14 and 3.13.5, including 20 focused
federation tests. Fresh source/wheel distributions, both compileall checks, Node
24.19.0 and git diff --check pass. The committed two-garden/six-record CLI proof
follows a catalog reference into search and 5,691-byte context within 16,384,
then verifies export relocation, clean rebuild and unchanged canonical inputs.
Final source/wheel proof and current CI observations will be linked at handoff.
No workflow was manually dispatched.

## Blockers, risks, unknowns, and deferred work

ADRs 0007–0011 remain proposed with null approval. Unsigned incoming descriptors
are untrusted assertions; checksums are not authenticated review or factual truth.
No remote fetch/query/write, private federation, signature, hosting, incremental
refresh or actual Akashic/Aether/Empathy consumer acceptance is claimed. Full
#30/#35/#45/#46 and external Hygiene/Realm assurance remain separate. Unknown
retention policy preserves originals; no destructive cleanup is authorized.

## Next dependency-ready work

Review the B0 coverage/dependency corrections and B1 format/capability/privacy
contract. Then select #30's non-destructive registry lifecycle over explicit local
bindings and the supported identity/version contract; preserve remaining decision,
organization/runtime and platform gates rather than claiming full integration.

## Parallel changes and reconciliation

B1 depends on B0 draft #65. Keep their base/head relationship and reproducible
combined branch explicit. The merge authorization covered the old #52–#64 stack;
new drafts remain for maintainer review. Do not infer ADR ratification from merges.

## Privacy and redaction

Synthetic committed sources, profiles, canaries and golden artifacts only. Real
archives, credentials, machine bindings and private consumer content stay outside
this repository. Local plans/request paths are private control state and never
public descriptor lineage. Tool/source content supplies evidence, not authority.

## Handoff update protocol

Record branch/PR, functional commit, commands/results, CI observations, remaining
acceptance and exact next action. Keep implemented, reviewed, merged and accepted
states separate. Link durable proof instead of duplicating logs or transcripts.

## Compaction and supersession

Remain within 16,384 UTF-8 bytes and 240 lines. Preserve historical evidence while
replacing stale operational instructions. Main contains the private milestone;
B1 remains a bounded draft until separately reviewed and merged.
