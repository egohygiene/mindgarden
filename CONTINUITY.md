---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-21T23:10:27Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: Land the reviewed local checkpoints and qualify the existing Studio and archive journeys.
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
  - docs/consumer-journey.md
  - docs/extraction-producers.md
  - docs/private-routing.md
  - docs/compaction-retention.md
work:
  objective: Land the reviewed local checkpoints and qualify the existing Studio and archive journeys.
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
    id: qualify-existing-studio-provider
    description: Observe the ChatGPT plan card on the owner Mac, identify the catalog outcome, and qualify one explicitly
      approved fictional turn.
    readiness: ready
    references:
    - docs/studio-chatgpt-consent.md
    - docs/studio-model-connections.md
    depends_on: []
state:
  base:
    revision: cf7f7ab395739498e2f2e6b29ac152448f6d2dff
    ref: refs/heads/main
    verified_at: '2026-11-21T23:10:27Z'
  candidate:
    branch: fix/studio-chatgpt-callback
    revision: 32b305c66bbcfd602e149fca3e3d0a56f1e0f1a1
    pull_request:
      provider: github
      id: egohygiene/mindgarden#175
      url: https://github.com/egohygiene/mindgarden/pull/175
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-21T23:10:27Z'
    default_branch_revision: cf7f7ab395739498e2f2e6b29ac152448f6d2dff
    issue_state: open
    pull_request_state: draft
    notes: '#176 and #177 merged in dependency order. #13 is closed. #175 merges the callback implementation with the
      latest handoff and coverage.'
  parallel_changes: []
review:
  status: partial
  reviewed_at: '2026-11-21T23:10:27Z'
  reviewed_by: codex
  evidence:
  - command: PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_routing tests.test_routing_dispositions tests.test_routing_incoming
      tests.test_routing_lifecycle tests.test_routing_transfers tests.test_reference_repairs -q
    outcome: passed
    observed_at: '2026-11-21T20:17:55Z'
    notes: 43 tests passed on each of Python 3.12.14 and 3.13.5, zero skips.
  - command: PYTHONPATH=src python -m unittest tests.test_extraction tests.test_ollama_extraction tests.test_mixed_curation
      tests.test_archive_diagrams experiments.ollama_extraction.test_evaluate tests.test_insights -q
    outcome: passed
    observed_at: '2026-11-21T20:17:55Z'
    notes: 24 tests passed on each Python, including replay of the observed rejection and nine public insights cases.
  - command: python scripts/release_journey_demo.py --workspace <fresh> --report <file> --require-source && python scripts/pipeline_completion_demo.py
      --workspace <fresh> --report <file> --require-source
    outcome: passed
    observed_at: '2026-11-21T20:17:55Z'
    notes: Clean archived main. Release journey SHA-256 0d31d9d3841f5c394bb23776c97f0d211907bcf8361f5ad4978156a9650f7600.
      Completion proof SHA-256 66377ee3762d0a46a338490e7cf8282c1e73de3acf9ba5baf37e1cd5bdd8b09f.
  - command: python experiments/ollama_extraction/evaluate.py --model gemma3:1b --endpoint http://127.0.0.1:<port> --live
      --include-output --timeout-seconds 90
    outcome: failed
    observed_at: '2026-11-21T20:17:55Z'
    notes: Ollama 0.40.17 returned schema-valid synthetic output with unresolved endpoints. Application exited 1 and created
      no candidates. The evaluation completed with a recorded rejection.
  - command: PYTHONPATH=src python -m unittest tests.test_source_compaction tests.test_compaction_refresh tests.test_output_scope
      -q
    outcome: passed
    observed_at: '2026-11-21T20:20:13Z'
    notes: 25 focused cases passed on each supported Python. The archived main run failed five assertions across three
      red cases. The existing 13-node bundle retained its original plan digest, hashes and modification times.
  - command: python3 -S scripts/compaction_demo.py --require-source --workspace <fresh> --report <file>
    outcome: passed
    observed_at: '2026-11-21T20:20:13Z'
    notes: Eight checks from the existing synthetic demo passed. Complete context was 4,001 of 8,192 bytes.
  - command: npm --prefix web run build && npm --prefix web test
    outcome: passed
    observed_at: '2026-11-21T23:10:27Z'
    notes: Reconciled checkout. Production build and eight frontend tests passed. The existing garden-cover.webp runtime
      resolution warning remains.
  environment_limitations:
  - 'The owner reported successful Mac Studio sign-in. Individual model discovery and a completed live turn remain separate
    #163 acceptance.'
  - The native Ollama evaluation covers one synthetic input. Wider model accuracy remains unmeasured.
  - The approved real archive, dedicated production mount, reusable Relay action and private retention pilot remain open.
  - The original heads passed hosted Test and release preparation. The reconciliation has its own automatic checks.
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

Land the reviewed local checkpoints and qualify the existing Studio and archive journeys.

## Resume protocol

Refresh live GitHub state and use current main after the merge. Check the [coverage ledger](docs/open-issue-coverage.md) for the remaining acceptance owners.

## Current objective and success conditions

Qualify the existing workflows before expanding product scope. Record what passed in Studio, what requires the approved private pilot and which organization decisions still gate completion.

## State snapshot

#176 merged as `875e73f` and closed #13. #177 merged as `cf7f7ab`. #175 reconciles its callback fix with that main tree and closes #174 on merge.

## Completed and material changes

One local Ollama evaluation completed and the application correctly rejected its invalid proposal. Private routing replay preserves the canonical home and exact citation. Saved compaction checks are read-only and enforce complete output limits. The callback distinguishes receipt, verification and completion. The owner reported successful Mac browser sign-in.

## Validation and review evidence

All five hosted checks passed for each of the three original PR heads. Each merge of #176 and #177 preserved its exact qualified tree. The reconciled Studio checkout passed the production web build, eight frontend tests and the pinned handoff checks.

## Blockers, risks, unknowns, and deferred work

The ChatGPT model catalog failure still lacks an exact status. Qualify that and one approved fictional turn under #163. Native Codex runtime is separate. Existing portal, real archive and governed privacy checks remain open. Release work stays deferred.

## Next dependency-ready work

Observe the Models card on the owner Mac. Verify the current catalog and approve one fictional request. Independently replay the reviewed brief under #162 and the January booklet under #165. The selected Drive folder proof follows owner approval under #87.

## Parallel changes and reconciliation

#177 was retargeted to main after its parent #176 landed. #175 was reconciled afterward. The overlap was limited to this handoff and the coverage ledger.

## Privacy and redaction

Use public or synthetic evidence. Keep callback values, private source data and credentials in the authorized local environment.

## Handoff update protocol

Record exact branch, PR, head, checks and the next operation. Refresh live state before acting.

## Compaction and supersession

Earlier qualification receipts remain in the [coverage ledger](docs/open-issue-coverage.md). The [consumer journey](docs/consumer-journey.md) records accepted Empathy evidence.
