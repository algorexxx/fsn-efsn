# W-backed continuation dispatched toward 9,000,000

The dispatcher started at 09:28:43 UTC on 14 October 2026,
from commit `1e99935bc09fc3fa7332d3e61e79a024e3e2d3ba`, hidden host PID 50736.
Frozen input manifest:
`10a48cb13eb9a18dd76984d16394fa60a09969c2884286fcb154e4bc73e44696`.
Prepared seal:
`86fa3123d28558d2cb1120c2a7910e10152c954848c96be07dd254086a4b70a1`.

Actual startup at 09:28:50 UTC passes mounted capacity with the exact W-backed
image and UUID on `/dev/loop0`. Distinct private mount/network namespaces have
only loopback down; the job runs as UID 1000. The job is checking the closed
8,700,000 inventory before its single replay writer. Startup alone adds no
verified blocks. Linux/D:/W: and image free space exceed the declared floors.
Protected source/recovery views remain read-only. Do not hash live database
files or the mounted image, change frozen inputs or launch another writer.

The startup observation at 09:29:12 UTC passed; its source/result are sealed here.
Host PID remains alive, early-dispatch and current host error logs are empty,
and no completed host-run record exists at this observation.

Target 9,000,000 adds 300,000 historical blocks, bounded by a fresh 79 GiB
sampled ceiling, six-hour cooperative stop, 6h15m Go, 6h30m replay outer and
eight-hour whole-job limits. These are caps, not an ETA. Keep local 7,170,976
fallback, independent 2,400,000 recovery, backup, archives and existing reserves.
No automatic next range or release selection change.

Runtime status:
`/home/rehearsal/results/restart-ticket-encoder-w-9000000-2026-10-14/status.json`.
Host records: `tmp/replay-w-9000000-2026-10-14/`.
Early dispatcher logs: `tmp/replay-w-9000000-dispatch.stdout.txt` and
`tmp/replay-w-9000000-dispatch.stderr.txt`.
Inspect inner verification/completion, outer `storage-completion.json`, host
exit and actual detach before accepting results. An unrelated Docker ISO may
remain attached; only this job's image attachment must be gone. Seal late outer
records separately without rewriting any earlier manifest.
