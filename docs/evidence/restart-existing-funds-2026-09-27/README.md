# Existing-funds recovery evidence

27 September 2026. Baseline `26b416c986cfb442280e96c564b9069ea7e8c591`.
Tests, documentation and evidence only; production candidates remain P1–P15.
See [the investigation report](../../restart-existing-funds.md).

| Experiment | Outcome |
| --- | --- |
| Controlled contributions and exact saved purchases | PASS, 9.15 seconds |
| Entrant-first live startup | FAIL, 154.51 seconds; no new block |
| Both miners ready before buyers | FAIL, 154.62 seconds; thirteen blocks but donation purchase remains pending |
| Cold diagnosis | Six database/pool subtests PASS; overall FAIL, 13.75 seconds, because the existing audit assumed one receipt log |
| Corrected independent retained ledger | PASS, 0.65 seconds; validates additional automatic mature-lock conversion |

The first sixteen canonical suffix blocks and original fixture identities are
referenced from `../restart-partition-history-2026-09-26/artifacts/canonical`.
`blocks/` retains only new blocks 17–31. The verifier checks the old prefix byte
for byte and matches both copies of the controlled/final account inventories.
The original small-reserve failure databases remain untouched: all 592 source
files are rehashed against the copy manifest. No real keys are used.

`run.sh` compiles and runs controlled recovery. `run-live.sh` records the first
live failure, `run-start-order.sh` resumes its stopped state without new funding,
and `run-diagnosis.sh` captures both complete cold ledgers and pool checks.
`run-ledger.sh` rechecks the retained ledger after the scoped test correction.
Each runner refuses to overwrite its log or executable. Live runners use private
loopback-only network namespaces; cold runners leave loopback down. Builds use
the existing offline Go 1.21.3 toolchain with race instrumentation.

The three `initial-*.go.txt` snapshots and source identity overrides preserve
the implementations used before subsequent test additions/corrections. Executable
hashes are recorded separately for all five builds. No completed failure log is
replaced by a later pass. `verify-evidence.py` checks expected failures as well as
passes, source preservation, funding amounts, saved transactions, every retained
canonical block and executable/source identities before refreshing `SHA256SUMS`.

The pending donation purchase has correct nonce and sufficient funding in both
cold pools. Its receiver's live pool/admission error was not captured. Neither
live run proves both-owner replenishment, a nonce rollback/repair, or an assured
reserve against further losses. No automatic rebroadcast or runtime change was
introduced.
