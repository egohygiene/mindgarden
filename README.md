# Mindgarden

🌱 A versioned knowledge garden and second-brain foundation for projects,
people, and organizations.

Mindgarden is the standalone source owner for the portable contract behind a
repository's `.garden/` directory. Obsidian vaults, agent context, search
indexes, and published sites are projections of that committed knowledge, not
competing sources of truth.

## Responsibilities

Mindgarden owns:

- the `.garden/` manifest and note metadata contracts;
- deterministic initialization, validation, indexing, and migration behavior;
- plain-Markdown knowledge lifecycle conventions;
- adapters for human, agent, and published views;
- provenance, confidence, review, visibility, and relationship semantics.

Mindgarden does not own:

- organization-wide agent policy or reusable intelligence contracts;
- development environment images;
- reusable CI/CD workflow implementation;
- organization-wide lint policy or repository propagation;
- Obsidian, Quartz, or another third-party tool's internal implementation.

Those boundaries allow the same committed knowledge to support an Obsidian
vault, a GitHub Pages garden, and multiple agent runtimes without creating
three competing stores.

## Stabilized v1 contract

[`contracts/v1/`](contracts/v1/) defines the additive JSON Schema 2020-12
contract for gardens, captured and normalized sources, durable knowledge,
claims and evidence, typed synapses, ordered provenance, projections, and
migration history. It makes stable identity, privacy, review, classification,
routing scope, and publication authority explicit without treating folders or
a third-party application as canonical.

The v1 schemas are the target contract for the 1.0 roadmap. The 0.1 CLI now
creates deterministic v1 gardens and performs review-gated, rollback-safe
v0 → v1 migration while retaining the existing v0 agent and publishing
surface. Hardened general v1 validation remains a separate gate. See the
[v1 contract model](docs/contracts-v1.md), [lifecycle command
contract](docs/initialization-migration.md), and [v0 → v1 compatibility
matrix](docs/v0-v1-compatibility.md).

## Implemented v0 surface

The extracted v0 engine includes:

- [`contracts/garden.schema.json`](contracts/garden.schema.json) for
  `.garden/garden.yaml`;
- [`contracts/note.schema.json`](contracts/note.schema.json) for Markdown YAML
  frontmatter;
- [`contracts/obsidian-profile.schema.json`](contracts/obsidian-profile.schema.json)
  for portable, reviewable Obsidian integration metadata;
- [`contracts/provenance.schema.json`](contracts/provenance.schema.json) for
  source-to-artifact integrity records;
- [`contracts/context-pack.schema.json`](contracts/context-pack.schema.json)
  and [`contracts/index.schema.json`](contracts/index.schema.json) for
  deterministic agent projections;
- [`contracts/publish-profile.schema.json`](contracts/publish-profile.schema.json)
  for fail-closed static-site publication;
- the installable [`mindgarden`](src/mindgarden/) Python package and unified
  command for validation, ingestion, indexing, search, context, publication,
  and verification;
- explicit domain, application, adapter, and interface package boundaries;
- compatibility shims under [`scripts/`](scripts/) for the incubated 0.x
  command paths;
- [`templates/note.md`](templates/note.md) for new knowledge notes.

## Installation

Mindgarden supports Python 3.12 and 3.13. Before the first PyPI release, install
an immutable checkout or a reviewed local clone:

```bash
python3 -m pip install "/path/to/mindgarden"
mindgarden --version
```

PyPI publication is part of the final 1.0 release gate; no provisional package
is published by this change.

Point the installed command at a consumer repository:

```bash
mindgarden init --repository-root "/path/to/new-consumer" --visibility "public"
mindgarden migrate --repository-root "/path/to/v0-consumer" --plan
mindgarden validate --repository-root "/path/to/consumer"
mindgarden verify --repository-root "/path/to/consumer"
mindgarden publish verify --repository-root "/path/to/consumer"
```

The package has no runtime Python dependencies. Initialization, migration,
validation, indexing, search, and context generation remain offline. See
[`docs/cli.md`](docs/cli.md) for the full command, exit-code, library, and
compatibility contracts.

The v0 parser deliberately supports only scalar values and scalar lists. This
keeps the foundational contract deterministic and dependency-free while the
larger authoring and indexing architecture matures.

## Provenance and extraction

The implementation graduated from Empathy with its relevant source history.
[`EXTRACTION.md`](EXTRACTION.md) records the immutable source revision and
extraction boundary; [`PROVENANCE.md`](PROVENANCE.md) records the commit map and
earlier design references.

No external project implementation is incorporated in this foundation pass.

The first consumer profile lives in [`profiles/obsidian/`](profiles/obsidian/).
It prefers native Obsidian capabilities and treats community plugins as explicit
human-approved options.

The portable agent surface lives in [`profiles/agent/`](profiles/agent/). Its
CLI is the dependency-free baseline; runtime-specific hooks and MCP servers may
wrap it later without changing canonical garden storage.

The public-site adapter lives in [`profiles/quartz/`](profiles/quartz/). It
filters canonical notes before an immutable Quartz checkout renders them, so
generator ignore rules are never treated as a privacy boundary.

See [`ROADMAP.md`](ROADMAP.md) for the path from this preserved v0 engine to the
first independently versioned release.
