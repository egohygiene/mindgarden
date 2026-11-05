---
schema: egohygiene.architecture-decision/v1
id: ADR-0011
title: Build public discovery from reviewed scoped projections
status: proposed
date: "2026-11-05"
decision_scope: repository
visibility: public
owners:
- egohygiene/mindgarden
issue: https://github.com/egohygiene/mindgarden/issues/16
pull_request: https://github.com/egohygiene/mindgarden/pull/66
related:
- ADR-0007
- ADR-0009
- ADR-0010
supersedes: []
superseded_by: []
affected_repositories:
- egohygiene/mindgarden
affected_contracts: []
implementation_status: in_progress
evidence:
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/16
  description: Owning federation requirements; this proposal supports the bounded offline checkpoint.
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/31
  description: Authorization, sensitivity and denied-metadata invariants apply before projection.
- type: implementation
  url: https://github.com/egohygiene/mindgarden/pull/66
  description: Draft local checkpoint, functional commit 015f396; not merged or fully accepted.
exceptions: []
approval: null
---

# ADR-0011: Build public discovery from reviewed scoped projections

## Context

The portable private-workflow stack is merged. #16 needs a versioned public
discovery contract before registry/federation integration and replaceable query
stores consume it. Existing v1 projection profiles, approved knowledge, scope
policy and retrieval services supply the owning contracts. Organization policy,
remote consumers and the broader #42 architecture sequence remain separate.

## Decision

Propose checksum-bound public descriptor/index/graph/agent artifacts built from
the existing human-approved `mindgarden.projection/v1` federation profile and an
explicit public-only publication session. Pin the authorized view and each
selected knowledge/claim revision. Claims require their selected reviewed subject.
Visibility alone cannot override review-required or never-exportable policy;
filter those contributions before opening bodies or computing public revisions.

Public artifacts contain a whitelisted representation of the selected reviewed
records, exact logical citations and induced typed relationships. Their revision
is computed from that public representation. Do not export session/profile
digests, review identities/rationale, raw source bytes, host paths, vault bindings,
private registry identities or a fingerprint over excluded private content.

Preserve one canonical home. The proposed v1 route is `<base_uri>notes/<id>/`;
this checkpoint declares routes without claiming that a renderer serves them.
Canonical source/knowledge files remain owned by each consumer. Catalogs link to
canonical pages and do not copy note bodies or transfer ownership.

An explicit digest-bound plan creates an immutable filesystem export in a fresh
caller-selected directory, or verifies an identical existing one. The descriptor
is written last; consumers verify complete membership/checksums before exposing
any records. Never overwrite or silently repair a conflicting/incomplete export.
Supplied-directory catalog requests pin expected public revisions, isolate
unavailable/invalid inputs, and quarantine all conflicting homes/identities.
Acquisition, HTTP APIs, signing and private federation are unavailable capabilities.

## Alternatives considered and rejected

Exporting the full internal index would disclose control metadata and potentially
private identities through hashes. Advertising private bindings would cross the
storage boundary. Scraping or fetching live sites would mix acquisition with
interpretation. A catalog copying bodies would obscure ownership. Requiring Git,
a database or a model would remove the offline baseline. Treating a checksum or
an asserted review label as authenticated human authority would overstate trust.

## Consequences and tradeoffs

The proposed contract is additive and preserves the supported v0 interface. It
uses the local draft policy, not ratified confidential-runtime assurance. Incoming
unsigned descriptors are untrusted producer assertions: hashes detect drift,
not authenticity or factual correctness. Expected revisions are supplied by the
operator; no wall-clock freshness or network liveness is inferred. Budgets and
unsupported states are explicit. New versions use fresh export directories;
destructive retention and publication/hosting remain separate reviewed work.

Implementation is explicitly authorized as a bounded checkpoint. This ADR remains
proposed with null approval; code review or merging does not self-ratify it.

## Implementation and evidence links

See [the public projection contract and reproducer](../federation.md), the
[coverage ledger](../open-issue-coverage.md), and the dependent implementation
draft recorded in CONTINUITY.md. Synthetic fixtures cover exact citations,
denied metadata, stale plans/revisions, corrupt bundles, conflicting homes,
interrupted writes, source/wheel rebuilds and operation without integrations.

## Replacement or exit strategy

Regenerate artifacts from unchanged canonical records. Remove an export without
changing sources; no consumer needs a hosted service to recover knowledge.
Incompatible descriptor/routes/policy changes require versioned contracts and
reviewed migration. Provider-specific acquisition, signatures, serving or storage
adapters must declare capabilities without replacing canonical garden ownership.

## Follow-up work

Human disposition; #16 private/local federation, incremental refresh and actual
consumer proofs; #17 rendered route/accessibility proof; #18 portal composition;
#20 golden consumer; #30 registry integration; #32 query-store import; #46
retention. Akashic #176 and Aether #69 retain their own compatibility/acceptance.
