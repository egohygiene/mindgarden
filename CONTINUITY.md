---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-21T17:11:01Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: Verify the optional ChatGPT plan connection against the bundled fictional Studio prompt.
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
  objective: Verify the optional ChatGPT plan connection against the bundled fictional Studio prompt.
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
    id: review-the-combined-chatgpt-plan-draft
    description: Review the combined draft and follow the local walkthrough to authorize the owner's eligible account.
    readiness: ready
    references:
    - docs/studio-chatgpt-consent.md
    - docs/studio-model-connections.md
    depends_on: []
state:
  base:
    revision: 7549ac6a2290a0da74a4ca00c750c8805806293d
    ref: refs/heads/feature/chatgpt-local-consent
    verified_at: '2026-11-21T17:11:01Z'
  candidate:
    branch: feature/studio-chatgpt-plan
    revision: 9e64b74b9e83e67b9f0a4e7c969c7a4e76f17b9d
    pull_request:
      provider: github
      id: egohygiene/mindgarden#172
      url: https://github.com/egohygiene/mindgarden/pull/172
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-21T17:11:01Z'
    default_branch_revision: 5cf24a29002f8e4f0a464b42819ec21ede33af2a
    issue_state: open
    pull_request_state: draft
    notes: 'Main 5cf24a2 with 36 open issues and 50 coverage rows. #171 consent implementation 48b7d2b stacks on #170.
      #172 at functional 9e64b74 stacks on #171 at 7549ac6. Hosted checks are tracked separately from the local rehearsal.'
  parallel_changes: []
review:
  status: partial
  reviewed_at: '2026-11-21T17:11:01Z'
  reviewed_by: codex
  evidence:
  - command: PYTHONPATH=src python -m unittest tests.test_chatgpt_credentials tests.test_chatgpt_callback tests.test_chatgpt_oauth
      tests.test_chatgpt_connection tests.test_studio_chatgpt tests.test_studio_chatgpt_visit tests.test_model_lab
      tests.test_studio_model_routes tests.test_studio_model_http tests.test_studio_codex tests.test_studio_assistant
      tests.test_assistant_provider_contract tests.test_monthly_booklet tests.test_visit_launch tests.test_codex_app_server_probe
      tests.test_local_web tests.test_package -q
    outcome: passed
    observed_at: '2026-11-21T17:11:01Z'
    notes: 123 focused cases passed per Python 3.12.14 and 3.13.5 with the optional verifier. Includes both local
      consent and Responses, exact fictional payload, midstream disconnect, stale cached model invalidation, and the
      existing fixture, booklet and provider regressions.
  - command: npm --prefix web ci --offline --no-fund --audit=false && npm --prefix web run build && npm --prefix web
      test
    outcome: passed
    observed_at: '2026-11-21T17:11:01Z'
    notes: Fresh source at 9e64b74. Node 24.19.0 and Vite production build passed, eight frontend cases passed. The
      existing runtime garden cover generated its normal build warning.
  - command: python scripts/check_studio_model_browser.py --chromium /usr/bin/chromium --axe <axe-core>
    outcome: passed
    observed_at: '2026-11-21T17:11:01Z'
    notes: Offline Chromium at 1440 and 390 px passed with four provider doubles. The same model slug cannot reuse
      a different provider's consent. The card clears stale choices on reauthentication, and Gemini/Ollama/default
      paths remain usable.
  - command: python -m build --no-isolation; pip install --no-index --no-deps mindgarden==0.1.0; python -I -m mindgarden
      visit --demo --interface studio --assistant providers --workspace <fresh> --chatgpt-state-directory <absent>
    outcome: passed
    observed_at: '2026-11-21T17:11:01Z'
    notes: Two distribution tests passed. Installed wheel showed the unconfigured ChatGPT setup card in Chromium without
      optional crypto. It did not create consent state or make a provider request.
  environment_limitations:
  - The offline run used synthetic authorization, signed identity fixtures and simulated Responses streams. An eligible
    owner session and its first live result still require explicit local verification.
  - The browser displays completed provider text. Stop waiting stops display, while a submitted response may finish.
    An idle browser shows the last check until another operation. Revocation and expiry are enforced on dispatch and
    delivery.
  - Native Codex agent isolation and interruption are independent of direct ChatGPT plan inference. Private source
    authorization, captured Drive evidence and media remain outside the fictional checkpoint.
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

Verify the optional ChatGPT plan connection against the bundled fictional Studio prompt.

## Resume protocol

Refresh GitHub state and use the combined branch. Follow the [local consent](docs/studio-chatgpt-consent.md) and [Models walkthrough](docs/studio-model-connections.md#chatgpt-plan).

## Current objective and success conditions

Use the owner-controlled profile to discover available models. Approve the exact fictional request, show output only after completion, and invalidate the catalog if consent changes.

## State snapshot

Main 5cf24a2 with 36 open issues and 50 coverage rows. #171 consent implementation 48b7d2b stacks on #170. #172 at functional 9e64b74 stacks on #171 at 7549ac6. Hosted checks are tracked separately from the local rehearsal.

## Completed and material changes

[Draft #171](https://github.com/egohygiene/mindgarden/pull/171) owns sign-in, protected state, refresh and disconnect. [Draft #172](https://github.com/egohygiene/mindgarden/pull/172) owns the optional plan Models card, the direct text adapter and the existing one-use approval. The HTTP reader now handles a response that closes after its declared content length.

## Validation and review evidence

The local signed OAuth and streamed Responses doubles exercise the CLI and real loopback Studio. All 123 focused cases passed per Python. Browser checks passed at desktop and mobile widths from a clean checkout. A clean installed wheel opened the setup card in signed-out state without creating credentials.

## Blockers, risks, unknowns, and deferred work

Owner consent and account entitlement are the remaining live test for plan usage. Native Codex execution, cancellation and sandboxing stay with #163. Drive remains parked with #87. Scoped access to private garden inputs and media generation are future work.

## Next dependency-ready work

Review the combined draft and follow the local walkthrough to authorize the owner's eligible account. Select **ChatGPT plan** in Models, check the reported catalog, preview the January fixture and explicitly approve one live request. Record the observed response or account limitation.

## Parallel changes and reconciliation

Draft order #155 → #156 → #157 → #158 → #159 → #160 → #167 → #168 → #169 → #170 → #171 → #172. Combined checkout `feature/studio-chatgpt-plan`.

## Privacy and redaction

Use synthetic public fixtures. Credentials and callback values stay in the authorized native process and private local state.

## Handoff update protocol

Record exact branch, issue, commit, commands, verification and the next concrete operation. Refresh live state before acting.

## Compaction and supersession

Earlier integration receipts remain linked from the [coverage ledger](docs/open-issue-coverage.md) and the parent draft handoff.
