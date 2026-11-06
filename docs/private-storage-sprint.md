# Private policy and storage sprint — 2026-11-06

The maintainer authorized #29 → #31 → #30 → #35 → #45 as additional small draft
checkpoints on top of #79. Main remains `30a2966`; #74–#79 remain draft/unmerged.
The previous combined base is `8e15314cb3419b1defaf1866aa6450d6703abb09`, whose
final automatic Test run 42177086645 passed. No merge or ADR approval is inferred.

## Dependencies and bounded scope

#29 supplies the shared local decision contract before #31 consumes it across
outputs. #30 reuses #31's owned cache inventory, without making native Windows
assurance a prerequisite for the Linux baseline. #35 consumes #11's source adapter
boundary and #29 policy; PDF acquisition, optional parser tools and model calls
remain separate. #45 consumes the PDF/media evidence and registry bindings for
mixed-source recovery. Full encrypted/runtime/provider proofs are later integration
requirements, not claims supplied by a filesystem flag.

Hygiene #39/#40 remain open with no comments. The inspected Hygiene main is
`92195e49b50778517ef670a7ec97c922dbdf9cec`; no normative classification/assurance
artifact was found under the referenced schema/spec/document paths. The existing
local policy is therefore still a proposed reference implementation, not adopted
organization policy. Realm #25 is an open program; its handoff directs current
remaining acceptance to #60, including encrypted-vault/key-broker and confidential
runtime proofs. Unknown policy and unproved restricted runtime fail closed.

A newly supplied ordinary or synthetic PDF may have an explicit digest-bound
initial classification review; a previously restricted source is never silently
reclassified. Default confidential processing must remain unavailable until its
external contracts and actual runtime/storage evidence exist. Real personal,
employment, business and provider data are out of scope.

| Issue | Checkpoint | Remaining acceptance | Draft / branch | Verification | Next action |
| --- | --- | --- | --- | --- | --- |
| #29 | Shared decision schema/API/CLI over existing scope model; policy adoption gaps explicit | Accepted Hygiene/Realm integration and declassification protocol | [#80](https://github.com/egohygiene/mindgarden/pull/80); `feature/29-policy-integration` over #79; `9fc0c9b` | 25 policy/scoped/contracts on 3.12; 5 policy on 3.13 | Review #80; #31 follows |
| #31 | Output-wide authorization/budgets/diagnostics and owned cache inventories | External assurance and broader runtime/provider matrices | [#81](https://github.com/egohygiene/mindgarden/pull/81); `feature/31-output-scope-enforcement` over #80; `1bbb38f` | 25 output/scoped/contracts on 3.12; 5 output on 3.13 | Review #81; #30 follows |
| #30 | Platform capability matrix, registry recovery and reversible owned cache handling | Native platform/ACL and encrypted host acceptance | [#82](https://github.com/egohygiene/mindgarden/pull/82); `feature/30-registry-cache-recovery` over #81; `9b8e008` | 39 registry/cache/contracts on 3.12; 5 cache recovery on 3.13 | Review #82; #35 follows |
| #35 | Versioned document bundle, optional local PDF reader and exact page/span evidence | Restricted runtime, OCR/office adapters and real consumer proof | [#83](https://github.com/egohygiene/mindgarden/pull/83); `feature/35-local-document-adapter` over #82; `e966e3e` | 20 PDF/adapter/contracts on 3.12; 8 PDF on 3.13; real Poppler 25.03.0 six-state proof | Review #83; #45 follows |
| #45 | Mixed archive/document/media inventory, triage and recovery proof | Encrypted/provider/platform integration and destructive GC | Pending | Pending | Restore/relocate mixed synthetic sources and resolve exact evidence |

## Review and recovery

Every checkpoint records the functional source, branch/base/PR, exact commands and
results, blockers and next action here and in CONTINUITY.md. Later drafts name the
preceding branch as their base. Keep all drafts unmerged for maintainer review,
retain every parent criterion, and distinguish implementation, testing and owner
acceptance. The final branch will preserve the complete combined checkout.
