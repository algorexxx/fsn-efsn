# W-backed continuation dispatched toward 12,600,000

The dispatcher started at 03:42:30 UTC on 17 October 2026,
from commit `b175fadfd00ab675d94b8ad3c523024d042b1ceb`, hidden host PID 85988.
Frozen input manifest:
`37fa37a087889696084f7f7039f620aaaf01b3d5fb12cc7c83b866fb01ad0e0a`.
Prepared seal:
`c6bcb156dc17665bf18fe266d0b27b7747b3cafc158f4e38441451d4e2bbd557`.

Actual startup at 03:42:45 UTC passes mounted capacity with the exact W-backed
image and UUID on `/dev/loop0`. Distinct private mount/network namespaces have
only loopback down; the job runs as UID 1000. The job is checking the closed
12,300,000 inventory before its single replay writer. Startup alone adds no
verified blocks. Linux/D:/W: and image free space exceed the declared floors.
Protected source/recovery views remain read-only. Do not hash live database
files or the mounted image, change frozen inputs or launch another writer.

The startup observation at 03:42:57 UTC passed; its source/result are sealed here.
The supplemental observer is byte-identical to the preceding observer:
it records allocation separately from content verification. Actual allocation
matches the prior closed 110,394,753,024 bytes, a zero-byte difference for this run.
The controller still requires exact starting file hashes before replay. Prior
4 KiB differences and the earlier failed allocation assertion remain preserved;
their cause remains unestablished. No content check was waived.
Host PID remains alive, early-dispatch and current host error logs are empty,
and no completed host-run record exists at this observation.

Target 12,600,000 adds 300,000 historical blocks, bounded by a fresh 115 GiB
sampled ceiling, six-hour cooperative stop, 6h15m Go, 6h30m replay outer and
eight-hour whole-job limits. These are caps, not an ETA. Keep local 7,170,976
fallback, independent 2,400,000 recovery, backup, archives and existing reserves.
No automatic next range or release selection change. The preceding preflight
refusal remains sealed in its original bundle; current byte-preserving observer
preparation passed the unchanged exact-change preflight gate.

Runtime status:
`/home/rehearsal/results/restart-ticket-encoder-w-12600000-2026-10-17/status.json`.
Host records: `tmp/replay-w-12600000-2026-10-17/`.
Early dispatcher logs: `tmp/replay-w-12600000-dispatch.stdout.txt` and
`tmp/replay-w-12600000-dispatch.stderr.txt`.
Inspect inner verification/completion, outer `storage-completion.json`, host
exit and actual detach before accepting results. An unrelated Docker ISO may
remain attached; only this job's image attachment must be gone. Seal late outer
records separately without rewriting any earlier manifest.
