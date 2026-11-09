# Provider-switch recovery checkpoint (#51)

This scenario runs the same scoped request through two distinguishable local
adapter fixtures, removes the first adapter and its caches, and reconstructs
equivalent structured context from canonical sources. The implementation and source/installed-engine qualification are merged.
[The acceptance receipt](overnight-sprint.md) maps all nine #51 criteria to the
fixture, report and recovery tests. Native macOS registry support is not a semantic
prerequisite for this scenario. Refs #51. No live provider account, Google connection or model is required.

## Required contracts and integration proofs

Existing #12/#16/#29/#31 context, graph, evidence and session interfaces are the
required contracts. #45 supplies immutable source storage. #49 assistant-memory
and #47 API/web are related later surfaces, not blanket gates for this bounded
CLI-based recovery scenario. No second memory store or provider framework is
introduced. Optional future live-provider proof is different from local fixture
conformance and does not promise identical model wording or behavior.

The [fixture inventory](../tests/fixtures/provider-continuity/README.md) includes
reviewed preferences, a project goal, a transformed artifact, decision rationale
and alternatives, a correction, a deprecated earlier claim, exact sources and
typed relationships. Unselected private records and unreviewed proposals are
excluded before ranking or traversal. The report states the omission policy
without enumerating denied identities, counts, paths or text.

## Historical dependencies

The scenario exposed a real retrieval gap: current corrections depending on an
approved deprecated claim disappeared because metadata dependency validation
removed the historical claim first. Approved deprecated/archived records now
participate in dependency validation and sensitivity inheritance. They remain
subject to visibility, execution and review authorization and stay out of current
search, graph nodes and context ranking. A denied or unreviewed historical
dependency still removes its current derivatives. This preserves review and
privacy boundaries rather than dropping lineage to make the fixture pass.

The old claim is retained in canonical storage. Its exact reference appears in
authored, reviewed correction history; no API that grants unrestricted access to
inactive records is added. Current claim retrieval returns the weekly correction,
not the superseded daily claim.

## Recovery procedure

1. Create the synthetic fixture and explicit offline session. Normalize the
   original source without changing it; validate the complete canonical garden.
2. Obtain structured context, typed graph and exact evidence through ordinary
   CLI commands. Save only disposable adapter and index state.
3. Remove the first fixture adapter, its directory and the scoped index created
   by this scenario. The source vault and canonical records remain intact.
4. Load the second adapter without the first being installed or available.
   Re-run the same CLI requests from documented bindings/session/profile files.
5. Compare structured context, source identities, represented revisions and
   policy. Distinct wire envelopes are expected. Assert that originals,
   identifiers, relationships, review/privacy state and knowledge bytes did not
   change; never treat generated caches as canonical.

```bash
python3 -S scripts/provider_switch_demo.py \
  --workspace .cache/provider-switch-proof --require-source \
  --report .cache/provider-switch-proof.json
cmp tests/fixtures/provider-continuity/expected-proof.json .cache/provider-switch-proof.json
```

Use a new or empty synthetic workspace. The script refuses existing human files.
Network, remote acquisition and external-process entry points are blocked in the
proof; this is not confidential-host isolation evidence. The same `-I` installed
engine check used by the other demos proves no checkout engine is substituted.

## Verification and limitations

The initial ordinary source run passes the committed golden. Focused regression,
complete compatibility and clean installed-engine results are recorded in the
[release checkpoint ledger](release-checkpoints.md) and CONTINUITY.md as observed.
The final PR/source/automatic-CI references are added at the checkpoint.

No proprietary chat-history migration, live inference, account change, semantic
quality guarantee or automatic provider permission is claimed. Session expiry
and revocation still govern new requests; already disclosed context cannot be
recalled from a provider. The source remains unreviewed even when derived
knowledge is explicitly approved by the synthetic reviewer.
