# W-backed continuation dispatched toward 11,100,000

The dispatcher started at 20:08:26 UTC on 15 October 2026,
from commit `0b769cfa9c56d388bb96e56556dea078e292c127`, hidden host PID 147132.
Frozen input manifest:
`0c07b0045797a2aa140c4ff351fde72f285b61cfec3bc47f3bb26591b92c1ed5`.
Prepared seal:
`2f184d53bbf7bae66a1e9d403b5afe034702ecea5a8161059e21fdaaec8e1d4d`.

Actual startup at 20:08:37 UTC passes mounted capacity with the exact W-backed
image and UUID on `/dev/loop0`. Distinct private mount/network namespaces have
only loopback down; the job runs as UID 1000. The job is checking the closed
10,800,000 inventory before its single replay writer. Startup alone adds no
verified blocks. Linux/D:/W: and image free space exceed the declared floors.
Protected source/recovery views remain read-only. Do not hash live database
files or the mounted image, change frozen inputs or launch another writer.

The startup observation at 20:08:41 UTC passed; its source/result are sealed here.
The supplemental observer is byte-identical to the preceding observer:
it records allocation separately from content verification. Actual allocation
matches the prior closed 95,340,163,072 bytes, a zero-byte difference for this run.
The controller still requires exact starting file hashes before replay. Prior
4 KiB differences and the earlier failed allocation assertion remain preserved;
their cause remains unestablished. No content check was waived.
Host PID remains alive, early-dispatch and current host error logs are empty,
and no completed host-run record exists at this observation.

Target 11,100,000 adds 300,000 historical blocks, bounded by a fresh 101 GiB
sampled ceiling, six-hour cooperative stop, 6h15m Go, 6h30m replay outer and
eight-hour whole-job limits. These are caps, not an ETA. Keep local 7,170,976
fallback, independent 2,400,000 recovery, backup, archives and existing reserves.
No automatic next range or release selection change.

Runtime status:
`/home/rehearsal/results/restart-ticket-encoder-w-11100000-2026-10-15/status.json`.
Host records: `tmp/replay-w-11100000-2026-10-15/`.
Early dispatcher logs: `tmp/replay-w-11100000-dispatch.stdout.txt` and
`tmp/replay-w-11100000-dispatch.stderr.txt`.
Inspect inner verification/completion, outer `storage-completion.json`, host
exit and actual detach before accepting results. An unrelated Docker ISO may
remain attached; only this job's image attachment must be gone. Seal late outer
records separately without rewriting any earlier manifest.
