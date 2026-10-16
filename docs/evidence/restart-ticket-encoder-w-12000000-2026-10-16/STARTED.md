# W-backed continuation dispatched toward 12,000,000

The dispatcher started at 15:34:24 UTC on 16 October 2026,
from commit `415b695ecbbbe2b2b7743fb8217230a90a5f7dbe`, hidden host PID 204744.
Frozen input manifest:
`3639e66d4b5e5644c14f3cb6c1121a89d93225468ad3125f99d02d894f0c437e`.
Prepared seal:
`a6048173135c524914ca56e8d80bb67aae36e9c0d7ac3561572c463878da8686`.

Actual startup at 15:34:39 UTC passes mounted capacity with the exact W-backed
image and UUID on `/dev/loop0`. Distinct private mount/network namespaces have
only loopback down; the job runs as UID 1000. The job is checking the closed
11,700,000 inventory before its single replay writer. Startup alone adds no
verified blocks. Linux/D:/W: and image free space exceed the declared floors.
Protected source/recovery views remain read-only. Do not hash live database
files or the mounted image, change frozen inputs or launch another writer.

The startup observation at 15:34:54 UTC passed; its source/result are sealed here.
The supplemental observer is byte-identical to the preceding observer:
it records allocation separately from content verification. Actual allocation
matches the prior closed 107,191,193,600 bytes, a zero-byte difference for this run.
The controller still requires exact starting file hashes before replay. Prior
4 KiB differences and the earlier failed allocation assertion remain preserved;
their cause remains unestablished. No content check was waived.
Host PID remains alive, early-dispatch and current host error logs are empty,
and no completed host-run record exists at this observation.

Target 12,000,000 adds 300,000 historical blocks, bounded by a fresh 112 GiB
sampled ceiling, six-hour cooperative stop, 6h15m Go, 6h30m replay outer and
eight-hour whole-job limits. These are caps, not an ETA. Keep local 7,170,976
fallback, independent 2,400,000 recovery, backup, archives and existing reserves.
No automatic next range or release selection change. The preceding preflight
refusal remains sealed in its original bundle; current byte-preserving observer
preparation passed the unchanged exact-change preflight gate.

Runtime status:
`/home/rehearsal/results/restart-ticket-encoder-w-12000000-2026-10-16/status.json`.
Host records: `tmp/replay-w-12000000-2026-10-16/`.
Early dispatcher logs: `tmp/replay-w-12000000-dispatch.stdout.txt` and
`tmp/replay-w-12000000-dispatch.stderr.txt`.
Inspect inner verification/completion, outer `storage-completion.json`, host
exit and actual detach before accepting results. An unrelated Docker ISO may
remain attached; only this job's image attachment must be gone. Seal late outer
records separately without rewriting any earlier manifest.
