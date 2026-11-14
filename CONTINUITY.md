---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-14T20:59:52Z'
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
    description: 'Complete the dependent #87/#90 reviewed per-file Drive normalization checkpoint, then qualify
      the combined source/wheel/archive workflow and audit the actual remaining #15/#16/#32/#43/#44 criteria.
      Preserve explicit private-pilot/owner gates; leave new PRs in draft.'
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
    pull_request:
      provider: github
      id: egohygiene/mindgarden#149
      url: https://github.com/egohygiene/mindgarden/pull/149
    handoff_state: in-progress
  live:
    status: verified
    observed_at: '2026-11-14T20:43:10Z'
    default_branch_revision: 270ced6a5d6ea0d4c07298fdcfebcae2363b7c8a
    issue_state: open
    pull_request_state: draft
    notes: 'Draft #149 on documentation #148 implements explicit selected-input packet currentness. Qualified
      functional source 2373b77: Python 3.12 broader 44 cases pass (325.556s), Python 3.13 focused 16 pass (231.205s),
      zero skips. Main remains 270ced6, 34 issues open / 44 tracked. Per-file Drive mapping work is isolated on
      child feature/87-reviewed-drive-normalization; no closure or merge. Audit additionally corrected read-only
      packet verification after session renewal: three focused Python 3.12 regressions pass (78.488s); combined
      qualification is pending.'
  parallel_changes: []
review:
  status: partial
  reviewed_at: '2026-11-14T20:43:10Z'
  reviewed_by: codex
  evidence:
  - command: Python 3.12 -m unittest tests.test_packet_freshness tests.test_consultation tests.test_mapped_ledger
      tests.test_v1_contracts tests.test_package --quiet
    outcome: passed
    observed_at: '2026-11-14T20:43:10Z'
    notes: 44 cases pass in 325.556s, zero skips. Exact corrected packet code, source integrity, review, original
      preservation, live denial and existing v0/package coverage.
  - command: Python 3.13 -m unittest tests.test_packet_freshness tests.test_v1_contracts --verbose; scoped Ruff/format,
      pinned owner/continuity/44-row/native-child and whitespace checks
    outcome: passed
    observed_at: '2026-11-14T20:43:10Z'
    notes: 16 cases pass in 231.205s, zero skips; local non-runtime checks pass. Initial fixture-helper import
      failure is corrected; it is not passing evidence. Broader combined/source-wheel qualification and exact-head
      CI remain separate.
  - command: Python 3.12 -m unittest tests.test_packet_freshness.PacketFreshnessTests.test_existing_packet_verification_survives_session_renewal_without_writes
      tests.test_packet_freshness.PacketFreshnessTests.test_verification_rejects_tampered_inventory_extra_files_and_changed_output
      tests.test_consultation.ConsultationTests.test_cli_create_replay_and_changed_review_reject_old_digest --verbose
    outcome: passed
    observed_at: '2026-11-14T20:59:52Z'
    notes: Three cases pass in 78.488s. Current authority verifies unchanged owned output without writes; old
      approval cannot apply changed evidence. Earlier 44/16-case evidence predates this additive verifier correction;
      final combined qualification remains pending.
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

Draft #149 on documentation #148 implements explicit selected-input packet currentness. Qualified functional source 2373b77: Python 3.12 broader 44 cases pass (325.556s), Python 3.13 focused 16 pass (231.205s), zero skips. Main remains 270ced6, 34 issues open / 44 tracked. Per-file Drive mapping work is isolated on child feature/87-reviewed-drive-normalization; no closure or merge.

## Completed and material changes

Added private versioned packet dependency comparison metadata, authority-neutral exact fingerprints and a read-only --previous-manifest mode. Current grants/evidence gate prior metadata access; historical-only identifiers are excluded. Corrections require a fresh reviewed apply and new output. Old packets and originals remain intact. Drive per-file mapping composition is next, not yet implemented.

## Validation and review evidence

Python 3.12 broader 44 tests pass (325.556s); Python 3.13 focused 16 pass (231.205s), zero skips. Scoped Ruff/format, pinned owners, continuity/coverage and whitespace pass. The initial fixture-helper import error is corrected. Exact-head automatic CI and combined artifact qualification remain separate.

## Blockers, risks, unknowns, and deferred work

Mac setup is parked. Actual private locations/collection, credentials and consumer/runtime authority remain unavailable. A supplied prior manifest is comparison data, not output-integrity or source authority. Reconciliation does not discover ungranted corrections. Required private pilot/model/owner decisions remain separate; #19/#27 and #88/#91 stay deferred.

## Next dependency-ready work

Complete the dependent #87/#90 reviewed per-file Drive normalization checkpoint, then qualify the combined source/wheel/archive workflow and audit the actual remaining #15/#16/#32/#43/#44 criteria. Preserve explicit private-pilot/owner gates; leave new PRs in draft.

## Parallel changes and reconciliation

Unmerged documentation #148 is the explicit base. New code drafts form a documented stack; the last child retains a reproducible combined checkout. Preserve original root WIP and all existing worktrees. Do not auto-merge new drafts or overwrite historical evidence.

## Privacy and redaction

Synthetic fixtures/evidence only. Real gardens, financial records, credentials, reports and private consumer configuration stay outside this public repository. Current offline source grants do not authorize hosted-model forwarding. No secret is requested in chat.

## Handoff update protocol

Record exact branch/PR, source/merge commits, tests and CI observations, remaining parent criteria, blockers and next action. Keep all 44 coverage rows and 24 proposed/null-approval ADRs. New setup defects get specific follow-ups only after the pilot reveals them.

## Compaction and supersession

Preserve twelve headings and 16384-byte/240-line bounds. The merge receipt supersedes earlier draft/pending snapshots without rewriting historical qualification. Proposed finishing order is for the requested sync; it does not start another batch.
