---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-20T06:51:40Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: Review synthetic bookmark, Drive and scoped Codex integration evidence before the first selected local
    pilot.
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
  - docs/integration-readiness.md
  - docs/bookmark-cleanup.md
  - docs/drive-capture.md
  - docs/scoped-research.md
  - docs/decisions/README.md
  - docs/acceptance-reconciliation.md
  - docs/bookmark-pilot.md
  - docs/evidence/integration-readiness-qualification.json
work:
  objective: Review synthetic bookmark, Drive and scoped Codex integration evidence before the first selected
    local pilot.
  success_conditions:
  - Complete bounded synthetic checkpoints with exact evidence and explicit review authority.
  - Preserve Python/v0, original sources, live scope enforcement and proposed ADR status.
  - Keep real inputs/credentials outside the repository and report unavailable live/private contracts honestly.
  active_issue:
    provider: github
    id: egohygiene/mindgarden#48
    url: https://github.com/egohygiene/mindgarden/issues/48
  next:
    kind: action
    id: review-integration-stack-and-select-local-input
    description: 'Review draft #155 then #156 then #157. Rehearse the private bookmark workflow, identify the
      first selected Chrome profile or HTML export, and choose a private work directory before a separate local
      run.'
    readiness: ready
    references:
    - docs/integration-readiness.md
    - docs/bookmark-pilot.md
    - docs/private-pilot.md
    depends_on: []
state:
  base:
    revision: c30d966673f3cedeeeb46395a88f975f07b4a568
    ref: refs/heads/integration/20261120-bookmark-drive-readiness
    verified_at: '2026-11-20T06:51:40Z'
  candidate:
    branch: integration/20261120-drive-codex-readiness
    revision: fcdb79dd3e56ae07b949e6675d5873bd8528c248
    pull_request:
      provider: github
      id: egohygiene/mindgarden#157
      url: https://github.com/egohygiene/mindgarden/pull/157
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-20T06:51:40Z'
    default_branch_revision: 5cf24a29002f8e4f0a464b42819ec21ede33af2a
    issue_state: open
    pull_request_state: draft
    notes: 'Main 5cf24a2. Draft #155 at b47c40a passed hosted Test and preparation. Draft #156 at c30d966 carries
      bookmark and routing proof. Draft #157 adds Drive and research proofs from fcdb79d. Hosted Test for the
      new drafts is observed separately. All 30 Mindgarden issues remain open, with 44 coverage rows.'
  parallel_changes: []
review:
  status: partial
  reviewed_at: '2026-11-20T06:51:40Z'
  reviewed_by: codex
  evidence:
  - command: PYTHONPATH="$PWD/src" python -m unittest tests.test_routing tests.test_routing_dispositions tests.test_routing_lifecycle
      tests.test_routing_transfers tests.test_routing_incoming tests.test_reference_repairs -q
    outcome: passed
    observed_at: '2026-11-20T06:44:57Z'
    notes: 42 tests each on Python 3.12.14 and 3.13.5. Wall times 61.971s and 60.331s. Zero skips.
  - command: PYTHONPATH="$PWD/src" python -m unittest tests.test_bookmarks tests.test_captured_bookmarks -v
    outcome: passed
    observed_at: '2026-11-20T06:46:09Z'
    notes: 14 tests per Python 3.12.14/3.13.5, zero skips (12.069s/12.318s).
  - command: PYTHONPATH="$MINDCAP_CHECKOUT/src" "$MINDCAP_PYTHON" experiments/capture_handoff/check.py --fixture-directory
      "$MINDCAP_CHECKOUT/tests/fixtures/chrome_bookmarks/multiple_profiles/User Data" --rehearse-private-cleanup
      | cmp - docs/evidence/bookmark-pilot-rehearsal.json
    outcome: passed
    observed_at: '2026-11-20T06:46:09Z'
    notes: Real pinned Mindcap 7ee766c producer. Resume and single-batch output match; exact replay, stale authorization,
      quarantine and retained original ZIP verified. Pinned Mindcap CLI capture and verify, guide packaging snippet
      and Mindgarden CLI inspect also passed.
  - command: Run the fourteen unittest modules listed in docs/evidence/integration-readiness-qualification.json
      using Python 3.12.14 and 3.13.5.
    outcome: passed
    observed_at: '2026-11-20T06:51:40Z'
    notes: 95 focused tests per Python passed (193.034s and 199.031s). Two distribution cases skipped before packaging
      and both passed per Python when rerun after build.
  - command: Run scripts/research_roles_demo.py with --check-golden from clean Git, an isolated wheel and an unpacked
      source archive.
    outcome: passed
    observed_at: '2026-11-20T06:51:40Z'
    notes: All three reproduce committed exact role evidence (154.035s, 156.456s, 154.290s). Full commands, package
      hashes and result limits in the qualification receipt.
  environment_limitations:
  - 'The local pilot needs a selected input and approved workspace. Actual Chrome import, Drive OAuth, Codex/model
    operation and private/Empathy consumer evidence remain open. Mindcap #35 owns recurring deltas. Akashic owns
    the reviewable public intake contract. Public policy transitions, manual accessibility, optional experiments,
    releases and ADR dispositions have separate requirements.'
  - All evidence in this batch is synthetic. Hosted tests and the deferred full audit have separate results.
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

Review synthetic bookmark, Drive and scoped Codex integration evidence before the first selected local pilot.

## Resume protocol

Refresh live issue and PR states. Check the integration guide and current draft base before using the local preflight.

## Current objective and success conditions

Demonstrate safe offline integration and record the remaining owner contracts and exact first operator actions.

## State snapshot

Main 5cf24a2. Draft #155 at b47c40a passed hosted Test and preparation. Draft #156 at c30d966 carries bookmark and routing proof. Draft #157 adds Drive and research proofs from fcdb79d. Hosted Test for the new drafts is observed separately. All 30 Mindgarden issues remain open, with 44 coverage rows.

## Completed and material changes

Draft #156 verifies exact reviewed rename and private bookmark capture/review/resume through the pinned Mindcap producer. Draft #157 clones reviewed records from a local Git remote, restores the separate vault and recovers exact packet/context/evidence. The packaged research rehearsal demonstrates distinct accounting and career plans with explicit source grants. The integration map accounts for all 30 open issues. References have been promoted or added to existing owning issues.

## Validation and review evidence

95 focused plus two separately run distribution cases pass on each supported Python. Pinned bookmark receipt matches. The research golden matches from clean Git, isolated wheel and unpacked source. Scoped lint, compile, format, 44-row and pinned ADR/continuity checks pass. Exact commands and results are in docs/evidence/integration-readiness-qualification.json.

## Blockers, risks, unknowns, and deferred work

The local pilot needs a selected input and approved workspace. Actual Chrome import, Drive OAuth, Codex/model operation and private/Empathy consumer evidence remain open. Mindcap #35 owns recurring deltas. Akashic owns the reviewable public intake contract. Public policy transitions, manual accessibility, optional experiments, releases and ADR dispositions have separate requirements.

## Next dependency-ready work

Review draft #155 then #156 then #157. Rehearse the private bookmark workflow, identify the first selected Chrome profile or HTML export, and choose a private work directory before a separate local run.

## Parallel changes and reconciliation

Stack order #155 → #156 → #157. The reproducible combined branch is integration/20261120-drive-codex-readiness. Preserve the original root worktree's four interrupted files.

## Privacy and redaction

Fixtures are synthetic. Keep actual bookmark and Drive capture, credentials, account-specific paths and reviewed personal outputs in the owner's private workspace.

## Handoff update protocol

Record the next bounded issue, exact source and PR, verification, remaining acceptance and next action. Keep canonical issue and decision requirements traceable through the coverage ledger.

## Compaction and supersession

This checkpoint supersedes earlier waiting-for-sync and current-work snapshots. The prior merge and test receipts retain their original observations.
