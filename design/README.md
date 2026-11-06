# Mindgarden design source

The [tokens](tokens/mindgarden.tokens.json) and
[schema](schemas/design-tokens.schema.json) capture the existing banner and
architecture illustration as a small reusable design foundation. They are public
design data, separate from Garden knowledge, source archives and review policy.
Generated CSS, Quartz settings, screenshots and images are consumers/projections.

Read [the visual reference](references/mindgarden-visual-style.md) and reusable
[image](prompts/image-generation-style.md) / [diagram](prompts/diagram-generation-style.md)
prompts. No new binary asset or image generation is needed to validate this work.

```sh
mindgarden design --format json
mindgarden design --format css
mindgarden design --format quartz
```

Each command validates the source before exporting. An explicit `--tokens` file
supports independent consumers. Unknown fields, unsafe font syntax, invalid
values and insufficient contrast fail with stable diagnostics. Normal text/link
pairs target at least 4.5:1; focus/control boundaries target at least 3:1. This is
color-foundation evidence, not complete WCAG 2.2 AA certification.

The JSON stays stack-neutral: semantic colors, local font-family fallbacks,
numeric spacing/borders/effects, labelled thin-line icons and layout guidance.
It may feed CSS, Quartz, Flutter, slides or diagrams; it selects no application
framework. Fonts use local/system fallbacks and require no web-font service.

The optional v1 Quartz consumer selects `"theme": "mindgarden-v1"` inside its
reviewed `x-site` settings. Its plan records the actual public `theme_revision`.
An optional supplied revision must match. CSS and Quartz colors are derived from
the installed source tokens, never maintained as a second color catalog. Omit the
theme to keep the existing unbranded adapter. Design tooling is optional for
contributors working on other parts of the engine.
