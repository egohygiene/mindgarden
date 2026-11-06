# Draft local scope and explicit bindings

This checkpoint implements a **local single-user reference policy** under #29.
It does not replace or claim conformance with unavailable Hygiene #39/#40
information-flow and isolation-assurance contracts. Aether/Realm session and
runtime integration remain separate work.

## Independent dimensions

`mindgarden.scope/v1` separates visibility (`public`, `organization`, `personal`,
`restricted`), persistence (`git-tracked`, `machine-local`, `encrypted-vault`),
execution (`networked`, `controlled-import`, `offline`), publication authority
(`publishable`, `review-required`, `never-exportable`) and a pinned policy
reference. Existing record lifecycle, epistemic confidence, authorship and review
remain separate. Optional `scope` fields extend the existing v1 records.

The legacy record visibility is a compatibility representation: public maps to
public, internal to organization, and private needs an explicit personal or
restricted mapping. A supplied scope must agree. Missing legacy classification
is supplied only by an explicit garden binding, never by crawling or guessing.
Bindings and canonical garden scope must agree when both are present.

The supported policy ID and content-bound revision are exposed by
`mindgarden.domain.scope.POLICY_REFERENCE`. Unknown or conflicting revisions
fail closed. This policy remains a proposed repository-local implementation.

## Inheritance and declassification

Public inputs do not weaken personal or organization restrictions. Personal and
organization inputs are independent domains; combining them requires restricted
output. Publication, execution and persistence restrictions join conservatively.
Restricted output requires encrypted-vault persistence, offline execution and
never-exportable publication. These are **requirements**, not proof of actual
encryption, network isolation or authorized confidential processing.

A local unencrypted filesystem adapter cannot satisfy an encryption requirement.
A lower-sensitivity destination requires a distinct reviewed derivative and
retains private source mappings privately; it never changes source classification.
No implicit declassification, public backlink or public private-source identifier
is authorized by an approved knowledge review alone.

## Explicit local bindings

`mindgarden.local-bindings/v1` has `gardens`, `vaults`, and `revoked_sessions`.
Each garden declares its stable `id`, absolute machine-local `root`, and scope.
Each vault declares its logical `id`, `adapter: filesystem`, and local `root`.
These descriptors belong outside portable records and Git-tracked configuration.
They contain no content, credentials or publication authorization.

Roots must be explicit, non-overlapping, non-symlink directories with matching
observed garden identities. A missing vault root can be planned for initialization;
a missing garden cannot be silently discovered elsewhere. Registration does not
copy or modify canonical content. `garden_fingerprint` is portable and excludes
declared generated roots while binding all canonical files.

This is the bounded #30 prerequisite, not the full registry lifecycle, overlay
composition, platform matrix or encrypted storage implementation. Linux synthetic
fixtures are tested; macOS and Windows behavior is not claimed.

## Session contract boundary

`mindgarden.session/v1` declares readable garden revisions, a nullable single
writable target, allowed visibility/review states, execution and publication
limits, projections, budgets, a policy revision and expiration. Revocations live
in machine-local state. Session syntax is defined here; complete query-path,
expiry and revocation enforcement is the separate #31 checkpoint. No session
can grant authority beyond the caller's explicitly supplied configuration.

## Shared policy integration checkpoint

`mindgarden policy inspect` describes the supported local policy and explicitly
unavailable organization/runtime/declassification integration. `policy evaluate
--input REQUEST` validates `scope-request/v1` and emits `scope-decision/v1` with
stable reason codes, joined scope requirements, an input digest and
`assurance: not-asserted`. It is read-only control data, not a new garden/session
model or a grant of runtime authority.

Query output joins and projection destinations consume the same decision service.
Visibility, persistence, execution, publication and knowledge review remain
independent. Ordinary private storage can retain stricter publication restrictions;
public output requires an independent publishable ceiling. Human review alone
cannot declassify a source. A reviewed declassification request remains explicitly
unavailable until the owning policy/runtime contract exists.

The [storage sprint](private-storage-sprint.md) records the inspected owner state
and dependency correction. Local policy ID/revision is unchanged: this exposes
and shares the existing semantics rather than silently adopting an upstream
policy or rewriting existing v1 classifications. Existing binding/session and
v0 compatibility guidance above still applies.

## Private assets and extension storage

The optional `assets` session projection and explicit source review-state grants
authorize [private inventory](mixed-source-vault.md). It inherits sensitivity and
all live-authority/output budgets; public requests are denied. Existing default
session grants and hashes stay unchanged unless this projection is requested.

Local vault bindings accept an explicit adapter identifier. The default runtime
installs only filesystem; callers must explicitly register other factories. A
control root is machine-local, and unsupported/removed adapters never fall back.
Capability booleans cannot authorize encryption, restricted execution or network
access. Provider credentials remain outside portable records.
