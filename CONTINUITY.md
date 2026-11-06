---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-06T06:02:03Z'
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
    id: egohygiene/mindgarden#11
    url: https://github.com/egohygiene/mindgarden/issues/11
  next:
    kind: action
    id: curation-transformation-conformance
    description: 'Implement #13 merge attribution/qualification preservation, exact relationship and selected-evidence
      validation, and authored redaction fixtures on a branch stacked over #74.'
    readiness: ready
    references:
    - https://github.com/egohygiene/mindgarden/issues/11
    depends_on: []
state:
  base:
    revision: 30a29668a02740a91e77aec22f670a8270ccddf4
    ref: refs/heads/main
    verified_at: '2026-11-06T05:27:17Z'
  candidate:
    branch: milestone/next-six-checkpoints
    revision: 65b15fb79f68b84b40f364fefedf3e85f87ab174
    pull_request:
      provider: github
      id: egohygiene/mindgarden#74
      url: https://github.com/egohygiene/mindgarden/pull/74
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-06T06:02:03Z'
    default_branch_revision: 30a29668a02740a91e77aec22f670a8270ccddf4
    issue_state: open
    pull_request_state: draft
    notes: 'Previous #68–#73 merged; new sprint drafts remain unmerged. No parent closure or ADR ratification.'
  parallel_changes: []
review:
  status: partial
  reviewed_at: '2026-11-06T06:02:03Z'
  reviewed_by: codex
  evidence:
  - command: .venv/bin/python -m unittest tests.test_source_adapters tests.test_adapter_conformance tests.test_v1_contracts
      -q
    outcome: passed
    observed_at: '2026-11-06T06:02:03Z'
    notes: 18 tests passed
  - command: .venv/bin/python -m build --sdist --wheel --outdir .cache/dist
    outcome: passed
    observed_at: '2026-11-06T06:02:03Z'
    notes: source and wheel built
  - command: .venv/bin/python -m unittest discover --start-directory tests -q
    outcome: passed
    observed_at: '2026-11-06T06:02:03Z'
    notes: 237 tests passed, 131.975 seconds
  - command: .cache/python313/bin/python -m unittest tests.test_source_adapters tests.test_adapter_conformance
      tests.test_v1_contracts -q
    outcome: passed
    observed_at: '2026-11-06T06:02:03Z'
    notes: 18 tests passed
  - command: .venv/bin/python scripts/private_garden_demo.py --workspace .cache/sprint11-private --require-source
    outcome: passed
    observed_at: '2026-11-06T06:02:03Z'
    notes: offline exact-reference/search/context/relocation golden proof passed
  - command: .venv/bin/python -m unittest tests.test_distribution -q
    outcome: passed
    observed_at: '2026-11-06T06:02:03Z'
    notes: 2 tests passed
  - command: python3 .cache/six_owner_checks.py
    outcome: passed
    observed_at: '2026-11-06T06:02:03Z'
    notes: proposed ADRs, continuity and 38 issue ledger passed
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

Draft #74 on milestone/next-six-checkpoints over main, functional source 65b15fb79f68b84b40f364fefedf3e85f87ab174. First bounded checkpoint is locally verified; no new parent acceptance or ADR approval.

## Completed and material changes

Versioned source-adapter declarations, bounded normalization/output checks, reusable deterministic fixture harness, synthetic reference extension and immutable observation compatibility. Confirmed sprint/dependency map replaces stale missing-numbering text.

## Validation and review evidence

Fresh source/wheel build passed. Python 3.12 full suite: 237 tests passed (131.975s). 18 targeted tests passed on Python 3.13; its full suite is running. Offline private-workflow golden proof and 2 distribution tests passed. Pinned owner/continuity/coverage checks, compileall and diff checks passed.

## Blockers, risks, unknowns, and deferred work

Mindcap #35 wire contract is not published at inspected main pin; synthetic reference extension claims no provider compatibility. Older archive specifications are now accessible and need structural assessment in #15. All ADRs remain proposed/null approval; broad consumer/model/installer work remains separate.

## Next dependency-ready work

Implement #13 merge attribution/qualification preservation, exact relationship and selected-evidence validation, and authored redaction fixtures on a branch stacked over #74.

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
