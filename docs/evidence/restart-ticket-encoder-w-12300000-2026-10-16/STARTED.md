# W-backed continuation dispatched toward 12,300,000

The dispatcher started at 21:38:57 UTC on 16 October 2026,
from commit `1d87112215fe6ecde235e9fd14e1568eecf4ea10`, hidden host PID 30736.
Frozen input manifest:
`68bbd910b1dc612d681bf4a6806893e475b950274836d557b8f0abdad949532a`.
Prepared seal:
`636fc7a071e17e3be0178b0244714452945d2f4edfd2910ec7f5ed23de3d0ba3`.

Actual startup at 21:39:10 UTC passes mounted capacity with the exact W-backed
image and UUID on `/dev/loop0`. Distinct private mount/network namespaces have
only loopback down; the job runs as UID 1000. The job is checking the closed
12,000,000 inventory before its single replay writer. Startup alone adds no
verified blocks. Linux/D:/W: and image free space exceed the declared floors.
Protected source/recovery views remain read-only. Do not hash live database
files or the mounted image, change frozen inputs or launch another writer.

The startup observation at 21:39:13 UTC passed; its source/result are sealed here.
The supplemental observer is byte-identical to the preceding observer:
it records allocation separately from content verification. Actual allocation
matches the prior closed 108,973,027,328 bytes, a zero-byte difference for this run.
The controller still requires exact starting file hashes before replay. Prior
4 KiB differences and the earlier failed allocation assertion remain preserved;
their cause remains unestablished. No content check was waived.
Host PID remains alive, early-dispatch and current host error logs are empty,
and no completed host-run record exists at this observation.

Target 12,300,000 adds 300,000 historical blocks, bounded by a fresh 114 GiB
sampled ceiling, six-hour cooperative stop, 6h15m Go, 6h30m replay outer and
eight-hour whole-job limits. These are caps, not an ETA. Keep local 7,170,976
fallback, independent 2,400,000 recovery, backup, archives and existing reserves.
No automatic next range or release selection change. The preceding preflight
refusal remains sealed in its original bundle; current byte-preserving observer
preparation passed the unchanged exact-change preflight gate.

Runtime status:
`/home/rehearsal/results/restart-ticket-encoder-w-12300000-2026-10-16/status.json`.
Host records: `tmp/replay-w-12300000-2026-10-16/`.
Early dispatcher logs: `tmp/replay-w-12300000-dispatch.stdout.txt` and
`tmp/replay-w-12300000-dispatch.stderr.txt`.
Inspect inner verification/completion, outer `storage-completion.json`, host
exit and actual detach before accepting results. An unrelated Docker ISO may
remain attached; only this job's image attachment must be gone. Seal late outer
records separately without rewriting any earlier manifest.
