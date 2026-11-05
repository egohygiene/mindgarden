# Synthetic federation checkpoint

Every file is authored synthetic material. `source.txt` is public evidence;
`profile.json` is an approved control-profile template whose exact selection/view
revision is bound by `tests/federation_fixture.py`. Negative canaries exercise
private/unreviewed/control metadata without using personal data. The fixture's
ephemeral canonical garden includes adversarial records to test authorization;
it is not a claim that pending/private records pass owner publication validation.

`expected/` is the public bundle for `repository-garden`. It includes only the
selected reviewed knowledge/claim records, exact logical source references, a
typed edge, descriptor/ownership metadata and an agent entrypoint. Source bytes,
review rationale and bindings remain outside this export. Do not regenerate the
golden files merely to conceal a contract or privacy regression.

`expected-proof.json` records the two-garden CLI/canonical-ownership/relocation/
clean-rebuild proof from `scripts/federation_demo.py`. It is deterministic from
the same synthetic inputs; real archives, credentials and private consumer data
remain out of this repository. Checksums are not signatures or authority proof.
