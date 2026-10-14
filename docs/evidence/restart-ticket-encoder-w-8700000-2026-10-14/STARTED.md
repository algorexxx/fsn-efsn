# W-backed continuation dispatched toward 8,700,000

The dispatcher started at 04:20:58 UTC on 14 October 2026,
from commit `bfccd8d63c09674ab1c5e46a3f9fc8cfa79201cf`, hidden host PID 117872.
Frozen input manifest:
`b83433b3fb4853a4e6bcc83294c3d1e2b9a727bdf3a09dcd6b3433067cd8edc8`.
Prepared seal:
`e2cacc1206d2fa520039f6119ccb1b9d6ae782e7c34b1f6b99bec2bb2ebcfd00`.

Actual startup at 04:21:07 UTC passes mounted capacity with the exact W-backed
image and UUID on `/dev/loop0`. Distinct private mount/network namespaces have
only loopback down; the job runs as UID 1000. The job is checking the closed
8,400,000 inventory before its single replay writer. Startup alone adds no
verified blocks. Linux/D:/W: and image free space exceed the declared floors.
Protected source/recovery views remain read-only. Do not hash live database
files or the mounted image, change frozen inputs or launch another writer.

The startup observation at 04:21:18 UTC passed; its source/result are sealed here.
Host PID remains alive, early-dispatch and current host error logs are empty,
and no completed host-run record exists at this observation.

Target 8,700,000 adds 300,000 historical blocks, bounded by a fresh 75 GiB
sampled ceiling, six-hour cooperative stop, 6h15m Go, 6h30m replay outer and
eight-hour whole-job limits. These are caps, not an ETA. Keep local 7,170,976
fallback, independent 2,400,000 recovery, backup, archives and existing reserves.
No automatic next range or release selection change.

Runtime status:
`/home/rehearsal/results/restart-ticket-encoder-w-8700000-2026-10-14/status.json`.
Host records: `tmp/replay-w-8700000-2026-10-14/`.
Early dispatcher logs: `tmp/replay-w-8700000-dispatch.stdout.txt` and
`tmp/replay-w-8700000-dispatch.stderr.txt`.
Inspect inner verification/completion, outer `storage-completion.json`, host
exit and actual detach before accepting results. An unrelated Docker ISO may
remain attached; only this job's image attachment must be gone. Seal late outer
records separately without rewriting any earlier manifest.
