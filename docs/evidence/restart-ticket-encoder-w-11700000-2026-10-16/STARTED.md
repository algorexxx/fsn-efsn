# W-backed continuation dispatched toward 11,700,000

The dispatcher started at 08:33:00 UTC on 16 October 2026,
from commit `c5e2f647ebfa0c5b2061c20557fe039a4328d01b`, hidden host PID 31276.
Frozen input manifest:
`2d312d51f9d2f3b376fe2f9dfc5d12f57ac2e10a4f4b27779cf63d1cca7bd5e5`.
Prepared seal:
`28a80b43fdcbbf2405d954b22205ec679221662b99a41e923c2db179429e1308`.

Actual startup at 08:33:12 UTC passes mounted capacity with the exact W-backed
image and UUID on `/dev/loop0`. Distinct private mount/network namespaces have
only loopback down; the job runs as UID 1000. The job is checking the closed
11,400,000 inventory before its single replay writer. Startup alone adds no
verified blocks. Linux/D:/W: and image free space exceed the declared floors.
Protected source/recovery views remain read-only. Do not hash live database
files or the mounted image, change frozen inputs or launch another writer.

The startup observation at 08:33:25 UTC passed; its source/result are sealed here.
The supplemental observer is byte-identical to the preceding observer:
it records allocation separately from content verification. Actual allocation
matches the prior closed 102,401,626,112 bytes, a zero-byte difference for this run.
The controller still requires exact starting file hashes before replay. Prior
4 KiB differences and the earlier failed allocation assertion remain preserved;
their cause remains unestablished. No content check was waived.
Host PID remains alive, early-dispatch and current host error logs are empty,
and no completed host-run record exists at this observation.

Target 11,700,000 adds 300,000 historical blocks, bounded by a fresh 108 GiB
sampled ceiling, six-hour cooperative stop, 6h15m Go, 6h30m replay outer and
eight-hour whole-job limits. These are caps, not an ETA. Keep local 7,170,976
fallback, independent 2,400,000 recovery, backup, archives and existing reserves.
No automatic next range or release selection change.

The [first preflight refusal](preflight-refusal-1/FAILURE.md) remains sealed.
It caught Windows line-ending changes before launch; byte-preserving correction
and repeated host/Linux preflight passed without changing any controller gate.
The single actual dispatch follows that correction.

Runtime status:
`/home/rehearsal/results/restart-ticket-encoder-w-11700000-2026-10-16/status.json`.
Host records: `tmp/replay-w-11700000-2026-10-16/`.
Early dispatcher logs: `tmp/replay-w-11700000-dispatch.stdout.txt` and
`tmp/replay-w-11700000-dispatch.stderr.txt`.
Inspect inner verification/completion, outer `storage-completion.json`, host
exit and actual detach before accepting results. An unrelated Docker ISO may
remain attached; only this job's image attachment must be gone. Seal late outer
records separately without rewriting any earlier manifest.
