---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-21T18:49:29Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: Verify ChatGPT plan consent from the optional Studio Models lab.
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
  - docs/studio-model-connections.md
  - docs/studio-chatgpt-consent.md
work:
  objective: Verify ChatGPT plan consent from the optional Studio Models lab.
  success_conditions:
  - Complete bounded synthetic checkpoints with exact evidence and explicit review authority.
  - Preserve Python/v0, original sources, live scope enforcement and proposed ADR status.
  - Keep real inputs/credentials outside the repository and report unavailable live/private contracts honestly.
  active_issue:
    provider: github
    id: egohygiene/mindgarden#163
    url: https://github.com/egohygiene/mindgarden/issues/163
  next:
    kind: action
    id: try-chatgpt-sign-in-from-studio
    description: Launch the combined fictional Models draft on the owner Mac and choose Continue with ChatGPT.
    readiness: ready
    references:
    - docs/studio-chatgpt-consent.md
    - docs/studio-model-connections.md
    depends_on: []
state:
  base:
    revision: 6785ca933587c39ca95fcf94f9190186d18e72cc
    ref: refs/heads/feature/studio-chatgpt-plan
    verified_at: '2026-11-21T18:49:29Z'
  candidate:
    branch: feature/studio-chatgpt-browser-login
    revision: 2d8a8ceb6cd10dfe4da03786019174b85d63c614
    pull_request:
      provider: github
      id: egohygiene/mindgarden#173
      url: https://github.com/egohygiene/mindgarden/pull/173
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-21T18:49:29Z'
    default_branch_revision: 5cf24a29002f8e4f0a464b42819ec21ede33af2a
    issue_state: open
    pull_request_state: draft
    notes: 'Main 5cf24a2 with 36 open issues and 50 coverage rows. #172 at 6785ca9 passed all five hosted checks.
      Draft #173 stacks on #172 with implementation 2d8a8ce.'
  parallel_changes: []
review:
  status: partial
  reviewed_at: '2026-11-21T18:49:29Z'
  reviewed_by: codex
  evidence:
  - command: PYTHONPATH=src python -m unittest tests.test_studio_chatgpt_login tests.test_chatgpt_connection tests.test_chatgpt_callback
      tests.test_studio_chatgpt_visit tests.test_model_lab tests.test_studio_model_routes -q
    outcome: passed
    observed_at: '2026-11-21T18:49:29Z'
    notes: 36 tests per Python 3.12.14 and 3.13.5 for exact-origin protected actions, idle status, armed callback,
      one attempt, bounded opener, cancel/close during exchange, scope revocation, and catalog invalidation. The broader
      125-case provider, account, booklet, CLI, and scope regression matrix also passed per interpreter.
  - command: npm --prefix web ci --offline --no-fund --audit=false && npm --prefix web run build && npm --prefix web
      test
    outcome: passed
    observed_at: '2026-11-21T18:49:29Z'
    notes: Clean checkout of 2d8a8ce, production build and eight frontend cases passed on Node 24.19.0.
  - command: python scripts/check_studio_model_browser.py --chromium /usr/bin/chromium --axe <axe-core>
    outcome: passed
    observed_at: '2026-11-21T18:49:29Z'
    notes: Chromium and axe passed at 1440 and 390 px. Studio launched the real broker and callback with fake OAuth,
      canceled and retried, showed authorization, offered renewal after expired Check and Run, and cleared the session
      on sign-out. Model check and inference stayed explicit.
  - command: python -m build --no-isolation; pip install --no-index --no-deps mindgarden==0.1.0; python -I -m mindgarden
      visit --demo --interface studio --assistant providers --workspace <fresh> --chatgpt-state-directory <absent>
    outcome: passed
    observed_at: '2026-11-21T18:49:29Z'
    notes: Two distribution tests passed. The offline-installed wheel showed Continue with ChatGPT. Without the optional
      verifier, explicit click showed setup guidance without creating consent state.
  environment_limitations:
  - The public proof used a fake browser opener and synthetic token exchange. Actual owner account consent and first
    live response are pending.
  - The sign-in action requires a graphical browser on the machine running Studio and the optional installed ID-token
    verifier. Studio uses the existing fictional authority and separate native callback.
  - 'Native Codex agent execution, private garden context, Drive, and media retain their own scope. Hosted #173 checks
    run separately.'
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

Verify ChatGPT plan consent from the optional Studio Models lab.

## Resume protocol

Refresh GitHub state and use the combined branch. Follow the [Studio sign-in guide](docs/studio-chatgpt-consent.md).

## Current objective and success conditions

Start consent from Models. Show the result after the native callback verifies it. Canceling or losing scope stops pending credential writes. Check the model list and approve the fictional prompt separately.

## State snapshot

Main 5cf24a2 with 36 open issues and 50 coverage rows. #172 at 6785ca9 passed all five hosted checks. Draft #173 stacks on #172 with implementation 2d8a8ce.

## Completed and material changes

[Draft #173](https://github.com/egohygiene/mindgarden/pull/173) opens the official consent page from Studio, shows redacted progress, and clears the previous catalog and approvals after a new credential or sign-out. The fictional Models command selects an owner-only default consent directory. The CLI lifecycle in #171 remains available.

## Validation and review evidence

Both supported Python interpreters passed the broad provider regressions and 36 focused login cases. Chromium desktop and mobile exercised Studio through the actual native callback with synthetic OAuth. Expiry, cancel, sign-out, and explicit model request controls passed. The installed wheel surfaced optional verifier setup from the button when needed.

## Blockers, risks, unknowns, and deferred work

Actual sign-in and the first plan response await a trial on the owner Mac. Native Codex execution, private sources, Drive, and media remain separate milestones.

## Next dependency-ready work

Launch the combined fictional Models draft on the owner Mac and choose Continue with ChatGPT. Finish the official consent, return to Studio, choose **Check connection**, preview the January fixture and approve one request.

## Parallel changes and reconciliation

Draft order #155 → #156 → #157 → #158 → #159 → #160 → #167 → #168 → #169 → #170 → #171 → #172 → #173. Combined checkout `feature/studio-chatgpt-browser-login`.

## Privacy and redaction

Use synthetic public evidence. Consent URLs and callback values stay in the native flow. Credentials remain in the authorized private directory.

## Handoff update protocol

Record exact branch, issue, commit, commands, verification and the next concrete operation. Refresh live state before acting.

## Compaction and supersession

Earlier integration receipts remain linked from the [coverage ledger](docs/open-issue-coverage.md) and the parent handoff.
