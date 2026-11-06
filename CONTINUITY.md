---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-06T03:55:44Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: 'Implement the six authorized draft checkpoints: #17, #38, #10, #18, #42 and #46.'
  includes:
  - six authorized synthetic draft checkpoints and their shared compatibility contracts
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
work:
  objective: 'Deliver six small draft PRs over merged #67; preserve Python/v0 and synthetic-only execution.'
  success_conditions:
  - Six reviewable draft PRs with explicit stack, evidence and retained parent scope.
  - Usable reviewed v1 preview; design, conformance, portal, proposed architecture and compaction contracts.
  active_issue:
    provider: github
    id: egohygiene/mindgarden#46
    url: https://github.com/egohygiene/mindgarden/issues/46
  next:
    kind: action
    id: maintainer-stack-sync
    description: "Sync with the maintainer and review #68 \u2192 #69 \u2192 #70 \u2192 #71 \u2192 #72\
      \ \u2192 #73 in order. Merge only after that sync; record separate human ADR disposition before\
      \ consequential #32/#47 choices. Combined checkout: feature/46-compaction-contracts."
    readiness: ready
    references:
    - https://github.com/egohygiene/mindgarden/issues/42
    depends_on: []
state:
  base:
    revision: 8a9650eca6c71f361a1bb4a81e3f9ce4a0e34765
    ref: refs/heads/main
    verified_at: '2026-11-06T02:04:00Z'
  candidate:
    branch: feature/46-compaction-contracts
    revision: dc80cddd77108994907d74c4ae9217149e3b1a98
    pull_request:
      provider: github
      id: egohygiene/mindgarden#73
      url: https://github.com/egohygiene/mindgarden/pull/73
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-06T03:55:44Z'
    default_branch_revision: 8a9650eca6c71f361a1bb4a81e3f9ce4a0e34765
    issue_state: open
    pull_request_state: draft
    notes: 'All six drafts remain pushed/unmerged. Final conformance follow-up 9e134e9 is carried through
      #71/#72/#73 with local branch merges. Main remains 8a9650e; all 38 parents remain open. New exact-head
      automatic checks follow the final push.'
  parallel_changes: []
review:
  status: partial
  reviewed_at: '2026-11-06T03:55:44Z'
  reviewed_by: codex
  evidence:
  - command: .venv/bin/python -m unittest discover --start-directory tests --verbose; .cache/python313/bin/python
      -m unittest discover --start-directory tests --verbose
    outcome: passed
    observed_at: '2026-11-06T03:55:44Z'
    notes: 231 tests each without skips; final compaction reader tightening additionally passes 10 tests
      on each version.
  - command: Clean git-archive -S scripts/compaction_demo.py / isolated installed-wheel -I scripts/compaction_demo.py
    outcome: passed
    observed_at: '2026-11-06T03:55:44Z'
    notes: 'Both match committed expected proof: 2 exact citations, 4001/8192-byte context, preserved
      originals and explicit review.'
  - command: .venv/bin/python -m build --sdist --wheel --outdir .cache/dist; both compile checks; pinned
      owner schemas; relative links; git diff --check
    outcome: passed
    observed_at: '2026-11-06T03:55:44Z'
    notes: Fresh code/resources and checks pass. CI results remain separate; no workflow manually launched.
  - command: .venv/bin/python -m unittest tests.test_publication_conformance tests.test_federation tests.test_site
      --verbose; same with .cache/python313/bin/python
    outcome: passed
    observed_at: '2026-11-06T03:55:44Z'
    notes: 38 tests each after final storage-root correction. Initial socket-restricted attempt was rerun
      with loopback permission.
  environment_limitations:
  - New exact-head CI after the final follow-up is recorded on the PRs; previous successful heads remain
    historical receipts.
  - Full accessibility/consumer/runtime, Relay deployment, raw-only compaction, retention execution and
    approved private-pilot gates remain open.
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

Resume the six authorized drafts in docs/garden-experience-milestone.md. Live
repository/user authority precedes this handoff. ADRs retain proposed status and
null approval. No merging is authorized in this batch; await maintainer sync.

## Resume protocol

Read git status, current issues/PRs, the batch map, ROADMAP.md, coverage ledger and
relevant decisions. Preserve Python/v0. Use synthetic fixtures and explicit
temporary bindings only. Keep real gardens and default registry locations alone.

## Current objective and success conditions

Deliver #17, #38, #10, #18, #42 and #46 as separate drafts. Keep dependent PRs
stacked with a reproducible combined checkout. Continue independent work where
external acceptance is blocked. A bounded proof does not close its parent issue.

## State snapshot

Base main 8a9650eca6c71f361a1bb4a81e3f9ce4a0e34765 merges #67. Its tree equals
tested 3463d46. The batch map records each source checkpoint, branch/base and PR.
The candidate above identifies functional source; later handoff commits may
change documentation only. All batch PRs remain drafts and parents remain open.

## Completed and material changes

#68 adds scoped v1 public projection, pinned offline Quartz rendering, exact citations, selected-only search/backlinks/graph, immutable outputs and a loopback preview. #69 adds versioned design tokens/schema/references, offline exports, an optional revision-bound Quartz/CSS consumer and mobile navigation/resize correction. #70 adds bounded complete public-output inspection, cache/log isolation, exact unique routes, live preview integrity/authority and shareable diagnostics; its reusable synthetic conformance pack covers eight leak surfaces. #71 adds pinned public site composition, portable ownership receipts, sibling preservation and partial-failure recovery. Relay action/deployment acceptance is explicitly retained. #72 documents all ten #42 topics with focused proposals, source/control/projection and full repository/runtime ownership, independent bookmark approvals, migration costs and conditional follow-ups. No runtime changes under #42. #73 adds v1 compaction/retention/private manifest contracts, scoped read-only preview, qualification-preserving curation handoff and authored archive→reviewed prompt→exact search→bounded context proof. No retention jobs, deletion, raw-only expansion or approved private pilot. Final audit follow-up 9e134e9 in #70 rejects malformed unselected storage-root aliases before output/cache planning; local branch merges propagate it through #71/#72/#73 without merging any PR.

## Validation and review evidence

Full 231-test suites pass on Python 3.12.14/3.13.5, with final compaction checks and 38 publication/federation/site checks on each version after the storage-boundary correction. Clean -S source and isolated -I wheel site/portal/compaction proofs match committed results. Fresh resources, compilation, owner metadata and whitespace pass. Earlier head CI passed; new follow-up heads are checked separately.

## Blockers, risks, unknowns, and deferred work

Full accessibility/large-corpus/real-consumer acceptance, Relay/host deployment,
restricted-runtime assurance and approved private compaction pilot remain separate.
No package/site publication, model service, destructive migration or human ADR
ratification is claimed. Rich body Markdown/assets remain outside the literal
site adapter. Source retention defaults to preserve.

## Next dependency-ready work

Sync with the maintainer and review #68 → #69 → #70 → #71 → #72 → #73 in order. Merge only after that sync; record separate human ADR disposition before consequential #32/#47 choices. Combined checkout: feature/46-compaction-contracts.

## Parallel changes and reconciliation

There were no open PRs at the batch start. The explicit review stack is recorded
in the batch map; style/docs are not new semantic prerequisites. Preserve the
final combined branch. Reconcile live changes before another batch.

## Privacy and redaction

Only synthetic records, archives and labels. Physical locations and private
control/profile/session/registry digests stay out of public artifacts. Source
instructions remain data and never confer execution, review or publication power.

## Handoff update protocol

At every checkpoint record functional commit, branch/base/PR, completed criteria,
exact commands and results, CI separately, remaining parent scope and next action.

## Compaction and supersession

Keep under 16384 bytes/240 lines. Link durable evidence instead of copying logs.
All six drafts await maintainer sync; parent closure requires its own evidence.
