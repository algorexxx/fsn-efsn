# Linux rehearsal and race investigation — 23 September 2026

The reboot enabled the dedicated D:-backed WSL environment. The committed
synthetic investigation reproduces on Linux with CGO disabled and enabled.
Race detection exposed a miner receipt-log ownership defect. This report records
the unchanged baseline and temporary overlays; subsequent implementation and
validation are in [the correction report](restart-corrections.md).

## Inputs and results

The initial source is commit `a93f45bf94a1a728383f3432b81ce9b3b764bd92`, exported
with `git archive`. Archive SHA-256:
`e41ae70760f4b204611eca0d6605c320e4c4f1ba410ca1b16d09a5b88063ff06`.
The initial Python parent-time overlay helper is an additional test runner.
The [environment and run metadata](evidence/restart-linux-2026-09-23/metadata.json)
records Ubuntu, kernel, GCC, verified Go archive, commands and log hashes.
Go 1.21.3 reproduces the historical build baseline; release toolchain selection
remains open.

| Experiment | Result |
| --- | --- |
| Committed suite, Linux, CGO disabled | All ten synthetic top-level tests / 22 leaf cases pass |
| Committed suite, Linux, CGO enabled | Same result |
| Parent-time reconstruction overlay, CGO enabled | Same cases pass with successful reconstruction required |
| Committed suite with race detector | Fails in `TestAutoBuyRuntime`; receipt-log and shared global-header races reported |
| Verifier import deferred until producer stops, ordinary CGO run | Synthetic suite passes |
| Same revised fixture, production miner, race detector | Receipt-log race reproduced in all three runtime repetitions |
| Same revised fixture, temporary receipt-log-copy overlay | All three runtime repetitions pass under the race detector |
| Updated complete synthetic suite, receipt-log-copy overlay, race detector | All ten synthetic tests pass; the opt-in backup probe is skipped |
| Updated synthetic suite, parent-time overlay, CGO enabled | All ten synthetic tests pass; the opt-in backup probe is skipped |
| Isolated read-only probe of the verified full database copy | Recorded identities/account/tickets and all eight sampled block/receipt commitments match |

Passing characterization tests deliberately includes reproducing known
reconstruction errors and the missing-ancestor panic. None of these results
establishes restart readiness, exhaustive concurrency safety, or a completed
full-state rehearsal.

## Receipt-log race

`miner/worker.go:copyReceipts` copies each receipt struct, retaining its `Logs`
slice and log pointers. The task receives these aliases. `resultLoop` writes
`log.BlockHash` after sealing while the main worker can copy the original state
logs in `StateDB.Copy` during `updateSnapshot`. The detector reports the write
at `miner/worker.go:602` and the read at `core/state/statedb.go:824`.

Both accesses are production paths within a single miner. Removing the concurrent
verifier import preserves this failure in three out of three runs. Evidence:
[isolated reproduction](evidence/restart-linux-2026-09-23/sequential-verifier-race.txt)
and [input metadata](evidence/restart-linux-2026-09-23/race-triage-metadata.json).

The [receipt-copy experiment](../tests/restart/run-receipt-copy-experiment.py)
creates a compiler overlay that copies the receipt log slice, each log struct,
and its topic/data slices. The production file on disk is not edited. With that
overlay, the same three repetitions pass:
[race output](evidence/restart-linux-2026-09-23/receipt-copy-overlay-race.txt).
The experiment concerns ownership of mutable log metadata, not a proposed
consensus-rule change. It does not establish the complete impact on historical
receipts, RPC snapshots, or every concurrent path. Review those before accepting
a production correction.

## Shared global-header access

The original test imported each mined block into its second in-memory chain
while the producer continued. `InsertChain` writes process-global `glb_parents`
through `datong.SetHeaders`; the producer's `Finalize` reads it. The
[initial race output](evidence/restart-linux-2026-09-23/baseline-race.txt)
captures this cross-chain access.

The fixture now collects both mined blocks, closes the producer, then imports
both in order. It still verifies independent transaction execution and ticket
creation, without concurrent two-chain use of the same global. This is a test
arrangement correction, not a production fix or proof that the global is safe.
Ordinary import/mining overlap in one node and true separate-process validation
remain to be tested.

## Actual backup inspection

The preserved C: chaindata was copied through a read-only bind mount into Linux
ext4 on D:. All 56,107 files (117,170,022,674 bytes) passed SHA-256 verification;
the source inventory remained unchanged. The original backup, keystore, node
identity, and explorer gateway are not changed. Copy verification establishes
copy integrity, not the validity or completeness of historical execution. See
[copy details and manifest location](restart-local-linux.md#verified-database-copy).

`TestPreservedBackupReadOnly` is an opt-in probe, skipped unless
`FUSION_RESTART_CHAINDATA` names a verified disposable copy. It opens LevelDB in
read-only mode, without creating a node, miner, RPC server, or P2P listener. It
compares the genesis, three head pointers, chain ID, complete head ticket map
and ticket commitment, and the investigated account against the saved RPC
observations. It also checks selected historical parent links and transaction/
receipt commitments and reports whether their state roots can be opened.

The probe passed with the copied database mounted read-only in a private mount
and network namespace. It confirmed genesis, chain ID 32659, all three head
pointers at 15,130,080, the recorded state root, all 491 tickets across eight
owners, their compressed commitment, and the investigated account's liquid
balance, time-lock intervals and nonce 233,427. The
[probe output](evidence/restart-linux-2026-09-23/backup-readonly-probe.txt)
and [isolation record](evidence/restart-linux-2026-09-23/probe-isolation.txt)
preserve the observations.

| Sampled height | Canonical block, parent link where applicable, transaction and receipt commitments | State root opens |
| --- | --- | --- |
| 0 | Pass | Yes |
| 1 | Pass | No; missing trie node |
| 1,000,000 | Pass | No; missing trie node |
| 15,129,056 (`B - 1024`) | Pass | No; missing trie node |
| 15,129,952 (`B - 128`) | Pass | No; missing trie node |
| 15,129,953 (`B - 127`) | Pass | Yes |
| 15,130,079 (`B - 1`) | Pass | Yes |
| 15,130,080 (`B`) | Pass | Yes |

This is consistent with retained recent state and unavailable older state,
not an archive-state backup. These samples do not establish the exact retained
range or prove that all unavailable state is due to normal pruning. Historical
balance queries at the missing roots require state regeneration or another
data source. Readable historical blocks/receipts are distinct from historical
state availability.

Opening a state root does not traverse all account/storage/code nodes. Sampled
blocks do not prove all 15 million blocks or indexes are present. Historical
execution, complete state availability, disk restart, and full-state bridge
construction remain separate gates. No production-parent block is signed here.

## Next work

1. Preserve the copy manifest and extend baseline inspection to complete
   history/state checks and a capacity-planned fresh replay.
2. Review the receipt-log correction and investigate ordinary mining/import
   overlap around the global parent-header slice.
3. Exercise historical reconstruction and the recovery sequence on disposable
   full state, with safe signing boundaries and separate-process verification.
4. Continue purchase retry/inclusion handling and the separate restart-anchor
   design. Neither requires broadening the agreed consensus scope.
