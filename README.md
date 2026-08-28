# Mindgarden

🌱 A versioned knowledge garden and second-brain foundation for projects,
people, and organizations.

Mindgarden is currently incubated inside Empathy as an independently
extractable holon. It defines the portable contract behind a repository's
`.garden/` directory without making Obsidian, a publishing engine, an agent
runtime, or a search backend the source of truth.

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

## Current contract

The incubating v0 contract includes:

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
- [`scripts/validate_garden.py`](scripts/validate_garden.py) for dependency-free
  repository validation;
- [`scripts/garden_agent.py`](scripts/garden_agent.py) for ingestion, indexing,
  explainable search, context packs, and `llms.txt`;
- [`templates/note.md`](templates/note.md) for new knowledge notes.

Validate a consumer repository from its root:

```bash
python3 mindgarden/scripts/validate_garden.py --repository-root .
python3 mindgarden/scripts/garden_agent.py --repository-root . verify
```

The v0 parser deliberately supports only scalar values and scalar lists. This
keeps the foundational contract deterministic and dependency-free while the
larger authoring and indexing architecture matures.

## Incubation and extraction

The original seed and external design references are recorded in
[`PROVENANCE.md`](PROVENANCE.md). The physical and dependency constraints that
keep this directory independently extractable are defined in
[`EXTRACTION.md`](EXTRACTION.md).

No external project implementation is incorporated in this foundation pass.

The first consumer profile lives in [`profiles/obsidian/`](profiles/obsidian/).
It prefers native Obsidian capabilities and treats community plugins as explicit
human-approved options.

The portable agent surface lives in [`profiles/agent/`](profiles/agent/). Its
CLI is the dependency-free baseline; runtime-specific hooks and MCP servers may
wrap it later without changing canonical garden storage.
