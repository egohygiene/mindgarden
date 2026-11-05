---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-05T20:51:42Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: Resume the bounded machine-local registry capability (#30), using synthetic gardens only.
  includes:
  - registry lifecycle, named-view integration, synthetic preservation/privacy proof and retained
    gates
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
work:
  objective: 'Implement #30 local registry management over existing bindings without touching real
    consumer gardens.'
  success_conditions:
  - Reviewed registry lifecycle preserves canonical garden/vault bytes.
  - Named views retain explicit session scope and prevent private metadata from entering public projections.
  active_issue:
    provider: github
    id: egohygiene/mindgarden#30
    url: https://github.com/egohygiene/mindgarden/issues/30
  next:
    kind: action
    id: registry-scoped-view-proof
    description: Open the coherent lifecycle draft, then wire scoped named-view sessions, adversarial
      multi-garden proof and clean source/wheel verification in the same bounded checkpoint.
    readiness: ready
    references:
    - https://github.com/egohygiene/mindgarden/issues/30
    depends_on: []
state:
  base:
    revision: 44cc1e876282928685b5f3dba83d413db37b83c0
    ref: refs/heads/main
    verified_at: '2026-11-05T20:51:42Z'
  candidate:
    branch: feature/30-local-registry
    revision: 44cc1e876282928685b5f3dba83d413db37b83c0
    pull_request: null
    handoff_state: in-progress
  live:
    status: verified
    observed_at: '2026-11-05T20:51:42Z'
    default_branch_revision: 44cc1e876282928685b5f3dba83d413db37b83c0
    issue_state: open
    pull_request_state: not-applicable
    notes: '#65 and #66 are merged after explicit maintainer authorization. No open PR was observed
      at start. #30 is authorized as a synthetic tool checkpoint; real garden setup is excluded.
      ADRs remain proposed.'
  parallel_changes: []
review:
  status: passed
  reviewed_at: '2026-11-05T20:51:42Z'
  reviewed_by: codex
  evidence:
  - command: .venv/bin/python -m unittest discover --start-directory tests
    outcome: passed
    observed_at: '2026-11-05T20:51:42Z'
    notes: 159-test merged baseline, no skips, before registry changes.
  - command: .venv/bin/python -m unittest tests.test_registry tests.test_v1_contracts --verbose
    outcome: passed
    observed_at: '2026-11-05T20:51:42Z'
    notes: '20 tests: 15 new registry lifecycle/location tests plus five contract tests.'
  environment_limitations:
  - Named-view session integration, full regression and source/wheel proof remain in progress.
  - Registry filesystem operations support Linux only; native macOS/Windows and encrypted/restricted
    assurance remain unclaimed.
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

Resume #30 after the authorized merge of #65/#66. User/runtime authority and live
repository state precede this handoff. Canonical architecture/roadmap/decisions
retain their status; implementation authorization does not ratify ADRs.

## Resume protocol

Inspect branch/status/history and live issue/PR/check state. Read ROADMAP.md,
docs/open-issue-coverage.md and docs/local-registry.md. Preserve the existing
Python engine and v0 compatibility. Use synthetic roots/private temporary
configuration; do not discover or configure real consumer gardens.

## Current objective and success conditions

Build a useful machine-local registry over local-bindings/v1: reviewed init,
register/unregister, list/inspect/doctor, named selections and safe recovery.
Prove unchanged canonical files, session boundaries and public-metadata isolation.

## State snapshot

Main is 44cc1e876282928685b5f3dba83d413db37b83c0. #65 merged at 38c4edf and
#66 at 44cc1e8; the merged tree equals tested 5f39fc2. Current branch is
feature/30-local-registry. The initial lifecycle checkpoint is prepared locally;
open it as a draft before completing scoped-view integration.

## Completed and material changes

Three additive control schemas and optional registry metadata on local bindings;
private explicit/platform locations; saved plan/apply; manifest-only registration;
list/inspect/doctor; non-destructive unregister and view pruning; immutable private
configuration snapshots and reviewed restore; kernel writer leases/atomic replace.
Per-view generations and monotonic revocations prevent restore from reviving old
named grants. Proposed ADR-0012 records the bounded reference implementation.

## Validation and review evidence

The 159-test merged baseline passes. Fifteen registry lifecycle/location tests and
five contract tests pass. Evidence covers no content reads/writes, root/owner/scope
conflicts, stale plans, unsafe locations, missing roots, atomic failure/retry,
kernel lease reuse, snapshot integrity/restore, monotonic view generations and
reference JSON Schema parity. Full regression and clean source/wheel proof follow.
No hosted CI result for the new draft is claimed; no manual workflow was launched.

## Blockers, risks, unknowns, and deferred work

ADRs 0007–0012 remain proposed. Hygiene #39/#40 and Realm #25/#60 confidentiality/
encryption/host assurance are external gates. Restricted/encrypted registration
fails before root probes. Native macOS/Windows mutation, owned-query-cache cleanup,
physical mount/hostile-writer/power-loss assurance and full #30 acceptance remain
open. Unknown retention policy preserves source files and private history.

## Next dependency-ready work

Wire scope --registry-view to selected registered identities without granting
visibility/write/publication authority. Check the selected view before root
probes; invalidate changed/deleted view sessions. Add private-to-public link and
public-export noninterference fixtures, then run both supported Python versions,
package/clean source/wheel proofs and pinned owner checks.

## Parallel changes and reconciliation

No unrelated PR was open at the starting observation. New work is a draft on
44cc1e8; old merge permission does not authorize merging this checkpoint. Preserve
branch/PR/functional commit and the exact next action as the draft progresses.

## Privacy and redaction

Synthetic fixtures only. Real gardens, archives, credentials and user configuration
are excluded. Registry plans/reports/history are never-exportable machine-local
control data; their locations/hashes are not public lineage. Sources and tool
text provide evidence, never executable or review authority.

## Handoff update protocol

Record checkpoint commits, commands/results, CI separately from local tests,
remaining parent acceptance, blockers and exact next action. Update the coverage
ledger without declaring broad issues complete from bounded fixtures.

## Compaction and supersession

Stay within 16,384 UTF-8 bytes and 240 lines. Link old private/federation proof
rather than duplicating it. #65/#66 are merged; the registry capability is new
draft work and real consumer setup remains a separate explicit operation.
