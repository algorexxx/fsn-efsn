# W-backed continuation dispatched toward 7,800,000

The corrected dispatcher started on 13 October 2026 at 10:10:18 UTC from
commit `0afddddb9dc635c9e86dfe4161578a259e4b7ab8`, hidden host PID 32612.
The original prepared inputs remain at commit `c11236772eafa0e1eaac4bed6db7a6a611d9f547`.
Frozen input manifest:
`87c96caa5e721bb26c4e7f40f2741b6d3bc64fe178e0b7311450f25fb881f5b9`.
Prepared seal:
`a4ede434193f90f9667ab06246ad47911ea09ebb513d5617d2a0ea29e23fe24c`.
Dispatcher correction seal:
`f579aa75c9d63a64e912fe2868741e73ede1fcdb3340ac867eba8cea58131c3a`.

Actual startup at 10:10:28 UTC passes mounted capacity with the exact W-backed
image and UUID on `/dev/loop0`. Distinct private mount/network namespaces have
only loopback down. The job is checking the closed 7,500,000 inventory before
its single replay writer; startup alone adds no verified blocks. Linux/D:/W:
free space exceeds declared floors, and the image has about 461.12 GiB free.
Protected source/recovery views remain read-only. Do not hash live database
files or the mounted image, change frozen inputs or launch another writer.

The [initial preflight refusal](PREFLIGHT-NOTE.md) concerned Docker Desktop's
unrelated read-only ISO; its attachment was left alone. The
[first dispatch refusal](DISPATCH-NOTE.md) concerned the old host log path.
Both occurred before test execution and remain preserved. `run-host-v2.ps1`
changes only that log destination. Its successful fresh validation preceded
this dispatch; replay/controller/input bytes are unchanged.

Target 7,800,000 adds 300,000 historical blocks, bounded by a fresh 60 GiB
sampled ceiling, six-hour cooperative stop, 6h15m Go, 6h30m replay outer and
eight-hour whole-job limits. These are caps, not an ETA. Keep the local
7,170,976 fallback, independent 2,400,000 recovery, backup, archives and existing
reserves. No automatic next range or release selection change.

Runtime status:
`/home/rehearsal/results/restart-ticket-encoder-w-7800000-2026-10-13/status.json`.
Host records: `tmp/replay-w-7800000-2026-10-13/`.
Early dispatcher logs: `tmp/replay-w-7800000-dispatch-v2.stdout.txt` and
`tmp/replay-w-7800000-dispatch-v2.stderr.txt`.
Inspect inner verification/completion, outer `storage-completion.json`, host
exit and actual detach before accepting results. Docker's unrelated ISO may
remain attached; only this job's image attachment must be gone. Seal final
outer records separately without rewriting any earlier manifest.
