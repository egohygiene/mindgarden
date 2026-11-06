---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-06T06:51:16Z'
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
    id: egohygiene/mindgarden#16
    url: https://github.com/egohygiene/mindgarden/issues/16
  next:
    kind: action
    id: review-source-workflow-sprint-stack
    description: 'Review draft #74 → #75 → #76 → #77 → #78 → #79 in dependency order. Preserve the stack
      until maintainer merge authorization; disposition proposed ADR-0022/ADR-0011 extension separately.
      Choose further bounded work from the retained-parent-scope column after review.'
    readiness: ready
    references:
    - https://github.com/egohygiene/mindgarden/issues/16
    depends_on: []
state:
  base:
    revision: 30a29668a02740a91e77aec22f670a8270ccddf4
    ref: refs/heads/main
    verified_at: '2026-11-06T05:27:17Z'
  candidate:
    branch: feature/16-rendered-garden-references
    revision: b88cc97c62cb855a029d30f00f23a9042166e1ac
    pull_request:
      provider: github
      id: egohygiene/mindgarden#79
      url: https://github.com/egohygiene/mindgarden/pull/79
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-06T06:51:16Z'
    default_branch_revision: 30a29668a02740a91e77aec22f670a8270ccddf4
    issue_state: open
    pull_request_state: draft
    notes: 'Previous #68–#73 merged; new sprint drafts remain unmerged. No parent closure or ADR ratification.'
  parallel_changes: []
review:
  status: partial
  reviewed_at: '2026-11-06T06:51:16Z'
  reviewed_by: codex
  evidence:
  - command: .venv/bin/python -m build --sdist --wheel --outdir .cache/dist
    outcome: passed
    observed_at: '2026-11-06T06:51:16Z'
    notes: fresh source and wheel built; new modules/contracts/examples/fixtures packaged
  - command: .venv/bin/python -m unittest discover --start-directory tests --verbose
    outcome: passed
    observed_at: '2026-11-06T06:51:16Z'
    notes: 260 passed, no skips; Python 3.12.14; 165.904 seconds
  - command: .cache/python313/bin/python -m unittest discover --start-directory tests --verbose
    outcome: passed
    observed_at: '2026-11-06T06:51:16Z'
    notes: 260 passed, no skips; Python 3.13.5; 154.450 seconds
  - command: 'Clean git-archive source -S and isolated wheel -I: private_garden_demo.py, compaction_demo.py,
      garden_reference_demo.py'
    outcome: passed
    observed_at: '2026-11-06T06:51:16Z'
    notes: all complete reports equal each other and committed goldens; source archive b88cc97
  - command: Clean source projection golden/schema matrix and installed v0 version/validate/verify/publish/library
      smoke
    outcome: passed
    observed_at: '2026-11-06T06:51:16Z'
    notes: passed; eight projections, 3 v0 notes/1 context profile/2 public notes
  - command: Both Python compileall; pinned owner/continuity/38-row checks; relative links; git diff --check
    outcome: passed
    observed_at: '2026-11-06T06:51:16Z'
    notes: passed; Node v24.19.0; proposed/null decisions preserved
  - command: Automatic Test runs 42172135507,42172295516,42176087142,42176123517,42176128594,42176129395
    outcome: passed
    observed_at: '2026-11-06T06:51:16Z'
    notes: all six implementation heads passed; no workflow manually dispatched
  environment_limitations:
  - CI is recorded for exact implementation heads; documentation-only handoff head status must be observed
    separately.
  - Runtime/memory measurement is Linux/session-specific; 4096-note generator bound is not a verified
    performance envelope.
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

All six drafts are pushed and unmerged. Combined checkout feature/16-rendered-garden-references at tested b88cc97; final handoff is documentation-only over it. Main remains 30a2966. Successful automatic Test runs exist on all six implementation heads; a later documentation-head run is separate.

## Completed and material changes

All six bounded sprint checkpoints: source-adapter conformance/extensions, curation transformations, historical/selective archives, append-only private routing lifecycle, complete projection matrix/measured corpus, and pinned rendered public garden data references/catalog refresh. Golden correction 3fe5689 was propagated through a6aa934/fef556e/b88cc97 without force pushes.

## Validation and review evidence

260 tests passed without skips on Python 3.12.14 (165.904 s) and 3.13.5 (154.450 s). Fresh source/wheel built. Clean -S source and isolated -I wheel private/compaction/reference reports equal committed goldens; clean eight-projection matrix and installed v0 smoke pass. 1024-note reference bounds, actual prior Quartz artifact, compile, relative links, diff and pinned owner/continuity/38-row checks pass. All six implementation-head Test runs passed.

## Blockers, risks, unknowns, and deferred work

No implementation blocker for these bounded drafts. Parent scope remains: Mindcap provider-neutral handoff, v2.0.1 reader, public/policy-changing/attached-graph moves, wider corpus/consumer proofs, private/remote federation and authentication, full installer and real Akashic/Aether pilots. ADRs remain proposed/null approval. Initial discovery/golden failures are documented and superseded by corrected checks; no parent issue or #20/#45 is claimed complete.

## Next dependency-ready work

Review draft #74 → #75 → #76 → #77 → #78 → #79 in dependency order. Preserve the stack until maintainer merge authorization; disposition proposed ADR-0022/ADR-0011 extension separately. Choose further bounded work from the retained-parent-scope column after review.

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
