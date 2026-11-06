# Synthetic provider continuity inventory

All content is authored synthetic evidence. No provider account, model call,
private archive or proprietary history export is used.

| Canonical record | Role and review/lifecycle state |
| --- | --- |
| `preferences` | Approved procedure: plain language and exact citations |
| `project-goal` | Approved weekly synthetic project review goal |
| `portable-brief` | Approved artifact summarizing the immutable normalized source |
| `ledger-decision` | Approved original decision with rationale and a hosted alternative |
| `review-correction` | Approved correction with exact historical claim references and previous-version provenance |
| `daily-review-claim` | Approved, deprecated earlier claim; retained as history, absent from current ranking |
| `weekly-review-claim` | Approved current claim explicitly superseding the earlier claim |
| `brief-supports-project` | Approved typed support relationship |
| Normalized/captured source and provenance | Immutable original/normalized bytes; source review remains unreviewed |

The fixture also contains an unreviewed proposal and an unselected garden. Those
records are not enumerated by scoped outputs or the evidence report. Altering the
unselected garden cannot alter recovered context. No denied count is emitted.

[The fixture builder](../../provider_continuity_fixture.py) creates the canonical
records, metadata, original vault and explicit session using existing services.
[The proof report](expected-proof.json) records selected immutable identities,
review state, policy, adapter versions, exact evidence and recovery checks.
Source normalization preserves supplied BOM/CRLF bytes in the original and saves
the deterministic normalized result separately. Authored correction provenance
binds the deprecated claim and its rationale without rewriting it.

The two [local adapters](adapters/) use distinguishable JSON and tool-message
envelopes. They transport the same structured evidence; they do not emulate model
understanding. The first adapter and its temporary state are actually removed
before the second reads any context. These fixtures define no new core provider
or assistant-memory contract.
