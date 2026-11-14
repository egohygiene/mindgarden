# Synthetic decision input

`snapshot.json` adapts Observatory's synthetic
`fixtures/expected/egohygiene--relay.repository.json` at
`f411b83398dd07aa3d5e6e2c89d1e8dfff746085`. The only semantic addition is an
explicit fictitious approval under example.test. It proves adapter behavior;
it establishes no real decision authority. Full ADR bodies remain canonical.

## Typed public relationship fixture

`relationships-projection.json` extends the original entirely synthetic graph with
one organization-scoped decision in another repository, one superseded local
decision and explicit typed issue/PR/commit/release evidence. Its fictitious approval
assertions remain under example.test. Source metadata contains no real/private ADR
bodies or accounts. Collection claims describe this authored fixture only.

The projection is sorted in actual Hygiene contract order and has the required
producer generator contract. Its pinned schema/semantic validator, exact Observatory
normalization, exact Mindgarden golden and Relay native consumer pass are in
`owner-proof.json`; source revisions/hashes are in `owner-inputs.json`. These are
verified software integration facts, not factual approval/model accuracy evidence.
Unknown claim/component/projection kinds remain unsupported. Unit adversaries add
private/stale/unknown targets and credential/wrong-revision URLs without making
those malformed variants claimed valid owner fixtures.

`expected-relationships.json` is the bounded public graph/context golden. The same
schema example is in `contracts/v1/valid/adr-projection.json` under test fixtures.
The optional owner verification command and exact boundaries are in
[the guide](../../../docs/adr-projections.md).
