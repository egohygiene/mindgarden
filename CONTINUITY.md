---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-21T09:17:54Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: Review Studio's scoped knowledge explorer and Drive capture evidence before a selected private pilot.
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
work:
  objective: Review Studio's scoped knowledge explorer and Drive capture evidence before a selected private pilot.
  success_conditions:
  - Complete bounded synthetic checkpoints with exact evidence and explicit review authority.
  - Preserve Python/v0, original sources, live scope enforcement and proposed ADR status.
  - Keep real inputs/credentials outside the repository and report unavailable live/private contracts honestly.
  active_issue:
    provider: github
    id: egohygiene/mindgarden#87
    url: https://github.com/egohygiene/mindgarden/issues/87
  next:
    kind: action
    id: review-explorer-and-select-drive-pilot
    description: Run the fictional graph and Sources tour on the owner's Mac. Review the draft stack, then authorize
      one selected Drive folder for a local capture and review.
    readiness: ready
    references:
    - docs/mindgarden-studio.md
    - docs/drive-capture.md
    depends_on: []
state:
  base:
    revision: d57ba2f2e6b3fc0cade28b3f8d14c8f041daabbc
    ref: refs/heads/feature/react-garden-studio
    verified_at: '2026-11-21T09:17:54Z'
  candidate:
    branch: feature/studio-knowledge-explorer
    revision: 593853c2d776aa56d83f5dea79c85bd43ace35da
    pull_request:
      provider: github
      id: egohygiene/mindgarden#160
      url: https://github.com/egohygiene/mindgarden/pull/160
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-21T09:17:54Z'
    default_branch_revision: 5cf24a29002f8e4f0a464b42819ec21ede33af2a
    issue_state: open
    pull_request_state: draft
    notes: 'Main 5cf24a2. #160 is draft on #159 at d57ba2f. Thirty issues remain open with 44 tracked rows.'
  parallel_changes: []
review:
  status: partial
  reviewed_at: '2026-11-21T09:17:54Z'
  reviewed_by: codex
  evidence:
  - command: npm --prefix web ci --offline --no-fund --audit=false && npm --prefix web run build && npm --prefix web
      test
    outcome: passed
    observed_at: '2026-11-21T09:17:54Z'
    notes: A clean Git checkout of the functional revision built Studio and passed eight TypeScript API tests.
  - command: PYTHONPATH=src python -m unittest tests.test_local_web tests.test_drive_normalization tests.test_package
      -q
    outcome: passed
    observed_at: '2026-11-21T09:17:54Z'
    notes: Twenty-five cases passed on each Python 3.12.14 and 3.13.5 with umask 0022. Tested evidence scope, revocation,
      missing lineage, fabricated provider markers and CLI compatibility.
  - command: python scripts/check_studio_browser.py --chromium /usr/bin/chromium --axe <local-axe.min.js> [--webgl]
    outcome: passed
    observed_at: '2026-11-21T09:17:54Z'
    notes: Chromium 151 verified 1440, 390 and 320px with 24 axe checks. Covered note-to-map navigation, trail, filtered
      graph, Sources, context bytes and no remote asset requests.
  - command: Launch mindgarden visit --interface studio --local-config <fictional bindings> --scope <fictional session>
      and open Sources in Chromium
    outcome: passed
    observed_at: '2026-11-21T09:17:54Z'
    notes: prepare_demo materialized its synthetic reviewed capture under an explicit bound session. Actual API and
      Sources rendered Captured evidence with eight exact Drive citations. Demo launch renders Fictional example and
      12 local-vault citations.
  environment_limitations:
  - The browser qualification was Linux Chromium. The owner Mac launch and live Drive OAuth/capture still need local
    operator evidence.
  - Studio reports reviewed frozen evidence within an explicit session. ChatGPT's Drive connector uses separate credentials.
  - Hosted checks, manual accessibility and parent acceptance remain separate.
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

Review Studio's scoped knowledge explorer and Drive capture evidence before a selected private pilot.

## Resume protocol

Refresh GitHub state and use [the Studio tour](docs/mindgarden-studio.md) from the combined branch.

## Current objective and success conditions

Explore authorized graph nodes, pivot through typed relationships, return to a note context, and inspect where reviewed evidence came from.

## State snapshot

Main 5cf24a2. #160 is draft on #159 at d57ba2f. Thirty issues remain open with 44 tracked rows.

## Completed and material changes

[#160](https://github.com/egohygiene/mindgarden/pull/160) adds a topic-aware graph, centered note neighborhoods and a trail. The note reader can open a map focus and return. Sources adds scoped Drive and vault citation counts with status based on verified local capture lineage. Functional commit `593853c`.

## Validation and review evidence

Eight frontend cases and 25 focused Python cases per version passed. Chromium covered the full flow at three viewport widths with both WebGL and fallback. The explicit synthetic capture opened with the Captured evidence badge. Exact commands are in this document's metadata.

## Blockers, risks, unknowns, and deferred work

The owner's separate local OAuth and selected folder are needed for a real Drive capture. Browser editing, hosted identity, publication, manual accessibility and the private consumer remain subject to #17, #47 and #87.

## Next dependency-ready work

Run the fictional graph and Sources tour on the owner's Mac. Review the draft stack, then authorize one selected Drive folder for a local capture and review.

## Parallel changes and reconciliation

Draft order #155 → #156 → #157 → #158 → #159 → #160. The combined branch is `feature/studio-knowledge-explorer`. Studio's Next.js lab remains independent under `experiments/next-rendering`.

## Privacy and redaction

Use the fictional fixtures for public demonstrations. Keep OAuth, account information, real file paths and the launch capability in the local workspace.

## Handoff update protocol

Record current PR and commit, exact permission scope, runnable checks, remaining acceptance and a resumable first action.

## Compaction and supersession

Prior checks remain linked from the [coverage ledger](docs/open-issue-coverage.md) and [integration readiness guide](docs/integration-readiness.md).
