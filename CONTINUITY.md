---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-21T17:05:46Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: Validate an explicit local ChatGPT consent session before a fictional plan-backed request.
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
  objective: Validate an explicit local ChatGPT consent session before a fictional plan-backed request.
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
    id: review-local-chatgpt-consent
    description: Review the local consent draft and the documented macOS test before authorizing an account.
    readiness: ready
    references:
    - docs/studio-chatgpt-consent.md
    depends_on: []
state:
  base:
    revision: 2e56fc4552b30144f94677a7d41817fccca86451
    ref: refs/heads/feature/studio-model-connections
    verified_at: '2026-11-21T17:05:46Z'
  candidate:
    branch: feature/chatgpt-local-consent
    revision: 48b7d2b805c0447c1f8ba89d7e68d4a799bf5b6b
    pull_request:
      provider: github
      id: egohygiene/mindgarden#171
      url: https://github.com/egohygiene/mindgarden/pull/171
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-21T17:05:46Z'
    default_branch_revision: 5cf24a29002f8e4f0a464b42819ec21ede33af2a
    issue_state: open
    pull_request_state: draft
    notes: 'Main 5cf24a2. #171 stacks on #170 at 2e56fc4. The consent implementation is 48b7d2b. GitHub has 36 open
      issues and 50 coverage rows.'
  parallel_changes: []
review:
  status: partial
  reviewed_at: '2026-11-21T17:05:46Z'
  reviewed_by: codex
  evidence:
  - command: PYTHONPATH=src python -m unittest tests.test_chatgpt_credentials tests.test_chatgpt_callback tests.test_chatgpt_oauth
      tests.test_chatgpt_connection tests.test_package -q
    outcome: passed
    observed_at: '2026-11-21T17:05:46Z'
    notes: 39 cases from clean source on Python 3.12.14 and 3.13.5 with the optional verifier. Includes real loopback,
      locally signed RS256, scope/nonce/audience rejection, owner-only credentials, rotating renewals and terminal/transient
      recovery.
  - command: python -m build --no-isolation; pip install --no-index --no-deps mindgarden==0.1.0; python -I -m mindgarden
      chatgpt status --state-directory <absent>
    outcome: passed
    observed_at: '2026-11-21T17:05:46Z'
    notes: Clean source archive carries requirements/chatgpt.txt. Offline wheel with no optional crypto dependency
      reports signed-out and leaves the requested directory absent.
  - command: GET https://auth.openai.com/.well-known/openid-configuration
    outcome: passed
    observed_at: '2026-11-21T17:05:46Z'
    notes: Public discovery matched issuer, token, signing keys, revocation URLs and RS256. No account or token was
      used.
  environment_limitations:
  - No actual ChatGPT consent, authenticated account status, or inference was attempted.
  - The first checkpoint selects one registration per explicit native state directory. The dependent Model Lab draft
    consumes its credential.
  - 'The native Codex App Server inference and interrupt boundary remains open under #163. No Drive work was requested
    for this pass.'
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

Validate an explicit local ChatGPT consent session before a fictional plan-backed request.

## Resume protocol

Refresh GitHub state, then follow the [local consent guide](docs/studio-chatgpt-consent.md).

## Current objective and success conditions

Open one explicit browser consent, verify the identity and plan-use scopes, then keep the renewable session in owner-only local state.

## State snapshot

Main 5cf24a2. #171 stacks on #170 at 2e56fc4. The consent implementation is 48b7d2b. GitHub has 36 open issues and 50 coverage rows.

## Completed and material changes

[Draft #171](https://github.com/egohygiene/mindgarden/pull/171) adds the optional `chatgpt` lifecycle and a separate one-use loopback receiver. Authorization uses PKCE and verified ID-token claims. Refresh and sign-out preserve the registration, and writer serialization protects rotating credentials.

## Validation and review evidence

Thirty-nine tests passed per supported Python on clean source. A dependency-free installed wheel proved the cached signed-out status and left the requested directory untouched.

## Blockers, risks, unknowns, and deferred work

The next independent draft binds the consent profile to the fixed fictional Studio scenario. Actual account eligibility and inference await the owner. Native Codex agent isolation and cancellation, Drive and media keep their own scope.

## Next dependency-ready work

Review the local consent draft and the documented macOS test before authorizing an account.

## Parallel changes and reconciliation

Draft order #155 → #156 → #157 → #158 → #159 → #160 → #167 → #168 → #169 → #170 → #171. The combined branch for consent is `feature/chatgpt-local-consent`.

## Privacy and redaction

Public tests use synthetic identities. Keep local credentials outside repository and garden records.

## Handoff update protocol

Record exact branch, issue, commit, commands, verification and the next concrete operation. Refresh live state before acting.

## Compaction and supersession

Earlier Studio receipts remain linked from the [coverage ledger](docs/open-issue-coverage.md).
