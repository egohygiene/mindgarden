# Quartz publishing profile

This profile turns a validated Mindgarden into a disposable Quartz v5 site
without making Quartz a knowledge source. Empathy's `.garden/` remains
canonical; the projector admits only notes that are both `reviewed` and
`public`.

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
python3 mindgarden/scripts/publish_garden.py \
  --repository-root . \
  verify

python3 mindgarden/scripts/quartz_site.py \
  --repository-root . \
  serve \
  --port 8080
```

The preview is available at <http://localhost:8080/>. The Quartz checkout,
projected Markdown, npm dependencies, and rendered output stay beneath the
ignored `.cache/mindgarden/` directory.

Build without serving:

```bash
python3 mindgarden/scripts/quartz_site.py \
  --repository-root . \
  build
```

The equivalent Taskfile commands are `task garden:publish:check`,
`task garden:site:build`, and `task garden:site:serve`.

## GitHub Pages

The Pages workflow validates and builds the site for pull requests. A push to
`main` additionally uploads the static artifact and deploys it through the
`github-pages` environment.

After merging the first publishing change, select **GitHub Actions** as the
repository's Pages source under **Settings → Pages** if it is not already
selected. The expected project-site URL is
<https://egohygiene.github.io/empathy/>.

Quartz and every GitHub Action are pinned to immutable commits. Updating the
engine means changing `quartz_commit` in [`profile.yaml`](profile.yaml),
rebuilding locally, and reviewing the resulting site before merge.
