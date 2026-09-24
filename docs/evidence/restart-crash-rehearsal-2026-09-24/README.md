# Interrupted-write evidence

24 September 2026. Source base `c0299b0`, with the three Go files identified in
the final source hash records overlaid. No mainnet anchor was activated and no
operator key or preserved database was used by the crash tests.

## Reproduction and intermediate results

- `windows-before.txt`: the new fault-injection harness against unchanged
  production code. Linear import and rollback pass, while ten reorganization
  cuts fail. Eight publish intermediate heads and two retain stale transaction
  lookups. The overall run correctly fails.
- `windows-before-startup.txt`: a second reproduction on unchanged production
  code, with cold blockchain startup performed before checking the interrupted
  indexes. The logs show the partial head passing startup and readiness. The ten
  failing cuts remain failures. This uses the final crash harness.
- `windows-after.txt`: focused crash cases pass after batching the reorganization
  indexes/markers. This precedes the empty-chain guard and checkpoint regression
  update; use the final results for the complete current source.
- `windows-full.txt` / `windows-exit-code.txt` and `linux-initial-full-race.txt` /
  `linux-initial-full-exit-code.txt`: the first broader runs fail only because
  `checkpoint_stored_fork` still expected the old ignored-error defect to occur.
  The correction instead returns the checkpoint error and keeps the accepted
  head. The new crash cases pass in those runs.
- `windows-focused.txt`: the crash cases and checkpoint regression pass after
  that test is updated to require rejection, unchanged accepted heads/indexes/
  transaction lookups and no head event. No production rule was weakened to
  preserve the old characterization's success.

The initial Linux source export was created with `git archive c0299b0`, then
overlaid with `core/blockchain.go` and `tests/restart/crash_test.go`.
`linux-initial-identity.txt` records that intermediate build. `run-linux.sh` is
its runner; the repeated-crash phase was correctly skipped after the full run's
nonzero exit. The final runner adds the updated `anchor_paths_test.go` as well.

## Final verification

- `windows-full-final.txt`: the complete Windows amd64 restart suite with the
  crash opt-in enabled passed in 100.921 seconds. Go 1.21.3, CGO disabled,
  `GOMAXPROCS=2`; `windows-final-exit-code.txt` records zero.
- `linux-full-race.txt` / `linux-full-exit-code.txt`: complete Linux synthetic
  restart suite with both the crash and service-process opt-ins enabled, using
  Go 1.21.3, CGO and the race detector. The private network namespace contains
  only enabled loopback for the devp2p service cases. The complete run passed
  with exit code zero.
- `linux-crash-race-2.txt` / `linux-crash-exit-code.txt`: two additional repetitions
  of the sixteen before/after write-boundary cuts in a network namespace with
  no external interfaces. These use the same final compiled binary. Both passed,
  giving 48 successful crash cuts across the three final Linux invocations,
  with no race report. The process-service scenarios also pass in the full run.
- `linux-build-tests.txt`, `linux-build-node.txt` and `linux-identity.txt`: compiler
  output and identities for the final test and complete node binaries.
- `windows-source-sha256.txt`: the same three source digests as the Linux build.
  `run-final-linux.sh` is the exact final runner, requiring a fresh results directory.

The final Linux export is `/home/rehearsal/fsn-efsn-crash-rehearsal` and the result
directory is `/home/rehearsal/results/restart-crash-rehearsal-2026-09-24/final`.
For another machine, compile the committed test sources, explicitly set
`FUSION_RESTART_CRASH_REHEARSAL=1`, and run `TestRestartCrashBoundaries` using the
instructions in [the test README](../../../tests/restart/README.md).

Child exit code 86 is required at each injected boundary. Intentional startup
refusal and injected rollback-storage failures in other tests also print child
`FAIL`/`CRIT` lines; their parents require and validate those failures. The suite's
top-level result and recorded exit code determine success. Logs are not claiming
that every printed child invocation starts successfully.

The full-preserved-data probes remain opt-in and are skipped here. The inherited
miner and rawdb package-test compile failures remain documented in previous
reports; this is not a whole-repository test claim. For the actual result's scope,
including power-loss, pruning, freezer, explicit-rewind and long-reorg limits,
see [the crash report](../../restart-crash-rehearsal.md).

## Ongoing baseline replay

`replay-progress.txt` records a separate observation at 08:34:00 UTC: height
2,211,072, with Linux free 73,857,372,160 bytes and D: free 67,049,279,488 bytes.
The retained replay executable digest remains unchanged. This is sampled
progress toward 2,700,000, not completion evidence. Its existing read-only source,
writer lock, identity manifest and per-batch disk reserves remain in effect.

`SHA256SUMS` covers all retained evidence except itself and `.gitattributes`.
Archived files do not undergo Git line-ending conversion.
