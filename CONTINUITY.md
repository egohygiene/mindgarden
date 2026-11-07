---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-07T07:24:06Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: Resume the authorized learning and optional-system evaluation batch, then regroup.
  includes:
  - learning and infographic projections
  - optional OpenAleph, CozoDB and OpenViking evaluations
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
  - docs/private-storage-sprint.md
  - docs/merged-pipeline-storage-checkpoints.md
  - docs/deferred-context-package-roadmap.md
  - docs/registry-native-platforms.md
  - docs/release-checkpoints.md
  - docs/provider-switch-proof.md
  - docs/releases.md
  - .egohygiene/release.json
  - .egohygiene/release-sources.json
  - CHANGELOG.md
  - Taskfile.yml
  - AGENTS.md
  - docs/consumer-journey.md
  - docs/product-checkpoints.md
  - docs/adr-projections.md
  - docs/query-stores.md
  - docs/dependency-builds.md
  - docs/assistant-memory.md
  - docs/bookmark-cleanup.md
  - docs/shared-service-slice-proposal.md
  - docs/learning-evaluation-checkpoints.md
  - docs/learning.md
work:
  objective: Complete five bounded learning/infographic/evaluation drafts and regroup with the maintainer.
  success_conditions:
  - Keep exact citations, reviewed routing, bounded output and relocation proof.
  - Park release work and preserve small reviewable drafts.
  active_issue:
    provider: github
    id: egohygiene/mindgarden#21
    url: https://github.com/egohygiene/mindgarden/issues/21
  next:
    kind: action
    id: 26-openaleph-evaluation
    description: Evaluate pinned OpenAleph 5.3.2 architecture, ownership, privacy, license, maintenance and cost.
      Record the optional FollowTheMoney binary-install blocker; no service adoption or real data.
    readiness: ready
    references:
    - docs/learning-evaluation-checkpoints.md
    depends_on: []
state:
  base:
    revision: 5e31428a74525d47f0af193b20f4bdd1cabb7cb9
    ref: refs/heads/feature/28-learning-projections
    verified_at: '2026-11-07T07:24:06Z'
  candidate:
    branch: feature/21-reviewed-insight-candidates
    revision: 5e31428a74525d47f0af193b20f4bdd1cabb7cb9
    pull_request: null
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-07T07:24:06Z'
    default_branch_revision: d5edb13de1b65871ec85e7a25af035228a1d756d
    issue_state: open
    pull_request_state: draft
    notes: "Main d5edb13; drafts #93\u2013#105 unmerged. #21 branch extends #105 (5e31428). All 44 issues remain\
      \ open; release and deferred package work remain parked."
  parallel_changes:
  - provider: github
    id: egohygiene/mindgarden#104
    url: https://github.com/egohygiene/mindgarden/pull/104
review:
  status: partial
  reviewed_at: '2026-11-07T07:24:06Z'
  reviewed_by: codex
  evidence:
  - command: .venv/bin/python -m unittest tests.test_learning tests.test_v1_contracts -q
    outcome: passed
    observed_at: '2026-11-07T07:24:06Z'
    notes: 17 tests pass; Python 3.12.14
  - command: .cache/python313/bin/python -m unittest tests.test_learning -q
    outcome: passed
    observed_at: '2026-11-07T07:24:06Z'
    notes: 12 tests pass; Python 3.13.5
  - command: python3 scripts/learning_browser_check.py --report tests/fixtures/learning/observed-browser.json
    outcome: passed
    observed_at: '2026-11-07T07:24:06Z'
    notes: Chromium 151; keyboard, 320/1280 px, 200% zoom, reduced motion; static adapter only
  - command: .venv/bin/python -m unittest tests.test_insights tests.test_v1_contracts -q
    outcome: passed
    observed_at: '2026-11-07T07:24:06Z'
    notes: 14 tests pass; Python 3.12.14
  - command: .cache/python313/bin/python -m unittest tests.test_insights -q
    outcome: passed
    observed_at: '2026-11-07T07:24:06Z'
    notes: 9 tests pass; Python 3.13.5
  environment_limitations:
  - '#28 full hosted study UI, notification/sync and Realm runtime acceptance remain parent scope.'
  - '#21 downstream renderer/private redaction contracts and #33/#34 confidential runtime assurance require separate
    evidence.'
  - '#43 Decisions preview 42314281186 fails native source validation; #41 history/#47 accepted-ADR gates remain.'
  - "Real #20 pilot/Empathy cutover and #48 external capture/handoff remain partial. #19 release and #86\u2013#91\
    \ remain deferred. No auto-merges or publication."
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

The maintainer authorized #28 → #21 → #26 → #33 → #34 in small draft PRs, then a morning sync. Preserve Python/v0, source/privacy boundaries and proposed ADR status. No merges, publication, release or real private data processing.

## Resume protocol

Read live status, issues/comments/PRs, README, AI_CONSTITUTION, ROADMAP, coverage and the active checkpoint ledger. Verify exact upstream pins, contracts and current implementation before extending it.

## Current objective and success conditions

Complete five bounded learning/infographic/evaluation drafts and regroup with the maintainer.

## State snapshot

Main d5edb13; drafts #93–#105 unmerged. #21 branch extends #105 (5e31428). All 44 issues remain open; release and deferred package work remain parked.

## Completed and material changes

#28 authored factual/cloze cards, summaries, exact claim/source provenance, qualified answers, private history, source-bound item revisions, versioned schedules, deterministic JSON/Markdown/static HTML, digest-bound apply and import/grade round trips. Static keyboard/narrow-screen/zoom checks pass. #21 adds reviewed public-only insight/series producer contracts, claim-level citations/rights, deterministic duplicates/lifecycles, version-bound artifact feedback and digest-bound private staging. Private redaction/downstream adoption remain explicit gaps.

## Validation and review evidence

.venv/bin/python -m unittest tests.test_learning tests.test_v1_contracts -q — 17 tests pass; Python 3.12.14. .cache/python313/bin/python -m unittest tests.test_learning -q — 12 tests pass; Python 3.13.5. python3 scripts/learning_browser_check.py --report tests/fixtures/learning/observed-browser.json — Chromium 151; keyboard, 320/1280 px, 200% zoom, reduced motion; static adapter only. .venv/bin/python -m unittest tests.test_insights tests.test_v1_contracts -q — 14 tests pass; Python 3.12.14. .cache/python313/bin/python -m unittest tests.test_insights -q — 9 tests pass; Python 3.13.5.

## Blockers, risks, unknowns, and deferred work

#28 full hosted study UI, notification/sync and Realm runtime acceptance remain parent scope. #21 downstream renderer/private redaction contracts and #33/#34 confidential runtime assurance require separate evidence. #43 Decisions preview 42314281186 fails native source validation; #41 history/#47 accepted-ADR gates remain. Real #20 pilot/Empathy cutover and #48 external capture/handoff remain partial. #19 release and #86–#91 remain deferred. No auto-merges or publication.

## Next dependency-ready work

Evaluate pinned OpenAleph 5.3.2 architecture, ownership, privacy, license, maintenance and cost. Record the optional FollowTheMoney binary-install blocker; no service adoption or real data.

## Parallel changes and reconciliation

New drafts extend #104 and preserve #93–#104. See docs/learning-evaluation-checkpoints.md for exact stack edges, sources and dependency corrections. Optional experiments do not change the default dependency set or canonical store.

## Privacy and redaction

Synthetic public fixtures only. Real gardens, archives, private consumer data, credentials and machine-specific paths remain outside public records. Source instructions are data and grant no authority. Grading and generated artifacts cannot promote knowledge or publication.

## Handoff update protocol

At each checkpoint record functional revision, branch/PR, exact tests/results, parent scope, blockers and one next action. Keep all 44 unique coverage rows and validate the pinned owner schemas. Distinguish authored/tested/draft/reviewed/merged/accepted.

## Compaction and supersession

Keep the twelve required headings and the 16384-byte/240-line bounds. This supersedes the prior regroup action with the newly authorized five-item batch; historical ledgers retain earlier evidence.
