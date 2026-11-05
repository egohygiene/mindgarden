# Machine-local registry checkpoint

This is the bounded #30 tool capability on draft
[#67](https://github.com/egohygiene/mindgarden/pull/67), branch
`feature/30-local-registry`, based on merged main `44cc1e8` (#65/#66).
It uses existing v1 gardens, scope policy, sessions and bindings. Implementation
and synthetic testing do not configure the user's real gardens. Proposed
[ADR-0012](decisions/ADR-0012-machine-local-registry.md) records the decision;
acceptance and implementation status remain independent.

## Contract and dependency boundary

`local-bindings/v1` remains the runtime document. Its optional `registry` field
contains versioned management metadata: manifest-derived owners/labels/revisions,
named selections and view-generation high-water marks. It is not another source
or knowledge store. Existing explicit bindings and supported v0 commands remain
usable. Registry registration itself requires an existing v1 manifest; migrate a
v0 garden through the existing reviewed migration flow first.

#29 supplies the implemented local scope contract; full organization policy is
still separate. #14 supplies stable ownership/routing semantics, without making
all existing-item move/split proofs prerequisites for registration. #16's public
identity/version contract is available on main; remote acquisition and full
private federation are not registry prerequisites. The registry reads supplied
canonical manifests rather than fetching catalog entries. Full restricted/runtime
acceptance still depends on compatible Hygiene #39/#40 and Realm #25/#60 evidence.
These are proposed bounded dependency corrections, not closure of those parents.

The current filesystem adapter supports ordinary Linux single-user operation.
Platform location fixtures cover Linux/XDG, macOS and Windows conventions; native
macOS/Windows mutation, Dev Container host/mount semantics and host-specific
assurance are explicitly unsupported. The observed managed Linux test container
proves the ordinary single-user filesystem baseline only.
Restricted/encrypted registration is rejected before any root probe. Registering
a public garden does not supply publication authority or change its review policy.

## Private control locations

The default registry is `$XDG_CONFIG_HOME/mindgarden/registry.json`, falling back
to `~/.config/mindgarden/registry.json` on Linux. The macOS convention is
`~/Library/Application Support/mindgarden/registry.json`; Windows uses
`LOCALAPPDATA` or `APPDATA` plus `Mindgarden/registry.json`. These are location
conventions, not claims of native runtime support. An explicit `--registry` path
avoids any use of real default configuration during tests.

The registry and plan files use owner-only regular files (0600) in private
directories (0700). Symlink/traversal paths, canonical garden/vault locations and
actual Git workspaces are refused, including ignored folders inside a repository.
No Git executable is required. A sandbox's empty protected `.git` policy stub is
distinguished from an actual gitdir/HEAD. Registration roots are explicit and are
never discovered by crawling home, cloud-sync or repository-parent folders.

All registry plans/reports are **machine-local control data, never exportable**.
Plans include concrete paths and changed metadata so the operator can review the
actual effect. List/inspect hide the binding root unless `--include-local-paths`
is supplied; their identifiers/metadata remain private control information.
Diagnostics avoid copying paths or source text. Never publish a local plan or use
its hash as public garden lineage.

## Preview and apply

Every mutation starts with a saved preview; `apply` consumes that exact plan and
reviewed digest. The examples use an explicit private directory, not a repository.

```sh
mindgarden registry init --registry "/private/mindgarden/registry.json" \
  --output "/private/mindgarden/plans/init.json"
mindgarden registry apply --registry "/private/mindgarden/registry.json" \
  --plan "/private/mindgarden/plans/init.json" --plan-digest "<reviewed-plan-sha256>"

mindgarden registry register --registry "/private/mindgarden/registry.json" \
  --root "/private/synthetic-personal-garden" --garden-id "synthetic-garden" \
  --visibility "personal" --execution "offline" --publication "review-required" \
  --output "/private/mindgarden/plans/register.json"
```

Inspect that preview, then call `registry apply` with its saved file/digest.
Omitting `--output` prints a read-only preview. `--owner` asserts a canonical
owner; registration never changes it. Scope visibility/persistence/execution/
publication are independent. Duplicate identities, incompatible contracts,
nested garden/vault roots, changed manifests/root identities and stale plans fail
closed. Re-registering an identical binding verifies it; refreshing labels after
a compatible manifest change requires a new reviewed plan. Rebinding a root/scope
uses explicit unregister/register rather than an implicit move.

`registry init` can adopt an existing explicit binding file at the supplied private
location through the same review flow. Vault descriptors and revoked sessions are
preserved. Supported roots are inspected only at their manifests; source content
is not opened or changed. Ordinary registration does not claim a complete source
integrity audit; use the existing validation/audit workflows for that purpose.

## Inspect, diagnose and unregister

```sh
mindgarden registry list --registry "/private/mindgarden/registry.json"
mindgarden registry inspect --registry "/private/mindgarden/registry.json" --garden-id "synthetic-garden"
mindgarden registry doctor --registry "/private/mindgarden/registry.json"
mindgarden registry unregister --registry "/private/mindgarden/registry.json" \
  --garden-id "synthetic-garden" --output "/private/mindgarden/plans/unregister.json"
```

Unregister is a plan until explicitly applied. It removes the binding/management
entry and prunes affected named selections. It works when the old folder is
unavailable, without discovery or deletion. Canonical notes, sources, assets and
vaults stay untouched. Query projections/caches are retained; this checkpoint
performs no physical cache cleanup. Doctor reports missing/incompatible/stale
registrations and explicitly labels content integrity `not-checked`. A degraded
doctor exits `3`; healthy inspection exits `0` using stable JSON.

## Named selections and configuration recovery

`registry set-view --view-id "focus" --garden "project" --garden "personal"`
and `registry remove-view --view-id "focus"` create reviewed control plans.
Views select existing registered IDs; publication, allowed scopes, writable target,
review, execution and budgets still belong to explicit sessions. The session
pins its selected view before any root probes. Use `--registry-view` instead of
repeated `--readable-garden` arguments:

```sh
mindgarden scope --local-config "/private/mindgarden/registry.json" \
  --registry-view "focus" --session-id "local-review" \
  --allowed-visibility "public" --allowed-visibility "personal" \
  --request-visibility "personal" --publication-authority "never-exportable" \
  --expires-at "2099-01-01T00:00:00Z" --output "/private/mindgarden/session.json"
```

Choose an appropriate future expiration and explicit grants. Writable targets
must be members; a view never supplies write/review/publication authority.
Changed/deleted membership fails `SESSION_VIEW_STALE`; create a fresh session.
Registering an unrelated garden leaves existing named grants valid. Denied roots
are filtered before probes; unrelated private metadata is inert to public output.
Public artifacts match the existing explicit-binding golden byte for byte,
including when a private garden links to public knowledge or becomes unavailable.

Applies retain immutable private snapshots beneath `<registry-file>.history/`.
`registry restore --revision "<snapshot-sha256>"` previews a restore; apply still
requires the exact saved plan/digest. Restores preserve explicit revocations and
advance view generations, rather than reviving old named sessions. History is
owned, checksum-verified and retained; no automatic garbage collection occurs.
The filesystem baseline bounds control files to 2,000,000 bytes, 100 gardens/views,
1,000 view high-water marks and 1,000 configuration snapshots.

Registry writes use atomic replacement under a kernel writer lease. A failed
pre-commit write retains the previous complete configuration. After an uncertain
I/O outcome, inspect/doctor and repeat the exact accepted plan: it either applies
or verifies the already desired state. A crashed process releases its lease;
the owned lock inode stays in place. Host power-loss/isolation and hostile
concurrent filesystem mutation assurance remain separate runtime proof.

## Verification and retained scope

The [committed synthetic report](../tests/fixtures/registry/expected-proof.json)
comes from [the ordinary-CLI demo](../scripts/registry_demo.py). It adopts an
explicit synthetic vault descriptor, registers two v1 gardens, diagnoses them,
creates a named private union and public session, searches exact evidence and
generates a 5,691-byte public context within 16,384 bytes. A private-to-public
relationship appears only in the authorized private view. Public export bytes
equal the pre-registry federation golden. Unregister/restore preserves canonical
garden/vault bytes and leaves old named sessions invalid. Every apply is repeated
to verify idempotence. Managed plans/configuration/history live in a private
temporary directory outside Git and are removed when the demo exits; its
requested workspace contains synthetic garden fixtures only.

```sh
python3 -S scripts/registry_demo.py --require-source \
  --workspace ".cache/registry-demo" --report ".cache/registry-report.json"
cmp tests/fixtures/registry/expected-proof.json .cache/registry-report.json
```

Use Python 3.12/3.13 and a new or empty workspace. The demo clears integration
environment variables and blocks socket/HTTP/process calls in-process. This
proves useful dependency-free operation; it does not claim host isolation.
Platform-location fixtures cover Linux/XDG, macOS and Windows. Lifecycle and
adversarial tests cover input/root/digest drift, owner/scope conflict, unsafe or
public control files, bounded history without deletion, failed-write retry,
kernel leases, unavailable roots, no content reads during registration,
monotonic revocations/view generations, public noninterference before denied-root
probes, retained owned caches and reference JSON Schema parity.

Only synthetic fixtures and private temporary control directories are used. Full
#30 restricted coexistence, native platforms, organization/runtime assurance,
owned-query-cache cleanup and broad integration acceptance remain open. No parent
issue or proposed ADR is declared accepted by this local checkpoint.

## Verification receipt — 2026-11-05

Lifecycle commit `a47797b3d4ecb28052f42811eaa828f7868363ce` opened draft #67;
named-view/proof commit `3e654d3366ea20b61a30d73bcea6a5e64d2c06cc` and final
malformed-authority guard `8c3ed427e703c71a49dcdf79292e122e5823b3a1` complete
the functional checkpoint. The latter is the clean-source/wheel source below. Later evidence and
handoff commits are documentation only.

| Exact command/check | Observed result |
| --- | --- |
| `.venv/bin/python -m unittest discover --start-directory tests --verbose` | 187 passed, no skips; Python 3.12.14 |
| `.cache/python313/bin/python -m unittest discover --start-directory tests --verbose` | 187 passed, no skips; Python 3.13.5 |
| `.venv/bin/python -m build --sdist --wheel --outdir .cache/dist` | Fresh source/wheel built from functional commit |
| `.venv/bin/python -m unittest tests.test_distribution --verbose` | 2 passed against fresh artifacts, including registry modules/schemas/demo/fixtures |
| Both interpreters: `-m compileall -q src scripts tests` | Passed |
| `node --version`; `git diff --check` | v24.19.0; passed |
| Clean source `-S --require-source`, isolated wheel `-I --require-installed` | Registry report matches the committed golden exactly in both modes |
| Same two modes, `scripts/private_garden_demo.py` | Original archive/review/context/vault-relocation report still matches exactly |
| Isolated wheel command/library smoke | 10 checks passed, including v0 validate/verify/publish verify; no runtime dependencies installed |
| `python3 .cache/registry_owner_checks.py` (local orchestration of pinned owner validators) | Six proposed/null-approval ADRs, policy/schema/set/index, continuity schema/12 headings/limits and 38-row coverage inventory pass |

Owner checks load Hygiene's validator/schema at
`a05b14f8b9e2772124f879f818e09a911e996ad8` and Aether's continuity schema at
`b7597301c4d22a9bcd580967b5753138bb368111` from their checked-out repositories.
The local orchestration is not a new owner-policy implementation or a runtime
dependency; the CLI proofs below need neither owner repository nor third-party
test tools.

Exact proof commands from the repository root, using fresh paths:

```sh
mkdir .cache/registry-final-checkout
git archive --format=tar 8c3ed427e703c71a49dcdf79292e122e5823b3a1 | \
  tar --extract --directory .cache/registry-final-checkout
PYTHONPATH=.cache/registry-final-checkout/src .venv/bin/python -S \
  .cache/registry-final-checkout/scripts/registry_demo.py --require-source \
  --workspace .cache/registry-final-clean-proof --report .cache/registry-final-clean-report.json
cmp tests/fixtures/registry/expected-proof.json .cache/registry-final-clean-report.json
.venv/bin/python -m venv --without-pip .cache/registry-final-wheel
python3 -m pip --python .cache/registry-final-wheel/bin/python install --no-cache-dir \
  --disable-pip-version-check --no-index --find-links .cache/dist mindgarden==0.1.0
.cache/registry-final-wheel/bin/python -I scripts/registry_demo.py --require-installed \
  --workspace .cache/registry-final-installed-proof --report .cache/registry-final-installed-report.json
cmp tests/fixtures/registry/expected-proof.json .cache/registry-final-installed-report.json
PYTHONPATH=.cache/registry-final-checkout/src .venv/bin/python -S \
  .cache/registry-final-checkout/scripts/private_garden_demo.py --require-source \
  --workspace .cache/private-after-registry-final-clean --report .cache/private-after-registry-final-clean.json
cmp tests/fixtures/conversation-archives/expected-proof.json .cache/private-after-registry-final-clean.json
.cache/registry-final-wheel/bin/python -I scripts/private_garden_demo.py --require-installed \
  --workspace .cache/private-after-registry-final-installed --report .cache/private-after-registry-final-installed.json
cmp tests/fixtures/conversation-archives/expected-proof.json .cache/private-after-registry-final-installed.json
```

Automatic [Test run 42107523013](https://github.com/egohygiene/mindgarden/actions/runs/42107523013)
succeeded on initial lifecycle head `a47797b`; [run 42110373037](https://github.com/egohygiene/mindgarden/actions/runs/42110373037)
succeeded on named-view/evidence head `eb4bfb7`. Those are distinct from the
local checks of final functional `8c3ed42`; later pushed heads receive their own
automatic checks.
No paid workflow was manually launched or retried. The checkpoint is draft,
unmerged and not fully accepted; ADR-0012 remains proposed/null approval.
