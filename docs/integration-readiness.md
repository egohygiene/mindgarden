# Integration readiness

The first working session should take a small Chrome bookmark export from
capture to a reviewed private result. Drive and Codex can follow against the
same garden. This sequence is based on the 30 open issues observed on
2026-11-20. The [coverage ledger](open-issue-coverage.md) retains their full
requirements and links to prior implementation.

## Work in order of what a first user needs

| Workstream | Existing issues | Finish condition |
| --- | --- | --- |
| Local bookmark, Drive and assistant pilot | #48, #87, #89 | Review one bounded Chrome batch, then separately verify an explicitly selected Drive collection and the authorized Codex workflow. Akashic intake and recurring capture have their own owner contracts. |
| Knowledge and evidence reliability | #13, #14, #20, #35, #37, #45, #46 | Collect the remaining model, policy, recovery or consumer evidence listed by each issue. Pilot evidence can support #37/#46. Empathy and the legacy archive in #20 require their own proof. |
| Scope and decisions | #29, #31, #41, #42 | Verify accepted classification and runtime controls, historical authority and maintainer dispositions. These gate the corresponding wider product claims. |
| Public and hosted consumers | #17, #18, #21, #43, #44, #47 | Finish public browsing and accessibility, the Relay portal workflow, reviewable infographic and Decisions interfaces, and the governed API/web/worker slice. |
| Deferred and optional | #19, #27, #34, #88, #91 | Record an explicit decision for releases, the OpenViking evaluation, installable context packages and RDF after their owners select work. |
| Umbrellas | #1, #2, #5, #40, #86 | Reconcile the aggregate outcome when their child work and integration evidence are ready. |

The accepted engine work in #15, #16, #32 and #90 is already on main. Draft
[#155](https://github.com/egohygiene/mindgarden/pull/155) records the prior
evidence and passed its automatic Test and preparation checks. The integration
proofs stack on that draft so the combined checkout keeps its handoff.

## First session

1. Run the fictional garden or the bookmark rehearsal before selecting any
   personal input. Choose a private workspace and separate locations for the
   garden, source vault and generated outputs. The
   [private pilot guide](private-pilot.md) documents the existing preflight.
2. Capture a small local Chrome selection using the supported Mindcap input.
   Review the proposed actions and inspect the cleaned browser import in a
   private output directory. Keep the original as recovery evidence. See the
   [bookmark workflow](bookmark-cleanup.md).
3. Add a Drive collection when the operator chooses the files and configures
   local OAuth. Review the first capture and refresh before treating a summary
   as current. See the [selected Drive workflow](drive-capture.md).
4. Use the local scoped research commands or connect the selected Codex runtime
   with an explicit session. The [research workflow](scoped-research.md) covers
   bounded read plans, exact citations and live authority checks.
5. Review a first output and its sources, then pick the next unmet acceptance
   requirement from the ledger. Once the backlog is dispositioned, do the
   requested separate audit, cleanup and lint/test pass.

## Dependencies confirmed for this batch

- #14 already implements reviewed private transitions. The new logical rename
  case verifies distinct identity, one searchable home, exact evidence, unchanged
  originals and repeat safety. Public and policy-changing transitions retain
  their #29 and proposed ADR-0022 dependencies.
- Mindcap #35 owns the recurring delta contract. Akashic #41 and #173–#176 own
  public identity, reviewed intake and publication. The first rehearsal uses
  the currently supported captured package and private output.
- Relay #40 still owns the reusable portal action needed by #18. The existing
  local composition tool and a published integrated portal have distinct
  acceptance tests.
- #34 has a pinned native trial that reached an explicit startup blocker and an
  offline projection proof. The latest reviewed release notes do not establish
  successful no-model startup or restricted-state containment. A deferment or
  further lab trial is a separate decision.

References from the integration discussion are grouped in
[#86](https://github.com/egohygiene/mindgarden/issues/86). The agent, acquisition,
resource and policy comparisons are assigned to their owning repositories.
