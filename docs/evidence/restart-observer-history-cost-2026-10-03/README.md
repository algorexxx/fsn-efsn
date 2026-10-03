# Observer history cost evidence — 3 October 2026

Baseline `7ef1351a`. The observer formats canonical-change hashes explicitly as
hexadecimal; the node and consensus are unchanged. The other code changes are
the exact diagnostic regression, earlier test cleanup and an opt-in bounded
measurement using retained public-test-key snapshots.

`initial-format-failure.txt` records the new assertion failing before the fix.
Its literal expected hashes come from the retained service fixture's head and
anchor. The failure also left an open test database until process exit, producing
a Windows cleanup warning; the test now registers cleanup immediately.

`attempt-1/windows` contains passing observer and command suites.
`attempt-1/linux` contains the passing race suites and the separate non-race
measurement (16.20 seconds, 66,544 KiB peak RSS). The namespace had loopback only;
dependency downloads were disabled. `cost.json` retains every measured duration,
allocation total and file-size sample. Temporary histories were removed by Go's
test cleanup. No production backup or real key was read.

The test retimes the existing `ipc-converged` two-node report into histories of
10, 100 and 1,000 snapshots. It measures three status/export/reopen samples and
one append per size. Timings exclude fixture construction and pre-sample GC.
Reopening uses warm OS caches in the same process. Export goes to a discard sink;
there is no export-file I/O measurement. Repeated snapshots compress better than
changing real data; closed file lengths are not peak disk allocation. This test
does not measure RPC acquisition, block growth or ticket timeline reconstruction.

`verify.py` checks matching platform source hashes, the original fixture hashes,
test exits, regression passes, race diagnostics, isolation and measurement shape.
It derives the summary and explicitly illustrative capacity arithmetic in
[checks.json](checks.json). It does not turn timings into a service-level guarantee.

Repeat with an unused attempt name:

```powershell
./docs/evidence/restart-observer-history-cost-2026-10-03/run-windows.ps1 -Attempt attempt-2
wsl -d FusionRehearsal -u root -- unshare --net -- bash /mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-observer-history-cost-2026-10-03/run-linux.sh attempt-2
```

The verifier is pinned to the recorded first attempt. Update that selection only
when intentionally reviewing a new run, retaining the earlier evidence.
See the [report](../../restart-observer-history-cost.md) for the operational finding
and next bounded workload, retention and deployment checks.
