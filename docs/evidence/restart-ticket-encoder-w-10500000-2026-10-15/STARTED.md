# W-backed continuation dispatched toward 10,500,000

The dispatcher started at 08:54:45 UTC on 15 October 2026,
from commit `293aa9709931249c814585b83b28cbd6a27cd6e2`, hidden host PID 101756.
Frozen input manifest:
`391cde363194e8f0e545d2215b6d3cce680f3bd1f0bae7c265a2c1777a5ae28d`.
Prepared seal:
`00a99a09d79cc0a1f652e6e1920320107dd62bdc81691a0b50cb8c076c917082`.

Actual startup at 08:54:54 UTC passes mounted capacity with the exact W-backed
image and UUID on `/dev/loop0`. Distinct private mount/network namespaces have
only loopback down; the job runs as UID 1000. The job is checking the closed
10,200,000 inventory before its single replay writer. Startup alone adds no
verified blocks. Linux/D:/W: and image free space exceed the declared floors.
Protected source/recovery views remain read-only. Do not hash live database
files or the mounted image, change frozen inputs or launch another writer.

The startup observation at 08:55:19 UTC passed; its source/result are sealed here.
The supplemental observer is byte-identical to the preceding observer:
it records allocation separately from content verification. Actual allocation
is 88,663,257,088 bytes, 4,096 bytes above the prior closed 88,663,252,992 bytes.
The cause is unestablished. The unchanged controller requires exact starting
file hashes before replay, independently of allocation. Those hashes are not
yet accepted at startup; any mismatch must refuse the writer. The earlier
failed allocation assertion remains preserved in its original bundle; this
capture passed and did not weaken any check or restart the job.
Host PID remains alive, early-dispatch and current host error logs are empty,
and no completed host-run record exists at this observation.

Target 10,500,000 adds 300,000 historical blocks, bounded by a fresh 95 GiB
sampled ceiling, six-hour cooperative stop, 6h15m Go, 6h30m replay outer and
eight-hour whole-job limits. These are caps, not an ETA. Keep local 7,170,976
fallback, independent 2,400,000 recovery, backup, archives and existing reserves.
No automatic next range or release selection change.

Runtime status:
`/home/rehearsal/results/restart-ticket-encoder-w-10500000-2026-10-15/status.json`.
Host records: `tmp/replay-w-10500000-2026-10-15/`.
Early dispatcher logs: `tmp/replay-w-10500000-dispatch.stdout.txt` and
`tmp/replay-w-10500000-dispatch.stderr.txt`.
Inspect inner verification/completion, outer `storage-completion.json`, host
exit and actual detach before accepting results. An unrelated Docker ISO may
remain attached; only this job's image attachment must be gone. Seal late outer
records separately without rewriting any earlier manifest.
