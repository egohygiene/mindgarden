# Rehearse a private bookmark cleanup

Start with one explicitly selected Chrome profile. Mindcap snapshots the
bookmarks and packages the exact evidence. Mindgarden writes a private inventory
and produces an HTML import after you review the contents. Akashic's public
handoff is tracked separately. [Bookmark workflow #48](https://github.com/egohygiene/mindgarden/issues/48)

## Try the synthetic path first

Use the pinned Mindcap checkout `7ee766c1c34adad239fc602499f624979a2d9cac` and
its Python environment. Run this from the Mindgarden checkout with
`MINDCAP_CHECKOUT` and `MINDCAP_PYTHON` set to those locations.

```sh
PYTHONPATH="$MINDCAP_CHECKOUT/src" "$MINDCAP_PYTHON" \
  experiments/capture_handoff/check.py --rehearse-private-cleanup \
  --fixture-directory "$MINDCAP_CHECKOUT/tests/fixtures/chrome_bookmarks/multiple_profiles/User Data"
```

The rehearsal runs Mindcap's actual producer against two committed fixture
profiles. It inspects the verified ZIP in the normal Mindgarden CLI, plans and
applies two one-item batches, and replays the plans. The resumed HTML, JSON and
quarantine files match a single-batch run byte for byte. It retains and renames
the HTTPS bookmark and preserves the app-specific bookmark in quarantine. Each
export retains its original ZIP, and the later capture invalidates the earlier
approval. Networking is blocked in the rehearsal process, which prints only
the summary. [Verification receipt](evidence/bookmark-pilot-rehearsal.json)

## Prepare a selected local capture

This is the operator procedure for a future approved personal pilot. Store the
workspace under an owner-only directory outside Git and outside the canonical
garden. On macOS, verify the Chrome profile directory you want in
`chrome://version`. Aim for a small first profile or rehearsal copy. The
verified ZIP and generated bundle have size limits. A source over the bundle
limit needs a smaller input rather than a trimmed or altered original.

```sh
umask 077
PILOT="$(mktemp -d "$(cd "$HOME" && pwd -P)/bookmark-pilot.XXXXXX")"
CHROME_ROOT="$HOME/Library/Application Support/Google/Chrome"
PROFILE_DIRECTORY="Default" # Replace with your selected profile directory.
mindcap capture chrome-bookmarks --strategy filesystem \
  --user-data-dir "$CHROME_ROOT" --profile "$PROFILE_DIRECTORY" \
  --output "$PILOT/capture"
# Substitute the finalized version directory printed by Mindcap.
CAPTURE="$PILOT/capture/archives/chrome-bookmarks/<source-id>/v1"
mindcap verify "$CAPTURE"
```

The producer exposes packaging as a Python API. For one selected profile, the
following snippet maps its observed capture ID to a logical alias you choose.
Use the same logical alias and source ID across future captures of that same
profile. The alias belongs in the private workspace. [Mindcap's pinned handoff](https://github.com/egohygiene/mindcap/blob/7ee766c1c34adad239fc602499f624979a2d9cac/docs/source-bundle-handoff.md)

```sh
"$MINDCAP_PYTHON" - "$CAPTURE" "$PILOT/bookmarks.zip" <<'PY'
import json
from pathlib import Path
import sys

from mindcap.plugins.chrome_bookmarks.handoff import bookmark_source_bundle

capture, destination = map(Path, sys.argv[1:])
manifest = json.loads((capture / "manifest.json").read_bytes())
normalized = json.loads((capture / manifest["normalized_path"]).read_bytes())
if len(normalized["profiles"]) != 1:
    raise SystemExit("Select one captured profile for the first rehearsal.")
profile = normalized["profiles"][0]
payload = bookmark_source_bundle(
    capture,
    source_id="private-browser-source",
    producer_revision="7ee766c1c34adad239fc602499f624979a2d9cac",
    profile_identities={profile["profile_id"]: "browser-profile-1"},
)
with destination.open("xb") as output:
    output.write(payload)
PY

printf '%s\n' '{"schema":"mindgarden.local-bookmark-catalog/v1","urls":[]}' \
  > "$PILOT/catalog.json"
mindgarden bookmarks --classification personal --input-format captured-source-bundle \
  --input "$PILOT/bookmarks.zip" --catalog "$PILOT/catalog.json" \
  --inspect --plan-file "$PILOT/inventory.json"
```

The explicit empty comparison catalog tells Mindgarden that this first pass has
no comparison list. `inventory.json` contains private bookmark metadata and
exact evidence. Open it locally. A Chrome Bookmark Manager HTML export is a
different shape from this ZIP. If HTML is the only artifact available, keep it
private and use it as a backup. Akashic's existing offline parser can inspect
that format in its own ignored local workspace. It does not create the verified
Mindcap ZIP for Mindgarden. [Akashic offline intake](https://github.com/egohygiene/akashic/blob/dc21c6a24506d748deb45f29ce54fc7e7bf69753/docs/bookmark-intake.md)

## Review and inspect the cleaned import

Choose the first few records in inventory order. Author a request with their
exact IDs, the inventory's source and catalog digests, and the existing local
policy reference. Use `offset: 0` and a `limit` equal to the first batch size.
The request requires one disposition per record. Choose `defer` for an
unresolved item. A merge requires an exact matching URL and an explicitly
retained target in the same or an earlier batch. Keep publication approval
false for this personal cleanup. [Request schema](../contracts/v1/bookmark-review-request.schema.json) · [Decision schema](../contracts/v1/bookmark-decision.schema.json)

Get the request's `policy` object from the same Python environment as the
Mindgarden CLI.

```sh
python -c 'import json; from mindgarden.domain.scope import POLICY_REFERENCE; print(json.dumps(POLICY_REFERENCE))'
```

Preview with `--request "$PILOT/request.json" --plan-file "$PILOT/plan.json"`
using the same classification, format, ZIP and catalog options as the inspect
command. Omit `--inspect`. Review the private plan file. Once the request
records your explicit human approval, preview again using a fresh plan file and
apply with `--apply --plan-digest <digest-of-final-approved-plan>` and
`--output-directory "$PILOT/export-01"`. Each changed plan or batch gets a new
file and export directory. Use the prior `review-receipt.json` and its exact
SHA-256 for the next batch. [Review and resume reference](bookmark-cleanup.md#local-review-flow)

Open `cleaned-bookmarks.html` locally in a text editor and compare the planned
titles, folders and omissions. Check `complete_review` in
`cleaned-bookmarks.json` and inspect `quarantine.json` for excluded entries. For
a browser check, manually import the HTML into a disposable Chrome profile
with sync disabled. After review, choose whether to import it into your usual
profile. The export adds bookmarks where Chrome imports them. Treat it as a
separate folder to review and keep the existing bookmarks in place until you
are satisfied. The original capture and previous exports remain available to
reproduce the cleanup or start another import.

## Remaining integration contracts

- Mindcap's current main `d58a3d18` still carries the proposed verified handoff
  from PR #42. Recurring verified deltas, cursor/reset behavior and broader
  consumer acceptance remain in #35. [Mindcap #35](https://github.com/egohygiene/mindcap/issues/35)
- Akashic main `dc21c6a2` has private intake. Its offline freshness join is in
  draft #226 at `d646333`; the existing cleanup keeps observed redirects
  deferred until a compatible accepted observation contract is available.
  [Freshness #173](https://github.com/egohygiene/akashic/issues/173) · [Intake umbrella #41](https://github.com/egohygiene/akashic/issues/41)
- The cross-repository boundary, accepted sanitized publication contract and
  generated public projection are still open. Mindgarden emits a fixed
  unavailable handoff status and retains all candidate evidence locally.
  [Boundary #174](https://github.com/egohygiene/akashic/issues/174) · [Candidate intake #175](https://github.com/egohygiene/akashic/issues/175) · [Public projection #176](https://github.com/egohygiene/akashic/issues/176)

The rehearsal verifies exported bytes. The actual Chrome import check, private
pilot, independent per-item public approval and Akashic draft PR are still
ahead. The local output is a cleaned bookmark import and private evidence. A
separate reviewed curation plan is needed to turn selected bookmarks into
searchable garden knowledge.
