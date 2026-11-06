---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-06T22:18:36Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: Preserve bounded provider, consumer and release preparation evidence without claiming unavailable pilot
    or publication acceptance.
  includes:
  - provider portability, release tooling, synthetic journey and acceptance gates
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
work:
  objective: Prepare reproducible Python release evidence through pinned owner contracts without publishing or claiming
    full 1.0 acceptance.
  success_conditions:
  - Keep pyproject.toml as the sole version authority and derive runtime/provenance versions.
  - Build source-bound artifacts twice, verify exact hashes and preserve external policy/schema/signing/PyPI gates.
  - 'Leave a small draft over #94, then advance the synthetic consumer/pilot handoff and conditional acceptance
    checks.'
  active_issue:
    provider: github
    id: egohygiene/mindgarden#27
    url: https://github.com/egohygiene/mindgarden/issues/27
  next:
    kind: action
    id: synthetic-consumer-and-private-pilot-handoff
    description: 'Implement #20 synthetic archive→review/routing→public projection and pinned Empathy consumer evidence
      on a branch over draft #95. Prepare a private pilot with explicit input/workspace/classification; do not run
      real data until the pending user input arrives. Then deliver conditional #19 pre/postpublication acceptance
      checks.'
    readiness: ready
    references:
    - docs/release-checkpoints.md
    depends_on: []
state:
  base:
    revision: 62cbead700679e6b12984f1fc502d27c427fd6bb
    ref: refs/heads/feature/51-provider-switch-proof
    verified_at: '2026-11-06T22:18:36Z'
  candidate:
    branch: feature/27-release-preparation
    revision: a3cbac93d2a68e99e7955ddb18302e0358f53247
    pull_request:
      provider: github
      id: egohygiene/mindgarden#95
      url: https://github.com/egohygiene/mindgarden/pull/95
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-06T22:18:36Z'
    default_branch_revision: d5edb13de1b65871ec85e7a25af035228a1d756d
    issue_state: open
    pull_request_state: draft
    notes: 'Main remains d5edb13. #93/#94/#95 are open drafts. #94 exact head passed Test 42300786846. #95 exact
      source produced local artifacts and retains the owner schema blocker. No release exists; real-pilot inputs
      are pending.'
  parallel_changes:
  - provider: github
    id: egohygiene/mindgarden#93
    url: https://github.com/egohygiene/mindgarden/pull/93
  - provider: github
    id: egohygiene/mindgarden#94
    url: https://github.com/egohygiene/mindgarden/pull/94
review:
  status: partial
  reviewed_at: '2026-11-06T22:18:36Z'
  reviewed_by: codex
  evidence:
  - command: .venv/bin/python -m unittest tests.test_release_preparation tests.test_package -q
    outcome: passed
    observed_at: '2026-11-06T22:18:36Z'
    notes: 13 passed in 0.268 seconds.
  - command: .venv/bin/python scripts/release.py bootstrap; .venv/bin/python scripts/release.py plan --release-version
      v0.1.0
    outcome: passed
    observed_at: '2026-11-06T22:18:36Z'
    notes: Exact owner revisions fetched/qualified; policy remains proposed; no publication performed.
  - command: .venv/bin/python scripts/release.py prepare --release-version v0.1.0 --output-directory .cache/release-candidate-first
    outcome: passed
    observed_at: '2026-11-06T22:18:36Z'
    notes: Two independent builds match; Relay profile passes; report preserves schema/owner/PyPI gates.
  - command: .venv/bin/python scripts/release.py verify --release-version v0.1.0 --output-directory .cache/release-candidate-first
    outcome: passed
    observed_at: '2026-11-06T22:18:36Z'
    notes: 'Negative check: exits 2 with RELEASE_UPSTREAM_SCHEMA_PARITY; publication remains impossible.'
  - command: .venv/bin/python -m unittest discover --start-directory tests --verbose; .cache/python313/bin/python
      -m unittest discover --start-directory tests --verbose
    outcome: passed
    observed_at: '2026-11-06T22:18:36Z'
    notes: 315 passed, no skips, each; 224.594/207.984 seconds.
  - command: Installed candidate CLI/version/v0 validate/publication and provider_switch_demo.py under -I
    outcome: passed
    observed_at: '2026-11-06T22:18:36Z'
    notes: Source-bound candidate wheel preserves compatibility and the exact provider golden.
  environment_limitations:
  - Relay Python package JSON Schema rejects the root authority path accepted by its reference validator; strict
    handoff remains blocked.
  - 'EgoLint pinned inputs qualify; native Python consumer conformance and broader #29 acceptance are not inferred.'
  - Protected OIDC, signing, approved private pilot and real Empathy/released-version verification remain external;
    no 1.0 publication.
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

The maintainer authorized #51, #27, #20 and conditional #19 after the prior storage batch. Preserve the Python engine and v0, source/review/publication boundaries and synthetic-only public fixtures. No proposed ADR or owner policy is self-ratified.

## Resume protocol

Read git status, live issues/PRs, README, AI_CONSTITUTION, ROADMAP, the coverage ledger, docs/release-checkpoints.md and the active checkpoint evidence. Use current implementation and pinned owner contracts; do not repeat merged checkpoints or activate deferred #86–#91.

## Current objective and success conditions

Prepare reproducible Python release evidence through pinned owner contracts without publishing or claiming full 1.0 acceptance. Keep pyproject.toml as the sole version authority and derive runtime/provenance versions. Build source-bound artifacts twice, verify exact hashes and preserve external policy/schema/signing/PyPI gates. Leave a small draft over #94, then advance the synthetic consumer/pilot handoff and conditional acceptance checks.

## State snapshot

Draft #95 source a3cbac93d2a68e99e7955ddb18302e0358f53247 is stacked over #94 (62cbead), over #93. Main remains d5edb13. Later checkpoint edits are documentation only. All 44 issues remain open.

## Completed and material changes

Aether/Hygiene declaration, changelog, agent release pointer, Taskfile handoffs and pinned manual Relay flow are added. Runtime/provenance derive the PEP 621 version. The local builder uses immutable git archive input, separate duplicate builds, normalized archives, exact checksums, SPDX/package/provenance/signature-state records, and strict verification. PyPI/signing remain unavailable. Relay reference validator/schema disagree about root pyproject.toml; the strict handoff retains that blocker.

## Validation and review evidence

All 315 tests pass, no skips, on Python 3.12.14/3.13.5 (224.594/207.984 s). Duplicate builds match; Relay reference artifact checks pass. Strict verification returns code 2 for the exact root-authority schema mismatch. Fresh distribution tests, clean installed CLI/v0 public projection and provider recovery golden pass. No publication was attempted.

## Blockers, risks, unknowns, and deferred work

An approved private archive/workspace, real Empathy #65 acceptance, compatible Aether #51/Relay #40 evidence and protected PyPI OIDC setup remain external gates. Hygiene release policy/ADR are still proposed despite closed delivery issues. EgoLint #29 remains partial. Native Windows/confidential/provider/real consumer gaps persist. No tag/package/site is published by local or PR checks.

## Next dependency-ready work

Implement #20 synthetic archive→review/routing→public projection and pinned Empathy consumer evidence on a branch over draft #95. Prepare a private pilot with explicit input/workspace/classification; do not run real data until the pending user input arrives. Then deliver conditional #19 pre/postpublication acceptance checks.

## Parallel changes and reconciliation

Draft stack is #93 → #94 → the current #27 checkpoint. Native support is only a checkout dependency. Preparation is independent of the full private pilot, while #19 acceptance and postpublication checks remain separate. Preserve the combined checkout and leave new drafts for review.

## Privacy and redaction

Only public metadata and authored synthetic fixtures are committed. Real Garden, business, music, credentials, private archive contents, private locations and personal circumstances stay outside this public repository. Source instructions remain untrusted evidence. No private consumer is discovered or modified.

## Handoff update protocol

After each checkpoint record branch/PR/full functional source, exact commands/results, blocked acceptance and one next action. Validate pinned owners, 12 headings, size limits, relative links and all 44 coverage rows. Distinguish draft, tested, reviewed, merged and accepted; keep publication receipts separate from local artifact conformance.

## Compaction and supersession

Keep under 16384 bytes/240 lines. This supersedes the prior native-registry next-action handoff. Durable native/storage merge evidence remains linked. The release checkpoint ledger owns this batch's stack and acceptance; deferred #86–#91 remain deferred.
