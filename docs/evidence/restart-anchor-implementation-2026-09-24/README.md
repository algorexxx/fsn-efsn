# Anchor prototype and rollback evidence

Source base: `8280db9`, with the Go files listed in `source-files.txt` replaced
by the implementation committed alongside this evidence. Mainnet's anchor is
unset. All signing uses the public synthetic key; no preservation database or
operator key is used by these tests.

## Current final source

- `windows-full-final-cache.txt`: complete ordinary restart suite, Windows amd64,
  Go 1.21.3, CGO disabled, `GOMAXPROCS=2`; passed in 96.397 seconds, exit zero.
  Large preserved-database probes are skipped in ordinary synthetic runs.
- `windows-source-sha256.txt`: hashes of every changed/new Go file in that run.
- The current Linux artifacts are in
  `/home/rehearsal/results/restart-anchor-implementation-2026-09-24/final-cache`.
  `run-final-cache.sh` is the exact final runner, using a separate source export,
  Go 1.21.3, GCC 13.3, CGO and the race detector. It builds `cmd/efsn` and runs
  `^TestRestart(Anchor|Rollback)` three times in a network namespace. The node
  build and all three repetitions passed. `linux-anchor-race-3.txt` records
  102 enabled-anchor subcase passes (34 per repetition), with no reported race.
  `linux-identity.txt`, the build logs, finish time and exit code zero identify
  the final artifacts. All 16 source hashes match the Windows workspace.
- The focused set includes 34 enabled-anchor cases, one configuration test,
  nine legacy characterization cases with the anchor disabled, and three
  rollback database cases. The expected injected storage error prints `CRIT`
  from a child process; its parent verifies the fatal exit and passes.

## Reproductions and intermediate checks

- `rollback-before-fix.txt` reproduces the original fatal unsupported-freezer
  result when rolling back a database without a freezer.
- `cache-before-fix.txt` and `cache-after-fix.txt` measure 8,796 versus 601 header
  reads for 600 imports after 8,192 stored descendants. The headers in this cost
  test are unsigned; only ancestry/canonical header operations are exercised.
- `windows-full.txt` and `windows-full-final.txt` are earlier passing iterations
  before the final cache correction. Their exit-code files and logs are retained
  as development history; use `windows-full-final-cache.txt` for current source.
- `run-final.sh` built an earlier final candidate but stopped when the inherited
  rawdb test package failed to compile. `complete-final.sh` confirmed that failure
  on unchanged source and completed the earlier focused race run. These precede
  the measured cache correction; `run-final-cache.sh` supersedes their binaries.

`core/rawdb` package tests refer to `params.RinkebyGenesisHash`, which this fork
does not define. The package test attempt and unchanged-export reproduction are
retained; they both fail to compile. The `params` package race tests passed in
the same package attempt. No stale tests were rewritten or excluded to claim a
whole-repository pass. The independently compiled restart suite directly tests
the changed rollback behavior, including a LevelDB database and genuine storage
failure handling.

## Reproduction

The Linux export is `/home/rehearsal/fsn-efsn-anchor-implementation`, originally
extracted from `git archive 8280db9`, then overlaid with the listed Go files.
The machine-specific scripts refuse existing result directories. For another
machine, export the committed source to a disposable directory, use the recorded
compiler/dependencies, and run:

```sh
CGO_ENABLED=1 GOMAXPROCS=2 GOTOOLCHAIN=local GOPROXY=off go test -race -p=2 -mod=readonly -c -o /tmp/restart-anchor-tests ./tests/restart
CGO_ENABLED=1 GOMAXPROCS=2 GOTOOLCHAIN=local GOPROXY=off go build -p=2 -mod=readonly ./cmd/efsn
cd tests/restart
unshare --net -- /tmp/restart-anchor-tests '-test.run=^TestRestart(Anchor|Rollback)' -test.v -test.count=3 -test.timeout=8m
```

Creating a network namespace requires the appropriate Linux privilege. The
recorded runner switches back to the unprivileged rehearsal user inside it.
The node is built, not started. This is not an end-to-end peer, miner-service,
freezer, process-crash or full-state mainnet rehearsal. See the
[implementation report](../../restart-anchor-implementation.md) for those gates.

The baseline replay to 2,000,000 remains a separate job using its unchanged,
identity-bound executable and target. A sampled replay progress record here is
only an observation during implementation, not completion evidence. At
06:42:36 UTC it had reached 1,604,288, with 75,352,391,680 Linux bytes and
79,522,516,992 D: bytes available. The retained executable hash still matched.

`SHA256SUMS` covers the retained evidence except itself and `.gitattributes`.
Logs are stored without Git line-ending conversion.
