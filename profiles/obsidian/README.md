# Obsidian Profile

This profile projects a Mindgarden consumer repository into an Obsidian vault
without moving or duplicating canonical knowledge.

## Vault topology

Open the consumer repository root as the vault. Obsidian stores shareable vault
configuration in the root `.obsidian/` directory, while durable knowledge stays
under `.garden/`. This avoids a nested vault and allows garden notes to link to
repository architecture, source, and documentation.

Only portable preferences belong in version control. Ignore workspace layouts,
caches, plugin binaries, and plugin-owned local data.

## Default dashboard

Native Obsidian Bases is the default dynamic-view layer. It reads Markdown
properties directly, supports table, list, and card views, and stores view
definitions as inspectable `.base` YAML files.

The default has no required community plugins and executes no dashboard
JavaScript. The first-party CSS snippet uses Obsidian variables and is scoped to
notes declaring `cssclasses: [mindgarden-dashboard]`.

## Optional Project Manager integration

Project Manager is declared as an optional plugin because it provides richer
table, Gantt, and Kanban views while retaining Markdown and YAML frontmatter as
the data store.

Mindgarden does not vendor the plugin, disable Restricted Mode, or write its
installation state. A human must review the upstream repository, install the
plugin from Obsidian's community directory, and enable it explicitly.

The v0 adapter does not claim full schema compatibility with every field the
plugin may create. Native Bases remains the stable project view until a future
Mindgarden adapter defines and tests that mapping.

## Dashboard Gallery influence

The dashboard composition is an original first-party implementation informed by
the idea of an Obsidian dashboard gallery. No external dashboard Markdown, CSS,
JavaScript, images, API integrations, or assets are copied.
