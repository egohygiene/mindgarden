# Deferred context-package product phase

**Status: captured proposal, not selected for implementation.** Parent
[#86](https://github.com/egohygiene/mindgarden/issues/86) has native GitHub
sub-issues #87, #88, #91, #89 and #90, with the proposed order below.

## Scheduling boundary

The maintainer requested these ideas **after the existing 38-issue queue**, then
an end-of-roadmap reconciliation/refactor. At that point, review actual delivered
contracts and consolidate, split or retire duplicates before choosing a batch.
Completion or explicit disposition of the original queue and a later maintainer
activation are scheduling gates. New work does not become a prerequisite of old
issues, and open umbrellas must not be falsely closed to satisfy the gate.

Main observed for this plan is `b9cc3fd3b8b68e56944d592e2092b07485de465a`.
The #74–#85 implementation/receipt stack is merged; this planning change adds no
runtime, source access, storage migration or accepted architecture decision.

## Deferred sub-issue roadmap

| Proposed step | Issue / scope | Existing owners and contracts | First later checkpoint |
| --- | --- | --- | --- |
| D0: reconcile | [#86](https://github.com/egohygiene/mindgarden/issues/86): composed AI-assisted garden/context-package phase | #40/#42 architecture; #13 AI proposals; #46/#49 compaction and memory | Disposition old delivery and decide whether each follow-up is still needed |
| D1: connect | [#87](https://github.com/egohygiene/mindgarden/issues/87): Drive capture/refresh, chosen garden location and CLI orchestration | #11 captured-source boundary; #30 registry; #35 documents; #45 vault; #47 shared interfaces; Mindcap capture | One explicit synthetic source and duplicate-safe interrupted refresh |
| D2a: select packages | [#88](https://github.com/egohygiene/mindgarden/issues/88): data-only install/update/remove and project selections | #16 existing package/reference contract; #14/#29/#31; #51 portability | One immutable local package and two independently scoped projects |
| D2b: evaluate semantic view | [#91](https://github.com/egohygiene/mindgarden/issues/91): RDF/JSON-LD graph with PROV lineage and packet access | #12/#16 graph/context; #13 interpretation; #29/#31 policy; #42 decisions; #46/#49 summaries | One tiny scoped projection, loss/round-trip report and permitted/denied readers |
| D3: research | [#89](https://github.com/egohygiene/mindgarden/issues/89): optional AI research role returning cited context | #12 retrieval; #13 plans; #31 scope; #47 services; #51 portability; Aether/Realm boundaries | Two scripted planners, bounded local research and failure/revocation proof |
| D4: composed proof | [#90](https://github.com/egohygiene/mindgarden/issues/90): synthetic structured analysis and reviewed preparation packet | #11/#13/#29/#31/#35/#45; #32 projections if justified; #47 clients | Two small synthetic account exports, overlap/transfer ambiguity and a reviewed Markdown/JSON packet |

These are an order to reassess, not blanket sequential gates. Package and research
fixtures can run without Drive; RDF is an optional representation to evaluate,
not required for every package. The first preparation-packet proof can use local
inputs, authored questions and deterministic calculations without a model.

## Reuse existing work rather than duplicate it

#13 already owns optional extraction of summaries, entities, claims and relations
through reviewed gardenization plans. #46 owns progressive compaction and refresh;
#49 owns compact assistant-memory projections. #47 owns shared CLI/API/web domain
behavior, and #51 owns provider-continuity conformance. They remain in the original
queue. The new phase composes their completed contracts; it does not replace them
or promise that model-generated interpretation is already implemented.

The original 38 issue IDs are:
`1, 2, 5, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 26, 27, 28, 29,
30, 31, 32, 33, 34, 35, 37, 38, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 51`.
There are now 44 open tracked issues: that original cohort plus six deferred
items #86–#91. This count does not mean six more immediate implementation tasks.

## Where files live

The garden's portable records live in a user-selected directory. A private Git
repository can version that directory and optionally synchronize it through
GitHub. It is separate from the public Mindgarden software repository. Private
summaries, identities and metadata require private storage too.

Original documents can have Drive as their source. An explicit private binding
connects a logical source/vault identity to its provider and current location.
References bind stable provider identity, represented revision/export and content
checksum, not a folder path that may change. Required immutable snapshots remain
in a configured vault; provider history is not assumed retained forever.
Credentials, sync tokens and machine-specific roots stay outside portable records.
This is a proposed integration profile, not a currently installed Drive adapter.

## Packet, graph and instruction distinctions

A garden is durable reviewed knowledge. A package is a versioned collection made
available to a chosen project/session. A context pack is the bounded selection
for one task. Approved skills can supply procedures; imported package text cannot
grant instruction, execution or data-access authority.

RDF describes a graph, JSON-LD can serialize it, and PROV-O can express provenance
within it. #91 evaluates a projection/mapping over current records first. These
representations do not themselves create semantic compression or guarantee that
an overview contains every fact a later question may need. Human/AI interpretation,
review, coverage limits and exact source drill-down remain explicit.

“Need to know” maps to real task/session permissions and inherited sensitivity,
with expiry and revocation. Installing a package does not unlock access. Filter
facts, relationships, provenance paths, identifiers and counts before model access
or output. This analogy does not claim government-clearance or confidential-host
certification. Existing Hygiene/Realm owner contracts still apply.

## CLI experience and implementation status

The existing tool already exposes initialization, registration, supplied-source
import, authored proposal review, scoped search/context/evidence and vault
recovery. Current commands include `init`, `registry`, `ingest`, `gardenize`,
`scope`, `search`, `context`, `evidence` and `vault`.

A future convenience flow could configure the garden/source locations once,
connect a source, refresh changes, review candidates, select packages, research a
question and export a reviewed result. Config/connect/refresh/install names and
argument syntax are proposals to review, not commands claimed available today.
CLI, future API/web clients and agents must use the same application services.

No provider, graph database, model, serialization migration or frontend is selected
here. Core behavior remains useful with AI/network integrations disabled. Actual
personal sources or professional circumstances are outside this public plan;
public tests use synthetic fixtures. All ADRs remain proposed/null approval.
