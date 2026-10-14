# W-backed continuation dispatched toward 9,900,000

The dispatcher started at 23:49:37 UTC on 14 October 2026,
from commit `5ad226022a7aa7170dbd9a1f8257ee3ecf52f2c8`, hidden host PID 51880.
Frozen input manifest:
`2c544f56c31c40deb0e06ff282ddfa3eaee5d2d46283434a1f015ad1c2150ad0`.
Prepared seal:
`8b06be6a0c7fc45e4965cedfad7b6cae544a2bcd13e463c9031eb16d94584c42`.
The bundle date is 15 October in the local Europe/Stockholm timezone.

Actual startup at 23:49:47 UTC passes mounted capacity with the exact W-backed
image and UUID on `/dev/loop0`. Distinct private mount/network namespaces have
only loopback down; the job runs as UID 1000. The job is checking the closed
9,600,000 inventory before its single replay writer. Startup alone adds no
verified blocks. Linux/D:/W: and image free space exceed the declared floors.
Protected source/recovery views remain read-only. Do not hash live database
files or the mounted image, change frozen inputs or launch another writer.

The startup observation at 23:49:53 UTC passed; its source/result are sealed here.
The supplemental observer is byte-identical to the preceding observer:
it records allocation separately from content verification. Actual allocation
matches the prior closed 83,045,781,504 bytes, a zero-byte difference for this run.
The controller still requires exact starting file hashes before replay. The
earlier failed allocation assertion remains preserved in its original bundle.
Host PID remains alive, early-dispatch and current host error logs are empty,
and no completed host-run record exists at this observation.

Target 9,900,000 adds 300,000 historical blocks, bounded by a fresh 90 GiB
sampled ceiling, six-hour cooperative stop, 6h15m Go, 6h30m replay outer and
eight-hour whole-job limits. These are caps, not an ETA. Keep local 7,170,976
fallback, independent 2,400,000 recovery, backup, archives and existing reserves.
No automatic next range or release selection change.

Runtime status:
`/home/rehearsal/results/restart-ticket-encoder-w-9900000-2026-10-15/status.json`.
Host records: `tmp/replay-w-9900000-2026-10-15/`.
Early dispatcher logs: `tmp/replay-w-9900000-dispatch.stdout.txt` and
`tmp/replay-w-9900000-dispatch.stderr.txt`.
Inspect inner verification/completion, outer `storage-completion.json`, host
exit and actual detach before accepting results. An unrelated Docker ISO may
remain attached; only this job's image attachment must be gone. Seal late outer
records separately without rewriting any earlier manifest.
