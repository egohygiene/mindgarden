---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-06T02:48:25Z'
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
    id: egohygiene/mindgarden#38
    url: https://github.com/egohygiene/mindgarden/issues/38
  next:
    kind: action
    id: public-conformance-checkpoint
    description: 'Branch feature/10-public-conformance from #69; deliver reusable publication/preview
      negatives and stable diagnostics, then #18/#42/#46.'
    readiness: ready
    references:
    - https://github.com/egohygiene/mindgarden/issues/10
    depends_on: []
state:
  base:
    revision: 8a9650eca6c71f361a1bb4a81e3f9ce4a0e34765
    ref: refs/heads/main
    verified_at: '2026-11-06T02:04:00Z'
  candidate:
    branch: feature/38-design-tokens
    revision: 5b59d8e3c6b8b0fbdb1acdcf25a76ebf99968f18
    pull_request:
      provider: github
      id: egohygiene/mindgarden#69
      url: https://github.com/egohygiene/mindgarden/pull/69
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-06T02:48:25Z'
    default_branch_revision: 8a9650eca6c71f361a1bb4a81e3f9ce4a0e34765
    issue_state: open
    pull_request_state: draft
    notes: 'Drafts #68/#69 are pushed; automatic CI observed separately from local tests. Four more drafts
      remain authorized. No merges before sync.'
  parallel_changes: []
review:
  status: partial
  reviewed_at: '2026-11-06T02:48:25Z'
  reviewed_by: codex
  evidence:
  - command: .venv/bin/python -m unittest discover --start-directory tests --verbose; .cache/python313/bin/python
      -m unittest discover --start-directory tests --verbose
    outcome: passed
    observed_at: '2026-11-06T02:48:25Z'
    notes: 201 tests each without skips; final CSS changes additionally pass 13 targeted tests and 3.13
      design tests.
  - command: .venv/bin/python -m build --sdist --wheel; isolated wheel design export; both compileall
      checks; python3 .cache/six_owner_checks.py; git diff --check
    outcome: passed
    observed_at: '2026-11-06T02:48:25Z'
    notes: Fresh source/wheel, token identity, pinned owner schemas and whitespace pass.
  - command: Prepared offline Quartz render and Chromium/Playwright loopback checks
    outcome: passed
    observed_at: '2026-11-06T02:48:25Z'
    notes: 60 files; search/backlinks/3 nodes/1 edge/zoom; no mobile overflow, external requests or page
      errors. Bounded layout/color evidence, not full WCAG acceptance.
  environment_limitations:
  - No new hosted CI result is claimed before the draft is pushed.
  - Full accessibility/large-graph/native/restricted-runtime, Relay/host deployment and approved private-pilot
    acceptance remain separate.
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

#68 adds scoped v1 public projection, pinned offline Quartz rendering, exact citations, selected-only search/backlinks/graph, immutable outputs and a loopback preview. #69 adds versioned design tokens/schema/references, offline exports, an optional revision-bound Quartz/CSS consumer and mobile navigation/resize correction.

## Validation and review evidence

201 tests pass on Python 3.12.14 and 3.13.5 without skips; final style changes pass targeted tests. Fresh source/wheel, isolated installed token export, both compile checks and owner metadata pass. Actual themed Quartz render: 60 files; Chromium search/backlinks/SVG zoom and 1360-to-390px resize pass, with zero external requests/page errors. Exact commands and prior #68 clean-source/wheel evidence are in the batch map.

## Blockers, risks, unknowns, and deferred work

Full accessibility/large-corpus/real-consumer acceptance, Relay/host deployment,
restricted-runtime assurance and approved private compaction pilot remain separate.
No package/site publication, model service, destructive migration or human ADR
ratification is claimed. Rich body Markdown/assets remain outside the literal
site adapter. Source retention defaults to preserve.

## Next dependency-ready work

Branch feature/10-public-conformance from #69; deliver reusable publication/preview negatives and stable diagnostics, then #18/#42/#46.

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
