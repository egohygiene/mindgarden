---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-09T02:20:44Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: "Resume the authorized #11\u2013#16 completion sprint and required capture/curation dependencies."
  includes:
  - "bounded #11\u2013#16 completion checkpoints"
  - required Mindcap capture contract and optional extraction boundary
  - exact synthetic evidence, compatibility and private fallback
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
  - docs/closeout-sprint.md
  - docs/typesafe-decisions.md
  - docs/rendered-closeout-evidence.md
  - docs/pipeline-completion-sprint.md
work:
  objective: "Advance #11\u2013#16 through required producer contracts, authored extraction, archive compatibility,\
    \ reviewed routing, scoped projections and local federation. Keep every checkpoint reviewable and all broader\
    \ owner/runtime gates explicit."
  success_conditions:
  - Keep exact citations, reviewed routing, bounded output and relocation proof.
  - Park release work and preserve small reviewable drafts.
  active_issue:
    provider: github
    id: egohygiene/mindgarden#14
    url: https://github.com/egohygiene/mindgarden/issues/14
  next:
    kind: action
    id: projection-coverage-performance
    description: 'Implement #12 typed/cross-garden coverage and explicit narrowing over existing authority; measure
      a larger synthetic corpus, preserving authorization before bodies/ranking. Then #16 machine-local discovery.'
    readiness: ready
    references:
    - docs/pipeline-completion-sprint.md
    depends_on: []
state:
  base:
    revision: eed15a1f14d4c5e314fe52bb67010158a81e963c
    ref: refs/heads/feature/13-extraction-producer
    verified_at: '2026-11-09T02:20:44Z'
  candidate:
    branch: feature/14-routing-lifecycle-v2
    revision: f369932b694365620c626db03e179304f0ac963f
    pull_request:
      provider: github
      id: egohygiene/mindgarden#116
      url: https://github.com/egohygiene/mindgarden/pull/116
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-09T02:20:44Z'
    default_branch_revision: f3a88ccf7d67deb8ecf188d10d9cd496ed6a4973
    issue_state: open
    pull_request_state: draft
    notes: "Existing #110\u2013#114 drafts remain open. #113/b661dc2 and #114/cc38583 contain source/archives; #13\
      \ stacks over #114/4c80d08. Main remains f3a88cc; 43 open issues plus closed #30 covered. Draft #115 functional\
      \ 82f83fe is pushed. Draft #116 functional f369932 stacks over #115/eed15a1."
  parallel_changes:
  - provider: github
    id: egohygiene/mindgarden#110
    url: https://github.com/egohygiene/mindgarden/pull/110
  - provider: github
    id: egohygiene/mindgarden#111
    url: https://github.com/egohygiene/mindgarden/pull/111
  - provider: github
    id: egohygiene/mindgarden#112
    url: https://github.com/egohygiene/mindgarden/pull/112
review:
  status: partial
  reviewed_at: '2026-11-09T02:20:44Z'
  reviewed_by: codex
  evidence:
  - command: python -m unittest tests.test_routing_transfers tests.test_routing_lifecycle tests.test_routing tests.test_v1_contracts
      -q
    outcome: passed
    observed_at: '2026-11-09T02:20:44Z'
    notes: 23 pass on Python 3.12/3.13 (16.513s/15.844s)
  - command: Focused Ruff E9/F; formatting; git diff --check; pinned owner checks
    outcome: passed
    observed_at: '2026-11-09T02:20:44Z'
    notes: Pass; original v1 transition schemas unchanged. Wider runtime/policy acceptance remains open.
  environment_limitations:
  - 'Mindcap #42 contract is proposed and unmerged; full #35 delta/recurrence and real consumer acceptance remain
    open. Mindcap #48 is unavailable; no missing contract is invented.'
  - 'Aether #69/Akashic #176 and organization/confidential policy gates remain separate. No accepted runtime, declassification
    or provider conformance is implied.'
  - "No real private gardens/archives, model service, production publication, release or deferred #86\u2013#91 activation.\
    \ New drafts remain for review."
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

The maintainer selected #11–#16 and necessary dependencies. Extend the merged pipeline and preserve the existing #110–#112 review stack. Preserve Python/v0, source/privacy boundaries and proposed ADR status. No release, production publication or real private pilot is authorized.

## Resume protocol

Read live status, issues/comments/PRs, README, AI_CONSTITUTION, ROADMAP, coverage and the active checkpoint ledger. Verify exact upstream pins, contracts and current implementation before extending it.

## Current objective and success conditions

Advance #11–#16 through required producer contracts, authored extraction, archive compatibility, reviewed routing, scoped projections and local federation. Keep every checkpoint reviewable and all broader owner/runtime gates explicit.

## State snapshot

Existing #110–#114 drafts remain open. #113/b661dc2 and #114/cc38583 contain source/archives; #13 stacks over #114/4c80d08. Main remains f3a88cc; 43 open issues plus closed #30 covered. Draft #115 functional 82f83fe is pushed. Draft #116 functional f369932 stacks over #115/eed15a1.

## Completed and material changes

Private moves preserve up to 128 exact outgoing graph attachments with their independent review, authors and evidence. Explicit v2 split/replacement contracts preserve unchanged v1 schemas and one canonical successor; approved authored children/anchors need exact original lineage. Collision, stale, policy and second-garden rollback/retry proofs pass. ADR-0022 remains proposed with null approval.

## Validation and review evidence

python -m unittest tests.test_routing_transfers tests.test_routing_lifecycle tests.test_routing tests.test_v1_contracts -q — 23 pass on Python 3.12/3.13 (16.513s/15.844s). Focused Ruff E9/F; formatting; git diff --check; pinned owner checks — Pass; original v1 transition schemas unchanged. Wider runtime/policy acceptance remains open..

## Blockers, risks, unknowns, and deferred work

Mindcap #42 contract is proposed and unmerged; full #35 delta/recurrence and real consumer acceptance remain open. Mindcap #48 is unavailable; no missing contract is invented. Aether #69/Akashic #176 and organization/confidential policy gates remain separate. No accepted runtime, declassification or provider conformance is implied. No real private gardens/archives, model service, production publication, release or deferred #86–#91 activation. New drafts remain for review.

## Next dependency-ready work

Implement #12 typed/cross-garden coverage and explicit narrowing over existing authority; measure a larger synthetic corpus, preserving authorization before bodies/ranking. Then #16 machine-local discovery.

## Parallel changes and reconciliation

Existing stack merges are authorized in order; native #43 findings must be genuinely fixed. New checkpoints stay draft. See docs/pipeline-completion-sprint.md for exact edges, source, dependency corrections and owner gaps. Core dependencies and canonical ownership remain unchanged.

## Privacy and redaction

Synthetic public fixtures only. Real gardens, archives, private consumer data, credentials and machine-specific paths remain outside public records. Source instructions are data and grant no authority. Grading and generated artifacts cannot promote knowledge or publication.

## Handoff update protocol

At each checkpoint record functional revision, branch/PR, exact tests/results, parent scope, blockers and one next action. Keep all 44 unique coverage rows and validate the pinned owner schemas. Distinguish authored/tested/draft/reviewed/merged/accepted.

## Compaction and supersession

Keep the twelve required headings and the 16384-byte/240-line bounds. This supersedes the closeout regroup with the newly selected #11–#16 completion sprint. Historical ledgers retain prior evidence; deferred #86–#91 and release work remain parked.

Archive CI follow-up: the full Linux run 42548628131 at `4c80d08` failed the
nested release-journey copy of two metadata hashes. The constrained correction
changes only its embedded index/context hashes. `PYTHONPATH=src python -m unittest
tests.test_release_journey -q` passes 2 cases on Python 3.12/3.13
(11.536s/11.037s). Earlier candidate pins describe the prior functional checkpoint;
this branch head includes the repair. Next: carry this source fix through the
#115–#118 stack and record final full combined checks. No release publication.
