# Validation and restart-anchor evidence

Archived on 24 September 2026. Times in the runner records are UTC.

## Preserved-data validation

- `full-integrity.txt` contains the completed current-state and canonical-history
  scans. History covers 15,130,081 blocks and 419,409,946 transactions/receipts,
  ending at the recorded backup hash with no reported structural failure.
  `integrity-*` records isolation, start/finish times and exit code zero.
- `million-*` records completed baseline execution through height 1,000,000,
  matching the source hash/root/ticket commitment. Runtime was 4,324.80 seconds;
  closed database size was 1,158,354,931 bytes; exit code was zero.
- `two-million-*` records only the start, capacity, isolation and successful
  read-only resume preflight for the next bounded phase. Its completion is
  pending. `run-replay-two-million.sh` is the exact continuation runner.

Those jobs use the retained baseline executables, not the new anchor tests.
The replay executable SHA-256 remains
`004d4eeb16fc27e68564ff34d18b5bb1c48829cb692b98770fe7c52543d26c1e`.
Its existing target manifest must match before resume. The same database is
extended, and the source stays mounted read-only in an isolated mount/network
namespace. Legacy verification shortcuts through block 2,680,000 are retained.
The structural scan is not transaction execution or complete consensus validation.

The active continuation log is
`/home/rehearsal/results/restart-replay-two-million-2026-09-24/replay.txt`.
Run the archived continuation script only once, using:

```sh
wsl -d FusionRehearsal -u root --exec unshare --mount --net --propagation private -- bash /mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-validation-2026-09-24/run-replay-two-million.sh
```

It refuses an existing results directory or another detected writer. A later
phase needs its own reviewed runner after clean completion. The active stop
file is `/home/rehearsal/replay/STOP-baseline-mainnet`; creating it requests a
controlled failure and database cleanup at the next batch boundary. Do not
kill WSL or overwrite the retained executable to stop or update the replay.

## Anchor characterization

Production source base: `82d685e`, unchanged. The only new Go source is
`tests/restart/anchor_paths_test.go`. `anchor-identity.txt` records the compiler,
final test executable and relevant source hashes from the separate Linux export
`/home/rehearsal/fsn-efsn-anchor`.

Linux build and run, with Go 1.21.3 and CGO enabled:

```sh
GOMAXPROCS=2 GOTOOLCHAIN=local GOPROXY=off go test -race -p=2 -mod=readonly -c -o /home/rehearsal/anchor-tests-final ./tests/restart
cd tests/restart
unshare --net -- runuser -u rehearsal -- /home/rehearsal/anchor-tests-final -test.run=^TestRestartAnchorEntryPointsCharacterization$ -test.v -test.count=3 -test.timeout=8m
```

`anchor-race-final-3.txt` passed all nine cases in all three repetitions with
no reported race. `windows-full.txt` passed the entire ordinary restart suite
with Windows amd64, the portable Go 1.21.3 compiler and CGO disabled in 92.499 seconds
(`go test ./tests/restart -v -count=1 -timeout=8m`). Full-backup probes
were skipped in that synthetic run. This is not a whole-repository test claim.

The characterization intentionally reproduces unsafe legacy behavior. It does
not implement the anchor or designate the synthetic checkpoint as a production
restart artifact. See [the investigation](../../restart-anchor-investigation.md)
for the exact findings, fixture limits and required enforcement points.

`SHA256SUMS` covers the archived evidence files other than itself and the Git
attributes file. Original logs are preserved without Git line-ending conversion.
