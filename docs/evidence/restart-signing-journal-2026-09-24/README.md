# Recovery signing evidence, 24 September 2026

Baseline commit: `3ae0c82`. Interpretation and remaining limits:
[restart-signing-journal.md](../../restart-signing-journal.md).
Only public test private scalars 1 and 2 were used for signing.

## Passing evidence

- `windows-unit-final.txt`: journal reservation/replay/conflict, identity and
  corruption checks, callback failure cases, truncated WAL, cross-process lock
  and four forced-process-termination boundaries.
- `linux-unit-final-race.txt`: the same final journal cases under Linux race
  detection, plus database tests and unsigned command compilation. The database
  corruption case in this file used CURRENT; the later manifest case is below.
- `windows-handover.txt`, `linux-handover-race.txt`: existing guard/rejection/
  funding tests plus three-stage signing-journal handover. Eight concurrent
  public API calls per stage produce one signature, matching the independent
  builder; two chains import the same blocks. Reopened journals recover the exact
  artifacts after head advance. Linux runs in a private network namespace.
- `windows-readonly-manifest.txt`, `linux-readonly-manifest-race.txt`: corruption
  rejection leaves every disposable database file hash unchanged. The original
  wrapper fails this same regression in
  `readonly-manifest-baseline-counterexample.txt` by silently repairing it.
- `backup-purchase-inventory.json`, `backup-inventory-run.txt`: read-only saved
  backup inspection at the pinned original head. Empty transaction journal; no
  automatic record for either wallet; nonces 233427 and 0.
- `backup-file-inventory.json.gz`: lossless compressed JSON metadata for all
  56,107 chain database files, including SHA-256 for seven mutable files.
  `backup-inventory-equality.json` records matching uncompressed before/after
  hashes; `backup-preservation.txt` records the exact verification scope.
  The original 117,170,022,674-byte database was not rehashed in full here.

## Reproduction and retained intermediate results

`check-linux.sh` builds from `tmp/recovery-signing-base.tar` (a `git archive` of
the baseline) plus the listed changed/new source files, using the existing WSL
toolchain/module cache. It refuses existing output paths. Its final source and
binary paths are `tmp/recovery-signing-linux-v2-src` and
`tmp/recovery-signing-linux-v2-tests`. `check-readonly-fixed.sh` installs the final
manifest regression into that source tree and runs the LevelDB package with race
detection. `check-readonly-baseline.sh` tests the baseline wrapper in a separate
temporary package, expecting failure. All corruption targets are Go temporary
test databases, never preserved chain data.

Windows used Go 1.21.3, `CGO_ENABLED=0`, `GOMAXPROCS=2`, offline cached modules and
`go test -p=2 -mod=readonly`. The restart binary is
`tmp/recovery-signing-final-windows-tests.exe`. Run it from `tests/restart` with
`-test.run=^TestRecovery(Guard|GuardRejects|GuardInsufficientReplacement|JournalHandover)$`,
`-test.v`, and `-test.timeout=2m`. The direct packages are `./internal/recovery`,
`./ethdb/leveldb`, and `./cmd/fsn-recovery`. Quote dotted test flags in PowerShell.

`inventory-windows.ps1` documents the exact whitelisted read-only inventory and
before/after checks. It requires the final Windows binary and refuses an existing
JSON report. The original run wrote two identical raw file inventories; these
remain locally at `tmp/signing-backup-files-before.json` and
`tmp/signing-backup-files-after.json`. The committed gzip contains their exact
bytes; it was verified by decompression. The script now writes gzip directly
and stores one inventory plus equality hashes instead of duplicate 11.5 MB files.

Retained intermediate files:

- `windows-unit.txt`, `linux-unit-race.txt`: earlier passing unit cases before
  the truncated-WAL test was added.
- `check-linux-initial.sh`, `linux-build.txt`: initial restart-test compilation
  failed because the inventory test passed an extra argument to an existing
  JSON helper. Correcting the call yields the final empty successful build log
  `linux-build-final.txt`. No production code was changed for that error.
- `readonly-baseline-counterexample.txt`: the initial CURRENT-corruption test
  passed on the original wrapper because it returned a different corruption
  error type. It is not evidence of the repair bug. Emptying the manifest instead
  reproduces the unsafe fallback and produces the expected baseline failure.
- An early Windows binary invocation used unquoted dotted flags and was rejected
  by Go's flag parser. The quoted invocation and final recorded handover pass.
  The first inventory script attempt followed a failed build and never opened the
  backup database; the corrected build and recorded inventory pass.

No real key was loaded; no transaction was submitted; no real block was signed;
no public node was started. The compact full-state fixture and replay checkpoints
were not opened by these tests. The new signing journal has not yet been wired
into the full-state two-node harness or a production key adapter.

`identities.json` records source/toolchain/binary hashes. `SHA256SUMS` covers all
other files in this evidence directory. Evidence bytes are excluded from Git
newline normalization.
