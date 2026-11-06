---
schema_version: aether.repository-continuity/v1
repository:
  id: egohygiene/mindgarden
  visibility: public
  default_branch: main
  continuity_path: CONTINUITY.md
document:
  status: active
  updated_at: '2026-11-06T21:51:25Z'
  max_bytes: 16384
  max_lines: 240
  stale_reason: null
  superseded_by: null
scope:
  purpose: Preserve bounded provider, consumer and release preparation evidence without claiming unavailable pilot
    or publication acceptance.
  includes:
  - provider portability, release tooling, synthetic journey and acceptance gates
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
  - ARCHITECTURE.md
  - SYSTEM.md
  - ROADMAP.md
  - docs/open-issue-coverage.md
  - docs/local-registry.md
  - docs/decisions/README.md
  - docs/garden-experience-milestone.md
  - docs/merged-experience-checkpoints.md
  - docs/source-workflow-sprint.md
  - docs/private-storage-sprint.md
  - docs/merged-pipeline-storage-checkpoints.md
  - docs/deferred-context-package-roadmap.md
  - docs/registry-native-platforms.md
  - docs/release-checkpoints.md
  - docs/provider-switch-proof.md
work:
  objective: Prove provider-switch recovery through two removable local adapter fixtures over existing scoped CLI
    contracts.
  success_conditions:
  - Recover preferences, project goal, artifact evidence, decision and correction history after removing the first
    provider and caches.
  - Preserve canonical IDs/digests/review/sensitivity and deny out-of-scope or unreviewed history.
  - Keep all external pilot/publication gates explicit and preserve the dependency-aware release stack.
  active_issue:
    provider: github
    id: egohygiene/mindgarden#51
    url: https://github.com/egohygiene/mindgarden/issues/51
  next:
    kind: action
    id: release-convention-preparation
    description: 'Finish full compatibility and isolated-wheel provider proof, record/open the #51 draft, then implement
      #27''s pinned release declaration/version/artifact flow independently of the blocked full private pilot.'
    readiness: ready
    references:
    - docs/release-checkpoints.md
    depends_on: []
state:
  base:
    revision: 7938f573100658908acc0a039974e60f8cf888aa
    ref: refs/heads/feature/30-macos-registry-conformance
    verified_at: '2026-11-06T21:51:25Z'
  candidate:
    branch: feature/51-provider-switch-proof
    revision: null
    pull_request: null
    handoff_state: in-progress
  live:
    status: verified
    observed_at: '2026-11-06T21:51:25Z'
    default_branch_revision: d5edb13de1b65871ec85e7a25af035228a1d756d
    issue_state: open
    pull_request_state: not-applicable
    notes: 'Main remains d5edb13. PR #93 is draft and its exact head passed automatic Test run 42297920995. The
      requested #51/#27/#20/#19 parents are open; no releases exist. Current source changes have not yet been published
      as a PR.'
  parallel_changes:
  - provider: github
    id: egohygiene/mindgarden#93
    url: https://github.com/egohygiene/mindgarden/pull/93
review:
  status: partial
  reviewed_at: '2026-11-06T21:51:25Z'
  reviewed_by: codex
  evidence:
  - command: .venv/bin/python -m unittest tests.test_provider_continuity tests.test_v1_retrieval tests.test_scoped_retrieval
      tests.test_output_scope -q
    outcome: passed
    observed_at: '2026-11-06T21:51:25Z'
    notes: 30 passed in 26.305 seconds. Initial test-harness invocations with a nonexistent module/missing --pack
      were corrected; the final command passes.
  - command: .venv/bin/python -S scripts/provider_switch_demo.py --workspace .cache/provider-switch-second --require-source
      --report .cache/provider-switch-second.json
    outcome: passed
    observed_at: '2026-11-06T21:51:25Z'
    notes: Committed golden matches; first provider and scoped index are absent before beta recovery.
  - command: .venv/bin/python -m build --sdist --wheel --outdir .cache/dist
    outcome: passed
    observed_at: '2026-11-06T21:51:25Z'
    notes: Fresh distributions built from current source; no runtime dependencies added.
  - command: Full unittest suites on Python 3.12.14 and 3.13.5
    outcome: not-run
    observed_at: '2026-11-06T21:51:25Z'
    notes: Running; record actual final results before completing the checkpoint.
  environment_limitations:
  - Local fixture adapters prove structured context continuity, not live model behavior or proprietary history transfer.
  - 'Approved private pilot, actual Empathy consumption, protected OIDC/registry/signing evidence remain external;
    #19 is not publishable.'
  - 'ADRs and Hygiene release baseline remain proposed; deferred #86–#91 are not activated.'
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

The maintainer authorized #51, #27, #20 and conditional #19 after the prior storage batch. Preserve the Python engine and v0, source/review/publication boundaries and synthetic-only public fixtures. No proposed ADR or owner policy is self-ratified.

## Resume protocol

Read git status, live issues/PRs, README, AI_CONSTITUTION, ROADMAP, the coverage ledger, docs/release-checkpoints.md and the active checkpoint evidence. Use current implementation and pinned owner contracts; do not repeat merged checkpoints or activate deferred #86–#91.

## Current objective and success conditions

Prove provider-switch recovery through two removable local adapter fixtures over existing scoped CLI contracts. Recover preferences, project goal, artifact evidence, decision and correction history after removing the first provider and caches. Preserve canonical IDs/digests/review/sensitivity and deny out-of-scope or unreviewed history. Keep all external pilot/publication gates explicit and preserve the dependency-aware release stack.

## State snapshot

The candidate is feature/51-provider-switch-proof over draft #93 (7938f573100658908acc0a039974e60f8cf888aa), while main remains d5edb13de1b65871ec85e7a25af035228a1d756d. All 44 issues remain open. The next three release checkpoints are authorized but not yet implemented.

## Completed and material changes

The provider fixture removes alpha code/state and the scoped index, then reconstructs identical structured context through beta using ordinary index/context/graph/evidence commands. The scenario exposed and fixes approved historical dependency validation without returning inactive claims in current ranking. Denied/unreviewed historical nodes still remove derivatives. No new provider SDK or memory system is introduced.

## Validation and review evidence

The source demo matches the committed golden: 13178 bytes within 16384, six selected reviewed records, exact evidence and typed correction lineage preserved. Thirty focused provider/retrieval/scoped/output tests pass on Python 3.12. Fresh source/wheel builds pass. Full suites on both supported Pythons and the isolated installed-engine proof are in progress; no new CI pass is claimed before the draft exists.

## Blockers, risks, unknowns, and deferred work

An approved private archive/workspace, real Empathy #65 acceptance, compatible Aether #51/Relay #40 evidence and protected PyPI OIDC setup remain external gates. Hygiene release policy/ADR are still proposed despite closed delivery issues. EgoLint #29 remains partial. Native Windows/confidential/provider/real consumer gaps persist. No tag/package/site is published by local or PR checks.

## Next dependency-ready work

Finish full compatibility and isolated-wheel provider proof, record/open the #51 draft, then implement #27's pinned release declaration/version/artifact flow independently of the blocked full private pilot.

## Parallel changes and reconciliation

PR #93 is the unmerged checkout base; native support is not a semantic gate for the provider scenario. Keep every new checkpoint as an explicit draft stack, preserve a combined checkout, and leave merge/publication for their applicable authority. Reconcile CONTINUITY.md semantically after each checkpoint.

## Privacy and redaction

Only public metadata and authored synthetic fixtures are committed. Real Garden, business, music, credentials, private archive contents, private locations and personal circumstances stay outside this public repository. Source instructions remain untrusted evidence. No private consumer is discovered or modified.

## Handoff update protocol

After each checkpoint record branch/PR/full functional source, exact commands/results, blocked acceptance and one next action. Validate pinned owners, 12 headings, size limits, relative links and all 44 coverage rows. Distinguish draft, tested, reviewed, merged and accepted; keep publication receipts separate from local artifact conformance.

## Compaction and supersession

Keep under 16384 bytes/240 lines. This supersedes the prior native-registry next-action handoff. Durable native/storage merge evidence remains linked. The release checkpoint ledger owns this batch's stack and acceptance; deferred #86–#91 remain deferred.
