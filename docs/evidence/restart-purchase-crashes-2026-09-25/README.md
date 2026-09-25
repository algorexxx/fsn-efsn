# Automatic-purchase process interruption evidence

25 September 2026, baseline `33e80d1`. Only the two test files recorded in
`identities.json` extend the executable. No production source changes.

Each final platform run covers sixteen abrupt exits, each followed by separate
recovery and cold-check processes. The tests use a real LevelDB, transaction
pool, estimator and encrypted public key 1. Every fresh recovery starts with the
wallet locked. The required saved-record bytes and restored pool contents are
checked before allowing the controller to resume.

From PowerShell in the repository root:

```powershell
& ./docs/evidence/restart-purchase-crashes-2026-09-25/check-windows.ps1
wsl.exe --distribution FusionRehearsal --user root --exec bash /mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-purchase-crashes-2026-09-25/check-linux.sh
```

The scripts use the existing Go 1.21.3 toolchains, offline module caches and
GOMAXPROCS=2. All databases are small disposable fixtures on C:. Linux parent and
child tests run as `rehearsal`, with race detection, in an isolated network
namespace. No complete-state dataset, real key, D:/W: database, replay checkpoint
or public peer is used. Use a fresh evidence directory when reproducing.

All sixteen final cases pass: Windows 104.47 seconds, Linux with race detection
175.07 seconds. No production fix was needed for these scenarios.

The initial Windows/Linux runs passed before assertions were strengthened to
require exact record presence/bytes at each cut, exact restored pool presence,
canonical receipt/ticket evidence, and a preserved cold head. Those initial logs
and their recovery helper are retained as `initial-*`. The earlier single-case
`windows-smoke.txt` also predates hexadecimal hash formatting in log output.
Unprefixed build/test logs and pinned binaries describe the final source only.

`write-identities.py` requires all sixteen named final cases on each platform,
checks that production source is unchanged from the baseline, then records test
source Git blobs, binary hashes and evidence checksums. Timestamps differ across
fixtures; no cross-platform transaction-hash equality is asserted.

Read [the investigation report](../../restart-purchase-crash-rehearsal.md) for
the boundary matrix and limits. Process exits leave the operating system alive;
this is not power-loss or exactly-once network-delivery evidence.
