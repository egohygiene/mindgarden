---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-13T22:12:53Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: 'Deliver the selected #37/#46/#90 context freshness, multi-source summary refresh and reviewed CSV mapping
    checkpoints.'
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
work:
  objective: 'Hand off the complete selected #37/#46/#90 draft integration stack with qualified source/artifacts
    and exact remaining parent scope.'
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
    id: freshness-mapping-next-checkpoint
    description: "Review #144 \u2192 #145 \u2192 #146 \u2192 #147 in order and sync this completed bounded batch.\
      \ Next proposed independent checkpoint: explicit reviewed source-correction to preparation-packet freshness;\
      \ optional #32 can follow. Preserve actual pilot/model/normative policy gates; do not merge new drafts or\
      \ start real processing without the applicable authority."
    readiness: ready
    references:
    - docs/freshness-mapping-sprint.md
    depends_on: []
state:
  base:
    revision: ac0e4ad4f30a55e0b8096bf816c719f0460912c0
    ref: refs/heads/feature/46-multisource-refresh
    verified_at: '2026-11-13T22:12:53Z'
  candidate:
    branch: feature/90-reviewed-csv-mapping
    revision: b7b279aab1ec3c38b77b7f3885374f5ca64f27fc
    pull_request:
      provider: github
      id: egohygiene/mindgarden#147
      url: https://github.com/egohygiene/mindgarden/pull/147
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-13T22:12:53Z'
    default_branch_revision: 6c9954bfa8ac65c94aa1db87c679a66227f736d8
    issue_state: open
    pull_request_state: draft
    notes: "Draft stack #144 \u2192 #145 \u2192 #146 \u2192 #147 preserves corrected ancestry. Combined functional\
      \ source b7b279a is qualified; main remains 6c9954b. #144/#145 exact Test/preparation pass; #146/#147 Test\
      \ observed running and preparation passes. 34 open / 44 tracked / ten closed; no parent closed by this batch."
  parallel_changes: []
review:
  status: partial
  reviewed_at: '2026-11-13T22:12:53Z'
  reviewed_by: codex
  evidence:
  - command: 'Both supported Pythons: -m unittest tests.test_compaction_refresh tests.test_compaction tests.test_source_compaction
      tests.test_context_dependencies tests.test_dependency_builds tests.test_selected_builds --quiet; new-fixture
      Ruff/format; pinned owner/whitespace checks.'
    outcome: passed
    observed_at: '2026-11-13T21:51:17Z'
    notes: 43 tests pass per Python, zero skips (105.284s / 102.118s). Initial invalid uppercase historical-only
      canary corrected to the existing identifier contract. No live/model accuracy or private pilot claim.
  - command: 'Both supported Pythons: -m unittest tests.test_mapped_ledger tests.test_consultation tests.test_source_adapters
      tests.test_v1_contracts tests.test_package --quiet; then final -m unittest tests.test_mapped_ledger --quiet
      with restore assertion; scoped Ruff/format, compilation, pinned owner and whitespace checks.'
    outcome: passed
    observed_at: '2026-11-13T22:02:22Z'
    notes: 40 broader cases per Python pass (85.007s / 83.178s), zero skips. Seven final mapped cases pass per Python
      after added restore assertion (12.566s / 12.104s). New-code lint/format passes. Corrected parent abbreviated
      revision to full required SHA and fast-forwarded child; no runtime change from that repair.
  - command: 'Both Pythons: -m unittest tests.test_context_dependencies tests.test_dependency_builds tests.test_selected_builds
      tests.test_v1_retrieval tests.test_scoped_retrieval tests.test_v1_contracts tests.test_compaction_refresh
      tests.test_compaction tests.test_source_compaction tests.test_mapped_ledger tests.test_consultation tests.test_source_adapters
      tests.test_package --quiet; distribution and 17-case clean Git/wheel/archive checks; scoped lint/format, compile,
      pinned owners, links and unchanged-runtime diff.'
    outcome: passed
    observed_at: '2026-11-13T22:12:53Z'
    notes: 102 tests per Python, zero skips (237.252s / 234.681s). Two distribution cases per Python pass. All 17
      boundary cases pass independently from clean Git (74.145s), installed wheel (75.018s), source archive (74.651s),
      zero skips. New schema/fixtures packaged; module origins pinned to selected install/source. Build 1.3.0 /
      setuptools 80.9.0; artifact hashes in receipt. Final handoff changes docs only; its CI is separate.
  environment_limitations:
  - Real private pilot, credentials, live Drive/model quality and confidential runtime remain unavailable/unperformed.
  - Full local/act, manual accessibility, destructive retention and release remain deferred.
  - No proposed ADR ratification, autonomous publication or original-source deletion.
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

The maintainer selected #37 → #46 → #90 by asking to continue the recorded next batch. Existing user authority permits implementation and draft PRs; it does not merge #144 or ratify ADRs. #88/#91 and release remain deferred.

## Resume protocol

Refresh issues/comments/PRs/CI, read current contracts and the sprint ledger. Use the isolated branch. Preserve all four original root WIP entries and existing worktrees.

## Current objective and success conditions

Hand off the complete selected #37/#46/#90 draft integration stack with qualified source/artifacts and exact remaining parent scope.

## State snapshot

Draft stack #144 → #145 → #146 → #147 preserves corrected ancestry. Combined functional source b7b279a is qualified; main remains 6c9954b. #144/#145 exact Test/preparation pass; #146/#147 Test observed running and preparation passes. 34 open / 44 tracked / ten closed; no parent closed by this batch.

## Completed and material changes

Added versioned reviewed column/date/sign mappings, separate explicit mapped-ledger-csv adapter/input profile and --ledger-mapping. Preserved strict CSV/v0 behavior, immutable originals, raw UTF-8 spans, canonical mapping provenance and stale-config guards. Normalization identity binds config while transaction/content identity stays separate. Two layouts/overlap reproduce eight transactions and exact 2259.76 packet; restore/rebind with old vault/mapping paths moved aside reproduces identical files. Combined 102-case selection passes both Pythons; all 17 new boundaries pass from clean Git, isolated installed wheel and unpacked source, including byte-identical mapped-packet vault recovery. Source/wheel builds and explicit distribution checks pass.

## Validation and review evidence

Both Pythons: -m unittest tests.test_context_dependencies tests.test_dependency_builds tests.test_selected_builds tests.test_v1_retrieval tests.test_scoped_retrieval tests.test_v1_contracts tests.test_compaction_refresh tests.test_compaction tests.test_source_compaction tests.test_mapped_ledger tests.test_consultation tests.test_source_adapters tests.test_package --quiet; distribution and 17-case clean Git/wheel/archive checks; scoped lint/format, compile, pinned owners, links and unchanged-runtime diff. — 102 tests per Python, zero skips (237.252s / 234.681s). Two distribution cases per Python pass. All 17 boundary cases pass independently from clean Git (74.145s), installed wheel (75.018s), source archive (74.651s), zero skips. New schema/fixtures packaged; module origins pinned to selected install/source. Build 1.3.0 / setuptools 80.9.0; artifact hashes in receipt. Final handoff changes docs only; its CI is separate.

## Blockers, risks, unknowns, and deferred work

No private inputs or selected live local model are available. Normative declassification, consequential architecture decisions and full parent acceptance remain separate. Synthetic correctness is not model quality or a private consumer's approval.

## Next dependency-ready work

Review #144 → #145 → #146 → #147 in order and sync this completed bounded batch. Next proposed independent checkpoint: explicit reviewed source-correction to preparation-packet freshness; optional #32 can follow. Preserve actual pilot/model/normative policy gates; do not merge new drafts or start real processing without the applicable authority.

## Parallel changes and reconciliation

#144 remains a draft with passing exact-head CI. Preserve its 3c61db4 tree in the explicit integration stack; #37 does not semantically depend on its routing fix. #90 normalization is independent of refresh correctness. Do not silently merge drafts or overwrite root WIP.

## Privacy and redaction

Synthetic committed fixtures only. Real gardens, sources, financial reports, local bindings and credentials stay outside this public repository. Source instructions are data. Knowledge review, storage, execution and publication authority remain separate.

## Handoff update protocol

At each checkpoint push a small draft PR and record branch/base/functional commit, exact commands/results, CI state, remaining parent scope and exact next action. Keep all 44 unique issue rows and 24 proposed/null-approval ADRs; validate pinned owner contracts.

## Compaction and supersession

Preserve these twelve headings and 16384-byte/240-line limits. The active batch supersedes earlier proposed scheduling only. Exact-head CI and qualified runtime evidence remain separate from later documentation handoffs.
