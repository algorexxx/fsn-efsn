# Parent-context isolation evidence

25 September 2026. Production baseline `bcbd1ce`; see the
[report](../../restart-parent-isolation.md) and permanent candidate P9.

| Result | Retained evidence |
| --- | --- |
| Before correction: independent verification and finalization both reject a valid block with `unknown ancestor` | `windows-before.txt`, using `baseline-test.go.txt` |
| Before correction: two race reports during actual competing mining/import | `../restart-purchase-rollback-2026-09-25/pre-fix-competing-race.txt` |
| Corrected isolation and unstored-header tests, five passes each on Windows | `windows-after.txt`, `check-windows.ps1` |
| Same two tests, five passes each with Linux race detection | `linux-parent-race.txt`, `check-linux.sh` |
| Nine anchor-entry cases pass, 12.90 seconds | `linux-anchor-race.txt`, `check-linux.sh` |
| Five actual-node regressions pass, 79.68 seconds; nonce rollback/repair takes 49.95 seconds | `linux-node-regressions-race.txt`, `check-linux.sh` |
| Corrected competing miners pass with race detection, 98.37 seconds | `../restart-purchase-rollback-2026-09-25/linux-competing-race.txt` |
| Broader core-package tests fail to compile in unchanged legacy test code | `linux-core-race.txt`, `check-core-linux.sh` |

The incompatible-database regression intentionally runs a failing child and
requires rejection. Its parent test passes; a search for every `FAIL` substring
would misclassify the result. Conversely, the core-package build failure is an
unresolved verification limitation, not a passing test. Empty build logs mean
successful quiet compilation only where followed by the recorded passing run.

The original baseline test printed its success description even after calling
`t.Errorf`. Its two errors and final failure are authoritative. The final test
guards that description with `!t.Failed()` and adds the separate header-batch case.

`identities.json` records normalized Git source blobs, raw file hashes, baseline,
binary hashes and the verified result counts. The final competing-miner binary
was built after all three P9 production edits and before adding the separate
header-batch regression. Its miner/rollback test sources match the final files;
it is not asserted to contain the final version of `finalize_parent_test.go`.
The parent-isolation binaries contain both final regressions. The earlier race
binary was overwritten after saving its hash in `race-binary-before.json`;
that hash is an identity record, not a retained executable.

Run `write-identities.py` from any working directory with Python to validate
recorded results and regenerate identities/checksums for both evidence folders.
It refuses missing or unexpected pass counts and unexpected production changes.
`SHA256SUMS` covers each folder's files except itself; `* -text` preserves bytes.
Test executables and disposable databases are local ignored artifacts.

The shell/PowerShell scripts preserve the actual local toolchain paths and
environment. Linux uses WSL `FusionRehearsal`, the `rehearsal` user and an isolated
network namespace; peer tests enable loopback only. They use short Linux `/tmp`
database/socket paths, public keys and synthetic funding. Rerunning scripts
overwrites their named result files, so use a separate evidence destination for
new results. No real key, preserved backup or W: restore was used.

No full historical replay or full-history synchronization is claimed. The
runtime diff is limited to `consensus/datong/consensus.go`, `core/blockchain.go`
and `core/headerchain.go`: five added lines, twenty-two removed lines.
