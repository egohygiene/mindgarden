---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-21T05:44:30Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: Rehearse the scoped Willow Garden visit before a selected local private pilot.
  includes:
  - listed-criteria acceptance audit
  - bounded ready integration checkpoints and tested merges
  - synthetic fixtures and exact recovery evidence
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
  - AGENTS.md
  - README.md
  - AI_CONSTITUTION.md
  - ARCHITECTURE.md
  - SYSTEM.md
  - ROADMAP.md
  - docs/open-issue-coverage.md
  - docs/integration-readiness.md
  - docs/bookmark-cleanup.md
  - docs/drive-capture.md
  - docs/scoped-research.md
  - docs/decisions/README.md
  - docs/acceptance-reconciliation.md
  - docs/bookmark-pilot.md
  - docs/evidence/integration-readiness-qualification.json
  - docs/local-garden-visit.md
work:
  objective: Rehearse the scoped Willow Garden visit before a selected local private pilot.
  success_conditions:
  - Complete bounded synthetic checkpoints with exact evidence and explicit review authority.
  - Preserve Python/v0, original sources, live scope enforcement and proposed ADR status.
  - Keep real inputs/credentials outside the repository and report unavailable live/private contracts honestly.
  active_issue:
    provider: github
    id: egohygiene/mindgarden#47
    url: https://github.com/egohygiene/mindgarden/issues/47
  next:
    kind: action
    id: visit-fictional-garden-and-review-stack
    description: 'Check out feature/local-garden-visit, run the fictional visit, then review drafts #155, #156, #157
      and #158 in order.'
    readiness: ready
    references:
    - docs/local-garden-visit.md
    - docs/integration-readiness.md
    - docs/open-issue-coverage.md
    depends_on: []
state:
  base:
    revision: ea5c3341c4f33e43db994451d3973208fe291ff4
    ref: refs/heads/integration/20261120-drive-codex-readiness
    verified_at: '2026-11-21T05:44:30Z'
  candidate:
    branch: feature/local-garden-visit
    revision: 1f27321d0f1d916e43a271e442b8b7c1aa22426c
    pull_request:
      provider: github
      id: egohygiene/mindgarden#158
      url: https://github.com/egohygiene/mindgarden/pull/158
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-21T05:44:30Z'
    default_branch_revision: 5cf24a29002f8e4f0a464b42819ec21ede33af2a
    issue_state: open
    pull_request_state: draft
    notes: 'Main 5cf24a2. Drafts #155 and #156 passed automatic checks. #157 failed both Linux standalone suites.
      #158 is the combined local visit review branch. 30 open issues and 44 tracked rows.'
  parallel_changes: []
review:
  status: partial
  reviewed_at: '2026-11-21T05:44:30Z'
  reviewed_by: codex
  evidence:
  - command: PYTHONPATH=src python -m unittest tests.test_local_web tests.test_mock_garden -q
    outcome: passed
    observed_at: '2026-11-21T05:44:30Z'
    notes: 11 cases per Python 3.12.14 and 3.13.5. Includes scoped HTTP, SHA-256 evidence, rejected access and preserved
      demo workspace.
  - command: python scripts/check_local_visit_browser.py --chromium /usr/bin/chromium --axe <local-axe.min.js>
    outcome: passed
    observed_at: '2026-11-21T05:44:30Z'
    notes: Chromium 151, axe-core 4.10.3. Search, exact excerpts, related notes, refreshed session, graph, bounded
      byte-identical download, keyboard and reduced motion at 1440/390/320px. Fifteen axe checks passed.
  - command: python -S scripts/mock_garden_demo.py --workspace <new> --require-source --check-golden --visit-fixture
      <new.zip>; cmp <new.zip> examples/mock-garden/visit.zip
    outcome: passed
    observed_at: '2026-11-21T05:44:30Z'
    notes: Full fictional proof plus deterministic visit fixture. SHA-256 3398ec1fbe7172f7a0e96c67d44b9e8cb01b466202ec967078bd4fc3aee801a7.
  - command: python -m build --sdist --wheel --no-isolation --outdir .cache/dist; pip install --no-index --find-links
      .cache/dist mindgarden==0.1.0
    outcome: passed
    observed_at: '2026-11-21T05:44:30Z'
    notes: Packaged web assets and fixture. Offline installed wheel launches the fictional and explicit sessions and
      resolves citations.
  - command: (umask 0022 && PYTHONPATH=src python -m unittest tests.test_drive_private_git -v)
    outcome: passed
    observed_at: '2026-11-21T05:49:00Z'
    notes: The pre-fix test failed with REGISTRY_PERMISSIONS. Fixture-only ea5c334 passed on Python 3.12.14
      and 3.13.5 in 69.363 and 62.626 seconds respectively. The runtime permission check is preserved.
  environment_limitations:
  - Browser and package qualification ran on Linux. Owner Mac use and private input selection remain pending.
  - Public and private hosted acceptance, browser review writes, background workers, assistive-technology review and
    real Drive/Empathy inputs require their existing gates.
  - The desktop and mobile demos use only synthetic data. Automatic and full-suite evidence are tracked separately.
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

Rehearse the scoped Willow Garden visit before a selected local private pilot.

## Resume protocol

Refresh GitHub state. Open [the local visit guide](docs/local-garden-visit.md) and run the demo before selecting any private inputs.

## Current objective and success conditions

Open, search and read reviewed fictional notes with exact evidence. Follow their graph and download a bounded context pack. Reopen the same workspace or start from a clean checkout.

## State snapshot

Main 5cf24a2. Drafts #155 and #156 passed automatic checks. The earlier #157 Linux failure is fixed locally and pushed at ea5c334. #158 is the combined local visit review branch. 30 open issues and 44 tracked rows.

## Completed and material changes

[#158](https://github.com/egohygiene/mindgarden/pull/158) adds the fictional Willow Garden, a scoped read-only browser and reproducible source-vault fixture. Functional commit `1f27321`. The stack's prior bookmark, Drive and Codex receipts remain in [integration readiness](docs/integration-readiness.md).

## Validation and review evidence

Eleven focused tests per Python and fifteen automated axe checks passed. Chromium exercised the complete visit at three viewport widths. The original golden replay, deterministic fixture rebuild and installed wheel smoke passed. The clean clone passed the browser tour. The earlier Linux failure on #157 was reproduced with umask 0022 and repaired by creating the fictional capture workspace with mode 0700. Both supported Pythons pass the exact regression. Commands and evidence are in this document's metadata and the local visit guide.

## Blockers, risks, unknowns, and deferred work

#17 and #47 retain public hosting, authenticated runtime, review writes, worker lifecycle and manual accessibility acceptance. #20 retains the owner-approved pilot and consumer work. Role grants and integrations remain subject to the existing decisions. Keep real inputs outside public Git.

## Next dependency-ready work

Check out feature/local-garden-visit, run the fictional visit, then review drafts #155, #156, #157 and #158 in order. After that review, use one selected private folder with explicit bindings and scope to rehearse the owner's first visit.

## Parallel changes and reconciliation

Draft stack #155 → #156 → #157 → #158. The combined branch is `feature/local-garden-visit`. The source worktree's independent in-progress files remain intact.

## Privacy and redaction

Use fictional fixtures for public evidence. Keep the per-launch access link, private paths, authorization and real data local.

## Handoff update protocol

Record actual issue and PR state, exact commits, commands, passing and failing evidence, acceptance gaps and the next runnable command.

## Compaction and supersession

Prior synthetic preparation and routing qualifications remain linked from the integration guide and coverage ledger.
