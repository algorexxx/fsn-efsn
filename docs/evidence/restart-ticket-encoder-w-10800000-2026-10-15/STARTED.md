# W-backed continuation dispatched toward 10,800,000

The dispatcher started at 14:10:59 UTC on 15 October 2026,
from commit `3afd454cdfb31bdc95f815c2b1b83caf60344730`, hidden host PID 139956.
Frozen input manifest:
`b1f341f395101ed4af57b5c060379202178f66877e02ef4a26dcafdb86baf7b9`.
Prepared seal:
`9c3c23a7a3de0a9928a855c4f891f85b9ca1985d7e3aaeaf9b7860913f1af473`.

Actual startup at 14:11:10 UTC passes mounted capacity with the exact W-backed
image and UUID on `/dev/loop0`. Distinct private mount/network namespaces have
only loopback down; the job runs as UID 1000. The job is checking the closed
10,500,000 inventory before its single replay writer. Startup alone adds no
verified blocks. Linux/D:/W: and image free space exceed the declared floors.
Protected source/recovery views remain read-only. Do not hash live database
files or the mounted image, change frozen inputs or launch another writer.

The startup observation at 14:11:27 UTC passed; its source/result are sealed here.
The supplemental observer is byte-identical to the preceding observer:
it records allocation separately from content verification. Actual allocation
matches the prior closed 92,005,642,240 bytes, a zero-byte difference for this run.
The controller still requires exact starting file hashes before replay. Prior
4 KiB differences and the earlier failed allocation assertion remain preserved;
their cause remains unestablished. No content check was waived.
Host PID remains alive, early-dispatch and current host error logs are empty,
and no completed host-run record exists at this observation.

Target 10,800,000 adds 300,000 historical blocks, bounded by a fresh 98 GiB
sampled ceiling, six-hour cooperative stop, 6h15m Go, 6h30m replay outer and
eight-hour whole-job limits. These are caps, not an ETA. Keep local 7,170,976
fallback, independent 2,400,000 recovery, backup, archives and existing reserves.
No automatic next range or release selection change.

Runtime status:
`/home/rehearsal/results/restart-ticket-encoder-w-10800000-2026-10-15/status.json`.
Host records: `tmp/replay-w-10800000-2026-10-15/`.
Early dispatcher logs: `tmp/replay-w-10800000-dispatch.stdout.txt` and
`tmp/replay-w-10800000-dispatch.stderr.txt`.
Inspect inner verification/completion, outer `storage-completion.json`, host
exit and actual detach before accepting results. An unrelated Docker ISO may
remain attached; only this job's image attachment must be gone. Seal late outer
records separately without rewriting any earlier manifest.
