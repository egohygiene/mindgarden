---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-21T20:20:13Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: Review the oldest backlog checkpoint and make saved compaction proofs safe to check.
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
  objective: Review the oldest backlog checkpoint and make saved compaction proofs safe to check.
  success_conditions:
  - Complete bounded synthetic checkpoints with exact evidence and explicit review authority.
  - Preserve Python/v0, original sources, live scope enforcement and proposed ADR status.
  - Keep real inputs/credentials outside the repository and report unavailable live/private contracts honestly.
  active_issue:
    provider: github
    id: egohygiene/mindgarden#46
    url: https://github.com/egohygiene/mindgarden/issues/46
  next:
    kind: action
    id: review-curation-then-compaction
    description: 'Review #176 first, then review #177 and its red/green regression and legacy replay evidence.'
    readiness: ready
    references:
    - docs/extraction-producers.md
    - docs/compaction-retention.md
    depends_on: []
state:
  base:
    revision: f348a8d38b44a265c46f7f98db10cfc662d8a20c
    ref: refs/heads/test/curation-routing-backlog
    verified_at: '2026-11-21T20:20:13Z'
  candidate:
    branch: fix/compaction-proof-audit
    revision: 85e06c5161dc622aef884ffd72846530e33d5261
    pull_request:
      provider: github
      id: egohygiene/mindgarden#177
      url: https://github.com/egohygiene/mindgarden/pull/177
    handoff_state: ready-for-review
  live:
    status: verified
    observed_at: '2026-11-21T20:20:13Z'
    default_branch_revision: 00ab34e873601239ce62c1e245c076987ae48f4a
    issue_state: open
    pull_request_state: draft
    notes: '#1 and #2 closed. GitHub showed 35 open issues. Draft #177 stacks on #176. Studio #175 is independent.'
  parallel_changes: []
review:
  status: partial
  reviewed_at: '2026-11-21T20:20:13Z'
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
  environment_limitations:
  - The native result covers one synthetic input. Wider model accuracy remains unmeasured.
  - The approved real legacy archive, dedicated production mount and reusable Relay action remain open.
  - 'Hosted checks run separately. Studio #175 still needs the owner Mac sign-in rerun.'
  - 'The #46 proof uses synthetic local bundles. The approved private retention pilot is pending.'
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

Review the oldest backlog checkpoint and make saved compaction proofs safe to check.

## Resume protocol

Refresh live GitHub state and review [draft #176](https://github.com/egohygiene/mindgarden/pull/176). Continue with [draft #177](https://github.com/egohygiene/mindgarden/pull/177). Use the [coverage ledger](docs/open-issue-coverage.md) for issue ownership.

## Current objective and success conditions

Keep fulfilled portfolio criteria closed and remaining work visible. Record the local producer result and verify one canonical home after reviewed routing and replay. Verify saved compaction proofs without creating files.

## State snapshot

Main `00ab34e`. GitHub showed 35 open issues and 51 ledger rows. #1 and #2 closed against their original criteria. #5 remains the execution umbrella. #177 targets #176 and the combined checkout is `fix/compaction-proof-audit`.

## Completed and material changes

Draft #176, implementation `976d1af`, records the native local Ollama evaluation for #13 and the composed private routing replay for #14. The accepted Empathy site and unresolved dedicated route are documented. #5, #13, #14, #18, #20 and #21 now link current acceptance evidence. Draft #177, implementation `85e06c5`, fixes read-only verification and byte accounting for #46.

## Validation and review evidence

Each supported Python passed 43 routing and 24 extraction, curation and insight tests. Both synthetic journeys passed from archived main. The one native model response matched JSON Schema and the application rejected invalid endpoints. Compaction regressions and legacy bundle replay passed. No private input was processed.

## Blockers, risks, unknowns, and deferred work

#14 retains policy-changing transfers and wider recovery. #20 retains owner-approved archive selection, conformance and dedicated route. #21 awaits a reviewed declassification contract. #46 retains the approved private pilot and broader retention acceptance. Release work stays deferred.

## Next dependency-ready work

Review #176 and its linked synthetic evidence. Merge closes #13. Then retarget #177 to updated main for review. Keep #14, #20 and #46 open for remaining scope.

## Parallel changes and reconciliation

Draft #176 targets main and #177 stacks on #176. Draft #175 independently addresses the Studio callback and also updates continuity and the coverage ledger. Reconcile those documents when both drafts land.

## Privacy and redaction

Use public or synthetic evidence. No archive or account authorization, private content, or credential belongs in Git.

## Handoff update protocol

Record the exact branch, issue, implementation commit, checks and next action. Refresh live state before acting.

## Compaction and supersession

The [consumer journey](docs/consumer-journey.md) updates earlier rehearsal-only Empathy observations. Earlier qualification receipts remain linked in the coverage ledger.
