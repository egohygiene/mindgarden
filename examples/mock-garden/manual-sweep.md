# Fictional garden sweep

ChatGPT drafted this proposal for a human reviewer from the fictional garden.
The [curation plan](manual-sweep.curation.json) records agent authorship and
leaves the procedure and both links unreviewed.

The keyboard navigation demonstration is a proposed career experiment. Example
Studio's brief names May 15, 2026 for a client delivery, while the conversation
names May 22. The agreement is missing, and the selected evidence leaves open
whether the demonstration and client delivery have any shared deadline.

The proposal gives the reviewer two next actions. Collect a short keyboard
walkthrough for the portfolio demonstration. Find the client agreement and
compare it with the brief and conversation. Keep both dates visible while that
agreement is unavailable. The two proposed `references` links give a reader
separate paths into the career note and the disputed delivery conversation.

| Selected evidence | Exact locator | What it supports |
| --- | --- | --- |
| [Career notes](seed/career.md#L5-L8) | `lines:5-8` | The proposed demonstration and its connection to the studio |
| [Business brief](seed/business.md#L5-L8) | `lines:5-8` | The brief's May 15 date and missing agreement |
| [Client conversation](seed/conversation.md#L5-L7) | `lines:5-7` | The reported May 22 and May 15 dates and the need to check the agreement |

The plan pins each normalized source ID, artifact revision, line selector and
selected-content checksum. Its proposed links pin the current reviewed note
revisions. The existing sources and notes retain their authorship and review
states. Both dates remain unresolved.

## Preview in a fictional workspace

Seed a new workspace with the [fictional garden launcher](README.md). From the
repository root, set `workspace` to its path and preview the curation plan:

```sh
workspace=/var/tmp/new-fictional-mindgarden
PYTHONPATH=src python -m mindgarden gardenize \
  --local-config "$workspace/clean-bindings.json" \
  --plan examples/mock-garden/manual-sweep.curation.json
```

The preview checks exact evidence and represented note revisions and reports
the workspace's `plan_sha256`. For the three line excerpts, the
`source-evidence` research operation uses the plan's citations and the fictional
workspace's `mock-session.json` source grants. The existing reviewed notes also
authorize their whole artifact citations through `evidence`.

A human reviewer can decide whether the checklist and its two link targets are
useful. Approval would require an explicit human review and a fresh preview of
that edited plan. This example stops at preview.
