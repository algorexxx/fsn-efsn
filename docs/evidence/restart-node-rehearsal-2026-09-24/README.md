# Service rehearsal and continued replay evidence

Source base: `552441b`. Production anchor activation remains unset. The final
source changes are `core/restart_anchor.go`, `tests/restart/autobuy_test.go` and
`tests/restart/node_rehearsal_linux_test.go`; their digests identify the exact
Windows workspace and separate Linux export used for the final verification.

## Service verification

- `initial-node-race.txt`: the first three process scenarios passed. This version
  predates the fourth startup case, readable anchor errors and the test lifecycle
  correction.
- `initial-full-race.txt`: all four new service scenarios passed, but the overall
  run failed in the older `TestAutoBuyRuntime` with `auto-buy did not initialize`.
  The assertion raced the controller's five-second retry after asynchronous miner
  startup. The complete failure is retained; it is not a passing suite result.
- `run-final.sh` produced that first complete Linux attempt. `run-final-lifecycle.sh`
  rebuilds after the test now waits for `Mining()` before starting the controller.
- `windows-full.txt`: the final ordinary Windows amd64 restart suite passed in
  97.445 seconds, Go 1.21.3, CGO disabled, `GOMAXPROCS=2`. The Linux-only service
  harness is excluded by its filename; preserved-data probes remain opt-in.
- `linux-identity.txt`, `linux-build-tests.txt` and `linux-build-node.txt` record the
  final Linux Go 1.21.3/GCC 13.3 builds, race-enabled test binary and full node
  binary. `linux-full-race.txt` and `linux-full-exit-code.txt` record the complete
  synthetic suite, which passed with the service harness enabled inside a loopback-only
  network namespace. `linux-repeated-race.txt` and its exit code record two additional runs
  of both the four service scenarios and auto-buy runtime. Both repetitions passed
  with exit zero: twelve service-subcase passes across the three final runs, and
  three auto-buy runtime passes. No race report appeared in those logs.

The first attempt to launch those repetitions had a shell quoting error, retained
in `repeat-launch-error.txt`; it ran no tests. The corrected standalone
`complete-repeats.sh` uses the same final binary after requiring the full-suite
exit code to be zero. `run-final-lifecycle.sh` includes the same quoting correction
for a fresh reproduction. No source or test assertion was changed for that retry.

The final Linux export is `/home/rehearsal/fsn-efsn-node-rehearsal`, created using
`git archive 552441b`, then overlaid with the three listed Go files. Final compiled
artifacts/results are in
`/home/rehearsal/results/restart-node-rehearsal-2026-09-24/final-lifecycle`.
The scripts are machine-specific, use cached dependencies and refuse existing
result directories. See [the report](../../restart-node-rehearsal.md) for portable
test scope and fixture limitations.

An intentional child `FAIL` for incompatible startup and a child `CRIT` for
injected rollback-storage failure are expected rejection evidence. Their parent
tests check the failure and pass. Do not count these as independent successful
node starts. Sparse fixtures also log the expected missing historical block #1
from the bloom indexer. Logs do not establish a successful full-chain index build.

## Preserved-data replay

`two-million-*` is the completed baseline replay phase from 1,000,000 through
2,000,000: exit zero after 5,928.57 seconds, finished 07:22:21 UTC, closed target
2,261,867,399 bytes. All final block/state/ticket commitments match the preserved
source, with 5,449 tickets. These extend the earlier start-only records in
`restart-validation-2026-09-24`.

`checkpoint-boundary-*` records the start, source read-only mount, empty external
network, capacity and sampled progress of continuation toward 2,700,000. It began
at 08:00:40 UTC after validating the existing 2,000,000 head read-only. These are
progress records, not phase-completion evidence. Its runner is
`run-replay-checkpoint-boundary.sh`.

The replay's retained executable SHA-256 is unchanged:
`004d4eeb16fc27e68564ff34d18b5bb1c48829cb692b98770fe7c52543d26c1e`.
Its source, target identity manifest and per-128-block capacity guards are unchanged.
The reserves are 20 GiB on Linux and 50 GiB on D:. The new phase crosses the end of
the legacy checkpoint range at 2,680,000; earlier blocks still use those shortcuts.
This is not complete historical consensus validation or a full-chain replay.

The active log is
`/home/rehearsal/results/restart-replay-checkpoint-boundary-2026-09-24/replay.txt`.
Do not launch another writer. The existing stop file
`/home/rehearsal/replay/STOP-baseline-mainnet` requests normal cleanup at the next
batch boundary; do not kill WSL to stop the replay.

`SHA256SUMS` covers archived evidence other than itself and `.gitattributes`.
Log files are preserved without Git line-ending conversion.
