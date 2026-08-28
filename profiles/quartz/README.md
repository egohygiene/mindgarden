# Quartz publishing profile

This profile turns a validated Mindgarden into a disposable Quartz v5 site
without making Quartz a knowledge source. The consumer's `.garden/` remains
canonical; the projector admits only notes that are both `reviewed` and
`public`.

Copy [`profile.yaml`](profile.yaml) and
[`quartz.config.yaml`](quartz.config.yaml) into the consumer repository at
`.garden/publishing/`, then replace the example identity, repository, entrypoint,
and base URL. Keep the profile filename as `quartz.yaml`; the renderer expects
the configuration beside it as `quartz.config.yaml`.

## Public boundary

The projector fails closed:

- private and internal notes are rejected by the public-garden validator;
- draft, proposed, deprecated, and archived notes are omitted;
- `.garden.local/`, provenance sidecars, context packs, indexes, templates,
  Obsidian configuration, and native Bases are never copied;
- symlinks and paths outside the repository are rejected;
- links to an excluded garden note fail the build rather than revealing it;
- links to public repository documents outside the projection become pinned
  GitHub source links.

The disposable projection includes a machine-readable marker so tooling can
safely replace only directories it created.

## Local validation and preview

Node.js 24, npm, Git, and Python 3 are required for a rendered preview. The
projection itself requires only Python 3.

```bash
python3 scripts/publish_garden.py \
  --repository-root "/path/to/consumer" \
  verify

python3 scripts/quartz_site.py \
  --repository-root "/path/to/consumer" \
  serve \
  --port 8080
```

The preview is available at <http://localhost:8080/>. The Quartz checkout,
projected Markdown, npm dependencies, and rendered output stay beneath the
ignored `.cache/mindgarden/` directory.

Build without serving:

```bash
python3 scripts/quartz_site.py \
  --repository-root "/path/to/consumer" \
  build
```

## GitHub Pages

The consumer repository owns its Pages workflow, domain, and any composition
with other static projections. It should invoke a pinned Mindgarden release or
commit, validate and render into `.cache/mindgarden/site/`, and upload that
directory as its Pages artifact. Select **GitHub Actions** as the Pages source
for that consumer repository.

Quartz and every GitHub Action are pinned to immutable commits. Updating the
engine means changing `quartz_commit` in the consumer-owned
`.garden/publishing/quartz.yaml`, rebuilding locally, and reviewing the
resulting site before merge.
