# W-backed continuation dispatched toward 9,300,000

The dispatcher started at 14:30:30 UTC on 14 October 2026,
from commit `36ae3069545b7cb6b057443c8a10b54e62c18a5c`, hidden host PID 103344.
Frozen input manifest:
`d0df1e838cf33f2f711d7e91fff91579823ca0322f80de2816d94bc587ea003e`.
Prepared seal:
`ca1c6fdf885f2ebbc664a3876e590d1876f9e251afae5bbe6e9c9f477f0b6609`.

Actual startup at 14:30:39 UTC passes mounted capacity with the exact W-backed
image and UUID on `/dev/loop0`. Distinct private mount/network namespaces have
only loopback down; the job runs as UID 1000. The job is checking the closed
9,000,000 inventory before its single replay writer. Startup alone adds no
verified blocks. Linux/D:/W: and image free space exceed the declared floors.
Protected source/recovery views remain read-only. Do not hash live database
files or the mounted image, change frozen inputs or launch another writer.

The first supplemental capture failed its assumption that allocated bytes must
exactly match the preceding closed measurement: 76,542,509,056 at startup versus
76,542,504,960 previously, a 4,096-byte difference. The cause is not established.
The failed script and failure record remain preserved. `capture-startup-v2.py`
records both measurements instead of treating allocation equality as content
identity; the revised observation passed at 14:32:39 UTC. This changes only the
supplemental observer. Frozen controllers still require every checkpoint file
hash to match the verified prior inventory before replay; that check is pending.
No runtime input, limit, preservation or content check was altered or waived.
Host PID remains alive, early-dispatch and current host error logs are empty,
and no completed host-run record exists at this observation.

Target 9,300,000 adds 300,000 historical blocks, bounded by a fresh 83 GiB
sampled ceiling, six-hour cooperative stop, 6h15m Go, 6h30m replay outer and
eight-hour whole-job limits. These are caps, not an ETA. Keep local 7,170,976
fallback, independent 2,400,000 recovery, backup, archives and existing reserves.
No automatic next range or release selection change.

Runtime status:
`/home/rehearsal/results/restart-ticket-encoder-w-9300000-2026-10-14/status.json`.
Host records: `tmp/replay-w-9300000-2026-10-14/`.
Early dispatcher logs: `tmp/replay-w-9300000-dispatch.stdout.txt` and
`tmp/replay-w-9300000-dispatch.stderr.txt`.
Inspect inner verification/completion, outer `storage-completion.json`, host
exit and actual detach before accepting results. An unrelated Docker ISO may
remain attached; only this job's image attachment must be gone. Seal late outer
records separately without rewriting any earlier manifest.
