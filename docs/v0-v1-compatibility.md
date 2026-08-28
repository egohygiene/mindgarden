# Mindgarden v0 to v1 compatibility

Mindgarden v1 is additive. Root-level schemas and the 0.1 CLI retain v0
behavior while `contracts/v1/` stabilizes the target format. Issue #7 will
implement deterministic plan/apply migration; this document defines the
behavior that implementation must follow.

## Compatibility matrix

| v0 concept or field | v1 representation | Migration rule |
| --- | --- | --- |
| `mindgarden.garden/v0` | `mindgarden.garden/v1` | Preserve garden `id`, owners, visibility, repository, and root intent; add canonical URI, kind, classification scope, contract capabilities, publication policy, routing declaration, and migration history explicitly. |
| `mindgarden.note/v0` | `mindgarden.knowledge/v1` | Preserve `id`, title, kind where compatible, owners, visibility, dates, aliases, and tags. Map the content file to `content.path` and hash its bytes. |
| v0 note kind `source` | `mindgarden.source/v1` plus optional knowledge | Normalize as a source first. Create durable knowledge only through a later reviewed plan. |
| `status: draft` | `status: proposed` | Preserve the pre-acceptance lifecycle without implying review. |
| `status: reviewed` | `status: active` plus `review` evidence | Do not mark `review.state: approved` unless reviewer identity and review time can be established. Otherwise retain legacy evidence in an `x-v0-*` extension and require review. |
| `reviewed: false` | `review.state: unreviewed` | Emit empty reviewers, `reviewed_at: null`, and explicit rationale where available. |
| `reviewed: true` | Review evidence, not an automatic approval | Preserve the fact but never invent reviewer identity or time. |
| `confidence: uncertain` | `confidence: unknown` | Preserve uncertainty without increasing certainty. Other confidence values map directly. |
| `sources` path strings | Source locators and provenance references | Resolve only verified local artifacts. Hash exact bytes. Missing or ambiguous sources become deferred mappings rather than invented references. |
| `related` | Typed `related` synapses | Preserve target identifiers and create explicit proposed relationships. |
| `supersedes` | Typed `supersedes` synapses and artifact references | Preserve history and direction. Do not delete the superseded record. |
| v0 provenance string transformations | Ordered transformation objects | Preserve order; record known generator/version/parameters and use explicit unknown or deferred evidence when unavailable. |
| Folder location | `content.path` authoring convenience | Never infer authoritative domain or topic solely from the folder. |
| `x-*` extension | `x-*` extension | Preserve when it does not conflict with canonical v1 meaning or privacy rules. |
| Unknown unprefixed field | Deferred/manual review | Do not silently drop, reinterpret, or promote it. |

## Required migration behavior

Migration is non-destructive and reviewable:

1. Read and validate the v0 garden without modifying it.
2. Produce a complete migration plan with a canonical digest.
3. Preserve stable identifiers across file moves and vocabulary refinement.
4. Compute hashes from observed bytes; never synthesize missing provenance.
5. Record every preserve, rename, split, merge, or defer mapping.
6. Write v1 into a separate staging tree using atomic operations.
7. Validate the complete staged garden before replacement is offered.
8. Require the reviewed plan digest for apply.
9. Leave canonical v0 knowledge unchanged if any operation fails.
10. Record an applied migration and rollback instructions after success.

Re-running the same plan against unchanged input must be idempotent. A changed
input invalidates the plan digest and requires a new review.

## Intentional incompatibilities

- v1 separates sources from durable knowledge;
- v1 separates lifecycle, epistemic state, confidence, review, visibility, and
  publication eligibility;
- v1 relationships are typed records rather than bare note identifiers;
- v1 cross-garden references use stable garden/artifact identities and reject
  mutable branch revisions;
- v1 domains and topics are authoritative, whereas folder placement is not;
- v1 closes unknown top-level fields unless they use `x-*`.

These changes prevent a mechanical migration from silently asserting truth,
review, public eligibility, taxonomy, or provenance that v0 never recorded.

## Rollback boundary

Migration does not rewrite the v0 source in place. Until a consumer explicitly
accepts a v1 cutover, its v0 garden and current CLI remain authoritative. A
rollback restores the previously selected canonical tree or pinned revision;
it does not reverse-engineer v0 by discarding v1-only evidence.
