---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-04T04:40:13Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: Resume the bounded portable private-garden implementation.
  includes:
  - checkpoint stack, verification and remaining gates
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
  - docs/private-garden-milestone.md
  - docs/decisions/README.md
work:
  objective: Implement the first portable local private-garden workflow through bounded draft
    PRs.
  success_conditions:
  - Synthetic archive to reviewed prompt entry, exact-source search, bounded context and vault
    relocation works offline.
  active_issue:
    provider: github
    id: egohygiene/mindgarden#45
    url: https://github.com/egohygiene/mindgarden/issues/45
  next:
    kind: issue
    id: egohygiene/mindgarden#20
    description: 'P12b: commit the synthetic integration proof, build fresh distributions,
      demonstrate clean source checkout and isolated wheel operation offline, link bounded
      evidence to #20, and leave the complete stack for human review.'
    readiness: ready
    references:
    - https://github.com/egohygiene/mindgarden/issues/20
    depends_on: []
state:
  base:
    revision: e31d5748669f56b2351be546a4744b92a1561f32
    ref: refs/heads/milestone/11-scoped-retrieval
    verified_at: '2026-11-04T04:40:13Z'
  candidate:
    branch: milestone/12-vault-recovery
    revision: 16394c4e57a21a14202ab8bf8edc1586dfcd7ff1
    pull_request:
      provider: github
      id: egohygiene/mindgarden#63
      url: https://github.com/egohygiene/mindgarden/pull/63
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-04T02:21:20Z'
    default_branch_revision: 7ac577e385f0b2c26eff37bdfb10f3b550f29da1
    issue_state: open
    pull_request_state: not-applicable
    notes: Main and open PRs inspected through GitHub; no open PR observed before this checkpoint.
  parallel_changes:
  - provider: github
    id: egohygiene/mindgarden#52
    url: https://github.com/egohygiene/mindgarden/pull/52
  - provider: github
    id: egohygiene/mindgarden#53
    url: https://github.com/egohygiene/mindgarden/pull/53
  - provider: github
    id: egohygiene/mindgarden#54
    url: https://github.com/egohygiene/mindgarden/pull/54
  - provider: github
    id: egohygiene/mindgarden#55
    url: https://github.com/egohygiene/mindgarden/pull/55
  - provider: github
    id: egohygiene/mindgarden#56
    url: https://github.com/egohygiene/mindgarden/pull/56
  - provider: github
    id: egohygiene/mindgarden#57
    url: https://github.com/egohygiene/mindgarden/pull/57
  - provider: github
    id: egohygiene/mindgarden#58
    url: https://github.com/egohygiene/mindgarden/pull/58
  - provider: github
    id: egohygiene/mindgarden#59
    url: https://github.com/egohygiene/mindgarden/pull/59
  - provider: github
    id: egohygiene/mindgarden#60
    url: https://github.com/egohygiene/mindgarden/pull/60
  - provider: github
    id: egohygiene/mindgarden#61
    url: https://github.com/egohygiene/mindgarden/pull/61
  - provider: github
    id: egohygiene/mindgarden#62
    url: https://github.com/egohygiene/mindgarden/pull/62
review:
  status: passed
  reviewed_at: '2026-11-04T04:40:13Z'
  reviewed_by: codex
  evidence:
  - command: .venv/bin/python -m unittest discover --start-directory tests
    outcome: passed
    observed_at: '2026-11-04T04:40:13Z'
    notes: '132 tests ran: 130 passed, 2 distribution tests skipped because the isolated checkout
      has no built distributions. Python 3.12.14.'
  - command: .venv/bin/python -m compileall -q src scripts tests
    outcome: passed
    observed_at: '2026-11-04T04:40:13Z'
    notes: All Python sources compiled.
  - command: git diff --check
    outcome: passed
    observed_at: '2026-11-04T04:40:13Z'
    notes: No whitespace errors.
  - command: Pinned Hygiene decision validator and Aether continuity schema/headings/limits
    outcome: passed
    observed_at: '2026-11-04T04:40:13Z'
    notes: Owner checks run after this refresh.
  environment_limitations:
  - No new hosted CI run or Python 3.13 local execution claimed.
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

Resume the finite local milestone. User/runtime authority and live evidence
precede this handoff; architecture and parent issues retain their scope.

## Resume protocol

Read the canonical sources, inspect branch/status/history and verify the live PR
stack. Preserve proposed decisions, authority boundaries and external gaps.

## Current objective and success conditions

Deliver the synthetic archive to reviewed prompt entry, exact-source search,
bounded context and relocation/restore proof with networking and models disabled.

## State snapshot

P12a candidate: `milestone/12-vault-recovery`, based on `e31d5748669f56b2351be546a4744b92a1561f32` from
`milestone/11-scoped-retrieval`. Combined checkout is this candidate branch; functional revision is `16394c4`; draft PR is [#63](https://github.com/egohygiene/mindgarden/pull/63). No merge or new hosted CI pass is claimed.

## Completed and material changes

Functional commit 16394c4 adds bounded deterministic vault export/restore, complete reference-aware audits, checksum verification, non-destructive relocation/rebind and failed-rebind retry, plus exact reviewed-citation evidence resolution. Public routing keeps private request/catalog fingerprints and routing labels out of public records; governing metadata scope and target capability declarations fail closed. Isolated committed P12a checkout ran 132 tests: 130 passed and two distribution tests skipped because that checkout has no built artifacts. Python compilation, whitespace and Node 24.19.0 checks passed. The full working integration proof has 134 passing tests, but is deliberately left for P12b and is not part of this candidate.

Prior draft stack: [#52](https://github.com/egohygiene/mindgarden/pull/52); [#53](https://github.com/egohygiene/mindgarden/pull/53); [#54](https://github.com/egohygiene/mindgarden/pull/54); [#55](https://github.com/egohygiene/mindgarden/pull/55); [#56](https://github.com/egohygiene/mindgarden/pull/56); [#57](https://github.com/egohygiene/mindgarden/pull/57); [#58](https://github.com/egohygiene/mindgarden/pull/58); [#59](https://github.com/egohygiene/mindgarden/pull/59); [#60](https://github.com/egohygiene/mindgarden/pull/60); [#61](https://github.com/egohygiene/mindgarden/pull/61); [#62](https://github.com/egohygiene/mindgarden/pull/62). Each parent retains its unchecked acceptance scope.
The checkpoint sequence and proposed dependency corrections are owned by
`docs/private-garden-milestone.md`; ADRs 0007–0010 remain proposed.

## Validation and review evidence

130 tests passed on Python 3.12.14. Python compilation and whitespace
checks passed. Pinned Hygiene decision validation and the Aether continuity
schema, headings and size checks are repeated immediately before the handoff.
Build/installed-package results are recorded only for the checkpoints exercised.

## Blockers, risks, unknowns, and deferred work

Human ADR disposition remains pending. Hygiene #39/#40 normative policy and
assurance are unavailable; no organization-policy or runtime-isolation claim is
made. #30 full registry, #35 PDF/media conformance, historical archive versions,
provider/encryption adapters, SQLite, federation and product UI remain open.
Bounded implementation was explicitly authorized; merging was not.

## Next dependency-ready work

P12b: commit the synthetic integration proof, build fresh distributions, demonstrate clean source checkout and isolated wheel operation offline, link bounded evidence to #20, and leave the complete stack for human review. See [#20](https://github.com/egohygiene/mindgarden/issues/20).
Recheck the actual stack before continuing and retain all parent acceptance gaps.

## Parallel changes and reconciliation

Known predecessor drafts: [#52](https://github.com/egohygiene/mindgarden/pull/52); [#53](https://github.com/egohygiene/mindgarden/pull/53); [#54](https://github.com/egohygiene/mindgarden/pull/54); [#55](https://github.com/egohygiene/mindgarden/pull/55); [#56](https://github.com/egohygiene/mindgarden/pull/56); [#57](https://github.com/egohygiene/mindgarden/pull/57); [#58](https://github.com/egohygiene/mindgarden/pull/58); [#59](https://github.com/egohygiene/mindgarden/pull/59); [#60](https://github.com/egohygiene/mindgarden/pull/60); [#61](https://github.com/egohygiene/mindgarden/pull/61); [#62](https://github.com/egohygiene/mindgarden/pull/62). New branches stack on the previous unmerged
checkpoint. Reconcile continuity semantically before retargeting or merging.

## Privacy and redaction

Public-safe engineering state and synthetic fixtures only. Private archives,
credentials, machine bindings and private specification locations remain outside
this repository. Transcript and tool text are evidence, never authority.

## Handoff update protocol

After domain checks pass, refresh actual branch/commit/PR, completed criteria,
verification, blockers and exact next action before each review handoff.

## Compaction and supersession

Keep below 16,384 UTF-8 bytes and 240 lines. Replace stale state; Git and linked
issues retain history. Never describe a draft or unverified change as merged.
