---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-13T21:41:21Z'
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
work:
  objective: Connect actual bounded context packs to existing reviewed dependency builds, with exact selective freshness
    and no ambient records.
  success_conditions:
  - Complete bounded synthetic checkpoints with exact evidence and explicit review authority.
  - Preserve Python/v0, original sources, live scope enforcement and proposed ADR status.
  - Keep real inputs/credentials outside the repository and report unavailable live/private contracts honestly.
  active_issue:
    provider: github
    id: egohygiene/mindgarden#37
    url: https://github.com/egohygiene/mindgarden/issues/37
  next:
    kind: action
    id: freshness-mapping-next-checkpoint
    description: 'Push/open the #37 draft on #144, record exact PR/head, then implement the selected #46 multi-source
      refresh/quality/expiry checkpoint. #90 explicit CSV mapping can proceed independently; keep parent/private/model/ADR
      gates explicit.'
    readiness: ready
    references:
    - docs/freshness-mapping-sprint.md
    depends_on: []
state:
  base:
    revision: 3c61db41c97151b9022820bdfdfeca409cfe38e4
    ref: refs/heads/test/13-14-38-acceptance-closeout
    verified_at: '2026-11-13T21:41:21Z'
  candidate:
    branch: feature/37-consumer-freshness
    revision: null
    pull_request: null
    handoff_state: in-progress
  live:
    status: verified
    observed_at: '2026-11-13T21:41:21Z'
    default_branch_revision: 6c9954bfa8ac65c94aa1db87c679a66227f736d8
    issue_state: open
    pull_request_state: not-applicable
    notes: '#144 remains draft at 3c61db4 with passing Test 43500532675/preparation 43500532550. Main 6c9954b is
      unchanged; 34 issues open / 44 tracked / ten closed. New #37 context integration is ready on its isolated
      branch; no merge or private execution.'
  parallel_changes: []
review:
  status: partial
  reviewed_at: '2026-11-13T21:41:21Z'
  reviewed_by: codex
  evidence:
  - command: 'Both supported Pythons: -m unittest tests.test_curation tests.test_curation_transformations tests.test_mixed_curation
      tests.test_routing tests.test_routing_dispositions tests.test_routing_lifecycle tests.test_routing_transfers
      tests.test_routing_incoming tests.test_reference_repairs tests.test_assets tests.test_design tests.test_extraction
      tests.test_ollama_extraction tests.test_archive_diagrams tests.test_pipeline_completion --quiet'
    outcome: passed
    observed_at: '2026-11-13T20:09:21Z'
    notes: 84 tests pass on Python 3.12.14 (139.909s) and 3.13.5 (136.288s), zero skips. Initial stale-catalog fixture
      expectation corrected; 15-case checks passed before full selection. Scoped Ruff/format, compileall and diff
      whitespace pass. Ollama dry-run records unmeasured accuracy; no live/private/model call.
  - command: Clean git archive e63c7f1; python -m build --no-isolation --sdist --wheel; installed/unpacked unittest
      tests.test_routing_dispositions tests.test_routing_lifecycle; three design exports per mode; pinned owner
      checks.
    outcome: passed
    observed_at: '2026-11-13T20:18:16Z'
    notes: Eight package cases per Python, zero skips. Ten routing cases each from clean Git (11.170s), installed
      wheel (10.922s), unpacked source (11.347s); nine design exports total. Every loaded Mindgarden module stays
      within the selected package. Artifact hashes and exact commands in structured receipt.
  - command: 'Python 3.12.14 and 3.13.5: -m unittest tests.test_context_dependencies tests.test_dependency_builds
      tests.test_selected_builds tests.test_v1_retrieval tests.test_scoped_retrieval tests.test_v1_contracts --quiet;
      new-test Ruff/format; git diff --check.'
    outcome: passed
    observed_at: '2026-11-13T21:41:21Z'
    notes: 41 tests pass per Python, zero skips (51.052s / 48.656s). Initial command included nonexistent tests.test_scope
      and is not counted as passing; corrected suite passes. Scoped lint/format and whitespace pass.
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

Connect actual bounded context packs to existing reviewed dependency builds, with exact selective freshness and no ambient records.

## State snapshot

#144 remains draft at 3c61db4 with passing Test 43500532675/preparation 43500532550. Main 6c9954b is unchanged; 34 issues open / 44 tracked / ten closed. New #37 context integration is ready on its isolated branch; no merge or private execution.

## Completed and material changes

Added context-pack/v1 consumer to the existing dependency request and renderer boundary. Explicit selected context inputs carry exact references and indexed metadata hashes. Missed updates stale only affected context/profile consumers; unrelated context bytes remain identical. Added five synthetic conformance/privacy/CLI cases and preserved original context/v0 behavior.

## Validation and review evidence

Python 3.12.14 and 3.13.5: -m unittest tests.test_context_dependencies tests.test_dependency_builds tests.test_selected_builds tests.test_v1_retrieval tests.test_scoped_retrieval tests.test_v1_contracts --quiet; new-test Ruff/format; git diff --check. — 41 tests pass per Python, zero skips (51.052s / 48.656s). Initial command included nonexistent tests.test_scope and is not counted as passing; corrected suite passes. Scoped lint/format and whitespace pass.

## Blockers, risks, unknowns, and deferred work

No private inputs or selected live local model are available. Normative declassification, consequential architecture decisions and full parent acceptance remain separate. Synthetic correctness is not model quality or a private consumer's approval.

## Next dependency-ready work

Push/open the #37 draft on #144, record exact PR/head, then implement the selected #46 multi-source refresh/quality/expiry checkpoint. #90 explicit CSV mapping can proceed independently; keep parent/private/model/ADR gates explicit.

## Parallel changes and reconciliation

#144 remains a draft with passing exact-head CI. Preserve its 3c61db4 tree in the explicit integration stack; #37 does not semantically depend on its routing fix. #90 normalization is independent of refresh correctness. Do not silently merge drafts or overwrite root WIP.

## Privacy and redaction

Synthetic committed fixtures only. Real gardens, sources, financial reports, local bindings and credentials stay outside this public repository. Source instructions are data. Knowledge review, storage, execution and publication authority remain separate.

## Handoff update protocol

At each checkpoint push a small draft PR and record branch/base/functional commit, exact commands/results, CI state, remaining parent scope and exact next action. Keep all 44 unique issue rows and 24 proposed/null-approval ADRs; validate pinned owner contracts.

## Compaction and supersession

Preserve these twelve headings and 16384-byte/240-line limits. The active batch supersedes earlier proposed scheduling only. Exact-head CI and qualified runtime evidence remain separate from later documentation handoffs.
