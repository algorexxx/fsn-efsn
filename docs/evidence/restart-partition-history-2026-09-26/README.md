# Genuine ancestry partition evidence

Baseline `12651ceaf3c1bf35ee8bda9bfd1ff95ccdfa1357`. See
[the report](../../restart-partition-history.md) for outcomes and limits.

`run-history.sh` builds the race binary with offline Go 1.21.3, measures and
exports only the last 90,001 original blocks using a read-only backup mount,
and runs focused body-validation checks. `measure-initial.txt` records the
incorrect Ethereum uncle-hash assertion; its exact source and binary identity
are retained. `runner-failures.txt` distinguishes test output from two failed
shell wrappers. The final export must match the corrected measurement report.

`prepare-copies.py` verifies the 230-file original export, creates two fresh
disposable copies and checks a 50-GiB storage reserve. `run-partition.sh` uses
those copies and the exported history inside a private loopback-only namespace.
Only public test keys 1–3 are used. The source backup is not mounted in this run.
Ordinary synchronization, mining and transaction rules are unchanged.

The raw history segment is retained locally under
`tmp/partition-history-2026-09-26/history.rlp`; the checksummed size, range and
hash reports identify it without committing 67 MiB of historical blocks.
Historical receipts and state before the preserved head are not included.

The live run exits 1 at the isolated-producer progress gate, before live healing
or nonce repair. `run-diagnosis.sh` cold-audits the nine- and sixteen-block
branches and passes ordinary stopped-node synchronization to the heavier branch.
`run-post-sync.sh` adds a separate accounting test and binary, confirms both cold
canonical databases agree, and checks exact saved-record identity plus actual
pool admission. The donation purchase is unfunded with nonce 7 already correct;
the entrant purchase is admitted. No purchase is mined by that check.

`run-original-fork.sh` adds a final test/binary. It augments the original stopped
equal-weight fork, preserves its heads, and repeats the exact explicit downloader
request that previously failed on missing header 15,085,106. That path now passes
and stores the remote branch; both canonical heads remain unchanged. The earlier
failed evidence remains in its original evidence directory.

`verify-history.py` checks extraction, installation and all unchanged source-export
files. `verify-evidence.py` additionally requires the retained live failure,
three subsequent passes, branch ledgers, correct-nonce funding rejection,
byte-identical records and the exact ancestor probe. `verify-index.py` checks
staged hashes and the precise investigation scope. The staged patch includes no
runtime source or dependency changes.
