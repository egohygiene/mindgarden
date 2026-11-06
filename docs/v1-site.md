# Reviewed v1 garden preview

This is the #17 reference checkpoint on `feature/17-v1-garden-preview`, based on
merged main `8a9650e`. It preserves v0 publishing and uses the existing reviewed
public selection service for v1. A site profile is `projection/v1` with `kind:
site` and a typed `x-site` adapter declaration. Source, review, scope and
publication policy remain the existing contracts.

## Offline content proof

```sh
python3 -S scripts/site_demo.py --require-source \
  --workspace "/tmp/synthetic-site-demo" --report "/tmp/synthetic-site-report.json"
```

Choose a new or empty workspace. The script uses committed synthetic fixtures,
blocks networking/process calls in-process, and creates an inspectable Quartz
content tree. Its report records exact citations and reproducible public hashes.
This is not host-isolation evidence. No default registry, real garden or archive
is discovered or configured.

Normal commands consume explicit authority and reviewed profiles:

```sh
mindgarden publish project --repository-root "/tmp/synthetic-site-demo/canonical" \
  --local-config "/tmp/synthetic-site-demo/bindings.json" \
  --scope "/tmp/synthetic-site-demo/session.json" \
  --profile "/tmp/synthetic-site-demo/profile.json" \
  --output-directory "/tmp/synthetic-site-demo/another-export-parent" --plan
```

The output parent must already exist. Inspect the JSON plan, then repeat with
`--apply --plan-digest "<reviewed-sha256>"`. `publish verify` checks an existing
content tree. A matching re-apply verifies it; conflicting, corrupt or incomplete
output is retained. Use a fresh parent for a changed represented revision.
V1 without bindings/session fails closed; v0 retains its existing commands.

## Optional renderer preparation

Quartz is a replaceable adapter. Preparing software is a separate acquisition
operation. The fixture pins the existing Quartz commit:
`075afd3f712da0088a07f5284a7b3aba37dd61b6`, using Node 24.

```sh
mkdir --parents "/tmp/synthetic-site-demo/canonical/.cache/mindgarden"
git clone --no-checkout --filter=blob:none "https://github.com/jackyzha0/quartz.git" \
  "/tmp/synthetic-site-demo/canonical/.cache/mindgarden/quartz"
git -C "/tmp/synthetic-site-demo/canonical/.cache/mindgarden/quartz" \
  checkout --detach "075afd3f712da0088a07f5284a7b3aba37dd61b6"
npm ci --prefix "/tmp/synthetic-site-demo/canonical/.cache/mindgarden/quartz" \
  --cache "/tmp/synthetic-site-demo/canonical/.cache/mindgarden/npm" \
  --ignore-scripts --no-audit --no-fund
mkdir "/tmp/synthetic-site-demo/rendered"
```

Rendering verifies the clean exact checkout, copies tracked files to an owned
temporary directory outside Git ignores, and installs from that cache with
`npm ci --offline --ignore-scripts`. It does not fetch a renderer during a scoped
build or edit its prepared sources. The pin's package lock supplies integrity.
No application model, database, Google account or hosted runtime is required.

## Build and preview

```sh
mindgarden site build --repository-root "/tmp/synthetic-site-demo/canonical" \
  --local-config "/tmp/synthetic-site-demo/bindings.json" \
  --scope "/tmp/synthetic-site-demo/session.json" \
  --profile "/tmp/synthetic-site-demo/profile.json" \
  --output-directory "/tmp/synthetic-site-demo/rendered" --plan
```

Inspect the plan, then repeat with `--apply --plan-digest "<reviewed-sha256>"`.
`site build --check` verifies the result without renderer/network calls. Replace
`build` with `serve` and add `--port 8080` to apply/verify the same build and start
a loopback preview at `http://127.0.0.1:8080/garden/`. Each request checks live
authority and the requested member's checksum; unknown or changed files are not
served. Stop with Ctrl-C. `serve --plan` remains read-only.

The initial adapter supplies note reading, search, tags, backlinks, typed
relationships and exact source trails. Bodies are literal reviewed text, so raw
Markdown/HTML/instructions remain data. Generated links navigate selected public
records. A local SVG relationship view has keyboard links and zoom controls, with
a complete textual list; selections over 200 nodes use the list. It has no CDN
dependency. Rich body Markdown and attachments require a later safety contract.

Canonical source hashes/locators are shown without copying raw archives or local
vault paths. The existing discovery descriptor/index/graph/agent files accompany
rendered pages. Canonical note routes remain `notes/<id>/`; a useful empty page
does not disclose omitted records or private counts.

## Scope still open

Full #17 WCAG 2.2 AA, extensive mobile/large-corpus evidence and real-consumer
acceptance remain open. #38 supplies reusable design tokens; #10 expands the
negative matrix; #18 proves portal composition. Hostile-writer, process/network
isolation, native runtime and actual deployment assurance remain separate.
See [the six-PR checkpoint map](garden-experience-milestone.md) and proposed
[ADR-0013](decisions/ADR-0013-reviewed-v1-site-projections.md).
