# Mindgarden architecture decisions

New decisions inherit [Hygiene policy v1.2.0](policy-reference.json). Decision status and implementation evidence are independent.

## Preserved legacy records

[ADR-0001 through ADR-0006](../../DECISIONS.md) remain canonical at their existing inline locations, with original labels and history unchanged. Their human-authority evidence remains part of the separately gated #41 migration. This checkpoint does not claim full ADR adoption or decision-ledger publication.

## New proposed decisions

| ID | Decision | Status | Date |
| --- | --- | --- | --- |
| [ADR-0007](ADR-0007-portable-consumer-knowledge.md) | Keep portable consumer records authoritative | Proposed | 2026-11-04 |
| [ADR-0008](ADR-0008-immutable-source-vault.md) | Separate source identity, immutable content, and location | Proposed | 2026-11-04 |
| [ADR-0009](ADR-0009-shared-local-application-services.md) | Extend shared Python application services for the local workflow | Proposed | 2026-11-04 |
| [ADR-0010](ADR-0010-local-scope-and-review-authority.md) | Keep local scope, review and publication authority independent | Proposed | 2026-11-04 |
| [ADR-0011](ADR-0011-public-federation-projections.md) | Build public discovery from reviewed scoped projections | Proposed | 2026-11-05 |
| [ADR-0012](ADR-0012-machine-local-registry.md) | Manage local registrations without changing canonical gardens | Proposed | 2026-11-05 |
| [ADR-0013](ADR-0013-reviewed-v1-site-projections.md) | Render reviewed v1 knowledge through the existing pinned Quartz adapter | Proposed | 2026-11-05 |
| [ADR-0014](ADR-0014-design-source-and-consumers.md) | Keep stack-neutral design tokens separate from derived consumers | Proposed | 2026-11-05 |
| [ADR-0015](ADR-0015-caller-owned-portal-composition.md) | Compose pinned public artifacts into caller-owned portal mounts | Proposed | 2026-11-05 |
| [ADR-0016](ADR-0016-query-store-baseline.md) | Keep portable records canonical and measure query adapters before adoption | Proposed | 2026-11-05 |
| [ADR-0017](ADR-0017-local-user-and-tenancy-boundary.md) | Keep the first workflow single-user and require a separate collaboration model | Proposed | 2026-11-05 |
| [ADR-0018](ADR-0018-minimal-runtime-topology.md) | Keep the local runtime minimal and let Realm own optional service composition | Proposed | 2026-11-05 |
| [ADR-0019](ADR-0019-bounded-operations-and-retention.md) | Keep background operations and retention reviewable and recoverable | Proposed | 2026-11-05 |
| [ADR-0020](ADR-0020-agent-interface-authority.md) | Expose bounded application services without letting agent interfaces grant authority | Proposed | 2026-11-05 |
| [ADR-0022](ADR-0022-reviewed-canonical-transitions.md) | Preserve canonical home changes as reviewed append-only provenance | Proposed | 2026-11-06 |
| [ADR-0021](ADR-0021-build-versus-integrate.md) | Keep optional product integrations behind evaluated replaceable boundaries | Proposed | 2026-11-05 |
| [ADR-0023](ADR-0023-document-classification-and-local-reader.md) | Classify new document inputs before optional local parsing | Proposed | 2026-11-06 |
| [ADR-0024](ADR-0024-private-assets-and-explicit-storage-ports.md) | Keep asset triage append-only and storage adapters explicitly supplied | Proposed | 2026-11-06 |
