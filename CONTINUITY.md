---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-21T09:04:30Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: Review the React Studio and its fictional offline walkthrough.
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
  objective: Review the React Studio and its fictional offline walkthrough.
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
    id: run-studio-on-owner-mac-and-review
    description: 'Build and open Studio on the owner''s Mac. Review #155 through #159 in order, then choose one explicit
      local session for the private pilot.'
    readiness: ready
    references:
    - docs/mindgarden-studio.md
    - CONTINUITY.md
    - docs/integration-readiness.md
    depends_on: []
state:
  base:
    revision: 46a152432930a10b3654d9789d3c15ee8144adf1
    ref: refs/heads/feature/local-garden-visit
    verified_at: '2026-11-21T09:04:30Z'
  candidate:
    branch: feature/react-garden-studio
    revision: d3b845915fc5b3f750e803753d68e731b7eee984
    pull_request:
      provider: github
      id: egohygiene/mindgarden#159
      url: https://github.com/egohygiene/mindgarden/pull/159
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-21T09:04:30Z'
    default_branch_revision: 5cf24a29002f8e4f0a464b42819ec21ede33af2a
    issue_state: open
    pull_request_state: draft
    notes: 'Main 5cf24a2. Draft #158 at 46a1524 passed all five hosted checks. #159 stacks on #158. Thirty issues
      remain open with 44 tracked rows.'
  parallel_changes: []
review:
  status: partial
  reviewed_at: '2026-11-21T09:04:30Z'
  reviewed_by: codex
  evidence:
  - command: npm --prefix web ci --offline --no-fund --audit=false && npm --prefix web run build && npm --prefix web
      test
    outcome: passed
    observed_at: '2026-11-21T09:04:30Z'
    notes: Clean-lock Vite and TypeScript build with generated license notices. Six Vitest API contract and request
      tests passed.
  - command: PYTHONPATH=src python -m unittest tests.test_local_web tests.test_mock_garden tests.test_package -q
    outcome: passed
    observed_at: '2026-11-21T09:04:30Z'
    notes: Twenty cases each under umask 0022 on Python 3.12.14 and 3.13.5. Shared scope, declined access, hashed
      assets, required build and classic compatibility.
  - command: python scripts/check_studio_browser.py --chromium /usr/bin/chromium --axe <local-axe.min.js> [--webgl]
    outcome: passed
    observed_at: '2026-11-21T09:04:30Z'
    notes: Chromium 151 at 1440, 390 and 320 pixels. Separate WebGL and fallback runs passed 18 axe checks each. Keyboard
      search and citations, reused route, no remote page requests and byte-exact context download passed.
  - command: python -m build --no-isolation && uv pip install --offline --no-index <wheel>
    outcome: passed
    observed_at: '2026-11-21T09:04:30Z'
    notes: Isolated source and wheel packaging checks for a Python-only checkout and a Studio build. Installed assets
      and exact evidence loaded; the notice stayed outside HTTP and was identical in both artifacts.
  - command: npm --prefix experiments/next-rendering ci --offline && npm --prefix experiments/next-rendering run typecheck
      && npm --prefix experiments/next-rendering run build
    outcome: passed
    observed_at: '2026-11-21T09:04:30Z'
    notes: Next.js 16.4.6 built a static page and a dynamic request-time page. Local production HTTP verified their
      render markers; browser filtering did not send a request.
  environment_limitations:
  - Studio was verified in Linux Chromium. The owner Mac launch and assistive-technology review remain pending.
  - 'Automatic GitHub checks are separate from the local qualification. #159 remains a draft.'
  - Hosted identity and worker/runtime decisions, review writes, live providers and the real private pilot retain
    their acceptance gates.
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

Review the React Studio and its fictional offline walkthrough.

## Resume protocol

Refresh GitHub state, read [the Studio guide](docs/mindgarden-studio.md), and use its fictional setup before selecting an owner-authorized private input.

## Current objective and success conditions

Open the local React dashboard, use keyboard search, follow citations and graph links, and download a bounded context pack. Compare the static and request-time Next.js lab routes separately.

## State snapshot

Main 5cf24a2. Draft #158 at 46a1524 passed all five hosted checks. #159 stacks on #158. Thirty issues remain open with 44 tracked rows.

## Completed and material changes

[#159](https://github.com/egohygiene/mindgarden/pull/159) adds Studio and the Next.js lab. Functional commits `7892a96` and `d3b8459`. The classic visit remains the default. The same Python process serves the Vite bundle and the authorized retrieval routes; optional WebGL uses the same result set as the 2D map.

## Validation and review evidence

The locked Studio and Next.js builds passed. Six frontend unit cases and twenty focused Python cases per version passed. The Chromium journey passed at three widths in WebGL and fallback modes, with eighteen axe checks per run. Source archives and offline installed wheels were tested in both packaging modes. Commands and remaining acceptance are listed in this document's metadata and [the Studio guide](docs/mindgarden-studio.md).

## Blockers, risks, unknowns, and deferred work

#17 and #47 retain the publication, hosted identity, editing, worker, and manual accessibility criteria. #20 and #86 retain the owner-approved private pilot and consumer work. Runtime and identity ADRs are proposed. Nx can be evaluated when shared build orchestration has a concrete consumer.

## Next dependency-ready work

Build and open Studio on the owner's Mac. Review #155 through #159 in order, then choose one explicit local session for the private pilot.

## Parallel changes and reconciliation

Draft order #155 → #156 → #157 → #158 → #159. The combined branch is `feature/react-garden-studio`. Earlier bookmark, Drive and Codex qualifications remain in [integration readiness](docs/integration-readiness.md).

## Privacy and redaction

Use the bundled fictional world for public demos and screenshots. Keep owner paths, real data and the per-launch access link local.

## Handoff update protocol

Record the intended operation, exact commit and PR, permissions, verification commands, and the next reproducible action.

## Compaction and supersession

Earlier scoped visit and integration receipts remain linked from the [coverage ledger](docs/open-issue-coverage.md).
