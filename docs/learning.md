# Private learning projections

`mindgarden learning` reads an explicit authored plan over reviewed canonical
knowledge and claims. It creates disposable factual/cloze cards, summaries,
source trails, a private study document and a due-item digest. Neither grading
nor exporting changes canonical knowledge or originals. No model is called.

Preview before writing:

```sh
mindgarden learning --local-config bindings.json --scope session.json \
  --input learning-plan.json
mindgarden learning --local-config bindings.json --scope session.json \
  --input learning-plan.json --apply --plan-digest PREVIEW_DIGEST \
  --output-directory /private/study/source-boundaries
```

Use the actual preview digest. The output directory must satisfy the existing
private-output policy, outside repository worktrees. Apply rechecks sources,
session authority and authored inputs; changed inputs invalidate the plan.
Outputs are immutable bundles, with recovery through verification/retry rather
than overwriting earlier exports.

The `contracts/v1/learning-*.schema.json` contracts separate candidates, factual
or single-answer `{{c1::answer}}` cards, summaries, decks, private grading events,
schedules and projections. See the committed synthetic
[authored plan](../tests/fixtures/learning/authored-plan.json). Review authority
is explicitly human; model-proposed material can be represented but never
self-approved. Draft, rejected, suspended and superseded material remains in the
JSON inspection trail, outside the study/due views. Low-confidence, uncertain,
inferred or contradictory evidence requires a qualified answer; source caveats,
claim relationships and exact locators remain attached. Quoted answers must
occur in the selected reviewed content. The rubric records what review expects;
the engine does not grade free-text answers or verify the truth of a paraphrase.

Review history is personal, machine-local and never exportable. Pass a history
with `--events`; append one explicitly authored event into a **new** bundle with
`--review-event`. Each event names the item revision, scheduler/version, grade,
reviewer, timestamp and previous event. Source revisions participate in the
item revision even when the answer text stays unchanged. Old events remain
inspectable but do not schedule edited items. Events after an explicit `--as-of`
view are retained without affecting that view; session expiry uses the real
clock and cannot be extended with this option.

`fixed-intervals` versions `1.0.0` and `2.0.0` are replaceable deterministic
examples, not a claim of learning efficacy or a standardized spaced-repetition
algorithm. Changing the requested scheduler/version recomputes the view while
preserving historical events and their original algorithm. Unsupported versions
fail with a stable diagnostic. Only approved cards are scheduled; summaries
appear in the study document and digest instead.

Import an exported `learning-projection.json` with `--import-projection`, plus
its separate history if desired. The engine resolves current canonical sources
and recomputes schedules; imported schedules are never authority. Source/item
changes require a newly authored/reviewed plan. JSON is the round-trip contract;
Markdown and HTML are display projections. The total bundle obeys both the
explicit plan and session byte budgets and fails rather than silently dropping
items or citations.

The static HTML has native keyboard-operated answer disclosure, source details,
semantic landmarks, narrow-screen and zoom support, escaped text and no scripts,
remote images or model service. `python3 scripts/learning_browser_check.py
--report tests/fixtures/learning/observed-browser.json` checks Chromium at
320/1280 pixels, 200% zoom and reduced motion. This is a static adapter proof,
not the full #17 application, screen-reader certification or Realm runtime
assurance. Richer hosted interfaces and optional proposal generators remain later integrations.
Notifications, hosted accounts and sync stay outside this issue’s core scope;
they are not added acceptance gates for the authored local workflow.


## Bounded due-card review

Use `--due-only` to render only approved cards due at the explicit `--as-of`
view boundary. `--review-limit` defaults to 20 (maximum 100), and
`--review-offset` selects a later page of that exact view. Unknown/invalid queue
options fail before source selection. Due dates sort by actual time instants,
including explicit offsets, before pagination.

```bash
mindgarden learning --local-config "/private/bindings.json" \
  --scope "/private/session.json" --input "/private/reviewed-deck.json" \
  --due-only --review-limit 20 --review-offset 0
```

Review the preview and apply with the same flags, a new private output directory
and the exact digest. The view/digest binds its limit and offset. The additional
`study-queue.json` gives exact item revisions, due times, scheduling reasons and
transparent selected/remaining counts within the explicit approved deck. HTML
and Markdown render only those cards, with answer disclosure, qualifications and
due states. Rejected/suspended cards and summaries are not scheduled as due cards.
An empty queue has a useful empty state. All bytes count toward existing budgets.
Outputs cannot overlap canonical storage or declared source vaults.

`learning-projection.json` still preserves the **complete** selected deck and
provenance for import; the smaller display is not canonical deletion. Review a
card and author its ordinary `learning-review-event/v1` using the queue's exact
`item_revision`, grade, operator, timestamp, scheduler/version and previous-event
identity. Supply `--review-event` and existing `--events` to preview/review a new
immutable export. Its grade advances only that exact card. An edited/source-changed
card keeps the old event as historical and needs current review. Changing history
or `as_of` changes the view; re-plan before paging/applying it.

Actual optional browser checks cover both full and due views:

```bash
python scripts/learning_browser_check.py --due-only \
  --axe-script .cache/next-sprint/axe/node_modules/axe-core/axe.min.js \
  --report /tmp/new-learning-due-browser.json
```

Omit `--due-only` for the full deck. The prepared optional axe script is pinned
at 4.10.3; no tool is downloaded during scoped generation. The
[due-view receipt](evidence/learning-due-browser.json) and
[full-view receipt](evidence/learning-full-browser.json) record Chromium
151.0.7922.173 / Playwright 1.62.0, 320/1280 pixels, native keyboard disclosure,
200% zoom, reduced motion and semantic landmarks. WCAG A/AA automated tag sets
report **zero violations and zero incomplete findings** for these static views.
Page networking is offline; no model, account or private data is used.
These are bounded browser/semantics proofs, not screen-reader certification or
acceptance of the broader hosted #17/#47 product.

## Listed #28 acceptance

| Criteria in issue order | Evidence |
| --- | --- |
| Versioned candidates/summaries/cards/events/schedules (1) | Existing closed learning schemas plus private queue schema |
| Reviewed sources, exact claim provenance and private history (2–4) | Shared scoped selection, source digests/qualifications and negative fixtures |
| Reject/edit/suspend/regenerate/remove without canonical writes (5) | Lifecycle/source-revision tests, immutable exports and complete JSON round trip |
| Replaceable explainable scheduling and qualified answers (6–7) | Versioned scheduler port, history/upgrade/staleness/contradiction cases |
| Deterministic exports and accessible web states (8–9) | JSON/Markdown goldens, due/empty states and actual full/due browser receipts |
| Useful authored no-model mode (10) | Factual/cloze/summary fixtures, missing-model/empty mode and CLI grade/import round trip |

The listed learning-projection scope is complete. Dependency correction: the
existing renderer/application boundary supports this private static study adapter;
a finished public garden or hosted account is not required to render accessible
learning states. Notifications, email, browser capture and hosted sync are explicit
non-goals in #28. The full #17 experience retains its own acceptance criteria.
