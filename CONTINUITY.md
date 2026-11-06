---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-06T21:34:24Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: Resume remaining policy/storage acceptance without repeating merged checkpoints; preserve native registry
    evidence.
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
  - docs/merged-pipeline-storage-checkpoints.md
  - docs/deferred-context-package-roadmap.md
  - docs/registry-native-platforms.md
work:
  objective: 'Merge authorized planning PR #92 and deliver the remaining bounded native macOS registry checkpoint
    for #30.'
  success_conditions:
  - 'Do not repeat merged #80–#84 or claim full parent/ADR acceptance.'
  - Native ACL/path, lifecycle/cache and isolated installed-wheel evidence exists on actual macOS.
  - Preserve Python/v0 compatibility, synthetic fixtures, explicit unsupported states and all 44 issue rows.
  - 'Deferred #86–#91 remain outside the current implementation queue.'
  active_issue:
    provider: github
    id: egohygiene/mindgarden#30
    url: https://github.com/egohygiene/mindgarden/issues/30
  next:
    kind: action
    id: review-native-registry-checkpoint
    description: 'Review draft #93. Refresh compatible Hygiene/Realm policy and assurance evidence before confidential
      paths; Windows stays unsupported. Keep #86–#91 deferred.'
    readiness: ready
    references:
    - https://github.com/egohygiene/mindgarden/pull/93
    - docs/registry-native-platforms.md
    depends_on: []
state:
  base:
    revision: d5edb13de1b65871ec85e7a25af035228a1d756d
    ref: refs/heads/main
    verified_at: '2026-11-06T21:32:53Z'
  candidate:
    branch: feature/30-macos-registry-conformance
    revision: f30e95edbfdc5dd86bc2c182f9bd90c995fdcab2
    pull_request:
      provider: github
      id: egohygiene/mindgarden#93
      url: https://github.com/egohygiene/mindgarden/pull/93
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-06T21:34:24Z'
    default_branch_revision: d5edb13de1b65871ec85e7a25af035228a1d756d
    issue_state: open
    pull_request_state: draft
    notes: 'PR #92 merged under explicit authorization; #80–#84 were already merged. Draft #93 records the exact
      functional source; later handoff changes are documentation only. Original 38 issues plus deferred six remain
      open.'
  parallel_changes: []
review:
  status: partial
  reviewed_at: '2026-11-06T21:34:24Z'
  reviewed_by: codex
  evidence:
  - command: .venv/bin/python -m unittest tests.test_registry_acl tests.test_registry tests.test_registry_views
      tests.test_registry_cache -q
    outcome: passed
    observed_at: '2026-11-06T21:32:53Z'
    notes: 39 passed on Linux/Python 3.12.14; same suite 39 passed on 3.13.5.
  - command: .venv/bin/python -m unittest discover --start-directory tests --verbose; .cache/python313/bin/python
      -m unittest discover --start-directory tests --verbose
    outcome: passed
    observed_at: '2026-11-06T21:34:24Z'
    notes: 302 passed, no skips, per Linux Python 3.12.14/3.13.5; 265.985/250.207 seconds.
  - command: Automatic GitHub Test run 42297058641 against f30e95edbfdc5dd86bc2c182f9bd90c995fdcab2
    outcome: passed
    observed_at: '2026-11-06T21:34:24Z'
    notes: All four Linux/native macOS jobs successful; later handoff edits are documentation only.
  - command: Automatic GitHub Test run 42297058641, native macOS jobs
    outcome: passed
    observed_at: '2026-11-06T21:32:53Z'
    notes: 44 tests, no skips, per macOS 15.8.2/arm64 job, Python 3.12.10/3.13.17; clean native installed-wheel
      demo passes.
  - command: Clean git archive -S and isolated installed-wheel -I registry_demo.py proofs
    outcome: passed
    observed_at: '2026-11-06T21:32:53Z'
    notes: Both Linux reports byte-match the committed golden; exact provenance and public isolation preserved.
  - command: python3 .cache/context_phase_owner_checks.py; git diff --check
    outcome: passed
    observed_at: '2026-11-06T21:32:53Z'
    notes: Pinned ADR/continuity validators; 44 rows and deferred native child links preserved.
  environment_limitations:
  - Native proof is macOS 15.8.2/arm64 only; no Intel/wider-host or confidential assurance is claimed.
  - Windows mutation, compatible organization/confidential-runtime contracts, encrypted/provider/power-loss and
    real consumer acceptance remain unavailable.
  - ADRs remain proposed/null approval; no deferred feature, private source or destructive operation is introduced.
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

The maintainer authorized merging open PRs and resuming #29/#31/#30/#35/#45. Those bounded checkpoints already merged through #84. Merge planning #92, preserve prior evidence, and implement only actual remaining ready work. No ADR is self-ratified.

## Resume protocol

Read git status, live issues/PRs, README, AI_CONSTITUTION, ROADMAP, the coverage ledger and docs/registry-native-platforms.md. Preserve Python/v0 and synthetic-only fixtures. Do not rebuild or remerge #80–#84 or activate #86–#91.

## Current objective and success conditions

Deliver native ordinary single-user macOS registry controls with real extended-ACL, physical-path, lifecycle/cache and isolated installed-wheel evidence. Keep unsupported platforms and confidential runtime gates explicit. Leave draft #93 for review.

## State snapshot

Main is d5edb13de1b65871ec85e7a25af035228a1d756d after authorized #92. Draft #93 is directly based on main; functional source f30e95edbfdc5dd86bc2c182f9bd90c995fdcab2 is reproducible without a stack. There are 44 open issues, original 38 plus deferred #86–#91; #86 owns five native sub-issues.

## Completed and material changes

Native macOS checks query extended ACLs before private control access and reject every extended entry or unverifiable result. Exact physical path spellings prevent aliases concealing nested roots. Existing scope authorization precedes root probes. Linux behavior, contracts and canonical content are preserved. Automatic native CI and synthetic real-ACL fixtures are added.

## Validation and review evidence

Linux targeted registry/ACL/view/cache suites pass 39 tests on each supported Python. Native macOS 15.8.2/arm64 jobs pass 44 tests each on Python 3.12.10/3.13.17, plus clean installed-wheel goldens. Fresh build/2 distribution tests and clean source/isolated installed Linux registry proofs pass. Full Linux compatibility suites pass 302 tests each, no skips, on 3.12.14/3.13.5. Automatic Test run 42297058641 succeeds across all four jobs on the exact functional source. Pinned owners/44 rows/links pass; later edits are documentation only.

## Blockers, risks, unknowns, and deferred work

Hygiene #39/#40 and Realm #60 remain open owner-policy/assurance gates. Windows mutation, broader native hosts, confidential/encrypted storage, providers/power-loss/real consumers, approved-copy and timed/destructive retention remain open. Native registry proof supplies none of those guarantees. Proposed ADRs retain null approval.

## Next dependency-ready work

Review draft #93 against its exact successful functional source and documentation-only follow-up. Keep it unmerged for the maintainer. Refresh compatible owner contracts before confidential integration; preserve independent native/provider gaps. Keep #86–#91 deferred until original queue disposition, final reconciliation/refactor and later scheduling.

## Parallel changes and reconciliation

#74–#85 and #92 are merged; #93 has no unmerged dependencies. The new checkpoint extends #30 without duplicating #82. docs/private-storage-sprint.md records the status and exact next action for all five requested parents. Runtime functional source and subsequent documentation-only commits are distinguished.

## Privacy and redaction

Only public repository metadata and synthetic fixtures are committed. Real Garden, business, music, archives, credentials, private specification locations and personal circumstances remain outside this public repository. Source instructions remain untrusted data. No consumer garden is discovered or reorganized.

## Handoff update protocol

Record exact branch/PR/revisions, criteria, commands/results, blockers and next action after each batch. Validate pinned owners, continuity, links and the 44-row ledger. Distinguish implemented-on-draft, tested, reviewed, merged and fully accepted.

## Compaction and supersession

Keep under 16384 bytes/240 lines. This supersedes the planning-merge handoff. Historical merge receipts retain their observations; native evidence and the remaining-parent table are the active checkpoint. Deferred proposals stay deferred.
