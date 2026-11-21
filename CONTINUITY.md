---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-21T14:09:51Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: Qualify the fictional Studio assistant and cited January booklet before a selected owner pilot.
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
  - docs/mindgarden-studio.md
  - experiments/next-rendering/README.md
  - docs/garden-brief.md
  - examples/mock-garden/manual-sweep.md
  - docs/studio-codex.md
  - docs/studio-assistant-pilot.md
work:
  objective: Qualify the fictional Studio assistant and cited January booklet before a selected owner pilot.
  success_conditions:
  - Complete bounded synthetic checkpoints with exact evidence and explicit review authority.
  - Preserve Python/v0, original sources, live scope enforcement and proposed ADR status.
  - Keep real inputs/credentials outside the repository and report unavailable live/private contracts honestly.
  active_issue:
    provider: github
    id: egohygiene/mindgarden#161
    url: https://github.com/egohygiene/mindgarden/issues/161
  next:
    kind: action
    id: review-fictional-studio-tour
    description: Rehearse and review the fictional Studio tour from the combined draft.
    readiness: ready
    references:
    - docs/studio-assistant-pilot.md
    - docs/studio-codex.md
    - docs/drive-capture.md
    depends_on: []
state:
  base:
    revision: 2b26ef1c4c7523b10ddd7aae180174984a1c205c
    ref: refs/heads/feature/studio-codex-preflight
    verified_at: '2026-11-21T14:09:51Z'
  candidate:
    branch: feature/scoped-studio-assistant-pilot
    revision: bb6c7d9eee005e344cde5acd4358c5974620b6a9
    pull_request:
      provider: github
      id: egohygiene/mindgarden#169
      url: https://github.com/egohygiene/mindgarden/pull/169
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-21T14:09:51Z'
    default_branch_revision: 5cf24a29002f8e4f0a464b42819ec21ede33af2a
    issue_state: open
    pull_request_state: draft
    notes: 'Main 5cf24a2. GitHub has 36 open issues and 50 coverage rows. #168 protocol commit 2b26ef1 stacks on #167.
      #169 stacks on #168 with functional commits a8429f2 and bb6c7d9. Automatic macOS registry and release preparation
      checks passed for a8429f2 at review time. The hosted Linux matrix was still running.'
  parallel_changes: []
review:
  status: partial
  reviewed_at: '2026-11-21T14:09:51Z'
  reviewed_by: codex
  evidence:
  - command: python -S scripts/check_codex_app_server.py --expected-version 0.159.0-alpha.3
    outcome: passed
    observed_at: '2026-11-21T14:09:51Z'
    notes: Isolated Linux App Server protocol verified with no model or account requests. Schema SHA-256 d862dc8a6fdcda2f386c43d246b05c5007f3bbfc16400ff3cac3780300833041.
  - command: PYTHONPATH=src python -m unittest tests.test_studio_assistant tests.test_assistant_provider_contract
      tests.test_monthly_booklet tests.test_visit_launch tests.test_codex_app_server_probe tests.test_local_web tests.test_package
      -q
    outcome: passed
    observed_at: '2026-11-21T14:09:51Z'
    notes: 41 tests passed each on Python 3.12.14 and 3.13.5. Covers exact scopes and bytes, adversarial events, cancellation,
      revocation, stale revisions, two offline adapters and launch.
  - command: npm --prefix web ci --offline --no-fund --audit=false && npm --prefix web run build && npm --prefix web
      test
    outcome: passed
    observed_at: '2026-11-21T14:09:51Z'
    notes: Clean checkout of bb6c7d9. Vite production build and eight tests passed on Node 24.19.0. Existing runtime-served
      garden cover generated a build warning.
  - command: python scripts/check_studio_assistant_browser.py --chromium /usr/bin/chromium --axe <axe-core> --artifacts
      <fictional-outputs>
    outcome: passed
    observed_at: '2026-11-21T14:09:51Z'
    notes: Working tree and clean checkout passed at 1440 and 390 px. Verified Finance lens, note citation, individual
      reviewed rows, open questions, separate approval and exact downloads. Byte-identical two-page Letter PDF, 8
      citations, 2259.76 USD net movement, and missing-account gap. PDF SHA-256 e55fa030c9b9c468eb69fc78f43555c9f148e26665342d185aa9c05f98d81415.
  - command: python scripts/check_studio_browser.py --chromium /usr/bin/chromium --axe <axe-core>
    outcome: passed
    observed_at: '2026-11-21T14:09:51Z'
    notes: Ordinary Studio passed at 1440, 390, and 320 px with the assistant disabled.
  - command: python -m build --no-isolation --outdir <dist>; venv pip install --no-index --no-deps --find-links <dist>
      mindgarden==0.1.0; venv python -I -m mindgarden visit --demo --interface studio --assistant fixture --workspace
      <fresh>
    outcome: passed
    observed_at: '2026-11-21T14:09:51Z'
    notes: Offline installed wheel of bb6c7d9 passed the same two viewport browser workflow. A separately built Python-only
      wheel preserved the classic reader.
  - command: python -S scripts/garden_brief_demo.py --workspace <fresh> --require-source
    outcome: passed
    observed_at: '2026-11-21T14:09:51Z'
    notes: 'The combined clean checkout reproduced #167''s reviewed brief, assistant ledger and exact note citation
      with networking blocked and zero model calls.'
  - command: PYTHONPATH=src python -m unittest tests.test_distribution -q
    outcome: passed
    observed_at: '2026-11-21T14:09:51Z'
    notes: Two tests passed against bb6c7d9's local source archive and wheel.
  environment_limitations:
  - The pilot uses a fixed fictional month and deterministic text and figures. No private inputs, hosted models, account
    access, or publishing were exercised.
  - '#163 remains open for actual host permissions, sign-in, cancellation and replay. A real #166 adapter follows
    the qualified first provider and maintainer selection.'
  - 'The independent selected Drive capture and owner review remain with #87. Optional RDF, JSON-LD and PROV-O formats
    remain with #91.'
  - Cancel stops fictional response delivery and clears partial browser output. A live runtime must qualify model
    interruption and recovery separately.
  - The full standalone suite was still running at the local checkpoint. Verified focused, package, and browser runs
    are listed above.
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

Qualify the fictional Studio assistant and cited January booklet before a selected owner pilot.

## Resume protocol

Refresh GitHub state, check out the exact combined branch, then follow the [Studio assistant guide](docs/studio-assistant-pilot.md).

## Current objective and success conditions

Preview approved note context, replay the offline answer, open an exact citation, and switch to Finance for a separately approved PDF and evidence manifest.

## State snapshot

Main 5cf24a2. GitHub has 36 open issues and 50 coverage rows. #168 protocol commit 2b26ef1 stacks on #167. #169 stacks on #168 with functional commits a8429f2 and bb6c7d9. Automatic macOS registry and release preparation checks passed for a8429f2 at review time. The hosted Linux matrix was still running.

## Completed and material changes

[Draft #168](https://github.com/egohygiene/mindgarden/pull/168) verifies the pinned Linux App Server protocol. [Draft #169](https://github.com/egohygiene/mindgarden/pull/169) adds scoped Studio chat, finance navigation, exact transaction review and local downloads. #167 provides the reviewed first-sweep brief. The draft leaves decisions proposed and uses the existing review and ledger services.

## Validation and review evidence

The isolated protocol handshake, 41 focused tests per Python, eight frontend tests and clean Chromium rehearsal passed. The booklet exposed the missing account and unresolved movement. The clean source run reproduced the PDF and manifest exactly. The same path passed from a fresh offline wheel install. The ordinary Studio remained usable at desktop and mobile widths.

## Blockers, risks, unknowns, and deferred work

The fictional checkpoint advances #163–#165. Target-host permission and live sign-in, a private reviewed month, and the second real provider remain open. #87 owns the selected Drive capture, and #91 owns optional semantic formats.

## Next dependency-ready work

Rehearse and review the fictional Studio tour from the combined draft. With target-host isolation and approved disclosure in place, use #163 to qualify supported Codex sign-in, one fictional stream, cancellation and recovery. When the owner is ready, use #87 to capture and review one selected Drive folder.

## Parallel changes and reconciliation

Draft order #155 → #156 → #157 → #158 → #159 → #160 → #167 → #168 → #169. Combined checkout `feature/scoped-studio-assistant-pilot`. #161 and five native sub-issues are tracked under #86.

## Privacy and redaction

Use the fictional fixture in public proposals. Keep private exports, evidence, session grants, accounts and provider credentials in authorized local storage.

## Handoff update protocol

Record exact branch, issue, commit, commands, verification and the next concrete operation. Refresh live state before acting.

## Compaction and supersession

Earlier Studio and integration receipts remain linked from the [coverage ledger](docs/open-issue-coverage.md).
