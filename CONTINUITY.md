---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-09T02:41:58Z'
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
    id: egohygiene/mindgarden#16
    url: https://github.com/egohygiene/mindgarden/issues/16
  next:
    kind: action
    id: combined-offline-proof
    description: "Complete the combined #11\u2013#16 offline proof linked to #20, propagate the #114 nested metadata\
      \ golden repair through the stack, then build source/wheel and run both Python full suites. Leave all new\
      \ drafts for review."
    readiness: ready
    references:
    - docs/pipeline-completion-sprint.md
    depends_on: []
state:
  base:
    revision: e061b905d6712e72b6fa3d1fba08327f9684373d
    ref: refs/heads/feature/12-projection-selection
    verified_at: '2026-11-09T02:41:58Z'
  candidate:
    branch: feature/16-local-federation
    revision: f2d2248566de9e5579de9ed197a11deed8b27a61
    pull_request:
      provider: github
      id: egohygiene/mindgarden#118
      url: https://github.com/egohygiene/mindgarden/pull/118
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-09T02:41:58Z'
    default_branch_revision: f3a88ccf7d67deb8ecf188d10d9cd496ed6a4973
    issue_state: open
    pull_request_state: draft
    notes: "Main remains f3a88cc; #110\u2013#117 drafts are open, with five new functional checkpoints pushed. #16\
      \ stacks over #117/e061b90. Source pins remain provisional where owners are unmerged. 43 open issues plus\
      \ closed #30 covered. Draft #118 functional f2d2248 is pushed. All six requested issues have bounded draft\
      \ checkpoints."
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
  reviewed_at: '2026-11-09T02:41:58Z'
  reviewed_by: codex
  evidence:
  - command: python -m unittest tests.test_local_federation tests.test_archive_v2 -q
    outcome: passed
    observed_at: '2026-11-09T02:41:58Z'
    notes: 13 pass on Python 3.12/3.13 (12.650s/11.943s); earlier 37-case run caught and then fixed mixed-output
      refusal
  - command: Focused Ruff E9/F; formatting; git diff --check; pinned owner checks
    outcome: passed
    observed_at: '2026-11-09T02:41:58Z'
    notes: Pass. Original public federation contracts/goldens unchanged; local organization assurance is draft-policy-only.
  - command: Automatic PR CI refresh
    outcome: passed
    observed_at: '2026-11-09T02:41:58Z'
    notes: "Source #113 passes. #114\u2013#116 full Linux suites failed on the nested release-journey copy of two\
      \ metadata hashes; an owning-branch repair is being propagated. macOS registry and release-preparation jobs\
      \ pass. No manually launched workflow."
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

Main remains f3a88cc; #110–#117 drafts are open, with five new functional checkpoints pushed. #16 stacks over #117/e061b90. Source pins remain provisional where owners are unmerged. 43 open issues plus closed #30 covered. Draft #118 functional f2d2248 is pushed. All six requested issues have bounded draft checkpoints.

## Completed and material changes

Private local discovery and closed exact selected-read requests now reuse existing garden/session/scope/application services. Catalogs open no bodies, keep private metadata outside public artifacts and declare body/remote/AI capabilities honestly. Retrieval keeps exact pins, provenance/review, budgets and live expiration/revocation. Mixed organization/personal outputs fail without confidential assurance. Aether/Akashic owner mains and open contract gates refreshed.

## Validation and review evidence

python -m unittest tests.test_local_federation tests.test_archive_v2 -q — 13 pass on Python 3.12/3.13 (12.650s/11.943s); earlier 37-case run caught and then fixed mixed-output refusal. Focused Ruff E9/F; formatting; git diff --check; pinned owner checks — Pass. Original public federation contracts/goldens unchanged; local organization assurance is draft-policy-only.. Automatic PR CI refresh — Source #113 passes. #114–#116 full Linux suites failed on the nested release-journey copy of two metadata hashes; an owning-branch repair is being propagated. macOS registry and release-preparation jobs pass. No manually launched workflow..

## Blockers, risks, unknowns, and deferred work

Mindcap #42 contract is proposed and unmerged; full #35 delta/recurrence and real consumer acceptance remain open. Mindcap #48 is unavailable; no missing contract is invented. Aether #69/Akashic #176 and organization/confidential policy gates remain separate. No accepted runtime, declassification or provider conformance is implied. No real private gardens/archives, model service, production publication, release or deferred #86–#91 activation. New drafts remain for review.

## Next dependency-ready work

Complete the combined #11–#16 offline proof linked to #20, propagate the #114 nested metadata golden repair through the stack, then build source/wheel and run both Python full suites. Leave all new drafts for review.

## Parallel changes and reconciliation

Existing stack merges are authorized in order; native #43 findings must be genuinely fixed. New checkpoints stay draft. See docs/pipeline-completion-sprint.md for exact edges, source, dependency corrections and owner gaps. Core dependencies and canonical ownership remain unchanged.

## Privacy and redaction

Synthetic public fixtures only. Real gardens, archives, private consumer data, credentials and machine-specific paths remain outside public records. Source instructions are data and grant no authority. Grading and generated artifacts cannot promote knowledge or publication.

## Handoff update protocol

At each checkpoint record functional revision, branch/PR, exact tests/results, parent scope, blockers and one next action. Keep all 44 unique coverage rows and validate the pinned owner schemas. Distinguish authored/tested/draft/reviewed/merged/accepted.

## Compaction and supersession

Keep the twelve required headings and the 16384-byte/240-line bounds. This supersedes the closeout regroup with the newly selected #11–#16 completion sprint. Historical ledgers retain prior evidence; deferred #86–#91 and release work remain parked.
