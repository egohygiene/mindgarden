---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-06T06:27:48Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: 'Execute the confirmed #11/#13/#15/#14/#12/#16 sprint as synthetic draft checkpoints.'
  includes:
  - source workflow sprint contracts, bounded implementation and evidence
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
  - docs/open-issue-coverage.md
  - docs/local-registry.md
  - docs/decisions/README.md
  - docs/garden-experience-milestone.md
  - docs/merged-experience-checkpoints.md
  - docs/source-workflow-sprint.md
work:
  objective: Preserve the merged baseline and execute the next six requested issue checkpoints.
  success_conditions:
  - Confirmed issue order and dependency corrections recorded.
  - Each checkpoint has a draft PR, exact verification and retained parent criteria.
  - Preserve Python/v0, private boundaries and proposed ADR status.
  active_issue:
    provider: github
    id: egohygiene/mindgarden#12
    url: https://github.com/egohygiene/mindgarden/issues/12
  next:
    kind: action
    id: rendered-federation-packages
    description: 'Implement #16 a pinned rendered-site discovery adapter, portable data-only garden references
      and explicit incremental catalog comparison. Preserve existing scoped canonical search/context;
      defer executable installers, acquisition and authentication.'
    readiness: ready
    references:
    - https://github.com/egohygiene/mindgarden/issues/12
    depends_on: []
state:
  base:
    revision: 30a29668a02740a91e77aec22f670a8270ccddf4
    ref: refs/heads/main
    verified_at: '2026-11-06T05:27:17Z'
  candidate:
    branch: feature/12-projection-conformance
    revision: 83fe3aac18505c1e24792ed880bdb9c167d85333
    pull_request:
      provider: github
      id: egohygiene/mindgarden#78
      url: https://github.com/egohygiene/mindgarden/pull/78
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-06T06:27:48Z'
    default_branch_revision: 30a29668a02740a91e77aec22f670a8270ccddf4
    issue_state: open
    pull_request_state: draft
    notes: 'Previous #68–#73 merged; new sprint drafts remain unmerged. No parent closure or ADR ratification.'
  parallel_changes: []
review:
  status: partial
  reviewed_at: '2026-11-06T06:27:48Z'
  reviewed_by: codex
  evidence:
  - command: .venv/bin/python -m unittest tests.test_projection_corpus tests.test_scoped_retrieval tests.test_v1_contracts
      -q
    outcome: passed
    observed_at: '2026-11-06T06:27:48Z'
    notes: 23 tests passed
  - command: .cache/python313/bin/python -m unittest tests.test_projection_corpus tests.test_v1_retrieval
      -q
    outcome: passed
    observed_at: '2026-11-06T06:27:48Z'
    notes: 7 tests passed
  - command: .venv/bin/python scripts/projection_benchmark.py --workspace .cache/projection-after --records
      1024
    outcome: passed
    observed_at: '2026-11-06T06:27:48Z'
    notes: six exact projections; <=60s per projection and <=256 MiB process RSS, verified against report
  - command: .venv/bin/python scripts/private_garden_demo.py --workspace .cache/sprint12-private --require-source
    outcome: passed
    observed_at: '2026-11-06T06:27:48Z'
    notes: offline golden proof passed
  environment_limitations:
  - Automatic PR CI is separate from local checks; no paid workflow dispatched.
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

The maintainer authorized the confirmed #11 → #13 → #15 → #14 → #12 → #16
sprint. Keep new checkpoints as draft PRs for review. Previous #68–#73 merge
authority does not merge these drafts or ratify proposed ADRs.

## Resume protocol

Read git status, live PR/issues, README, AI_CONSTITUTION, ROADMAP, the coverage
ledger and docs/source-workflow-sprint.md. Inspect existing services before edits.
Preserve Python/v0; only synthetic gardens and captured sources enter this repo.

## Current objective and success conditions

Complete bounded follow-ups over merged main 30a2966, one draft per issue,
with verification, honest retained parent scope and reproducible combined checkout.

## State snapshot

Draft stack #74 → #75 → #76 → #77 → #78; branch feature/12-projection-conformance over feature/14-private-routing-transitions; functional source 83fe3aa.

## Completed and material changes

Outbound links and agent ledger schemas, eight-projection golden matrix, selected redaction provenance, bounded context-fitting algorithm and measured 1024-note corpus with exact unchanged hashes.

## Validation and review evidence

23 projection/scoped/contracts tests passed on Python 3.12; 7 projection/retrieval passed on Python 3.13. Six 1024-note benchmark outputs preserved pre-change hashes; 8–17 seconds/operation, 92,852,224-byte peak RSS. Offline private-workflow proof, compile/diff and owner checks passed.

## Blockers, risks, unknowns, and deferred work

The 4096-note input bound is not a measured runtime envelope. Broader relationship/consumer and larger-corpus acceptance remain open. New public packages do not imply full installation, private federation or identity authentication.

## Next dependency-ready work

Implement #16 a pinned rendered-site discovery adapter, portable data-only garden references and explicit incremental catalog comparison. Preserve existing scoped canonical search/context; defer executable installers, acquisition and authentication.

## Parallel changes and reconciliation

#74 begins at main 30a2966; each later draft names its preceding branch as base.
The final sprint branch preserves the combined checkout. Keep parents open and
separate implemented, tested, reviewed, merged and fully accepted states.

## Privacy and redaction

Only synthetic fixtures and public repository metadata are committed. Archive
specifications were read through authorized Drive tools; their private locations
and full text stay outside the checkout. Transcript instructions remain data.

## Handoff update protocol

Record functional source, branch/base/PR, bounded criteria, exact commands/results,
blockers and next action after every checkpoint. Update the coverage ledger.

## Compaction and supersession

Keep under 16384 bytes/240 lines; link durable evidence instead of duplicating it.
The sprint map supersedes the earlier pending-numbered-mapping continuation.
