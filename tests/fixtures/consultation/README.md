# Synthetic declared ledger and reviewed packet

These account aliases, movements and review decisions are invented test data.
They contain no person's financial records. The UTF-8 CSV format is explicitly
declared, not an inferred bank-specific parser:

```csv
transaction_id,account_id,date,amount,currency,description
example,account-a,2026-01-02,-12.30,USD,Synthetic movement
```

Transaction IDs must be stable within the supplied account alias; the adapter
never derives real-world identity from amount/date/merchant similarity. Amounts
are signed decimal strings, dates are ISO calendar dates, and request review
declares each currency's precision. Debit/credit columns, localized formats,
currency conversion and arbitrary bank exports need explicit future adapters or
reviewed normalization before this contract can be used.

The overlap repeats the exact groceries row. Eight unique transaction identities
remain. Authored review pairs the two 300.00 movements as an internal transfer;
the 19.99 debit stays unclassified. Independently expected January USD totals are
income 2500.00, expenses -230.25, refunds 10.00, internal transfer net 0.00,
unclassified -19.99 and net movement **2259.76**. These are not balances or a
statement of assets/liabilities. Coverage is declared, with a missing account and
an explicit account-b interval gap; dates do not prove complete history.

`expected-proof.json` is produced by `scripts/consultation_demo.py`. The fixture
imports through the existing source/vault CLI, retains originals and unreviewed
source state, applies a separately authored reviewed summary, searches/contextualizes
it, creates a private reviewed packet, then relocates/restores the vault and
rebuilds exact packet/index/context/evidence bytes from clean garden files.
Networking, HTTP, external processes and models are blocked in this demonstration.

The committed contract fixtures preserve a concrete reviewed request, packet and
normalized row. Source authority is not supplied by a portable fixture: the demo
creates a separate machine-local offline session with exact source grants. The
review fields are synthetic local assertions, not authenticated organization
approval. Attachments contain selected normalized evidence rows; exporting raw
statements/PDFs and an approved real private pilot remain separate work.
