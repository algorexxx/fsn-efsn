# Restored startup: database-open refusals — 9 October 2026

**PASS: four bounded actual CLI refusal cases.** The unchanged unselected startup
candidate refuses an exclusively locked database, a directory unreadable by its
uid, a malformed CURRENT file and a corrupt current manifest. Each exits 1 with
the expected preflight diagnostic, before protocol initialization or console
execution. The [verifier](verification.json) checks every case's command result,
reason, cold file inventory and restored directory mode.

The fixtures are four small copies of the prior [positive-run fixture](../restart-restored-startup-positive-2026-10-09/README.md).
An exclusive advisory LevelDB lock was obtained before authenticating/copying the
closed source against its final inventory. No live LevelDB was hashed. The lock
case holds the destination LOCK without opening a database or running a writer;
hash comparison occurs before acquisition and after release. The unreadable case
temporarily sets only its disposable chain directory to mode 000, then restores
the original mode in `finally` before inventory comparison. Corruptions are made
only to disposable copies and retained as evidence. All tested chain-file names
and bytes remain unchanged across refusal, including the deliberately bad bytes.

The same CLI binary is reused without rebuilding:
`07aa74a3f58132e5ff1465152402d5ea3b01738c0017af5dfd5672a75a2550cd`.
Its synthetic network-profile shim is test-only and excluded from the proposed
runtime patch. One Go worker, niceness 10, a 45-second process ceiling with
ten-second kill grace, private network namespace with only loopback down, empty
peer lists and disabled mining/auto-buy bound each case. The runner uses uid 1000
so the permission failure is real. No original backup, active historical replay,
recovery checkpoint, real key or production source selection is involved.

The [run record](qualification/run.json) retains exact argv, timestamps, capacity,
input/binary identities and file hashes. The four earlier positive phases and
fifteen earlier refusals were not rerun. This closes the listed open/permission/
lock refusal slice only. Complete-history pruning-mode startup and shutdown,
application of the checks to the preserved full snapshot, selected-host cost and
independent review remain open. There is no runtime patch change in this run.
