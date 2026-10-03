# Reuse the observer's validated opening state

3 October 2026, baseline `3a760271`. Opening an observer history already replays
and validates its complete event log. The first operation now consumes that
validated state once instead of immediately repeating the same replay. At 1,000
prior snapshots, the paired local reopen/status median fell from 1.55 seconds to
0.74 seconds. Retained status, history exports and ticket timelines remain
byte-identical in the deterministic comparison.

The only production source changed is
[`internal/observe/history.go`](../internal/observe/history.go). This belongs to
the external observer. The node executable, consensus, recovery anchor and
P1–P16 candidate inventory are unchanged.

## Ownership and validation

`OpenHistory` still validates metadata, scope, event order, bounds and every
event through the existing complete replay before returning a handle. LevelDB's
exclusive directory lock prevents another supported handle from changing that
history while it remains open. The existing operation mutex serializes accesses
within the handle.

The reconstructed state is retained in memory until the first operation that
needs it. That operation takes ownership and clears the handle's reference.
Subsequent operations replay normally. Closing the handle clears the reference,
and append clears it before validation or storage attempts. A failed append
therefore cannot make a later operation return an uncommitted state. Early
configuration rejection leaves the validated state available because it has not
read or changed it.

This extends the lifetime of the reconstructed incident/path state between open
and first use or close. It does not retain another raw event-log copy or persist
derived state. A caller that opens and idles a handle keeps that reconstructed
state alive for longer. The event format, budget, sequence checks, review rules,
CLI and public interfaces are unchanged; no migration is needed.

## Paired measurement

The unchanged `TestHistoryRetainedSnapshotCost` ran first on the baseline, then
on the candidate, with the same public two-node snapshot fixture, Go 1.21.3,
`GOMAXPROCS=2`, WSL ext4 and no race instrumentation. Each reopen/status value is
the median of three samples. One extra snapshot has already been appended when
reopen/status is measured, so the largest history contains 1,001 reports.

| Prior snapshots | Baseline reopen/status | Candidate reopen/status | Reduction | Baseline allocated bytes | Candidate allocated bytes | Logical bytes after append |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 10 | 36.45 ms | 23.61 ms | 35.2% | 12,038,928 | 10,490,296 | 313,783 |
| 100 | 173.86 ms | 114.86 ms | 33.9% | 39,322,840 | 25,442,000 | 2,877,975 |
| 1,000 | 1,550.73 ms | 739.60 ms | 52.3% | 295,393,720 | 157,632,352 | 28,520,777 |

Allocation totals are cumulative allocations during the operation, not retained
RAM or peak RSS. The largest sample allocates 46.6% fewer bytes. These are warm
OS-cache reopenings within one process, with garbage collection before each
sample outside its timed interval. They exclude command startup, RPC acquisition
and growing block ancestry; they do not establish cold-disk or deployed CLI
latency. Later operations on the same handle still replay, and the logical data
sizes are exactly equal. The earlier [history-cost report](restart-observer-history-cost.md)
retains its original measurements; this table uses a fresh paired baseline.

## Correctness results

Windows observer/CLI suites and Linux observer/CLI suites with race detection
pass. New regressions cover a rejected first operation (budget, observation
order, scope and review sequence), caller mutation of returned status, close
before first use, competing first reviews, and an injected storage-write failure.
Existing corruption checks still reject opening invalid history.

The archived baseline implementation was rebuilt through a compiler overlay;
the current working source was not switched. Three retained-fixture tests
produced six byte-identical baseline/candidate artifacts: incident status,
incident history, fork status, displaced block history, and both wallet ticket
timelines. Source manifests identify the exact inputs. The first comparison
launch failed because its previously built temporary executable was absent;
exit 127 is retained. Rebuilding immediately before comparison passed.

The existing two-node mixed-workload test also passes with race detection in
223.09 seconds. Using public test keys in a loopback-only namespace, it advances
from block 24 to 31 through six IPC/HTTP collection rounds, settles mining, and
fills a 512 KiB history. It finishes with 38 events and 522,018 logical bytes.
Rejected snapshot/backfill appends and both retries return exit 1 with no stdout.
Earlier evidence remains an unchanged prefix, retries preserve the final export,
and fresh offline status and both wallet inventories match retained/executed
state. Both child nodes shut down successfully; no race was reported.

The reused workload's raw `RuntimeChanges: false` field is inherited scenario
metadata, not a correct description of this candidate's source diff. This
candidate changes observer history handling as described above; it changes no
node runtime source. The verifier uses source hashes and does not treat that
legacy field as proof of an unchanged observer.

## Remaining deployment work

The optimization removes one redundant replay, not the linear growth in replay
cost or retained bytes. The example 64 MiB budget still needs a deliberate
retention policy. Longer advancing ancestry, ticket-timeline cost, wider forks,
production transport and collection scheduling remain to validate. Retention
must preserve anchor baselines, unresolved incidents, review identity and
displaced evidence. Collection-failure and missed-cadence notifications need a
path that still works when history storage rejects appends.

No production backup, real signing key, public endpoint or large restore was
used. This closes the duplicate-replay comparison in the
[main plan](restart-plan.md); it does not approve continuous deployment or launch.
See the [evidence bundle](evidence/restart-observer-open-replay-2026-10-03/README.md)
for raw results, exact runners and the verifier.
