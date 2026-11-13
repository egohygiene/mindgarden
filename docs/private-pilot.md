# Run the selected local pilot

The software checkpoints are merged through #147 at main `270ced6`; the
[current merge receipt](evidence/freshness-mapping-stack-merge.json) and
[remaining-work/setup plan](remaining-work-and-local-setup.md) preserve exact
evidence and the existing setup owners.
The actual private pilot has **not run**: the operating system, private workspace,
selected Drive folder IDs, local credentials and applicable classification/runtime
authority have not been supplied. No real account, original or financial content
was accessed. This guide and `pilot preflight` make the next operation concrete.

## Select the workspace and policy

Use the actual classification of the material. This first pilot supports explicit
ordinary personal policy on private, untracked POSIX paths. Restricted processing
remains unavailable without the actual confidential storage/runtime contract;
do not relabel records to get past that boundary. Windows credential/preflight
mutation and private Git deployment need their separate platform proof.

Keep the software checkout separate from three private sibling locations:
`/private/control` for configuration, `/private/garden` for portable knowledge and
`/private/sources` for immutable originals. Reports/captures get separate private
output directories. These are placeholders, not discovered or created user paths.
Choose new/empty locations, owned mode 0700, with controls mode 0600. Credentials
belong in a separate private folder outside Git and `.garden`.

Install an explicitly reviewed source checkout or locally built wheel. The engine
needs only Python 3.12/3.13. To prove it before connecting anything, run the three
synthetic scripts with new workspaces and `--check-golden --require-source`:
`consultation_demo.py`, `drive_consultation_demo.py` and `research_demo.py`.
The research preflight fixture needs a private directory outside Git (for example,
under a resolved `/var/tmp` on Linux). These scripts deliberately use synthetic
data, block network/process calls and refuse nonempty workspaces.

## Initialize an empty private garden and source vault

```sh
mindgarden init --repository-root /private/garden --garden-id personal-preparation \
  --title "Private preparation" --kind personal --visibility private --owner local-owner
```

Review the preview and repeat with `--apply --plan-digest SHA256`. Create the
private `/private/control/bindings.json` using this local-only shape with your
actual absolute paths. No credential, account number or remote URI is required:

```json
{
  "schema": "mindgarden.local-bindings/v1",
  "gardens": [{
    "id": "personal-preparation",
    "root": "/private/garden",
    "scope": {
      "schema": "mindgarden.scope/v1",
      "visibility": "personal", "persistence": "machine-local",
      "execution": "offline", "publication": "review-required",
      "policy": {
        "id": "mindgarden-local-single-user/v1",
        "revision": "sha256:fa8695b2cb501f893b541bd957f06f6931ae144dd9d3a285ed186d47bdfe55da"
      }
    }
  }],
  "vaults": [{"id": "private-sources", "root": "/private/sources", "adapter": "filesystem"}],
  "revoked_sessions": []
}
```

This complete scope uses the current draft local single-user policy. It is not
organization ratification or confidential-host assurance. Preserve the exact policy
revision; the Python helper `mindgarden.domain.scope.local_scope()` supplies the
installed version's ordinary local scope if the policy changes in a later release.

```sh
mindgarden vault init --local-config /private/control/bindings.json --vault-id private-sources
```

Review and repeat with `--apply --plan-digest SHA256`. The source vault is
independent of the garden location. Its machine path stays in local bindings;
portable evidence references use logical IDs, exact revisions and content hashes.

## Establish bounded read authority and preflight

Select a near-term future expiration with an explicit timezone offset. Author a
new private session filename; refresh always uses a new file after input changes:

```sh
mindgarden scope --local-config /private/control/bindings.json --session-id initial-read \
  --readable-garden personal-preparation --allowed-visibility personal \
  --allowed-review-state approved --execution offline --publication-authority never-exportable \
  --request-visibility personal --max-results 100 --max-context-bytes 262144 \
  --expires-at FUTURE_RFC3339 --output /private/control/initial-read.json

mindgarden pilot preflight --local-config /private/control/bindings.json \
  --scope /private/control/initial-read.json --garden-id personal-preparation \
  --vault-id private-sources --classification personal
```

Preflight reads only explicit configuration and authorized metadata, checks live
session policy/revisions and initialized filesystem-vault metadata, and writes
nothing. It does not scan originals, contact Drive, invoke a model or audit every
object. `ready-to-attempt` is not content approval, live authentication, verified
backup or a completed pilot. Use actual classification; the flag cannot supply
external confidential assurance or authorize unseen content.

## Capture a small reviewed collection, then import separately

Follow [selected Drive setup](drive-capture.md) for official optional OAuth,
private credentials and a reviewed `drive-binding/v1`. Explicitly choose folder
IDs, supported formats/exports, recursion and budgets. Google read-only consent
is account-wide; the application's reviewed selection narrows actual reads.
Add `--drive-binding /private/control/drive-binding.json` to preflight. Missing or
expired credentials produce `blocked`; a present cached token is still not live
authentication. Do not paste credentials into chat.

Use the guide's `capture drive` preview and reviewed apply, then its separate
`ingest --source-scope` preview and apply. Start with one small selected collection.
Supported text and declared six-column ledger CSV are normalized. The separate
[reviewed CSV mapping adapter](csv-ledger-mappings.md) now handles explicitly
supplied UTF-8 CSV in the two declared layouts. Its reviewed mapping and original
identity must be preserved. Automatic Drive-capture-to-mapped-CSV composition
remains a proposed #87/#90 checkpoint; do not assume that supplying a Drive ZIP
applies a per-file mapping. Other layouts remain unsupported until explicitly
reviewed; transaction IDs, amounts and coverage are never guessed.
Drive PDF/images are preserved-only, with separate document extraction/policy
acceptance required. Native Docs/Sheets exports declare their losses.

Captures, checkpoints, originals and all review configuration stay private.
Keep the complete normalization preview: its exact normalized source citations
are inputs to review and the explicit `source_grants` wrapper. Refresh uses a new
capture directory and `--previous-checkpoint`; old evidence remains. Neither
refresh nor successful import approves a summary or makes an old report current.

## Review, retrieve and create the preparation packet

Use [the packet guide](consultation-packets.md) to author a private
`consultation-request/v1`: exact source citations, selected date/account/currency
scope, explicit revision choices, classifications, transfer pairing, observed
versus declared coverage, attachments and unresolved questions. Synthetic fixture
values are shape examples, not judgments about your finances.

Create a private wrapper `{"source_grants": [EXACT_NORMALIZED_SOURCE_REFERENCES]}`.
Author a fresh session with the selected exact grants and `--projection
source-evidence` plus each needed read projection (`search`, `graph`, `backlinks`,
`context`, `evidence`, `index`). The existing source-grant boundary remains
personal, machine-local, offline and never-exportable. A grant is permission to
inspect exact source evidence, not knowledge review.

Use ordinary `gardenize` preview/plan/apply for a separately authored summary
and explicit human review. Refresh the read session after curation. Then search,
inspect exact citations, build a bounded context and preview `packet`. Review
the actual calculated totals, gaps and selected normalized evidence before applying
the exact plan digest to a new private output directory. The packet is Markdown/
JSON plus selected normalized evidence; it is not a raw-statement/PDF export,
source-backed balance sheet, financial completeness or legal interpretation.

## Attach the assistant and verify recovery

Use [the scoped Codex profile](../profiles/agent/codex.md) and [research guide](scoped-research.md)
for ordinary CLI research. Review actual consumer/runtime policy before any private
context reaches an assistant. The current offline local session **does not grant
hosted-model access**. Until that boundary is established, Codex can help with
synthetic/configuration/code and the deterministic local packet works without a
model. No global agent configuration or account is changed by these commands.

Run `vault audit`, then explicit reviewed `vault export`, `restore` and `relocate`
plans using new private destinations. Preserve originals/backups and rebind the
same logical vault identity. Author a fresh session, rebuild the index/context
and compare exact packet/evidence references. Do not delete or replace originals.
Record the tested source revision, commands, results and gaps privately; only a
redacted synthetic receipt belongs in this public repository.

The exact next action is to select the OS/workspace/folder and verify the actual
policy/runtime/credential setup locally. Then run this non-destructive preflight
and a small explicitly approved capture. #20's real archive, Empathy, publication
and broader consumer acceptance, and #87/#89/#90 parent scope remain open.
