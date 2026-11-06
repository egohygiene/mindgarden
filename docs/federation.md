# Public federation projection checkpoint

The additive #16 checkpoint builds supplied local v1 records into checksum-bound
public discovery artifacts. It uses the existing Python application services and
CLI. Google, GitHub hosting, model providers, web servers and databases are not
required. [ADR-0011](decisions/ADR-0011-public-federation-projections.md) is proposed;
this implementation does not ratify it or complete the broader federation issue.

## Inputs and authority

Supply explicit machine-local bindings and a `mindgarden.session/v1` session
whose allowed visibility is exactly `public`, review state exactly `approved`,
requested scope public, and publication authority `publishable`. The session must
permit `index`, `graph` and `llms`. Normal expiration, revocation, represented
revision and output-budget checks apply. Applying an export also requires the
target garden to be the session's explicit writable garden.

Use the existing `mindgarden.projection/v1` profile with kind `federation`, status
`planned`, public visibility and explicit human approval. `source_revision` pins
the current **authorized public view** from the index's `inputs`; this checkpoint
supports its `sha256:` form. `inputs` selects exact immutable knowledge/claim
references, including each claim's reviewed subject. Empty inputs mean an empty
projection. Garden and profile allowlists both apply. Empty kind/domain/topic
allowlists never grant publication for values absent from them.

Public visibility is separate from publication authority. Review-required and
never-exportable records and evidence closures are removed before bodies are
opened and before public revisions/counts are computed. Unknown scopes/policies
fail closed. Applying a proposal never manufactures review or factual authority.

`base_uri` is a credential-free canonical HTTPS base ending in `/`. Local literal
hosts/IPs, query strings, fragments, traversal, symlinks and ambiguous paths are
rejected. This validates declared routes; it does not perform DNS, HTTP, hosting
or network-isolation verification. V1 note routes are declared as
`<base_uri>notes/<id>/`; serving them is retained #17 acceptance. V0 routes remain
unchanged. Exact citations use logical source IDs/revisions/selectors, independent
of absolute source storage locations; HTTP source-serving is not implemented.

## Plan, apply and check

Create the export parent explicitly. The profile's portable `output_root` selects
the immutable bundle directory beneath `--output-directory`; parents must exist.
The example profile uses `federation`. Export targets cannot overlap canonical
`.garden` records or declared private vaults.

```sh
mindgarden federation build \
  --local-config "/private/bindings.json" \
  --scope "/private/public-session.json" \
  --profile "/private/reviewed-federation-profile.json" \
  --output-directory "/private/exports/revision-a" \
  --plan
```

Inspect the plan, then repeat with `--apply --plan-digest "<plan_sha256>"`.
Use `--check` to verify the existing bundle against current reviewed inputs.
Changed profile bytes, authority, destination or represented inputs invalidate
the plan. Plans are private control documents; do not publish their digests as
public lineage. Public descriptor revisions bind only the sanitized representation.

The directory contains `garden.json`, `index.json`, `graph.json`, `llms.txt` and
`.mindgarden-federation.json` (ownership marker). All are reproducible. The descriptor
binds the other public artifacts' SHA-256 hashes and byte sizes. The public index
contains selected reviewed knowledge/claims, canonical routes, exact citations,
uncertainty/attribution and inclusion reasons. Graph endpoints must belong to
that selection. Agent instructions identify all linked text as untrusted evidence.
No raw source bytes, local paths, private binding identities, session/profile
hashes or review identities/rationale are exported.

An identical re-apply verifies without changing files. A different, unowned or
incomplete directory is refused; use a fresh export parent and retain the old
one for inspection. The descriptor is written last, and readers verify all
members before using the index. Caught interrupted writes remove only files
created by that attempt where ownership/content can be verified. A crash may
leave an incomplete directory, which remains invalid; automatic repair, concurrent
writers, power-loss durability and destructive cleanup are not claimed.

## Supplied public catalog

The machine-local request uses `mindgarden.federation-catalog-request/v1`:

```json
{
  "schema": "mindgarden.federation-catalog-request/v1",
  "bundles": [
    {
      "directory": "/private/exports/revision-a/federation",
      "expected_revision": "sha256:<exact-public-descriptor-revision>"
    }
  ]
}
```

```sh
mindgarden federation catalog --input "/private/public-catalog-request.json"
```

Only explicitly supplied public bundles are read. The catalog contains canonical
links and selected public metadata, never copied note bodies or machine locations.
Input order does not affect output. Missing, incompatible, stale and corrupt
inputs produce a `partial` catalog with generic stable diagnostic codes while
verified gardens remain usable. Duplicate garden identities or conflicting
canonical homes quarantine all conflicting entries, rather than choosing a winner.
A complete catalog exits `0`; partial coverage exits `3` with the JSON result on
stdout. Other contract failures use existing CLI diagnostics/exit codes.

At most 16 bundles and 10,000 aggregate records are supported. Each serialized
artifact is limited to 2,000,000 bytes and a bundle to 8,000,000 bytes. Session
candidate limits apply before selection; an incomplete selection fails rather
than silently publishing a truncated garden. The agent entrypoint also respects
the session context-byte budget. Large-corpus runtime/memory proof remains #12.

Checksums establish content consistency, not origin authentication, actual human
approval or factual truth. Incoming descriptors remain untrusted producer
assertions. Freshness means agreement with the explicitly selected immutable
revision, not an inferred claim that a remote garden is current or available.

## Reproduce and remaining acceptance

Run the committed synthetic two-garden proof from a new or empty workspace:

```sh
python3 scripts/federation_demo.py --workspace ".cache/federation-demo" \
  --report ".cache/federation-demo-report.json"
python3 -m unittest tests.test_federation
```

The proof compares rebuilt artifacts with committed golden files, verifies
exact source references, relocates the export, rebuilds from a clean synthetic
garden and reproduces the same catalog. Network/process entry points are blocked
in-process and provider environment is cleared; this is not host isolation proof.

The schemas and [coverage ledger](open-issue-coverage.md) retain #16's remaining
private/internal local federation, incremental refresh, signature/authentication,
remote query/serving, rendered route, Akashic/Aether and actual consumer acceptance.
No site is deployed and no parent issue is closed. #30 can consume the supported
identity/version contract, while broader registry/platform/runtime gates remain.

## Verification evidence — 2026-11-05

The bounded implementation [#66](https://github.com/egohygiene/mindgarden/pull/66)
and roadmap [#65](https://github.com/egohygiene/mindgarden/pull/65) are merged
after explicit maintainer authorization. Main `44cc1e8` has the tested `5f39fc2`
tree. The preparation receipts below retain their original branch/revisions;
merging did not ratify ADR-0011 or complete #16. The combined review branch was
`feature/16-local-federation-projections`, based on B0 `3caea8d`. Functional commit:
`015f39676387a4e00c338fdb017a98c6cd11b821`; the verified clean-source archive
was `9149b2f8421936f0c5723fb068812f82acd27e38` (merging B0 documentation only).
The later registry checkpoint [#67](https://github.com/egohygiene/mindgarden/pull/67)
also reproduces these public golden bytes with managed named-view sessions.

| Command/check | Observed result |
| --- | --- |
| `.venv/bin/python -m unittest discover --start-directory tests` | 159 passed, no skips; Python 3.12.14 |
| `.cache/python313/bin/python -m unittest discover --start-directory tests` | 159 passed, no skips; Python 3.13.5 |
| `.venv/bin/python -m unittest tests.test_federation --verbose` | 20 passed |
| `.venv/bin/python -m build --sdist --wheel --outdir .cache/dist` | Fresh artifacts built; distribution/resource checks pass |
| Both interpreters: `-m compileall -q src scripts tests` | Passed |
| `node --version`; `git diff --check` | v24.19.0; passed |
| Clean source `-S --require-source`, isolated wheel `-I --require-installed` | Federation report matches committed golden byte-for-byte in both modes |
| Installed v0 `--version`, `validate`, `verify`, `publish verify` | 0.1.0; 3 notes/1 context pack; 2 deterministic public notes |
| Installed environment distribution inventory | Only `mindgarden`; no runtime Python dependencies |
| Clean source private archive/vault proof | Original committed private-workflow report still matches exactly |
| Pinned Hygiene/Aether owner checks | Five ADRs retain proposed/null approval; policy/set/schema/index and continuity schema/headings/limits pass |
| Coverage inventory | Exactly 38 unique issue rows; no parent issue closed |

Exact clean-source and wheel commands, from the repository root with fresh
paths (the observed `HEAD` was the archive commit above):

```sh
mkdir .cache/federation-clean-checkout
git archive --format=tar HEAD | tar --extract --directory .cache/federation-clean-checkout
PYTHONPATH=.cache/federation-clean-checkout/src .venv/bin/python -S \
  .cache/federation-clean-checkout/scripts/federation_demo.py --require-source \
  --workspace .cache/federation-clean-proof --report .cache/federation-clean-report.json
cmp tests/fixtures/federation/expected-proof.json .cache/federation-clean-report.json
.venv/bin/python -m venv --without-pip .cache/federation-wheel
python3 -m pip --python .cache/federation-wheel/bin/python install --no-cache-dir \
  --disable-pip-version-check --no-index --find-links .cache/dist mindgarden==0.1.0
.cache/federation-wheel/bin/python -I scripts/federation_demo.py --require-installed \
  --workspace .cache/federation-installed-proof --report .cache/federation-installed-report.json
cmp tests/fixtures/federation/expected-proof.json .cache/federation-installed-report.json
PYTHONPATH=.cache/federation-clean-checkout/src .venv/bin/python -S \
  .cache/federation-clean-checkout/scripts/private_garden_demo.py --require-source \
  --workspace .cache/private-after-federation-clean --report .cache/private-after-federation-clean.json
cmp tests/fixtures/conversation-archives/expected-proof.json .cache/private-after-federation-clean.json
```

Hosted main [Test run 41960090464](https://github.com/egohygiene/mindgarden/actions/runs/41960090464)
and B0 [Test run 41963994340](https://github.com/egohygiene/mindgarden/actions/runs/41963994340)
succeeded. B1 [Test run 41965122996](https://github.com/egohygiene/mindgarden/actions/runs/41965122996)
also succeeded on `9149b2f8421936f0c5723fb068812f82acd27e38`, containing the
verified functional code. Later documentation-only heads may have fresh checks;
see the draft's current checks. No workflow was manually dispatched.

## Rendered discovery and reusable public garden references

The follow-up adapter accepts a completed local rendered site with an exact
public descriptor revision **and** the SHA-256 of its complete site manifest.
It verifies all site bytes, reconstructs the standalone federation ownership
marker in memory, and proves that rendered routes exactly cover the selected
public index. It consumes machine artifacts; it does not scrape page HTML.

A catalog input can declare `format: "rendered-site"` and
`expected_manifest_sha256`. The default remains the existing standalone bundle.
A manifest pin cannot be silently ignored for a standalone input. Every source
remains explicitly supplied; no URL, provider, local garden or registry is fetched
or discovered automatically.

Verified rendered sources expose `mindgarden.garden-package/v1`: publisher garden
and canonical URI, public represented revision, descriptor hash, rendered revision
and manifest hash, with `read-only`, `data-only` authority. It is a portable
reference to public reviewed data. It preserves publisher ownership and does not
approve the content as the consumer's own knowledge. Local paths and project
selection remain outside this reference. Installing executable skills, remote
acquisition, automatic updates, dependency resolution and project lockfiles are
separate future work. Existing scoped canonical search/context is unchanged;
this checkpoint does not introduce a competing package-session authority model.

An optional `previous` catalog produces deterministic `added`, `unchanged`,
`updated` and `not-retained` states. A changed rendered-manifest pin is an update
even when the selected knowledge revision is identical. Missing, stale, invalid
or conflicting current inputs contribute **no** previous records as fallback.
Diagnostics contain stable codes and no acquisition paths or payload text.

`garden_reference_demo.py --workspace /tmp/new-reference-proof --require-source`
reproduces committed authored-renderer fixtures with networking and process calls
blocked, and proves relocation and refresh behavior. This is a contract fixture,
not a real renderer invocation. Separately, the adapter verified the previous
actual pinned offline Quartz artifact: 60 complete files and 3 canonical routes,
manifest SHA-256 `c6e7b74c84acc25e235f728989a6b860616b27cdbbfdcdcdb7d9bd87a6c0549d`.

Akashic #176 and Aether #69 were refreshed: both are open, with no comments.
Akashic owns a provisional projection preserving its catalog/Atlas IDs and review
versus observation semantics; no generic Markdown/site fixture proves that
integration. Aether owns the broader session capability contract. Private/internal
federation, signatures/authentication, remote acquisition/serving and their real
consumer proofs remain unavailable or unproven; the descriptor advertises those
limits. The reusable-package direction remains a proposed decision.
