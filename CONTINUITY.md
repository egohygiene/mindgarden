---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-06T10:57:04Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: 'Execute the authorized #29/#31/#30/#35/#45 private policy and storage draft checkpoints.'
  includes:
  - private policy, output enforcement, registry, document and vault checkpoints
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
work:
  objective: Extend the existing stack through the five authorized private policy/storage checkpoints.
  success_conditions:
  - Confirmed issue order and dependency corrections recorded.
  - Each checkpoint has a draft PR, exact verification and retained parent criteria.
  - Preserve Python/v0, private boundaries and proposed ADR status.
  active_issue:
    provider: github
    id: egohygiene/mindgarden#35
    url: https://github.com/egohygiene/mindgarden/issues/35
  next:
    kind: action
    id: mixed-source-vault-checkpoint
    description: 'Implement #45 mixed archive/PDF/media asset manifests, append-only non-destructive triage
      and explicit storage adapter registration. Prove restore/relocation with exact references and no
      Google/model services; retain external encrypted/provider/platform gates.'
    readiness: ready
    references:
    - https://github.com/egohygiene/mindgarden/issues/35
    depends_on: []
state:
  base:
    revision: 30a29668a02740a91e77aec22f670a8270ccddf4
    ref: refs/heads/main
    verified_at: '2026-11-06T05:27:17Z'
  candidate:
    branch: feature/35-local-document-adapter
    revision: e966e3e10d9279cbb4ef7c518a35ab01f2d610e5
    pull_request:
      provider: github
      id: egohygiene/mindgarden#83
      url: https://github.com/egohygiene/mindgarden/pull/83
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-06T10:57:04Z'
    default_branch_revision: 30a29668a02740a91e77aec22f670a8270ccddf4
    issue_state: open
    pull_request_state: draft
    notes: 'Existing #74–#79 and new storage drafts remain unmerged. No parent closure or ADR ratification.'
  parallel_changes: []
review:
  status: partial
  reviewed_at: '2026-11-06T10:57:04Z'
  reviewed_by: codex
  evidence:
  - command: .venv/bin/python -m unittest tests.test_documents tests.test_source_adapters tests.test_v1_contracts
      -q
    outcome: passed
    observed_at: '2026-11-06T10:57:04Z'
    notes: 20 passed
  - command: .cache/python313/bin/python -m unittest tests.test_documents -q
    outcome: passed
    observed_at: '2026-11-06T10:57:04Z'
    notes: 8 passed
  - command: .venv/bin/python scripts/document_demo.py --workspace .cache/pdf-final-proof --tool-directory
      /usr/bin --require-source --report .cache/pdf-final-proof.json
    outcome: passed
    observed_at: '2026-11-06T10:57:04Z'
    notes: real Poppler 25.03.0 six states, page golden, repeat import, scratch cleanup pass
  - command: .venv/bin/python scripts/private_garden_demo.py --workspace .cache/pdf-private-compatibility
      --require-source
    outcome: passed
    observed_at: '2026-11-06T10:57:04Z'
    notes: full existing golden matched
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

The maintainer authorized #29 → #31 → #30 → #35 → #45 on top of the existing
#74–#79 stack. Keep new checkpoints as draft PRs for review. This instruction
does not authorize merging or ratifying proposed ADRs.

## Resume protocol

Read git status, live PR/issues, README, AI_CONSTITUTION, ROADMAP, the coverage
ledger and docs/private-storage-sprint.md. Inspect existing services before edits.
Preserve Python/v0; only synthetic gardens and captured sources enter this repo.

## Current objective and success conditions

Complete bounded follow-ups over draft #79 (8e15314), one draft per issue,
with verification, honest retained parent scope and reproducible combined checkout.

## State snapshot

Draft #83 on feature/35-local-document-adapter is stacked over #82/#81/#80/#79. Functional source e966e3e; all drafts remain unmerged.

## Completed and material changes

Optional local PDF reader and versioned bundle/page contracts with original hashes, parser provenance, page geometry and exact UTF-8 word spans. Explicit digest-bound initial human classification for new ordinary synthetic inputs; default restricted processing unavailable before input/parser/temp access. Six incomplete/error states fail without partial ingestion. Proposed ADR-0023 is unapproved.

## Validation and review evidence

20 document/adapter/contracts tests pass on 3.12; 8 document tests pass on 3.13. Real Poppler 25.03.0 six-state/page-golden/idempotence/cleanup proof passes. Existing private CLI golden and owner/compile/diff checks pass.

## Blockers, risks, unknowns, and deferred work

Normative Hygiene #39/#40, Realm #25/#60, encrypted storage/key broker and confidential runtime are unavailable here. OCR/office/semantic layout/attachment extraction and real private consumer acceptance remain parent scope. Initial classification is not declassification or publication approval.

## Next dependency-ready work

Implement #45 mixed archive/PDF/media asset manifests, append-only non-destructive triage and explicit storage adapter registration. Prove restore/relocation with exact references and no Google/model services; retain external encrypted/provider/platform gates.

## Parallel changes and reconciliation

#80 begins at #79; each later draft names its preceding branch as base.
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
The private-storage map supersedes the previous six-checkpoint review-only next action.
