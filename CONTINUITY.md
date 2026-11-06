---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-06T02:04:00Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: 'Implement the six authorized draft checkpoints: #17, #38, #10, #18, #42 and #46.'
  includes:
  - registry lifecycle, named-view integration, synthetic preservation/privacy proof and retained gates
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
    id: egohygiene/mindgarden#17
    url: https://github.com/egohygiene/mindgarden/issues/17
  next:
    kind: action
    id: finish-public-preview-checkpoint
    description: 'Finish actual Quartz/browser/package proof, push draft #17 checkpoint, then continue
      #38/#10/#18/#42/#46 without routine confirmation.'
    readiness: ready
    references:
    - https://github.com/egohygiene/mindgarden/issues/17
    depends_on: []
state:
  base:
    revision: 8a9650eca6c71f361a1bb4a81e3f9ce4a0e34765
    ref: refs/heads/main
    verified_at: '2026-11-06T02:04:00Z'
  candidate:
    branch: feature/17-v1-garden-preview
    revision: 8a9650eca6c71f361a1bb4a81e3f9ce4a0e34765
    pull_request: null
    handoff_state: in-progress
  live:
    status: verified
    observed_at: '2026-11-06T02:04:00Z'
    default_branch_revision: 8a9650eca6c71f361a1bb4a81e3f9ce4a0e34765
    issue_state: open
    pull_request_state: not-applicable
    notes: '#67 is merged, with the exact tested 3463d46 tree. 38 issues and no open PRs at start. Six
      new drafts are authorized; merging and ADR ratification await maintainer sync.'
  parallel_changes: []
review:
  status: partial
  reviewed_at: '2026-11-06T02:04:00Z'
  reviewed_by: codex
  evidence:
  - command: .venv/bin/python -m unittest discover --start-directory tests
    outcome: passed
    observed_at: '2026-11-06T02:04:00Z'
    notes: 188-test merged baseline, no skips.
  - command: .venv/bin/python -m unittest tests.test_site tests.test_v1_contracts tests.test_publish_garden
      --verbose
    outcome: passed
    observed_at: '2026-11-06T02:04:00Z'
    notes: 20 targeted site/schema/v0-publishing tests; actual rendering/browser/package proof in progress.
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

Resume the six authorized draft checkpoints in docs/garden-experience-milestone.md.
Live repository/user authority precedes this handoff. Proposed decisions retain
null approval; draft implementation and merging do not ratify architecture.

## Resume protocol

Read branch/status, live issues/PRs, the six-checkpoint handoff, ROADMAP.md and
coverage ledger. Preserve Python/v0. Use synthetic fixtures and explicit temporary
bindings only. Do not configure real gardens or default registry locations.

## Current objective and success conditions

Deliver #17, #38, #10, #18, #42 and #46 as six separate drafts. Keep dependent PRs
stacked and preserve a combined checkout. Continue independent work when a real
external gate blocks full integration; leave all merging for maintainer sync.

## State snapshot

Base main 8a9650eca6c71f361a1bb4a81e3f9ce4a0e34765 merges #67. Its tree equals
tested 3463d46. Current branch feature/17-v1-garden-preview has the initial v1
public-site implementation locally; first draft pending. #67's old draft wording
in earlier documents is historical and must be reconciled during this batch.

## Completed and material changes

V1 public selection reused for site projections; typed x-site adapter declaration;
create-or-verify content/site manifests; private digest-bound plans; literal body
rendering, exact citations, selected-only typed links and useful empty selection.
CLI publish/site dispatch preserves v0. Rendering uses separately prepared clean
Quartz 075afd3 and offline npm cache, copying tracked sources into an owned scratch
tree. Scratch inputs live outside Git because Quartz honors ancestor ignores.
A loopback preview serves only manifest members with live authority/hash checks.

## Validation and review evidence

188-test merged baseline passes. 20 targeted site/schema/v0 publication checks
pass. Actual renderer/browser and fresh package/clean-install proof are in
progress. Renderer acquisition was explicit, separate from offline query/build.
No deployment, manually launched paid workflow, package publication or model call.

## Blockers, risks, unknowns, and deferred work

Full #17 accessibility/large corpus and real-consumer acceptance, #18 Relay/host
proof, #10 normative policy/runtime integration and #46 approved private pilot
remain broader scope. #42 produces proposed decisions only. Restricted/encrypted
assurance depends on external Hygiene/Realm contracts; source retention defaults
to preserve. Rich body Markdown/assets are outside the initial literal adapter.

## Next dependency-ready work

Finish #17 rendering/browser/resource evidence, open its coherent draft, update
branch/PR/commits here, then proceed through #38/#10/#18/#42/#46. Every checkpoint
updates the six-PR map, exact commands/results and next action. No routine
confirmation between authorized checkpoints; no automatic merge.

## Parallel changes and reconciliation

No open PR at start. Stack later review branches explicitly; it is a combined
checkout convenience, not an invented semantic dependency on style/doc work.

## Privacy and redaction

Only synthetic canonical roots, archives and labels. Keep physical paths, private
control/profile/session hashes and registry metadata out of public artifacts.
Source text stays data and never grants execution or review authority.

## Handoff update protocol

Record source commit, branch/base/PR, completed checkpoint, local and hosted
results separately, retained parent scope, blockers and exact next action.

## Compaction and supersession

Keep under 16384 bytes/240 lines. Link evidence reports instead of duplicating
logs. All six drafts await maintainer sync; broader parent closure needs its own
acceptance evidence.
