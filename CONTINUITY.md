---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-14T20:35:10Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: Audit independent backlog work and implement explicit packet currentness, then per-file reviewed Drive
    normalization, using synthetic fixtures.
  includes:
  - listed-criteria acceptance audit
  - bounded ready integration checkpoints and tested merges
  - synthetic fixtures and exact recovery evidence
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
  - AGENTS.md
  - README.md
  - AI_CONSTITUTION.md
  - ARCHITECTURE.md
  - SYSTEM.md
  - ROADMAP.md
  - docs/open-issue-coverage.md
  - docs/decisions/README.md
  - docs/local-consultation-workflow.md
  - docs/freshness-mapping-sprint.md
  - docs/dependency-builds.md
  - docs/compaction-retention.md
  - docs/consultation-packets.md
  - examples/mock-garden/README.md
  - docs/curation-routing-design-acceptance.md
  - docs/csv-ledger-mappings.md
  - docs/evidence/freshness-mapping-qualification.json
  - docs/remaining-work-and-local-setup.md
  - docs/evidence/freshness-mapping-stack-merge.json
  - docs/private-pilot.md
  - docs/repository-audit-followthrough.md
work:
  objective: Audit independent backlog work and implement explicit packet currentness, then per-file reviewed
    Drive normalization, using synthetic fixtures.
  success_conditions:
  - Complete bounded synthetic checkpoints with exact evidence and explicit review authority.
  - Preserve Python/v0, original sources, live scope enforcement and proposed ADR status.
  - Keep real inputs/credentials outside the repository and report unavailable live/private contracts honestly.
  active_issue:
    provider: github
    id: egohygiene/mindgarden#90
    url: https://github.com/egohygiene/mindgarden/issues/90
  next:
    kind: action
    id: repository-audit-packet-checkpoint
    description: 'Finish local packet-currentness checks, push the first draft on documentation PR #148, then
      compose reviewed per-file CSV mappings with the captured Drive adapter in a dependent draft. Mac setup is
      parked; actual Drive/Codex/private processing and owner decisions remain separate.'
    readiness: ready
    references:
    - docs/repository-audit-followthrough.md
    - docs/consultation-packets.md
    depends_on: []
state:
  base:
    revision: 136c6638d019746ca8fd8fbee7abd32e978ec3e3
    ref: refs/heads/docs/merged-stack-and-remaining-plan
    verified_at: '2026-11-14T20:35:10Z'
  candidate:
    branch: feature/90-packet-freshness
    revision: null
    pull_request: null
    handoff_state: in-progress
  live:
    status: verified
    observed_at: '2026-11-14T20:35:10Z'
    default_branch_revision: 270ced6a5d6ea0d4c07298fdcfebcae2363b7c8a
    issue_state: open
    pull_request_state: draft
    notes: 'Main remains 270ced6; only documentation draft #148 was open at refresh. All 34 open issues and selected
      comments refreshed. Packet dependency manifest/read-only comparison is implemented on feature/90-packet-freshness;
      functional verification is in progress. No parent closure, new issue or merge; original four root WIP entries
      untouched.'
  parallel_changes: []
review:
  status: partial
  reviewed_at: '2026-11-14T20:35:10Z'
  reviewed_by: codex
  evidence:
  - command: ruff check and ruff format --check on new packet-currentness modules/fixtures; git diff --check
    outcome: passed
    observed_at: '2026-11-14T20:35:10Z'
    notes: Scoped lint/format and whitespace pass. Runtime checks are still running; no full or final CI pass
      is claimed.
  - command: Python 3.12 -m unittest tests.test_packet_freshness tests.test_consultation --quiet (initial attempt)
    outcome: failed
    observed_at: '2026-11-14T20:35:10Z'
    notes: '23 cases ran in 260.458s: 22 passed and one new test imported a nonexistent fixture helper. Corrected
      to the actual FilesystemVault._object_path; fresh checks are running. This failure is not product qualification.'
  environment_limitations:
  - Actual private pilot, OAuth/Drive/Codex/model quality and confidential runtime remain unperformed; actual
    configuration/classification/consumer authority required.
  - 'Hygiene #39, Realm #28/#29/#30, Relay #5/#27/#33, Pace #5, Akashic #173–#176 and Empathy #65 refreshed open;
    owner issue status is not ADR approval.'
  - 'Full local/act and manual accessibility remain separate; #19/#27 and #88/#91 stay deferred.'
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

The maintainer parked Mac setup and authorized independent repository audit/implementation. Continue bounded existing issues with synthetic data and draft PRs; no ADR ratification, release, merge or unspecified private-source authority is implied.

## Resume protocol

Refresh live issues/comments/PRs and read the audit follow-through, coverage and current contracts. Use the isolated stack based on #148; preserve all four original root WIP entries and prior worktrees.

## Current objective and success conditions

Audit independent backlog work and implement explicit packet currentness, then per-file reviewed Drive normalization, using synthetic fixtures.

## State snapshot

Main remains 270ced6; only documentation draft #148 was open at refresh. All 34 open issues and selected comments refreshed. Packet dependency manifest/read-only comparison is implemented on feature/90-packet-freshness; functional verification is in progress. No parent closure, new issue or merge; original four root WIP entries untouched.

## Completed and material changes

Added private versioned packet dependency comparison metadata, authority-neutral exact fingerprints and a read-only --previous-manifest mode. Current grants/evidence gate prior metadata access; historical-only identifiers are excluded. Corrections require a fresh reviewed apply and new output. Old packets and originals remain intact. Drive per-file mapping composition is next, not yet implemented.

## Validation and review evidence

Scoped lint/format/whitespace pass. The initial 23-case run had one corrected test-helper import error; current 3.12 broader and 3.13 focused checks are in progress. No pending run is called passing; main's prior qualification remains separately pinned in its existing receipts.

## Blockers, risks, unknowns, and deferred work

Mac/M3 information was supplied, but installation is parked at the maintainer's request. Real locations/collection, credentials and applicable consumer/runtime authority remain unavailable; actual private pilot/model accuracy and normative policy decisions remain separate. #19/#27 and #88/#91 stay deferred.

## Next dependency-ready work

Finish local packet-currentness checks, push the first draft on documentation PR #148, then compose reviewed per-file CSV mappings with the captured Drive adapter in a dependent draft. Mac setup is parked; actual Drive/Codex/private processing and owner decisions remain separate.

## Parallel changes and reconciliation

Unmerged documentation #148 is the explicit base. New code drafts form a documented stack; the last child retains a reproducible combined checkout. Preserve original root WIP and all existing worktrees. Do not auto-merge new drafts or overwrite historical evidence.

## Privacy and redaction

Synthetic fixtures/evidence only. Real gardens, financial records, credentials, reports and private consumer configuration stay outside this public repository. Current offline source grants do not authorize hosted-model forwarding. No secret is requested in chat.

## Handoff update protocol

Record exact branch/PR, source/merge commits, tests and CI observations, remaining parent criteria, blockers and next action. Keep all 44 coverage rows and 24 proposed/null-approval ADRs. New setup defects get specific follow-ups only after the pilot reveals them.

## Compaction and supersession

Preserve twelve headings and 16384-byte/240-line bounds. The merge receipt supersedes earlier draft/pending snapshots without rewriting historical qualification. Proposed finishing order is for the requested sync; it does not start another batch.
