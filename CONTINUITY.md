---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-21T16:47:35Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: Verify explicit local model connections with the bundled Willow Garden scenario.
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
work:
  objective: Verify explicit local model connections with the bundled Willow Garden scenario.
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
    id: review-studio-model-connections
    description: Launch and review the Models pilot from the combined draft with the bundled fictional scenario.
    readiness: ready
    references:
    - docs/studio-model-connections.md
    - docs/studio-codex.md
    depends_on: []
state:
  base:
    revision: a865353b43a19a6794e00ae6fe0a9c97ac1adb7f
    ref: refs/heads/feature/scoped-studio-assistant-pilot
    verified_at: '2026-11-21T16:47:35Z'
  candidate:
    branch: feature/studio-model-connections
    revision: 78d41c358f07ce2c894d9a22e85a9705f2ac0bf6
    pull_request:
      provider: github
      id: egohygiene/mindgarden#170
      url: https://github.com/egohygiene/mindgarden/pull/170
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-21T16:47:35Z'
    default_branch_revision: 5cf24a29002f8e4f0a464b42819ec21ede33af2a
    issue_state: open
    pull_request_state: draft
    notes: 'Main 5cf24a2 with 36 open issues and 50 coverage rows. #169 at a865353 passed all five automatic checks.
      Draft #170 stacks on #169 with functional commits 0ec6521 and 78d41c3.'
  parallel_changes: []
review:
  status: partial
  reviewed_at: '2026-11-21T16:47:35Z'
  reviewed_by: codex
  evidence:
  - command: PYTHONPATH=src python -m unittest tests.test_model_lab tests.test_studio_model_routes tests.test_studio_model_http
      tests.test_studio_codex tests.test_studio_assistant tests.test_assistant_provider_contract tests.test_monthly_booklet
      tests.test_visit_launch tests.test_codex_app_server_probe tests.test_local_web tests.test_package -q
    outcome: passed
    observed_at: '2026-11-21T16:47:35Z'
    notes: 74 focused tests per interpreter on Python 3.12.14 and 3.13.5 at 0ec6521.
  - command: npm --prefix web ci --offline --no-fund --audit=false && npm --prefix web run build && npm --prefix web
      test
    outcome: passed
    observed_at: '2026-11-21T16:47:35Z'
    notes: Fresh Git checkout of 0ec6521. Production Vite build and eight frontend cases passed on Node 24.19.0. Existing
      runtime-served garden cover generated a build warning.
  - command: python scripts/check_studio_model_browser.py --chromium /usr/bin/chromium --axe <axe-core>
    outcome: passed
    observed_at: '2026-11-21T16:47:35Z'
    notes: 1440 and 390 px passed with offline adapters. Account checked and credit display, per-model consent, approved
      prompt comparison, exact two-stage Ollama install, and provider-disabled navigation.
  - command: Codex App Server initialize, initialized, account/read (refreshToken=false) in a network-disabled Bubblewrap
      process
    outcome: passed
    observed_at: '2026-11-21T16:47:35Z'
    notes: Native 0.159.0-alpha.3 returned unconfigured using an empty sandbox home. Mocked protocol also exercises
      ChatGPT limits, unavailable usage, credentials filtering, and npm env node resolution.
  - command: mindgarden visit --demo --interface studio --assistant providers --workspace <fresh>
    outcome: passed
    observed_at: '2026-11-21T16:47:35Z'
    notes: Native Ollama 0.40.17 served verified gemma3:1b over 127.0.0.1 with cloud disabled. Browse Models, check,
      select, preview, approve and observe the response. The small model copied two figures and misstated coverage.
      The UI retains the preview for comparison.
  - command: ModelLab.check -> ModelLab.install_preview -> ModelLab.install with gemma3:1b
    outcome: passed
    observed_at: '2026-11-21T16:47:35Z'
    notes: Native empty Ollama inventory registered the model in 0.58 seconds using verified cached weights. Missing,
      wrong and repeated approval attempts sent no additional pull. Weight SHA-256 2f8c3d137f2496dcb4019e17a50f2974b89c1be1a742db3c80cc86f91cafeeef.
  - command: PYTHONPATH=src python -m unittest tests.test_studio_model_http -q
    outcome: passed
    observed_at: '2026-11-21T16:47:35Z'
    notes: 12 adapter cases per Python interpreter passed after the Ollama cold-start limit changed to 120 seconds.
  - command: python -m build --no-isolation; pip install --no-index --no-deps mindgarden==0.1.0; python -I -m mindgarden
      visit --demo --interface studio --assistant providers --workspace <fresh>
    outcome: passed
    observed_at: '2026-11-21T16:47:35Z'
    notes: Clean checkout of 78d41c3. Two distribution tests passed. An offline-installed wheel detected no Gemini
      key and passed the cold approved Ollama path in 8.88 s. An earlier cold run under parallel verification exceeded
      the original 55-second limit.
  environment_limitations:
  - Requires the owner Mac for real account checks. The current environment had no Gemini key and used an empty Codex
    home for the protocol smoke.
  - Codex reports account status only. A native restricted runtime or eligible, consented Sign in with ChatGPT inference
    needs separate qualification. Browser interruption ends waiting, while an upstream request may finish.
  - 'Text-only fictional inputs. Image and video artifacts, live access to private garden context, and the selected
    Drive capture in #87 remain separate.'
  - 'Automatic #170 checks are separate from the verified local checkpoint.'
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

Verify explicit local model connections with the bundled Willow Garden scenario.

## Resume protocol

Refresh GitHub state, use the combined branch, then follow the [Models pilot setup](docs/studio-model-connections.md).

## Current objective and success conditions

Check explicit provider status, preview the same fictional text, pick a model, and verify one-use inference and download approvals. Keep account credentials with their configured runtimes.

## State snapshot

Main 5cf24a2 with 36 open issues and 50 coverage rows. #169 at a865353 passed all five automatic checks. Draft #170 stacks on #169 with functional commits 0ec6521 and 78d41c3.

## Completed and material changes

[Draft #170](https://github.com/egohygiene/mindgarden/pull/170) adds the Models view, Codex account and usage metadata, Gemini Developer API text, and local Ollama inference and downloads. The broker sends the bundled fictional prompt and retains no chat log. The dependency correction allows independent fictional Gemini and Ollama proof while the full #166 journey follows qualified live Codex.

## Validation and review evidence

Desktop and mobile Chromium passed the offline approval and model-switch workflow. A real isolated Ollama runtime executed the bundled scenario and registered the verified Gemma model from an empty inventory with one approved pull. The installed Codex protocol returned the expected unconfigured state in an isolated empty home. 74 focused tests passed on each Python version, and the clean installed wheel replayed the cold Ollama request.

## Blockers, risks, unknowns, and deferred work

Actual owner authentication, authenticated quotas and the first Gemini response need the target setup. Codex model turns need restricted runtime or separately consented inference qualification. The small Ollama model misstated fictional coverage. Output remains a generated draft alongside the approved fixture. Drive and media artifacts remain separate.

## Next dependency-ready work

Launch and review the Models pilot from the combined draft with the bundled fictional scenario. On the owner Mac, run `codex login`, set the Gemini key in the Studio process environment, and check each card. Verify the reported Codex account data and explicitly approve the same fictional Gemini run. Track Codex inference under #163.

## Parallel changes and reconciliation

Draft order #155 → #156 → #157 → #158 → #159 → #160 → #167 → #168 → #169 → #170. Combined checkout `feature/studio-model-connections`. #161 and its five native sub-issues remain under #86.

## Privacy and redaction

Use only the bundled fictional data for public proofs. Keep credentials and private workspace records in authorized local storage.

## Handoff update protocol

Record exact branch, issue, commit, commands, verification and the next concrete operation. Refresh live state before acting.

## Compaction and supersession

Earlier Studio and integration receipts remain linked from the [coverage ledger](docs/open-issue-coverage.md).
