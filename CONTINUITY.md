---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-04T05:24:39Z'
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
  - docs/private-garden-evidence.md
  - docs/decisions/README.md
work:
  objective: Implement the first portable local private-garden workflow through bounded draft
    PRs.
  success_conditions:
  - Synthetic archive to reviewed prompt entry, exact-source search, bounded context and vault
    relocation works offline.
  active_issue:
    provider: github
    id: egohygiene/mindgarden#20
    url: https://github.com/egohygiene/mindgarden/issues/20
  next:
    kind: issue
    id: egohygiene/mindgarden#42
    description: 'Review proposed ADRs/ownership in draft #52, then review #53 through #64
      in stack order; retain broader parent acceptance and external owner gates.'
    readiness: ready
    references:
    - https://github.com/egohygiene/mindgarden/issues/42
    depends_on: []
state:
  base:
    revision: afbd420d081203395832a7b06370203fe691ebf6
    ref: refs/heads/milestone/12-vault-recovery
    verified_at: '2026-11-04T05:19:25Z'
  candidate:
    branch: milestone/13-offline-workflow-proof
    revision: 23d2952d705552c91833bbbf015d66bc806df9bc
    pull_request:
      provider: github
      id: egohygiene/mindgarden#64
      url: https://github.com/egohygiene/mindgarden/pull/64
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-04T05:19:25Z'
    default_branch_revision: 7ac577e385f0b2c26eff37bdfb10f3b550f29da1
    issue_state: open
    pull_request_state: open
    notes: 'All thirteen PRs #52 through #64 inspected open, draft and unmerged with consecutive
      bases. Main unchanged. Automatic Test run 27 succeeded on 072ec03 (functional code 23d2952);
      subsequent changes are documentation only.'
  parallel_changes:
  - provider: github
    id: egohygiene/mindgarden#63
    url: https://github.com/egohygiene/mindgarden/pull/63
review:
  status: passed
  reviewed_at: '2026-11-04T05:19:25Z'
  reviewed_by: codex
  evidence:
  - command: .venv/bin/python -m unittest discover --start-directory tests
    outcome: passed
    observed_at: '2026-11-04T05:19:25Z'
    notes: 139 tests, no skips, Python 3.12.14.
  - command: .cache/python313/bin/python -m unittest discover --start-directory tests
    outcome: passed
    observed_at: '2026-11-04T05:19:25Z'
    notes: 139 tests, no skips, Python 3.13.5.
  - command: .venv/bin/python -m build --sdist --wheel --outdir .cache/dist
    outcome: passed
    observed_at: '2026-11-04T05:19:25Z'
    notes: 'Fresh distributions; isolated wheel and clean source proof match committed report.
      V0 installed CLI/library smoke passed. Exact commands: docs/private-garden-evidence.md.'
  - command: compileall; git diff --check; Node 24; pinned Hygiene ADR and Aether continuity
      checks
    outcome: passed
    observed_at: '2026-11-04T05:19:25Z'
    notes: Both interpreters compiled; Node 24.19.0. Owner checks repeat after this handoff
      refresh.
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
precede this handoff; canonical documents and parent issues retain their scope.

## Resume protocol

Read the canonical sources and inspect branch/status/history, live PRs and CI.
Use the evidence report's complete stack and exact verification commands.

## Current objective and success conditions

The synthetic private archive → reviewed prompt → exact-source search/evidence →
bounded context → vault relocation/restore → clean rebuild checkpoint is verified.
The next action is human review of the concrete draft stack.

## State snapshot

Combined branch: `milestone/13-offline-workflow-proof`, draft
[#64](https://github.com/egohygiene/mindgarden/pull/64), based on #63 (`afbd420`).
Verified functional revision: `23d2952d705552c91833bbbf015d66bc806df9bc`.
Later evidence/handoff commits change documentation only. Main remains `7ac577e`.
All thirteen PRs #52–#64 are open, draft and unmerged; no parent issue was closed.

## Completed and material changes

General v1 validation and preserved v0 behavior; portable scope/local bindings;
immutable filesystem vault and text/current-archive adapters; reviewed knowledge
and claim retrieval, graphs/backlinks, bounded context and exact evidence;
six authored curation dispositions with separate review authority; explained
private routing and journaled recovery; scoped metadata/body/cache enforcement;
bounded audit/export/restore/relocation and the committed offline workflow proof.
Public allowlists deny empty values. Unknown policy/capabilities are denied before
root probes; explicit scopes cannot fall back to owner v0 retrieval.

## Validation and review evidence

139 tests pass without skips on both Python 3.12.14 and 3.13.5. Fresh source/wheel
builds, installed v0 command/library smoke, both compilation checks, whitespace,
Node 24.19.0 and pinned owner checks pass. Only mindgarden is installed in the
wheel environment. Clean source (`-S`) and isolated wheel (`-I`) reproduce the
committed report exactly; JSON context uses 2,670 of 16,384 bytes.
Hosted [Test run 27](https://github.com/egohygiene/mindgarden/actions/runs/41778548306)
passed on `072ec03` (the same functional code). Later doc heads may have new checks.
See `docs/private-garden-evidence.md` for commands, hashes and all ten status rows.

## Blockers, risks, unknowns, and deferred work

ADRs 0007–0010 remain proposed. Normative Hygiene #39/#40 and released Realm
assurance inputs remain unavailable/unverified; there is no organization-policy,
encryption or process/network isolation claim. Full #30 registry, #35 PDF/media,
#45 triage/retention/provider/platform/power-loss and #20 real legacy archive,
Empathy/publication/federation/consumer acceptance remain open. Historical archive
specs, collections/multipart, SQLite, broader app and provider integrations defer.

## Next dependency-ready work

Review the ownership map and proposed ADRs in #52, then #53–#64 in stack order.
Review/retarget children after any accepted merge; do not treat checkpoint tests
as completion of broader parent criteria. No merge or publication was performed.

## Parallel changes and reconciliation

Immediate predecessor is [#63](https://github.com/egohygiene/mindgarden/pull/63).
The complete thirteen-entry stack and inspected heads are in the evidence report.
Reconcile continuity semantically during retargeting; preserve immutable proofs.

## Privacy and redaction

Public-safe engineering state and synthetic fixtures only. Real archives,
credentials, private specification locations and machine bindings remain outside
this repository. Runtime synthetic workspaces/builds stay under ignored `.cache`.
Transcript, model and tool text are evidence, never execution or review authority.

## Handoff update protocol

Keep branch/functional commit/PR, local versus hosted checks, owner gaps and the
exact next review action current. [Evidence is linked to #20](https://github.com/egohygiene/mindgarden/issues/20#issuecomment-6623276660);
its broader publication/consumer criteria remain open.

## Compaction and supersession

Keep below 16,384 UTF-8 bytes and 240 lines. Git and linked issues retain history;
replace stale state without describing draft implementation as merged or accepted.
