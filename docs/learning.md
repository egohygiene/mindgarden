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
assurance. Review-history editing/sync, automated proposal generation, notification
scheduling and richer hosted study interfaces remain parent scope.
