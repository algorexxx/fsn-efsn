# Bounded anchor startup measurement

4 October 2026. Initial acceptance bounds declared before attempt 1:

- 10,000 and 100,000 synthetic descendants beyond the fixed test anchor.
- At each depth: disabled-anchor control, aligned full/header/fast heads,
  full/fast heads at half/three-quarter depth, and damaged canonical index at
  the first descendant after the anchor.
- Fresh child process for each case and a reopened LevelDB before measurement.
  The operating-system page cache is not cleared. Fixture state is reused and
  headers are unsigned; this is startup ancestry/index work, not execution,
  seal validation, peer synchronization or mainnet state coverage.
- Each fixture is at most 512 MiB. Combined genesis setup and chain construction
  must finish within 120 seconds, perform at most `8 * (depth + 1) + 256` stored
  header reads, and finish with at most 512 MiB accounted by Go `MemStats.Sys`.
  These are local rehearsal limits, not a service guarantee. `Sys` is neither
  peak resident memory nor cumulative allocation; both cumulative allocations
  and the whole test command's external resource accounting are also recorded.
- Successful cases preserve all database keys and expected heads; enabled cases
  retain mining readiness. Both startup entry points must reject the damaged
  index and leave the damaged database unchanged.

`tests/restart/anchor_startup_test.go` reuses the existing fixture, header-read
counter, database digest and assertion helpers. Measurement calls the production
`SetupGenesisBlock` and `NewBlockChain` in service order, with separate timings
and read counts. Each builds a fresh anchor proof cache. The unchanged original
backup and running historical replay are not opened by this test.

Run inside the existing private network namespace:

```text
wsl.exe -d FusionRehearsal -u root -- unshare --net bash /mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-anchor-startup-2026-10-04/run-linux.sh attempt-1
```

The opt-in test skips without `FUSION_RESTART_ANCHOR_STARTUP=1`. The runner uses
the existing offline Go dependency cache, records source/binary identities and
puts disposable database fixtures on Linux ext4. It refuses an existing attempt
directory and does not replace prior evidence. It adds no runtime patch or
production anchor. Results are accepted only after the captured exit is checked.

## Initial result and declared follow-up

Attempt 1 passed all eight cases in 18.92 test seconds. At 100,000 descendants,
genesis setup plus chain construction took 2.78 seconds with aligned heads and
3.81 seconds with split heads. The 100,000 fixture occupied 31,015,492 bytes;
the measured command's maximum resident set was 76,020 KiB. The retained attempt
contains its exact test source, runner and identities.

100,000 fifteen-second intervals cover about 17.4 days. Before attempt 2, extend
the same four cases to 1,000,000 descendants (about 173.6 days at that assumed
interval) to measure a months-long startup window. The time, read and memory
bounds above remain unchanged; the linear-read bound uses the selected depth.
Run only the new depth using the runner's second argument
`^TestRestartAnchorStartupCost$/^1000000$`; do not repeat the passing smaller
fixtures. This follow-up passed all four cases in 204.34 test seconds with
zero build and test exits. The aligned checks took 25.973 seconds combined; split
heads took 37.314 seconds; both entry points rejected the damaged index in
28.381 seconds combined. All declared bounds passed. See the
[interpretation and limits](../../restart-anchor-startup.md).

Captured test sources use `.go.txt` so evidence does not become another Go test
package. The original captured runners wrote `.go` files, renamed byte-for-byte
after completion; the reusable runner now writes `.go.txt` directly. Each
`added-test.sha256` still names the actual compiled source in `tests/restart`.
