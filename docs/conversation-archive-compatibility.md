# Conversation archive adapter checkpoint

`conversation-archive` 1.1.0 consumes an explicitly supplied ZIP. It performs no
acquisition, model calls, remote routing, persistence, publication, or execution of
transcript instructions. Human curation remains a separate authored plan.

The authoritative specifications were refreshed on 2026-11-06: v1.2.1, v2.0.0,
the v2.0.1 delivery patch, v3.2.2 and v3.2.3, including the approved ChatGPT copy dated
2026-10-30, marked `active` and `unpiloted-contract`. They were read through the
authorized document connector. Private specification bodies, provider identifiers,
and actual archives are outside this repository. This importer does not claim
that either producer workflow has been piloted.

| Contract | Tested package/evidence interpretation | Explicit boundary |
| --- | --- | --- |
| v3.2.2 and v3.2.3, §6, §7, §26 | Envelope `3.2`, preservation controls `2.0`, strict JSON, single-unit ZIP, exact SHA-256 inventory | Collections and multipart packages remain untested; see the historical profiles below |
| Full-source, §7–8 | Original ZIP, message IDs, native IDs, speakers, ordered content, source records, branch graph, reading view, available times, assets and unavailable-asset states | No chronology inferred from absent times; no text/title/filename matching across unrelated archive identities |
| Summary/journey, §6, §9 | Stable journey headings, exact UTF-8 byte spans, optional machine-index agreement, summary-derived status | No invented messages, speakers, timestamps, or verbatim transcript coverage |
| Delivery, §6.2 | Primary/fallback attempt history retained independently of normalized evidence | Packaging transport failure is not source incompleteness; no external delivery claims verified |
| Producer validation | `pass` or `incomplete` retained; reported failures rejected | Importer checks are `package-integrity-and-evidence-structure`, never full producer conformance |

The prose leaves complete wire schemas for some manifest aggregates unspecified,
including `source_scope`, `counts`, and `schema_registry`. These remain opaque
preserved metadata. The importer checks versions on known actual controls rather
than inventing those aggregate schemas. Creative, editorial, and archive knowledge
handoffs are preserved inside the immutable package; they are not implicitly
converted to approved Mindgarden knowledge. External predecessor references and
producer routing/execution outcomes are not independently verified. These are
compatibility gaps, not claimed support for all producer acceptance criteria.

Normalized message identity is `(archive_id, message.id)` plus its content hash.
Identical messages in overlapping revisions reuse evidence records and content
objects. Each newly observed ZIP adds immutable capture/provenance without
rewriting the earlier attribution. The same text in an unrelated archive does
not prove conversation identity. Attachment bytes are retained independently;
no media or executable content is opened as instructions. Explicitly restricted
attachments require an encrypted adapter unavailable in the filesystem baseline.

ZIP handling rejects traversal, links, special/encrypted members, ambiguous
case/Unicode paths, duplicate keys, missing/extra inventory members, bad checksums,
and unresolved local message/branch/asset references. Bounds are 100 MiB captured,
4,096 members, 64 MiB/member, 256 MiB expanded, ratio 200, and 10,000 records/units.
No extraction to arbitrary filesystem paths occurs.

The committed `tests/fixtures/conversation-archives` members are synthetic importer
fixtures, with explicitly incomplete upstream producer validation. Tests construct
deterministic ZIPs for both versions and profiles and exercise fallback packagers,
overlapping exports, hostile packages, and archive-to-reviewed-prompt curation.

```sh
mindgarden ingest --repository-root /private/garden \
  --local-config /private/bindings.json --vault-id private-sources \
  --input /private/captured.zip --source-id supplied-archive \
  --title "Supplied archive" --origin urn:private:archive \
  --captured 2026-11-04T00:00:00Z --owner local-owner \
  --rights "Private source; no publication permission" \
  --media-type application/zip --adapter conversation-archive \
  --manifest-version 3.2.3 --plan
```

Apply the same inputs with `--apply --plan-digest SHA256` after inspecting the
preview. Changed ZIP bytes, bindings, or canonical records invalidate that digest.
Refs #15, #11, #13. Historical-format migration, producer integration, and broader
archive acceptance remain parent scope.

## Historical compatibility and selective attachments

`conversation-archive-v1` 1.0.0 accepts explicitly selected v1.2.1 ZIPs using
§6's minimal single-unit layout and conversation schema `1.0`. Optional §8.2
asset inventories are checked when present; checksums are verified when supplied.
Required files and source messages are synthetic committed fixtures. Missing IDs
use a conversation-snapshot hash plus index, explicitly marked snapshot-local;
they do not imply cross-export continuity. Observed IDs use the caller's explicit
source namespace. Unknown timestamps stay unknown. Original runtime asset paths
stay inside the preserved ZIP, outside portable catalog metadata.

The v2.0.1 document is a delivery patch requiring v2.0.0. Both were read: envelope
`2.0`, preservation `2.0`, mandatory source/asset/validation controls, and the
non-recursive two-pass SHA-256 packaging contract differ from v1. A conforming
v2.0.1 reader and fixture matrix are **not implemented**. Selection fails with
`ADAPTER_UNSUPPORTED`; availability of the specifications is no longer the
blocker. Do not reinterpret it as v3.2 or claim v2 producer compatibility.

Current and legacy readers accept an explicit `attachment_selection` with mode
`all`, `catalog-only` or `selected` and `asset_ids`. Legacy asset IDs are their
portable archive paths. The CLI exposes `--attachment-mode` and repeatable
`--asset-id`. Default `all` preserves existing behavior. Unselected attachments
produce separate catalog identities, while selected units retain the exact byte
identity. Every declared checksum is checked even for unselected bytes. The raw
ZIP remains immutable and complete; selection controls normalization, not storage
redaction. A restricted original still requires an unavailable encrypted boundary.

Only known package controls are parsed as JSON. Attachment JSON remains opaque
source evidence. Catalogs, messages and available branch/time metadata are not
curation approvals. Tests prove v1.2.1 → authored review → exact-source search,
overlap identity limitations, selection and malformed-package rejection with
network/process execution blocked. Real provider archives and full producer
workflow conformance remain separate acceptance work.
