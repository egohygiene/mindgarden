# Optional selected Drive capture

This bounded #87 checkpoint adds `capture drive`, a read-only Drive v3 adapter,
private local OAuth setup and a supplied-capture source adapter. It reuses the
existing garden, scope, immutable vault and normalization contracts. No Google
package, account, hosting, model or network is required for ordinary CLI use.

## Policy and storage

A versioned [binding](../contracts/v1/drive-binding.schema.json) explicitly selects
folders, optional file IDs, recursion/depth, MIME/export types and request/time/
byte limits, with initial human review and a supported personal scope. **Capture
requires `execution: controlled-import`. An offline scope is rejected before
provider access; `--allow-network` cannot override it.** Organization/restricted,
encrypted, unknown or conflicting policy stays unavailable in this checkpoint.

The captured manifest retains that controlled-import scope. Supply its exact
`source-scope.json` during separate normalization; importing into an offline
garden inherits the stricter offline policy. No existing source classification,
knowledge review or publication authority is weakened. These are explicit local
operator assertions, not confidential-host or organization identity assurance.

Files are addressed by provider ID, observed version and captured checksum.
Names/folder locations are hints, not identity. Uploads preserve original bytes;
native documents preserve an immutable **export snapshot**, not a fictional
downloadable native original or an assurance that Drive history persists forever.
Metadata is checked before/after each read and the collection is re-enumerated.
Partial/incomplete listings, changed versions, denied/missing files, unsupported
shared-drive metadata and corruption fail explicitly. Removal from a collection
is reported as unavailable/unlisted, not proof of deletion; old evidence remains.

## Configure credentials on the pilot machine

Follow Google's [desktop Python quickstart](https://developers.google.com/workspace/drive/api/quickstart/python)
to enable the API and obtain an installed-application OAuth client. The helper
requests [Drive read-only scope](https://developers.google.com/workspace/drive/api/guides/api-specific-auth);
Google consent/admin/verification requirements remain provider responsibilities.
That OAuth scope is account-wide read access; the narrower folder/file selection
is enforced by this application's reviewed binding, not by a folder-only OAuth
grant. The transport implements no remote write operation.
Use absolute, owned private paths outside Git and garden records. Keep these
files and their contents out of chat and this repository.

```sh
python -m pip install -r requirements/drive.txt
chmod 600 /private/credentials/desktop-client.json
mindgarden capture authorize --client-file /private/credentials/desktop-client.json \
  --token-file /private/credentials/drive-token.json
export MINDGARDEN_DRIVE_TOKEN_FILE="/private/credentials/drive-token.json"
```

The optional official `google-auth-oauthlib==1.5.0` handles PKCE/state and desktop
loopback consent. The listener is loopback-only with a 180-second consent wait;
token exchange uses the fixed Google endpoint, a 10-second network timeout and
no redirects. Credential files are private mode 0600 and cannot be stored under
Git or `.garden`. The normal capture transport reads a valid cached token and
never opens a consent flow or refreshes implicitly. To renew explicitly:

```sh
mindgarden capture authorize --refresh --token-file /private/credentials/drive-token.json
```

Refresh permits only the Google token endpoint, at most three calls within its
30-second network budget and per-call ceiling. SDK backoff is not application
work. SDK errors are sanitized; tokens are never printed. As an alternative,
local OAuth tooling may supply `MINDGARDEN_DRIVE_ACCESS_TOKEN`; configure one mode
at a time. There is no ambient account discovery, service-account fallback or
credential in portable records. POSIX private-file controls are required for the
credential-file helper; Windows credential mutation is not claimed supported.

## Capture, inspect, normalize and refresh

Prepare a local binding using the [synthetic example](../tests/fixtures/contracts/v1/valid/drive-binding.json)
as a shape reference, replacing IDs and review/configuration with your own. Its
test values do not authorize an account. Use an already initialized private vault:

```sh
mindgarden capture drive --input /private/drive-binding.json \
  --local-config /private/bindings.json --vault-id private-sources \
  --output-directory /private/capture-01
```

The preview binds the reviewed **acquisition operation**, not unknowable future
content. Inspect the scope, selection, destination and budgets; repeat with
`--apply --allow-network --plan-digest SHA256`. Every provider operation is GET
against the fixed Google API host, with redirects/proxies disabled, bounded
streaming and zero automatic capture retries. Selection/storage changes are
checked during acquisition and output. Credentials, raw provider errors and
sensitive file names do not enter ordinary error diagnostics.

Verified partial bytes enter the existing immutable vault. A private checkpoint
next to the output retains exact verified IDs/versions/content identities; an
interrupted invocation can resume. A leftover crash lock needs explicit operator
recovery; no unknown files or original objects are removed. New snapshots use new
immutable output directories. `--previous-checkpoint` reuses verified unchanged
objects for the same selection/review; it never overwrites the earlier checkpoint
or output. Changed selection needs a new review, and unavailable objects are not
silently repaired or treated as healthy.

Inspect `manifest.json` before the ordinary digest-bound import:

```sh
mindgarden ingest --repository-root /private/garden --local-config /private/bindings.json \
  --vault-id private-sources --input /private/capture-01/capture.zip \
  --source-id selected-drive-collection --title "Selected capture" \
  --origin urn:example:selected-drive-collection --captured 2026-11-13T00:00:00Z \
  --owner local-owner --rights "Explicitly supplied material" \
  --media-type application/vnd.mindgarden.drive-capture+zip \
  --adapter drive-capture --manifest-version 1.0.0 \
  --source-scope /private/capture-01/source-scope.json
```

Repeat with `--apply --plan-digest SHA256`. Source/scope file changes invalidate
the plan. This import normalizes supported text and the declared ledger CSV;
PDF/images are explicitly **preserved-only**, with separate document/media
processing still required. Native Docs export text without embedded media; Sheets
CSV represents **the first sheet only**. Arbitrary bank formats, conflicting row
versions within one package, unsupported exports and malformed packages are not
silently interpreted. Normalization and review remain separate: captured sources
stay unreviewed until the normal curation process is used.

Refresh does not automatically rewrite, approve or retire reviewed knowledge.
Reports represent their exact selected snapshots; checking one is not proof that
it contains the latest Drive version or every account. New content needs fresh
selected evidence/reconciliation and review. Wider dependency-aware freshness is
still #37/#46/#87 scope. Normalization is bounded to 1,000 units per supplied
capture; this checkpoint does not claim a whole-account or arbitrary-size import.

## Verified contract and remaining proof

Official v3 [file metadata](https://developers.google.com/workspace/drive/api/reference/rest/v3/files),
[listing](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/list),
[download](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/get),
[export](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/export)
and [export formats](https://developers.google.com/workspace/drive/api/guides/ref-export-formats)
were checked on 2026-11-13. Version includes metadata changes; it is not a native
immutable export revision. Native export has a provider 10 MB limit; this bounded
adapter imposes stricter declared file/collection ceilings. It does not follow
shortcuts or claim shared-drive, multi-sheet, historical-revision or all-MIME support.

The official OAuth SDK's actual 1.5.0 wheel API and SHA-256 were checked, and its
constructor was exercised offline with google-auth 2.62.2 / requests-oauthlib
2.0.0. [The observation](evidence/drive-sdk-observation.json) distinguishes that
from live consent/account access. Credential/provider tests run without SDK
installation, real credentials, paid services or model calls.

`scripts/drive_consultation_demo.py` composes two mocked captures, a rename/version
change, eight reused normalized rows, authored review, the searchable summary and
6,129-byte context, then exact packet/index/context/evidence after restore and
relocation. Thirteen immutable objects and both snapshots remain. The
[complete golden](../tests/fixtures/consultation/expected-drive-proof.json) uses a
synthetic provider; **live OAuth, actual Drive and the real private pilot remain
unperformed**. Wider platform/private-Git/provider assurance and parent acceptance
stay open. A browser app, hosted service and model provider are not selected here.
