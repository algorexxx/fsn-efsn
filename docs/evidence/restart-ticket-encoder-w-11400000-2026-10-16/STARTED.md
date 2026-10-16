# W-backed continuation dispatched toward 11,400,000

The dispatcher started at 01:16:31 UTC on 16 October 2026,
from commit `e032a05eeeddb7db3a66d5d09024b5ff143d441b`, hidden host PID 87064.
Frozen input manifest:
`2731b093a92ad7c99edd3b3d8eb0f1ba0c1490da650a287c685f66dd77bbf3ac`.
Prepared seal:
`e5bbf601712e0915de5088cef083946e5ec18123ffed10a8a59ca21a062b843c`.

Actual startup at 01:16:44 UTC passes mounted capacity with the exact W-backed
image and UUID on `/dev/loop0`. Distinct private mount/network namespaces have
only loopback down; the job runs as UID 1000. The job is checking the closed
11,100,000 inventory before its single replay writer. Startup alone adds no
verified blocks. Linux/D:/W: and image free space exceed the declared floors.
Protected source/recovery views remain read-only. Do not hash live database
files or the mounted image, change frozen inputs or launch another writer.

The startup observation at 01:16:46 UTC passed; its source/result are sealed here.
The supplemental observer is byte-identical to the preceding observer:
it records allocation separately from content verification. Actual allocation
matches the prior closed 98,262,872,064 bytes, a zero-byte difference for this run.
The controller still requires exact starting file hashes before replay. Prior
4 KiB differences and the earlier failed allocation assertion remain preserved;
their cause remains unestablished. No content check was waived.
Host PID remains alive, early-dispatch and current host error logs are empty,
and no completed host-run record exists at this observation.

Target 11,400,000 adds 300,000 historical blocks, bounded by a fresh 104 GiB
sampled ceiling, six-hour cooperative stop, 6h15m Go, 6h30m replay outer and
eight-hour whole-job limits. These are caps, not an ETA. Keep local 7,170,976
fallback, independent 2,400,000 recovery, backup, archives and existing reserves.
No automatic next range or release selection change.

Runtime status:
`/home/rehearsal/results/restart-ticket-encoder-w-11400000-2026-10-16/status.json`.
Host records: `tmp/replay-w-11400000-2026-10-16/`.
Early dispatcher logs: `tmp/replay-w-11400000-dispatch.stdout.txt` and
`tmp/replay-w-11400000-dispatch.stderr.txt`.
Inspect inner verification/completion, outer `storage-completion.json`, host
exit and actual detach before accepting results. An unrelated Docker ISO may
remain attached; only this job's image attachment must be gone. Seal late outer
records separately without rewriting any earlier manifest.
