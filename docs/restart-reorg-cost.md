# Compatible-reorganization storage cost

4 October 2026. All six bounded storage cases pass after correcting a receipt
bloom omission in the test fixture. This adds opt-in tests and evidence only;
the node runtime and P1–P17 candidate inventory are unchanged.

The [earlier interrupted-write test](restart-crash-rehearsal.md) demonstrated and
corrected partial publication during a small compatible reorganization. Its
remaining questions included larger atomic batches and shorter but heavier
replacement branches. This measurement extends those storage cases; it does not
replace the earlier actually executed/sealed-branch checks.

## Workload and acceptance

Both branches share one fixed test anchor. Old suffixes contain 1,024 or 4,096
blocks of difficulty 1. Replacements contain either one more block at difficulty
1, or half as many at difficulty 3, and are explicitly checked to be heavier.
Each block has 32 synthetic transactions, 256-byte transaction data and one
64-byte log per receipt. Eight transactions per overlapping height are common
to both branches. The largest canonical branch holds 131,104 transactions.

Separate processes prepare, write and verify each case using real LevelDB on
Linux ext4. Preparation stores coherent body/receipt commitments but reuses one
state; blocks and transactions are unsigned and unexecuted. The writer calls
the existing `WriteBlockWithState` path, measuring canonical reconstruction,
index changes and head publication rather than consensus validation or execution.

The declared limits are 512 MiB of closed fixture files, 120 seconds for the
write/switch, and at canonical batch submission: 64 MiB of key/value payload,
1 GiB live Go heap and 1.5 GiB Go-accounted system memory. Each child also has a
200-second timeout. These are test acceptance limits, not node configuration or
new protocol limits. The [evidence bundle](evidence/restart-reorg-cost-2026-10-04/README.md)
retains the declarations made before execution and both attempts.

## Passing results

| Old blocks → new blocks | Measured write/switch | Canonical batch key/value bytes | Live Go heap at batch submission |
| --- | --- | --- | --- |
| 1,024 → 1,025 | 0.901 s | 2,034,981 | 124,850,408 |
| 1,024 → 512 | 0.423 s | 1,562,747 | 88,212,424 |
| 4,096 → 4,097 | 5.366 s | 8,135,973 | 446,493,528 |
| 4,096 → 2,048 | 2.117 s | 6,250,619 | 375,917,144 |

All four complete writes publish the multi-block canonical replacement and all
three head markers in one batch. The longest replacement inserts 131,104 lookup
entries and removes 98,304 old-only entries. The shorter 4,096 → 2,048 switch
inserts 65,536 lookup entries, removes 114,688, and deletes 2,048 obsolete
canonical heights above its new tip. Shared transactions retain their new
canonical lookup.

Two further cases exit with code 86 immediately before or after the actual
canonical batch write for the 4,096 → 2,048 switch. The fresh verification
process sees precisely the complete old branch before, and complete new branch
after. Both persisted and loaded full/header/fast heads agree, with no rewind.
The fixed anchor, all canonical indexes and transaction lookup entries, body and
receipt commitments, receipt/log identities, available state and readiness pass.
First/last transaction and receipt resolution also passes for every canonical
block, covering shared and branch-specific examples.

The complete accepted run takes 54.44 test seconds; its largest closed fixture
is 23,524,761 bytes (about 22.4 MiB, compressed on disk). External accounting
reports 609,940 KiB maximum resident set for the command (about 596 MiB).
Go live heap at batch submission is a point sample, not a continuous peak.
Key/value payload omits serialization/backend overhead; LevelDB's separate
`ValueSize` counter also excludes put keys. Neither is total process memory.

## Fixture failure retained

Attempt 1 built and performed its writes, but all six cold checks failed with
`stored body or receipt commitments differ`. Synthetic receipts had logs but
zero blooms when their header commitments were created. The storage decoder
reconstructs bloom from logs, making the reopened commitment different.
Attempt 2 initializes receipt blooms exactly as `core/state_processor.go` does.
No acceptance bound or integrity assertion was weakened. Attempt 1 remains a
failed fixture run, with its original sources and outputs retained.

## Consequence and limits

The bounded results support retaining the atomic canonical batch correction.
Its largest measured key/value payload is about 7.8 MiB, while measured live heap
is much larger. The implementation also retains decoded branches, transactions
and displaced logs; these measurements do not attribute every allocation or
justify splitting the atomic write. No additional runtime optimization is made.

This closes the local G2 storage-cost case at the declared depths and payloads,
including a shorter/heavier replacement and process-exit boundaries. It is not
a maximum-gas-block test, arbitrary-depth guarantee, production memory sizing,
concurrent-reader snapshot guarantee, seal/native-call verification, or a power-
loss/torn-write durability claim. No transaction execution or wallet accounting
is inferred from these synthetic bodies. The final supported release matrix and
actual-host resource acceptance remain open; expand this test only for a changed
implementation, concrete failure or newly declared supported workload.

The test uses the existing offline Go 1.21.3 Linux/amd64 rehearsal toolchain and
private network namespace while baseline replay runs separately. It does not
open the backup/replay stores, sign with real keys or change ordinary fork choice.
