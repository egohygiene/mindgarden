# Portable private-garden milestone

This is the finite local checkpoint for #42, #10, #11, #12, #13, #15, #14,
#29, #31 and #45. Each parent keeps its original acceptance criteria. User
implementation authorization does not ratify proposed ADRs or authorize merging.

## Observed baseline

Base: `7ac577e385f0b2c26eff37bdfb10f3b550f29da1`. Python 3.12.14 passes 48
existing tests. Fresh source/wheel builds and clean installed-command/library
smoke checks pass. Normal `validate` rejects initialized v1 gardens because it
still expects `garden.yaml`. No open PR was observed before this milestone.
V1 schemas and lifecycle exist; general v1 validation/retrieval do not.

## Proposed dependency corrections

| Contract or proof | Required before | Later acceptance retained |
| --- | --- | --- |
| #42 ownership, identity and service decisions | New milestone boundaries | Human ratification and remaining architecture sequence |
| #29 scope/inheritance contract | Routing and scoped projection interfaces | Hygiene #39/#40 normative policy/assurance integration |
| #45 content reference and filesystem port | V1 source ingestion | Full audit, export, restore, relocation and adapter proofs |
| #30 explicit safe local root bindings | Resolving garden/vault identities | Registry lifecycle and private overlay composition |
| #11 normalization contract | Archive parsing | Mindcap #35 bookmark handoff and #48 integration |
| #13 authored curation plans | Archive-to-reviewed-knowledge proof | Optional model producer and wider curation proofs |
| #35 confidential document adapter | Full document/media acceptance | Not required to preserve opaque source bytes locally |

These corrections separate prerequisite contracts from later integration proofs;
they do not declare the corresponding parent issues complete. Existing accepted
v0/v1 behavior may advance independently of the broader #40/#41 program.
Unavailable contracts remain gaps, not substituted organization policy.

## Checkpoint stack

Each branch is based on the preceding unmerged checkpoint. Record actual PR
URLs, base/head commits, checks and combined checkout in CONTINUITY.md. A draft
PR is review material, not a merged or accepted result.

| Checkpoint | Branch suffix | Partial issues | Required evidence |
| --- | --- | --- | --- |
| P01 | 01-architecture | #42 | Ownership map, policy pin, proposed decisions, dependency corrections |
| P02 | 02-v1-validation | #10 | Normal CLI validates v1; version/schema/reference diagnostics |
| P03 | 03-provenance-privacy | #10 | Hash/path/publication negatives and v0 compatibility |
| P04 | 04-scope-bindings | #29, #30 | Scope compatibility, inheritance and explicit-root fixtures |
| P05 | 05-local-vault | #45 | Immutable identity, verification, capability and failure states |
| P06 | 06-source-adapters | #11 | Repeat import, stale-plan rejection and consumer extension adapter |
| P07 | 07-v1-retrieval | #12 | Reviewed search, typed graph/backlinks, bounded context and reproducibility |
| P08 | 08-curation | #13 | Authored dispositions, exact evidence and separate reviewer authority |
| P09 | 09-conversation-archives | #15 | Current-profile golden, overlap and malformed-package fixtures |
| P10 | 10-private-routing | #14 | Explained fallback, canonical home and journaled partial-failure recovery |
| P11 | 11-scoped-retrieval | #31 | Denied-content/metadata, budget, expiry and revocation adversaries |
| P12 | 12-vault-recovery | #45, #20 | Offline clean-checkout archive-to-context and relocation/restore proof |

## Contract and authority defaults

Keep the Python runtime dependency-free and preserve v0 schemas, CLI and library
behavior. Extend current v1 metadata/content records rather than adding another
garden model. Logical `{garden, id}`, immutable SHA-256 content and physical
bindings are distinct. Existing garden-relative source references remain valid.

Captured originals stay separate and immutable. Duplicate bytes can share
storage, but titles, similar text and matching filenames do not prove message
or conversation identity. Adapters consume captured bytes without network or
model calls. Explicit adapter registration must not require domain edits.

Human approval is explicit per candidate, with reviewer, review time and
rationale bound into the reviewed plan digest. Applying proposals alone never
promotes their review state. Original evidence is not overwritten or deleted.
Ambiguous routes stay private or unresolved; missing fallback never implies a
public target. Derived outputs inherit every contributing restriction.

Current archive checkpoint: separately tested v3.2.2/v3.2.3 single-unit ZIPs,
both full-source and compact summary/journey profiles. Archive envelopes use
schema 3.2 while preservation records use 2.0; Mindgarden contracts are separate.
Compact phases are summary-derived, not recovered dialogue. The inspected
private specifications and their personal routing profiles are not copied here.
Historical v1.2.1/v2.0.1, collections and multipart support remain compatibility
gaps until their exact contracts and fixtures are tested.

## Finite usable proof

A committed synthetic archive must yield a reviewed prompt-bank entry through an
authored curation plan. Search returns its exact source selector and hash; a
bounded context pack includes it. Relocation and restore retain that reference.
A clean combined checkout rebuilds projections with networking, Google and model
integrations disabled. Link the public-safe evidence to #20 while leaving its
real legacy archive, Empathy, publication and consumer acceptance open.

SQLite #32, federation, web/API productization, authentication, collaboration,
provider adapters, encrypted runtime assurance, destructive garbage collection,
PDF extraction and media triage remain outside this finite checkpoint.
