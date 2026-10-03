# Observer incident text and bounded history cost

3 October 2026, baseline `7ef1351a`. The only production-code change is explicit
hexadecimal formatting of two hashes in the external observer's canonical-change
incident. The node executable, consensus and P1–P16 candidates are unchanged.

## Diagnostic correction

`common.Hash.Format` renders its underlying bytes for `%s`, overriding the
otherwise readable `String` method. The observer now calls `Hex()` for the old
tip and common ancestor. The exact-string regression uses the already retained
27 September service fixture's block-25 and anchor hashes, rather than deriving
its expected text through the formatter under test.

The regression first failed against the old code. Its early failure also exposed
late test cleanup on Windows; cleanup is now registered as soon as the history
opens. Both the initial failure and corrected suite results are retained. The
regression checks text and stable incident identity again after reopening and
catch-up. Windows observer/command suites and Linux suites with race detection
pass. No history migration is needed: incident details are reconstructed from
saved events. Existing event bytes, incident IDs and review decisions are not
changed by the formatting correction. Existing exported status files remain
historical captures and are not rewritten.

## Bounded local measurement

`TestHistoryRetainedSnapshotCost` is opt-in. It uses the existing two-node
`ipc-converged` public-test-key report, with only observation times advanced. It
builds histories of 10, 100 and 1,000 snapshots, then measures status replay, one
additional public `Record` call, export to a discard sink, and reopen plus status.
Setup uses the existing validated append helper and is excluded from operation
timings; it does not measure the total cost of accumulating the history through
repeated CLI invocations. Exact status comparisons check replay and reopening.

The measurement ran without race instrumentation on WSL ext4, Go 1.21.3,
`GOMAXPROCS=2`. The independent race suite checks correctness. Each read/export/
reopen operation has three samples; append has one. Garbage collection runs before
each sample outside the timed interval. Reopening is in the same process with
warm OS caches, not a cold disk or power-loss test. There are no RPC requests,
node processes, backup reads or growing block ancestry in this measurement.

| Retained snapshots before append | Status median | One append | Export median | Reopen + status median | Logical size after append | Closed file sizes |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 10 | 6.97 ms | 10.59 ms | 8.32 ms | 30.22 ms | 313,783 B | 81,436 B |
| 100 | 72.85 ms | 81.84 ms | 85.15 ms | 167.41 ms | 2,877,975 B | 726,839 B |
| 1,000 | 693.31 ms | 680.90 ms | 754.12 ms | 1,447.20 ms | 28,520,777 B | 7,155,991 B |

The last history has 1,001 snapshots, approximately 27.20 MiB logical and 6.82 MiB
in closed file lengths. Repeated content compresses unusually well; that physical
ratio is not a production sizing assumption or a filesystem-allocation measure.
The whole measurement took 16.20 seconds and peaked at 66,544 KiB resident memory.
At 1,000 snapshots, median status replay allocated about 131 MiB cumulatively and
reopen/status about 282 MiB; allocation totals are not retained RAM or peak RSS.

## Implications for deployment

The observed growth is about 28,492 logical bytes per snapshot. At that size, the
64 MiB example budget would hold approximately 2,355 snapshots: about 9.8 hours
at a 15-second cadence or 39.3 hours at a 60-second cadence. These are illustrative
snapshot-only calculations, not selected cadences or guarantees. Backfill,
baselines, reviews and larger reports consume additional budget. Compression
does not extend the logical budget. At exhaustion, appends stop without pruning.

Code inspection and these samples agree that local work grows with history size:
opening validates the complete log, and status/append replay it again. The current
CLI therefore pays for more than one replay. The RPC timeout does not bound this
local work. Increasing the byte budget alone does not establish sustainable
collection. No cache, index, pruning, rotation or new history format is introduced
by this investigation.

The next bounded experiment should combine advancing block/receipt batches with
snapshots, measure the actual command's acquisition and replay cost, and test
exhaustion and reopening at the chosen test budget. Use explicit event/byte/time
caps and compact synthetic state. Compare a single replay per command with the
current implementation before considering a persistent derived-state cache.
Any eventual retention scheme must preserve anchor baselines, unresolved incidents,
review identity and displaced evidence across history boundaries; starting an
empty history is not an accepted workaround. Cadence, retention and notification
delivery remain launch gates in the [main plan](restart-plan.md).

[Evidence and reproduction](evidence/restart-observer-history-cost-2026-10-03/README.md)
include source hashes, the initial regression failure, both platform suites, raw
samples, resource measurements and a verifier. This does not establish production
RPC throughput, long-chain ticket timeline cost, concurrent scheduling, network
latency, representative compression, notification delivery or public readiness.
