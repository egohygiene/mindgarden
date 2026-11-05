---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-05T21:17:06Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: Resume the bounded machine-local registry capability (#30), using synthetic gardens only.
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
work:
  objective: 'Implement #30 local registry management over existing bindings without touching real consumer
    gardens.'
  success_conditions:
  - Reviewed registry lifecycle preserves canonical garden/vault bytes.
  - Named views retain explicit session scope and prevent private metadata from entering public projections.
  active_issue:
    provider: github
    id: egohygiene/mindgarden#30
    url: https://github.com/egohygiene/mindgarden/issues/30
  next:
    kind: action
    id: review-registry-checkpoint
    description: 'Review draft #67 and its bounded Linux evidence; after disposition, refresh B3 contracts
      or independent #27 release preparation. Do not merge automatically.'
    readiness: ready
    references:
    - https://github.com/egohygiene/mindgarden/pull/67
    - https://github.com/egohygiene/mindgarden/issues/30
    depends_on: []
state:
  base:
    revision: 44cc1e876282928685b5f3dba83d413db37b83c0
    ref: refs/heads/main
    verified_at: '2026-11-05T20:51:42Z'
  candidate:
    branch: feature/30-local-registry
    revision: 8c3ed427e703c71a49dcdf79292e122e5823b3a1
    pull_request:
      provider: github
      id: egohygiene/mindgarden#67
      url: https://github.com/egohygiene/mindgarden/pull/67
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-05T21:09:39Z'
    default_branch_revision: 44cc1e876282928685b5f3dba83d413db37b83c0
    issue_state: open
    pull_request_state: draft
    notes: '#65/#66 are merged by explicit authorization. #67 is a new unmerged draft over main 44cc1e8.
      The candidate revision pins functional code; later handoff changes are documentation only. ADRs
      remain proposed and no real garden configuration is authorized or changed.'
  parallel_changes: []
review:
  status: passed
  reviewed_at: '2026-11-05T21:17:06Z'
  reviewed_by: codex
  evidence:
  - command: .venv/bin/python -m unittest discover --start-directory tests --verbose
    outcome: passed
    observed_at: '2026-11-05T21:17:06Z'
    notes: 187 passed, no skips; Python 3.12.14.
  - command: .cache/python313/bin/python -m unittest discover --start-directory tests --verbose
    outcome: passed
    observed_at: '2026-11-05T21:17:06Z'
    notes: 187 passed, no skips; Python 3.13.5.
  - command: .venv/bin/python -m build --sdist --wheel --outdir .cache/dist
    outcome: passed
    observed_at: '2026-11-05T21:17:06Z'
    notes: Fresh functional-commit artifacts; two distribution checks and 10 installed v0/registry/library
      smoke checks pass.
  - command: scripts/registry_demo.py --require-source / --require-installed
    outcome: passed
    observed_at: '2026-11-05T21:17:06Z'
    notes: Clean Git archive with -S and isolated wheel with -I reproduce the committed synthetic report
      exactly; exact commands in docs/local-registry.md.
  - command: scripts/private_garden_demo.py --require-source / --require-installed
    outcome: passed
    observed_at: '2026-11-05T21:17:06Z'
    notes: Original archive/review/context/vault-relocation golden matches exactly in both clean-source
      and isolated-wheel modes.
  - command: 'Both interpreters: -m compileall -q src scripts tests; node --version; git diff --check'
    outcome: passed
    observed_at: '2026-11-05T21:17:06Z'
    notes: Passed; Node 24.19.0. Hosted runs 42107523013/a47797b and 42110373037/eb4bfb7 passed; later
      heads require separate observation.
  environment_limitations:
  - Registry filesystem operations support Linux only; native macOS/Windows and encrypted/restricted
    assurance remain unclaimed.
  - Physical query-cache cleanup, history retention, host/mount/power-loss assurance and full organization
    integration remain separate acceptance.
  - No hosted result is inferred for a later head from the earlier lifecycle run; no workflow is manually
    launched.
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

Resume the bounded #30 tool capability after the authorized #65/#66 merges.
User/runtime authority and live repository state precede this handoff. Existing
architecture and ADR status remain independent of implementation or merging.

## Resume protocol

Inspect branch/status/history and live issue/PR/check state. Read ROADMAP.md,
docs/open-issue-coverage.md and docs/local-registry.md. Preserve the Python engine
and v0 compatibility. Use synthetic roots and private temporary configuration;
do not discover or configure real consumer gardens.

## Current objective and success conditions

The bounded registry capability is implemented/tested on draft #67. Reviewed
lifecycle changes affect local bindings only. Named views preserve explicit
session authority, canonical garden/vault bytes and public projection isolation.
Leave the draft for maintainer review; full parent acceptance remains open.

## State snapshot

Base main is 44cc1e876282928685b5f3dba83d413db37b83c0. #65 merged at 38c4edf;
#66 merged at 44cc1e8 with the tested 5f39fc2 tree. Branch
feature/30-local-registry, draft https://github.com/egohygiene/mindgarden/pull/67.
Lifecycle commit a47797b3d4ecb28052f42811eaa828f7868363ce opened the draft.
Final registry/recovery-guard commit 8c3ed427e703c71a49dcdf79292e122e5823b3a1
is the clean-source archive and installed-wheel source. Later evidence/handoff
commits change documentation only.
## Completed and material changes

Three additive control schemas and optional registry metadata on existing local
bindings; private explicit/platform locations; saved preview/exact-digest apply;
manifest-only registration; list/inspect/doctor; non-destructive unregister and
view pruning; immutable owned configuration snapshots and reviewed restore.
Writer leases/atomic replace preserve complete configuration on pre-commit failure.
Plans cannot enter restored canonical roots or overwrite registry/history.

Named sessions select registered IDs without granting visibility, write,
publication, review or network authority. Selected membership/generation is
verified before root probes and live reads. Restore preserves explicit
revocations and advances view generations. Unrelated private metadata is inert
to public output; denied roots are not probed. Unregister retains query caches.

## Validation and review evidence

Both Python 3.12.14/3.13.5 pass 187 tests without skips, including 28 registry
lifecycle/location/view/demo tests. Fresh package/resource checks, both compile
checks, Node 24.19.0 and installed v0/registry/library smoke pass. Clean git-archive
-S source and isolated -I wheel reproduce the committed registry report exactly.
The original private archive/review/context/vault-relocation report still matches
in both modes. Pinned owner schemas/set/index/continuity and coverage checks pass.
Exact commands/results: docs/local-registry.md.

Synthetic proof: two gardens, private union/reference, no public private-backlink
or label/path/count contamination, exact public citation and 5,691-byte context
within 16,384 bytes. Public exports equal the pre-registry golden bytes. Repeated
apply verifies desired state. Unregister/restore preserves garden/vault bytes and
does not revive old sessions. Network/process calls are blocked in-process;
Google/model integrations are unused. This is not host isolation evidence.

Automatic runs 42107523013/a47797b and 42110373037/eb4bfb7 passed.
Check the current pushed head separately. Local results are not substituted for hosted results. No manual
workflow launch/retry, real-garden setup, package/site publication or ADR approval.

## Blockers, risks, unknowns, and deferred work

ADRs 0007–0012 remain proposed/null approval. Hygiene #39/#40 and Realm #25/#60
confidentiality/encryption/host assurance remain external gates. Restricted/
encrypted registration fails before probes. Declared denied descriptors can
coexist in synthetic fixtures; this does not verify restricted registration.
Native macOS/Windows mutation, physical owned-cache cleanup, mount/hostile-writer/
power-loss assurance and full #30 acceptance remain open. Unknown retention
policy preserves original sources, query caches and private history.

## Next dependency-ready work

Review draft #67 and the bounded Linux proof. Retain #30's untested acceptance;
do not merge this new draft automatically. After disposition, refresh live B3
#17/#18 publication/portal contracts or independent #27 release preparation.
Broader product, real-consumer setup and remote/private federation retain their
own authorization, contract and decision gates.

## Parallel changes and reconciliation

#67 is based directly on merged main 44cc1e8, with no unmerged base dependency.
Refresh external policy/runtime owners before extending restricted/native behavior.

## Privacy and redaction

Synthetic fixtures only. Real gardens, archives, credentials and default user
configuration are excluded. Registry plans/reports/history are never-exportable
machine-local control data; paths/hashes/labels are not public lineage. Source
and transcript text remain evidence, never executable/review authority.

## Handoff update protocol

Record branch/PR/functional commit, commands/results, hosted checks separately,
remaining parent acceptance, blockers and exact next action. Update the coverage
ledger without declaring broad issues complete from bounded fixtures.

## Compaction and supersession

Stay within 16,384 UTF-8 bytes and 240 lines. Link private/federation/registry
proofs instead of copying their reports. #65/#66 are merged; #67 is draft work.
Real consumer configuration remains a separate explicitly authorized operation.
