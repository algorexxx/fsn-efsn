# Mixed observer workload evidence — 3 October 2026

Baseline `db549c03`. Tests and documentation only; runtime and consensus are
unchanged. `run-linux.sh` uses a private loopback-only namespace and compact
synthetic devnet state with public test keys 1 and 2. Dependencies are offline.

`attempt-1/plain` contains the passing ordinary-build command measurement
(152.59 seconds). `attempt-1/race` contains the passing independent
race-instrumented validation (163.71 seconds). All four child node runs exited
cleanly, with no race reports. Final verification passed; see [checks.json](checks.json).

The history has an explicit 512 KiB logical budget. Both anchor inventories are
captured before mining. Six rounds alternate real IPC/HTTP snapshots and
block/receipt backfills while one ordinary miner produces. After mining stops
and delayed work settles, snapshots fill the budget until rejected, followed by
smaller backfills. Both failure types are retried. After the nodes shut down,
offline status, export and wallet timelines must remain readable and unchanged.

Each workload folder contains the configurations, anchor truth, executed final
ticket inventory, every command's output/diagnostics and before/after node status,
aggregate timing records, retained exports and summary. Exports use `.json` names
but contain JSON Lines, matching the existing investigation convention. They are
audit evidence, not supported history import packages. Temporary node and history
databases are removed by test cleanup.

Only ordinary-build command durations are used as measurements. They include the
complete child command and exclude harness status checks and file writes. Samples
are small and use local endpoints; alternating transports while history grows
does not isolate transport overhead. Race timings are not comparable performance
samples. Resource measurements include the test process and its child workload.

`verify.py` checks tested source hashes, test/child exits, absence of race reports,
namespace isolation, six rounds of increasing coverage, unchanged controls,
explicit budget failures, immutable export prefixes, preserved status and both
offline inventories against executed state. It writes `checks.json` after both
runs pass. It is pinned to `attempt-1`.

The normal run retained 39 events using 522,399 logical bytes; the race run
retained 38 events using 521,039 bytes. Both rejected snapshots, backfills and
their retries without changing the saved status or exports. All 61 stopped-node
command captures matched before/after; both offline inventories matched executed
state in each run. Smaller backfills could still fit after a larger snapshot was
rejected, so exhaustion is specific to the proposed event's size.

Reproduce with an unused attempt name:

```powershell
wsl -d FusionRehearsal -u root -- unshare --net -- bash /mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-observer-mixed-workload-2026-10-03/run-linux.sh attempt-2
```

See the [report](../../restart-observer-mixed-workload.md) for the finding and
remaining cadence, retention, ancestry, delivery and deployment work. No backup,
production key or large restore is involved.
