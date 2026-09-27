# Offline observer ticket evidence — 2026-09-27

This run implements and tests the [external ticket timeline](../../restart-observer-tickets.md)
on top of source baseline `babec5e`. No node runtime source changes belong to
this work. The runtime changes are confined to the observer command/package.

`attempt-1/windows` contains the passing Windows Go 1.21.3 suite/build results.
`attempt-1/linux` contains Linux Go 1.21.3 suite/build results with race detection,
inside a network namespace exposing only loopback. Both run the complete
`internal/observe` and `cmd/fsn-observe` suites, including existing local
HTTP/IPC adapter tests. Dependency downloads are disabled. No node service is
started and no production endpoint or private key is used. Both platforms passed
116 tests/subtests. The verifier's [checks.json](checks.json) records matching
timeline hashes and the independent ledger/event comparison.

`inputs.sha256.json` pins the retained ordinary-mining fixture and reviewed native
implementation inputs. Platform manifests pin the tested observer source bytes.
`node-1.json` and `node-2.json` are actual derived reports, compared byte for byte
across platforms. Their inventories and events are independently compared to
the preserved block-29 ledger and native-event audit by `verify.py`.

Reproduce using an unused attempt name:

```powershell
./docs/evidence/restart-observer-tickets-2026-09-27/run-windows.ps1 -Attempt attempt-2
wsl -d FusionRehearsal -u root -- unshare --net -- bash /mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-observer-tickets-2026-09-27/run-linux.sh attempt-2
```

The runners refuse to overwrite their output directories. `verify.py` checks
the committed `attempt-1` evidence and regenerates `checks.json`.
Preliminary focused Windows checks passed before the recorded full run.

Ordinary-mining inputs are accepted blocks from the earlier isolated rehearsal.
Branch replacement, native outcome and inventory variations are separate
observer unit fixtures; they are not claimed as fresh consensus execution.
In particular the branch replacement header is not newly signed or imported.
Cold-read/export assertions concern immutable logical history, not LevelDB file
bytes. Native report tests verify interpretation of deletion outcomes, not the
validity or full financial effect of a double-mining report.

This evidence does not establish historical baseline acquisition, live competing
reorganization collection, sustained throughput, large-history resource use,
endpoint honesty, complete account accounting or production deployment readiness.
