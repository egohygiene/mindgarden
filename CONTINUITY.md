---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-06T03:17:31Z'
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
    id: egohygiene/mindgarden#42
    url: https://github.com/egohygiene/mindgarden/issues/42
  next:
    kind: action
    id: compaction-retention-contract-checkpoint
    description: 'Branch feature/46-compaction-contracts from #72; deliver versioned non-destructive compaction/retention
      contracts and authored synthetic evidence, preserving review authority and originals.'
    readiness: ready
    references:
    - https://github.com/egohygiene/mindgarden/issues/46
    depends_on: []
state:
  base:
    revision: 8a9650eca6c71f361a1bb4a81e3f9ce4a0e34765
    ref: refs/heads/main
    verified_at: '2026-11-06T02:04:00Z'
  candidate:
    branch: docs/42-architecture-decisions
    revision: d17f01c4cfa01145090d14aff97624f636fe7f92
    pull_request:
      provider: github
      id: egohygiene/mindgarden#72
      url: https://github.com/egohygiene/mindgarden/pull/72
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-06T03:17:31Z'
    default_branch_revision: 8a9650eca6c71f361a1bb4a81e3f9ce4a0e34765
    issue_state: open
    pull_request_state: draft
    notes: 'Drafts #68 through #72 are pushed. #46 is the final authorized checkpoint. All merging awaits
      maintainer sync; all new ADRs remain proposed/null approval.'
  parallel_changes: []
review:
  status: partial
  reviewed_at: '2026-11-06T03:17:31Z'
  reviewed_by: codex
  evidence:
  - command: python3 .cache/six_owner_checks.py
    outcome: passed
    observed_at: '2026-11-06T03:17:31Z'
    notes: "15 indexed ADR-0007\u20130021 all proposed/null approval; pinned Hygiene/Aether schemas, continuity\
      \ bounds and 38 issue rows."
  - command: python3 .cache/six_doc_links.py; git diff --check
    outcome: passed
    observed_at: '2026-11-06T03:17:31Z'
    notes: 17 documentation files and 96 relative links; no runtime changes.
  - command: git diff 0d34a6b -- src tests scripts contracts profiles pyproject.toml MANIFEST.in --exit-code
    outcome: passed
    observed_at: '2026-11-06T03:17:31Z'
    notes: 'Exact tested #71 runtime retained; 221-test source evidence unchanged.'
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

#68 adds scoped v1 public projection, pinned offline Quartz rendering, exact citations, selected-only search/backlinks/graph, immutable outputs and a loopback preview. #69 adds versioned design tokens/schema/references, offline exports, an optional revision-bound Quartz/CSS consumer and mobile navigation/resize correction. #70 adds bounded complete public-output inspection, cache/log isolation, exact unique routes, live preview integrity/authority and shareable diagnostics; its reusable synthetic conformance pack covers eight leak surfaces. #71 adds pinned public site composition, portable ownership receipts, sibling preservation and partial-failure recovery. Relay action/deployment acceptance is explicitly retained. #72 documents all ten #42 topics with focused proposals, source/control/projection and full repository/runtime ownership, independent bookmark approvals, migration costs and conditional follow-ups. No runtime changes under #42.

## Validation and review evidence

Documentation-only #72 passes pinned Hygiene ADR/policy/set/index, Aether continuity, 96 relative links and whitespace checks. Runtime is unchanged from #71, whose 221 tests pass on both supported Python versions. No redundant full local test run is claimed for #72.

## Blockers, risks, unknowns, and deferred work

Full accessibility/large-corpus/real-consumer acceptance, Relay/host deployment,
restricted-runtime assurance and approved private compaction pilot remain separate.
No package/site publication, model service, destructive migration or human ADR
ratification is claimed. Rich body Markdown/assets remain outside the literal
site adapter. Source retention defaults to preserve.

## Next dependency-ready work

Branch feature/46-compaction-contracts from #72; deliver versioned non-destructive compaction/retention contracts and authored synthetic evidence, preserving review authority and originals.

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
