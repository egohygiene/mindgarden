# Mindgarden v1 contract model

Mindgarden v1 defines the portable semantic contract shared by repository,
personal, and organization gardens. The schemas are additive design authority.
The 0.1 CLI initializes v1 and migrates validated v0 gardens through a reviewed
plan while the established agent and publication commands retain v0 behavior.
Hardened general v1 validation remains issue #10.

Every schema uses JSON Schema 2020-12, has a stable URN identifier, closes
unknown top-level fields, and permits namespaced extension fields matching
`x-*`. The canonical registry is [`contracts/v1/`](../contracts/v1/).

## Registry

| Contract | Instance discriminator | Responsibility |
| --- | --- | --- |
| Common | Not instantiated | Stable identifiers, immutable revisions, authors, reviews, visibility, paths, hashes, classification sets, and references. |
| Garden | `mindgarden.garden/v1` | Garden identity, ownership, supported contracts, roots, classification scope, publication allowlist, routing declaration, and migration history. |
| Source | `mindgarden.source/v1` | Faithfully captured and deterministically normalized source artifacts. |
| Knowledge | `mindgarden.knowledge/v1` | Durable human-readable maps, concepts, decisions, projects, procedures, insights, references, and notes. |
| Claim | `mindgarden.claim/v1` | Checkable statements, epistemic state, confidence, and supporting or conflicting evidence. |
| Synapse | `mindgarden.synapse/v1` | Typed local or cross-garden artifact relationships. |
| Provenance | `mindgarden.provenance/v1` | Input hashes, ordered transformations, generator identity, origin, output hash, and rights. |
| Projection | `mindgarden.projection/v1` | Disposable indexes, graphs, context packs, agent entrypoints, sites, and federation outputs governed by publication policy. |
| Migration | `mindgarden.migration/v1` | Reviewable plan or history evidence for movement between contract versions. |

## Independent semantic axes

Mindgarden never collapses these axes into one status:

- `status` describes lifecycle, not truth, approval, or publication;
- `epistemic_state` describes how a claim is known;
- `confidence` communicates uncertainty without granting authority;
- `authors` preserves human or agent authorship;
- `review` records separate human authority;
- `visibility` classifies the record's privacy boundary;
- `publication` or a projection policy grants or denies projection eligibility;
- `domains` and `topics` classify knowledge regardless of filesystem path.

The normative producer defaults are fail-closed:

| Record or situation | Default |
| --- | --- |
| Captured source | `visibility: private`, `publication: excluded` |
| Agent-authored knowledge | `status: proposed`, `review.state: unreviewed` |
| New knowledge with no explicit policy | `visibility: private`, `publication: excluded` |
| Unknown confidence | `confidence: unknown` |
| Public projection selection | Deny unless visibility and review are explicitly allowlisted |

Schema `default` values document producer behavior; consumers must not assume a
validator mutates an instance to insert them. Producers emit the fields
explicitly.

## Identity and references

An artifact identity is the pair `{garden, id}`. A garden also declares a
stable `canonical_uri`. Paths, titles, aliases, repository URLs, and rendered
URLs do not replace that identity.

References may include an immutable revision in one of these forms:

- `git:<40-lowercase-hex-commit>`;
- `sha256:<64-lowercase-hex-digest>`;
- `version:<v1-semantic-version>`.

Mutable branch and tag references are not contract revisions. A `null` revision
means the stable canonical identity is intentionally followed; it does not mean
an unknown branch should be guessed.

## Classification and layout

`domains` and `topics` are authoritative classification. Folders support
authoring and projection ergonomics only. A knowledge record is not duplicated
to appear in multiple domain folders, and tags do not mirror the complete
taxonomy. Renaming or moving a Markdown file preserves `{garden, id}`.

## Sources, knowledge, and evidence

A source is captured evidence, not automatically durable knowledge. A
normalized source points back to at least one captured input. Knowledge may
select exact source locators and hashes. Claims express evidence direction as
`supports`, `contradicts`, `uncertain`, or `supersedes`. Typed synapses relate
artifacts without copying either artifact into another garden.

Rights, origin, hashes, ordered transformations, and source relationships stay
explicit. When a value cannot be established, a producer uses an allowed
`null`, an empty list, or a deferred migration mapping. It never manufactures
portable provenance.

## Privacy and publication

Raw captured sources cannot be publication-eligible. Public knowledge must be
active, approved, explicitly public, and marked eligible. Public projections
must:

- use an immutable source revision;
- use `default_action: deny`;
- allow only public visibility;
- require approved review;
- exclude raw sources;
- select records through explicit kind/domain/topic allowlists.

These structural rules are necessary but not a complete leak detector. Body,
attachment, link, log, and cross-record validation belongs to issue #10.

## Extensions

Top-level extension fields use a lowercase kebab-case `x-` prefix, such as
`x-example-adapter`. Extensions cannot change canonical field meaning or weaken
privacy, provenance, review, or publication requirements. Unprefixed unknown
fields fail validation.

## Conformance evidence

Golden instances live under `tests/fixtures/contracts/v1/valid/`. The
adversarial mutation matrix under `tests/fixtures/contracts/v1/invalid/`
exercises identity, dates, privacy, provenance, cross-garden revisions,
relationships, extension fields, review authority, classification, origin,
migration history, and publication policy.

Install the pinned development tools and run the contract suite:

```bash
python3 -m pip install \
  --disable-pip-version-check \
  --requirement "requirements/test.txt"
python3 -m unittest tests.test_v1_contracts --verbose
```

The published `mindgarden` wheel retains zero runtime dependencies.
