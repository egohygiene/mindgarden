---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-21T19:34:31Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: Complete ChatGPT browser sign-in in Studio and direct users back to the right interface.
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
  objective: Complete ChatGPT browser sign-in in Studio and direct users back to the right interface.
  success_conditions:
  - Complete bounded synthetic checkpoints with exact evidence and explicit review authority.
  - Preserve Python/v0, original sources, live scope enforcement and proposed ADR status.
  - Keep real inputs/credentials outside the repository and report unavailable live/private contracts honestly.
  active_issue:
    provider: github
    id: egohygiene/mindgarden#174
    url: https://github.com/egohygiene/mindgarden/issues/174
  next:
    kind: action
    id: retry-chatgpt-sign-in-on-owner-mac
    description: 'Build Studio from draft #175, retry consent on the owner Mac and observe the Models card.'
    readiness: ready
    references:
    - docs/studio-chatgpt-consent.md
    - docs/studio-model-connections.md
    depends_on: []
state:
  base:
    revision: 00ab34e873601239ce62c1e245c076987ae48f4a
    ref: refs/heads/main
    verified_at: '2026-11-21T19:34:31Z'
  candidate:
    branch: fix/studio-chatgpt-callback
    revision: 5b522d1291a1b75a8b5dc212d77356135ac548bb
    pull_request:
      provider: github
      id: egohygiene/mindgarden#175
      url: https://github.com/egohygiene/mindgarden/pull/175
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-21T19:34:31Z'
    default_branch_revision: 00ab34e873601239ce62c1e245c076987ae48f4a
    issue_state: open
    pull_request_state: draft
    notes: "PRs #155\u2013#173 in the Studio stack merged. GitHub showed 37 open issues. This ledger tracks 51 rows."
  parallel_changes: []
review:
  status: partial
  reviewed_at: '2026-11-21T19:34:31Z'
  reviewed_by: codex
  evidence:
  - command: PYTHONPATH=src python -m unittest tests.test_chatgpt_callback tests.test_studio_chatgpt_login tests.test_chatgpt_connection
      tests.test_studio_chatgpt_visit tests.test_chatgpt_oauth tests.test_studio_chatgpt tests.test_model_lab tests.test_studio_model_routes
      -q
    outcome: passed
    observed_at: '2026-11-21T19:34:31Z'
    notes: 65 cases passed on Python 3.12.14 and 3.13.5. They cover callback correlation, issuer and error handling, verified local storage, cancellation, safe
      connection actions and explicit provider checks.
  - command: npm --prefix web ci --offline --no-fund --audit=false && npm --prefix web run build && npm --prefix web test
    outcome: passed
    observed_at: '2026-11-21T19:34:31Z'
    notes: Production build and eight frontend cases passed on Node 24.19.0. Vite retains the existing garden-cover.webp
      runtime resolution warning.
  - command: python scripts/check_studio_model_browser.py --chromium /usr/bin/chromium --axe <axe-core>
    outcome: passed
    observed_at: '2026-11-21T19:34:31Z'
    notes: At 1440 and 390 px, real loopback callbacks with synthetic OAuth covered Studio and terminal guidance, accessibility,
      interrupted HTTP responses, provider error and retry, verification, reload and sign-out.
  environment_limitations:
  - The original Mac callback shape and failure stage are unknown. The proof uses only synthetic OAuth.
  - Live account eligibility and a completed plan request await the owner Mac trial. Native Codex, private garden context,
    Drive and media have separate scope.
  - The Python ID-token verifier remains an optional dependency. Hosted checks run separately.
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

Complete ChatGPT browser sign-in in Studio and direct users back to the right interface.

## Resume protocol

Refresh GitHub state and build the draft branch locally. Follow the [Studio sign-in guide](docs/studio-chatgpt-consent.md).

## Current objective and success conditions

Return from browser consent to the correct interface. Show progress during verification, report a correlated failure promptly and show a verified saved session after reload.

## State snapshot

Studio sign-in #173 merged at main `00ab34e`. [Draft #175](https://github.com/egohygiene/mindgarden/pull/175) targets main at implementation `5b522d1` and addresses #174. The coverage ledger tracks 51 rows.

## Completed and material changes

The callback accepts bounded OAuth response extensions and preserves exact state, host, path, issuer and one-use checks. The two return pages use fixed copy and a hashed stylesheet. Studio shows verification, recovers interrupted status checks and recognizes a saved local session on a fresh visit.

## Validation and review evidence

The old stall was reproduced with a synthetic additional field and a synthetic provider error. Python provider tests, the production web build, eight frontend cases and Chromium with axe at desktop and mobile widths cover the recovery. Hosted checks are separate.

## Blockers, risks, unknowns, and deferred work

The reason for the owner Mac's live failure remains unverified. Live consent and the first completed plan response await an owner-side rerun under #163.

## Next dependency-ready work

Build Studio from `fix/studio-chatgpt-callback` on the owner Mac and choose **Continue with ChatGPT**. Return to **Models**, look for **Signed in to ChatGPT**, then choose **Check connection** and approve the fictional January request.

## Parallel changes and reconciliation

The former Studio stack #155 through #173 is merged. Draft #175 is a single PR against main.

## Privacy and redaction

Use synthetic public evidence. Callback values and credentials stay in the native flow and private state.

## Handoff update protocol

Record the branch, issue, commit, exact checks, blockers and next action. Refresh live state before acting.

## Compaction and supersession

Earlier integration receipts remain linked in the [coverage ledger](docs/open-issue-coverage.md).
