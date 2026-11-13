# Authored curation fixtures

All content is synthetic. `authored-plan.json` covers the six dispositions and
reviewed transformations; tests bind its selectors to the ingested fixture.

`disposition-cases.json` supplies explicit authored decisions for scratch,
duplicate, corrupted, low-information and unsafe material in
`disposition-source.txt`. These labels are human judgments, not automatic content
classification. “Corrupted” describes unusable captured text; checksum corruption
still fails validation and cannot be accepted as a reviewed disposition.

The routing tests bind each decision to an exact line and hash. They verify that
the private controller retains its rationale and evidence, including when another
candidate is explicitly published. Source instructions are never executed.
