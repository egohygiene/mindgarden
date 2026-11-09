# Synthetic extraction proposals

`page.txt` and `responses.json` are authored fiction. The fixture recipe imports
an existing synthetic v2.0.2 conversation, two synthetic captured bookmark records
and this page through ordinary ingestion. All originals remain in the private test
vault. Responses are test producer outputs, not measured model results.

Expected review cases: attributed assistant suggestion; exact supporting quote;
ambiguous Alex withheld from entity mapping; unknown `guarantees` relation withheld;
positive/negative accuracy reports and their explicit disagreement; empty successful
bookmarklet extraction; interrupted/resumed batch; provider failure and invalid
output distinct from empty extraction. No source instruction grants execution.

The review test explicitly approves keeping attributed, unverified proposals,
then rebuilds search/graph with exact original citations. It does not prove those
fictional claims true or satisfy real consumer/provider acceptance.
