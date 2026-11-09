# OpenAleph architectural evaluation — 2026-11-07

Recommendation for review: **adapt selected patterns; defer service adoption**.
OpenAleph is useful as an investigative document/entity system. Replacing the
portable garden or private source boundary with its database/service stack adds
operations and changes authorization semantics without a demonstrated need.
This evaluation is not an accepted ADR, a deployment approval or a performance
benchmark. No OpenAleph service or private data was deployed.

## Evidence and reproducibility

Evaluated upstream [5.3.2](https://github.com/openaleph/openaleph/releases/tag/5.3.2),
released 2026-08-25, exact commit
`14c3e96a5844589574a48dc3093c106fb07fd8c9`. All source links below use that commit:

- [Project/dependency metadata](https://github.com/openaleph/openaleph/blob/14c3e96a5844589574a48dc3093c106fb07fd8c9/pyproject.toml): Python >=3.12,<3.15;
  FollowTheMoney >=4.10.1,<5, OpenAleph Search, Flask, SQLAlchemy,
  authlib, worker components, service-layer storage providers and Sentry.
- [Compose topology](https://github.com/openaleph/openaleph/blob/14c3e96a5844589574a48dc3093c106fb07fd8c9/docker-compose.yml): PostgreSQL 17,
  Elasticsearch 9.3.3, Redis, ingest/analyze/translate workers and persistent
  database/archive/index volumes. The search example allocates a 1 GiB Java heap;
  that is a configuration observation, not a measured whole-service minimum.
- [Permission semantics](https://github.com/openaleph/openaleph/blob/14c3e96a5844589574a48dc3093c106fb07fd8c9/docs/user-guide/103/permissions.md):
  collection-wide read/write, highest group grant, administrator access to all
  collections, no per-document or expiring permission; streaming API requires
  write access even for reads.
- [Backup contract](https://github.com/openaleph/openaleph/blob/14c3e96a5844589574a48dc3093c106fb07fd8c9/docs/dev-admin-guide/102/backup.md):
  archive + PostgreSQL are the minimal backup; Elasticsearch is rebuildable.
- [Actual license](https://github.com/openaleph/openaleph/blob/14c3e96a5844589574a48dc3093c106fb07fd8c9/LICENSE.txt): **MIT** for this repository/version.
  Preserve notices for any future copied implementation. This does not review
  the licenses of all container images, models, datasets or dependencies; no
  upstream code/assets are copied here.

The live repository was not archived and showed a push on 2026-11-04. This is
activity evidence, not a support commitment or security audit. Several Compose
images use mutable `main`/`alpine` tags and a worker Git dependency is not an
immutable transitive lock. A pinned OpenAleph commit alone is insufficient to
reproduce a complete deployment. Any service experiment must capture image
**digests**, dependency/model locks and restore procedures separately.

## Comparison with current Mindgarden contracts

| Dimension | Evidence / difference | Proposed disposition and owner |
| --- | --- | --- |
| Canonical data / ontology | FollowTheMoney entities and properties support structured investigative data; Mindgarden owns portable knowledge, claims, typed synapses and exact source locators | **Adapt** explicit entity mappings only in an export adapter; never silently convert a person mention into an identity or replace canonical records (#11/#13, Mindgarden) |
| Ingestion / normalization | Dedicated ingest/analyze/translate workers separate document processing from search | **Adapt** separated capture/normalization/job boundaries; Mindcap owns capture fidelity, Mindgarden #11/#15/#35 deterministic evidence; remote acquisition stays separate |
| Entity resolution / cross-reference | Investigative entity model enables cross-referencing, requiring identity/disambiguation decisions beyond lexical retrieval | **Defer** automatic resolution; proposed matches need evidence, confidence, contradiction and human merge authority (#13/#14), not inferred canonical equality |
| Lexical / indexed search | Elasticsearch-backed OpenAleph Search adds a service and indexed query model | **Keep** #12/#32 reference and optional SQLite baseline; a future export-backed service must prove scoped result/citation parity and measurable corpus benefit |
| Graph / provenance | Entity relationships and investigation diagrams are useful views; they do not by themselves preserve Garden claim review or exact evidence spans | **Adapt** visual/query projections with a provenance sidecar; retain Garden IDs, represented revisions, locators and typed edges (#12/#16) |
| Permissions / collaboration | Collection read/write and highest group grant differ from per-record sensitivity, review authority, output budgets, TTL and revocation | **Reject** treating upstream permissions as the #29/#31 policy authority; a separately approved gateway must filter before ranking/traversal and prevent cross-collection leakage |
| Deployment / runtime | Database, search, queue/workers, extraction services, storage and authentication need operation | **Defer** default deployment; Realm owns provisioning/isolation/service lifecycle; this is outside the single-user Python core (#17/#47) |
| APIs / export | FollowTheMoney-style interchange can decouple investigations from source storage, but streaming read requires upstream write capability | **Adapt** one-way explicitly selected public/synthetic export first; no privileged bidirectional sync or raw-source upload |
| Backup / restore | Archive + authoritative database survive search-index loss; search is rebuilt | **Adapt** the rebuildable-projection pattern already in #32/#37/#45; do not confuse an index backup with original/knowledge backup |
| Security / private data | Broad administrators, group sharing, search/log/cache replicas and optional service providers widen the sensitive boundary | **Defer** personal archives until Realm/Hygiene runtime and redaction contracts are approved; no real data in this evaluation |
| License / maintenance | MIT source, recent release/activity; transitive images/models/services require separate inventory | **Adapt** evaluation discipline, not dependency adoption; owner review before copying code or packaging services |
| Exit / migration | An exported entity view can be discarded; canonical storage migration would require reconciliation of IDs, reviews and evidence | **Prefer** removable sidecar export/rebuild; keep originals and Garden records independent; no zero-cost service migration claim |

## Threat model for personal archives and sensitive sources

| Risk / trust boundary | Required control before any private service trial | Current evidence / gap |
| --- | --- | --- |
| Conversation instructions or document text becomes execution authority | Treat all captured text as evidence; no tools/network/publication granted by source content | Core source-data boundary exists; no OpenAleph agent/tool execution evaluated |
| Sensitive names, transactions, attachments, snippets or counts leak across scopes | Filter exact authorized records **before** export/index/query; segregate experiments and omit denied metadata; restrict backup/log/error access | #31 synthetic core proof exists; collection permissions alone cannot supply it |
| Group inheritance or streaming API grants excess write access | A least-privilege intermediary with explicit operation/session authority; no read client receives a write-capable credential | Upstream documents this mismatch; intermediary unavailable and not implemented here |
| False entity merge turns an allegation into a fact | Preserve attribution, uncertainty, competing identities and explicit reviewed merge decisions | No entity-resolution prototype; remain proposed matches |
| Embeddings/extraction/translation sends data to an unapproved provider | Explicit adapter capabilities, outbound policy, provider disclosure and declared data retention | No provider/runtime trial; installation is not proof of private processing |
| Database/search replicas, archives, logs, Sentry or backups outlive consent | Separate #46 original, canonical, projection and publication retention; audit revocation/deletion/export and telemetry settings | No OpenAleph lifecycle/deletion guarantee tested |
| Raw source download/sharing defeats a redacted insight | Export only an approved public derivation with public-safe evidence; never relabel a private citation | #21 deliberately blocks unavailable private redaction; full contract remains a prerequisite |
| Corruption/upgrade or adapter removal loses knowledge | Keep canonical records/source vault outside service; manifest export IDs/revisions; verify clean rebuild and restore before adoption | Core local restore exists; no OpenAleph runtime recovery or migration measured |

This model assumes a single authorized local operator for the current engine.
It does not grant multi-user/tenant, encrypted processing or network-isolation
assurance to either product.

## Cost, ownership and proposed next experiment

Relative to a file engine and optional embedded SQLite, the service topology has
**high setup/operations cost**, **medium-to-high continuing resource/storage
cost**, and **high policy/integration cost**. Reasons: several stateful services,
search heap and duplicate indexes, extraction/analysis workers, backups/upgrades,
SSO/group administration, monitoring, possible model/provider costs and a policy
gateway. Local single-user Python remains low in comparison. No dollar quote,
latency/throughput, disk/RSS benchmark or production sizing is claimed.

Mindgarden owns reviewed records, mappings, query semantics and an optional
export adapter. Mindcap owns captures and source package contracts. Realm owns
any future service provisioning, secrets, egress, isolation and lifecycle.
Observatory may read normalized health/freshness evidence; it does not own
remediation, knowledge approval or privacy decisions. Hygiene supplies normative
information-flow policy. These follow the existing architecture ownership map,
not a newly accepted cross-repository contract.

One narrowly scoped follow-on is sufficient: export an explicitly selected
synthetic/public `Document` projection with a Garden provenance sidecar to the
**actual pinned FollowTheMoney validator**, then re-import only artifact/status
references. Preserve Garden logical ID, content/revision hash, exact locators,
review and scope separately; export no inferred Person/Organization entities.
No service is required. Keep it outside default dependencies, compare selected
IDs/content/qualifications and prove clean removal.

The dependency probe was attempted in an isolated disposable virtualenv:

```sh
python3 -m pip --python .cache/evaluations/openaleph-python/bin/python install \
  --only-binary=:all: --report .cache/evaluations/ftm-install.json \
  followthemoney==4.10.1
pkg-config --modversion icu-i18n
```

The first command **failed**: transitive `normality` requires `pyicu>=2.10.0`,
with no compatible binary available. The second **failed**: ICU development
metadata is absent. There is no successful dependency lock, FtM validator run,
entity export compatibility claim or OpenAleph service test. That optional
prototype gap does not invalidate the architectural comparison. A later owner
can supply a pinned isolated ICU build or approved image and exact model schema;
we do not invent format details or add a core dependency to force the experiment.

Revisit when a measured corpus exceeds #32's useful baseline, reviewed entity
cross-referencing becomes a concrete consumer requirement, or an owner supplies
the service policy/runtime/restore contracts; review evidence again by
2027-01-01. Until then, **adapt patterns and defer deployment** is a proposed
recommendation. The #26 architectural evaluation is complete with this adapt/defer outcome;
[the acceptance receipt](../overnight-sprint.md) records its criteria. This does
not adopt a service or accept a proposed architecture decision.
