# Provenance

## Empathy graduation

The runnable v0 implementation was extracted from
[`egohygiene/empathy`](https://github.com/egohygiene/empathy) at
`f8313641fa05cb1d062057a426b094c0e3770522`. The source directory tree was
`59edf41e612aacf8c4be5aa8d923392796e92d1e`.

| Empathy source commit | Extracted Mindgarden commit |
| --- | --- |
| `3216ff5ece20b821748348b0d0353b4cfa5a392b` | `f3098762c24c1e6651b6504dc6a4a979a4986b41` |
| `24302e1c5135597df92e320266dd45e501b1f745` | `b51effefe70144e952743a8e7ad9828e8136a6e8` |
| `6ae21e35f0bfc49925e17e3f2b738994dc8dd31b` | `95abfe51a8e609c9ea26cefbdabbe0f747a5d098` |
| `fe4fc45eaf4896f2056620d5a3bcf6393006c126` | `ccdb2c03fa8f26c3e23d6d8fea972ba739381ab5` |
| `61903ffd27bf2ab2ee88ee1bdbbf1c2c310034e0` | `87441389730aa411408ed5ce3c1c9d48763bef4d` |
| `e0f924a768e3c55fab0b45ec7dbc87ced94f8729` | `88b19ed24f289a150ea417df40514bb8c4b11805` |
| `222920b6f08449d2200ad702cfff40596cce62fd` | `9bc3f72ce12dc6226d839db56376ffef3e0768ef` |
| `df4f280253049bd2cd754bacae4c9ccc358ec8aa` | `3174e3c8b5fba559b7b0f66bdd97c46deef76fb4` |
| `6c9fa6a3c13cc154388f52705bf6eaa9aa407a4b` | `ee83f644ef947150706f8fc15b31db48e535e358` |

Every extracted commit contains an `Empathy-Source-Commit` trailer, making the
mapping machine-discoverable from Git history as well as this record.
The extracted tip's tree is exactly
`59edf41e612aacf8c4be5aa8d923392796e92d1e`, matching the recorded Empathy
subtree. Commit SHAs differ because the standalone history has different
parentage and publication metadata.

## Ego Hygiene seed

Mindgarden was incubated from [`egohygiene/mindgarden`](https://github.com/egohygiene/mindgarden)
at commit `ec2bb919a555d5df5f18223cc3b47e34cfdfea15`.

The seed contained:

- `.gitignore`;
- `LICENSE`;
- `README.md`.

The MIT license is retained verbatim. The README was expanded during
incubation to define the capability boundary and v0 contract.

## External design references

The following projects informed architectural research but contributed no code
or assets to this import:

- `itechmeat/open-second-brain` — local-first Markdown agent memory,
  deterministic tools, provenance, snapshots, and runtime adapters;
- `shannhk/llm-wikid` — compiled knowledge pages, source tracing, confidence,
  human-review gates, and knowledge linting;
- `StepanKropachev/obsidian-pm` / DotPM — Markdown-frontmatter project data and
  interchangeable Obsidian views;
- `InlitX/Obsidian-Dashboard-Gallery` — optional Obsidian dashboard patterns;
- Dark Factory — shared-memory agent-system reference architecture;
- `AnswerDotAI/llms-txt` — a compact, Markdown-native agent discovery
  entrypoint with curated links to deeper context;
- `jackyzha0/quartz` — Obsidian-compatible static publishing, backlinks,
  graph navigation, search, tags, and GitHub Pages deployment patterns.

External implementations must be evaluated independently for compatibility,
security, maintenance, and license obligations before any future incorporation.
In particular, a repository without an explicit license is reference-only.

Quartz remains an external MIT-licensed build dependency pinned by commit in
the publishing profile. No Quartz implementation code or assets are vendored
into Mindgarden.
