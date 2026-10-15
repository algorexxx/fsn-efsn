# W-backed continuation dispatched toward 10,200,000

The dispatcher started at 04:52:14 UTC on 15 October 2026,
from commit `c2442c25d32fb58f326ce792a31b2938c0f90c7a`, hidden host PID 30280.
Frozen input manifest:
`a8618aef240176cef0d5687c220ad186341d6031758ae9d59a51a9f88263e974`.
Prepared seal:
`c9816a79dbe1cbb6e64e502be1ce096ecff461cd4bf4b1a773e10eb2393030fd`.

Actual startup at 04:52:22 UTC passes mounted capacity with the exact W-backed
image and UUID on `/dev/loop0`. Distinct private mount/network namespaces have
only loopback down; the job runs as UID 1000. The job is checking the closed
9,900,000 inventory before its single replay writer. Startup alone adds no
verified blocks. Linux/D:/W: and image free space exceed the declared floors.
Protected source/recovery views remain read-only. Do not hash live database
files or the mounted image, change frozen inputs or launch another writer.

The startup observation at 04:52:43 UTC passed; its source/result are sealed here.
The supplemental observer is byte-identical to the preceding observer:
it records allocation separately from content verification. Actual allocation
matches the prior closed 85,798,092,800 bytes, a zero-byte difference for this run.
The controller still requires exact starting file hashes before replay. The
earlier failed allocation assertion remains preserved in its original bundle.
Host PID remains alive, early-dispatch and current host error logs are empty,
and no completed host-run record exists at this observation.

Target 10,200,000 adds 300,000 historical blocks, bounded by a fresh 92 GiB
sampled ceiling, six-hour cooperative stop, 6h15m Go, 6h30m replay outer and
eight-hour whole-job limits. These are caps, not an ETA. Keep local 7,170,976
fallback, independent 2,400,000 recovery, backup, archives and existing reserves.
No automatic next range or release selection change.

Runtime status:
`/home/rehearsal/results/restart-ticket-encoder-w-10200000-2026-10-15/status.json`.
Host records: `tmp/replay-w-10200000-2026-10-15/`.
Early dispatcher logs: `tmp/replay-w-10200000-dispatch.stdout.txt` and
`tmp/replay-w-10200000-dispatch.stderr.txt`.
Inspect inner verification/completion, outer `storage-completion.json`, host
exit and actual detach before accepting results. An unrelated Docker ISO may
remain attached; only this job's image attachment must be gone. Seal late outer
records separately without rewriting any earlier manifest.
