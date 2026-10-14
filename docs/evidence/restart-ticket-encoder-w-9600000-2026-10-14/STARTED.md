# W-backed continuation dispatched toward 9,600,000

The dispatcher started at 19:42:21 UTC on 14 October 2026,
from commit `bcddbe9875f8f11720f9de00bb8c0f121b1606b6`, hidden host PID 43248.
Frozen input manifest:
`0437b7f21bfe9bdac1943a33e399ddbcb20a396261500e7de0a3fe08a3644a47`.
Prepared seal:
`b502f2e8495d2f41b5b3a543ea3a00640132897e2b9fa910ef8e0850c1725128`.

Actual startup at 19:42:30 UTC passes mounted capacity with the exact W-backed
image and UUID on `/dev/loop0`. Distinct private mount/network namespaces have
only loopback down; the job runs as UID 1000. The job is checking the closed
9,300,000 inventory before its single replay writer. Startup alone adds no
verified blocks. Linux/D:/W: and image free space exceed the declared floors.
Protected source/recovery views remain read-only. Do not hash live database
files or the mounted image, change frozen inputs or launch another writer.

The startup observation at 19:42:47 UTC passed; its source/result are sealed here.
The supplemental observer is byte-identical to the preceding corrected observer:
it records allocation separately from content verification. Actual allocation
matches the prior closed 80,277,336,064 bytes, a zero-byte difference for this run.
The controller still requires exact starting file hashes before replay. The
preceding run's failed allocation assertion remains preserved in its own bundle.
Host PID remains alive, early-dispatch and current host error logs are empty,
and no completed host-run record exists at this observation.

Target 9,600,000 adds 300,000 historical blocks, bounded by a fresh 87 GiB
sampled ceiling, six-hour cooperative stop, 6h15m Go, 6h30m replay outer and
eight-hour whole-job limits. These are caps, not an ETA. Keep local 7,170,976
fallback, independent 2,400,000 recovery, backup, archives and existing reserves.
No automatic next range or release selection change.

Runtime status:
`/home/rehearsal/results/restart-ticket-encoder-w-9600000-2026-10-14/status.json`.
Host records: `tmp/replay-w-9600000-2026-10-14/`.
Early dispatcher logs: `tmp/replay-w-9600000-dispatch.stdout.txt` and
`tmp/replay-w-9600000-dispatch.stderr.txt`.
Inspect inner verification/completion, outer `storage-completion.json`, host
exit and actual detach before accepting results. An unrelated Docker ISO may
remain attached; only this job's image attachment must be gone. Seal late outer
records separately without rewriting any earlier manifest.
