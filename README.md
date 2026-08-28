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
- [`scripts/validate_garden.py`](scripts/validate_garden.py) for dependency-free
  repository validation;
- [`scripts/garden_agent.py`](scripts/garden_agent.py) for ingestion, indexing,
  explainable search, context packs, and `llms.txt`;
- [`scripts/publish_garden.py`](scripts/publish_garden.py) and
  [`scripts/quartz_site.py`](scripts/quartz_site.py) for reviewed-public
  projection and pinned Quartz rendering;
- [`templates/note.md`](templates/note.md) for new knowledge notes.

From a Mindgarden checkout, point the commands at a consumer repository:

```bash
python3 scripts/validate_garden.py --repository-root "/path/to/consumer"
python3 scripts/garden_agent.py --repository-root "/path/to/consumer" verify
python3 scripts/publish_garden.py --repository-root "/path/to/consumer" verify
```

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
