# Caller-owned portal composition

Mindgarden builds/checks the garden artifact and ownership manifest. Relay owns
workflow orchestration. Consumer repositories own the final portal, publication
authority, host settings and deployment. This checkpoint composes local supplied
public artifacts; it does not deploy or grant publication authority.

First build a reviewed public site through [the v1 adapter](v1-site.md). Then
author a private `portal-request/v1` control file:

```json
{
  "schema": "mindgarden.portal-request/v1",
  "classification": "machine-local-control",
  "publication": "never-exportable",
  "source": {
    "directory": "/explicit/public-site/garden",
    "expected_revision": "sha256:<64 hexadecimal characters>",
    "expected_manifest_sha256": "<64 hexadecimal characters>"
  },
  "portal": {
    "directory": "/explicit/existing/portal",
    "base_uri": "https://example.test/project/",
    "mount": "garden"
  }
}
```

Use the site's `.mindgarden-site.json` revision and the SHA-256 of its exact
bytes. Obtain the manifest pin through the trusted producer/review handoff. An
unsigned supplied manifest proves integrity against that pin, not authenticity,
review authority or absence of all possible sensitive content. Do not derive the
expected checksum from an untrusted download and call that authentication.

```sh
mindgarden site compose --input request.json --plan
mindgarden site compose --input request.json --apply --plan-digest <reviewed-digest>
mindgarden site compose --input request.json --check
```

Planning reads explicit inputs and writes nothing. Application rechecks the
request, complete source membership/checksums and destination. Existing identical
outputs verify idempotently; conflicting caller files/receipts are retained.
Only the selected mount and new `.mindgarden-portal.json` receipt are owned.
Sibling content is neither scanned nor deleted. A nested mount requires its
parent directory to exist already. Symlinks, traversal, overlapping source/output
trees and unsupported schemas fail closed.

The portable receipt lists owned paths/checksums, exact site manifest pin,
represented revision, canonical base/mount, renderer commit and supported
contract versions. Machine-specific locations and control digests stay in the
private plan. Moving inputs/outputs requires a new local plan; the public receipt
remains reproducible. It contains no signatures or source-vault locations.

The complete garden is verified before the receipt is written. A failure before
that receipt must block artifact upload/deployment. A complete copy left by a
receipt failure can be verified and retried with the same unchanged plan. A
conflicting/truncated receipt or incomplete pre-existing garden is preserved for
inspection; use a fresh output directory instead of silently repairing it. There
is no power-loss atomicity claim across the whole portal or concurrent-writer
coordination. Whole-portal staging/promotion remains the deployer's responsibility.

For GitHub Pages project hosting, use portal base `https://owner.example/project/`
and site base `https://owner.example/project/garden/`. A dedicated subdomain can
use `https://notes.example/` plus `/garden/`. Non-Pages static hosts use the same
explicit HTTPS base/path contract. This command changes no DNS/CNAME or host
configuration. A changed base requires rebuilding the site, not rewriting URLs
after the manifest was checked.

The synthetic fixture composes garden, intelligence, decisions and history, tests
changed inputs/route pins, conflicts, failed receipts, retry and relocated clean
rebuilds. Its authored renderer fixture is distinct from #17's actual pinned
offline Quartz proof:

```sh
python -S scripts/portal_demo.py --require-source --workspace new-proof --report proof.json
python -m unittest tests.test_portal --verbose
```

## Relay compatibility gap

The inspected Relay revision is
[`b4a88db20bc26f9ddefbee174baa8162cbe94ff2`](https://github.com/egohygiene/relay/tree/b4a88db20bc26f9ddefbee174baa8162cbe94ff2).
[Relay #4](https://github.com/egohygiene/relay/issues/4) owns release/publication
profiles; [Relay #40](https://github.com/egohygiene/relay/issues/40) specifically
owns the reusable Mindgarden validation/portal action. The pinned tree contains
other publication actions, but no Mindgarden action to claim as this integration.
Do not copy Relay's workflows into Mindgarden or invent an action version.

A future pinned action must install a pinned engine and renderer, run validation
and public gates, build into staging, check this final receipt, and emit artifacts
only on success. PR mode validates/previews without production credentials;
main mode promotes a fully checked portal through the consumer's deployment
authority. Actions and external renderers must use immutable pins. The local
contract and fixtures can advance before that independent owner proof. Actual
Relay/Empathy migration, hosting, promotion/rollback and production idempotence
remain open #18 criteria.
