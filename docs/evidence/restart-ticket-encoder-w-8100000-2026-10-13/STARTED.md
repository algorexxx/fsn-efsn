# W-backed continuation dispatched toward 8,100,000

The dispatcher started on 13 October 2026 at 16:15:24 UTC from commit
`192be8d6cab0777a61ee10a7cbb44297710a2163`, hidden host PID 99268.
Frozen input manifest:
`8db5f5bea414f6b9394234ddd5e5c12b9e7887d5f51dfcd39e738f117b9f34b4`.
Prepared seal:
`b8b3a957af4b58eb46150f9b2aa22a7eac12a5290a3e51ee01938e73da2ed7f5`.

Actual startup at 16:15:33 UTC passes mounted capacity with the exact W-backed
image and UUID on `/dev/loop0`. Distinct private mount/network namespaces have
only loopback down; the job runs as UID 1000. The job is checking the closed
7,800,000 inventory before its single replay writer; startup alone adds no
verified blocks. Linux/D:/W: and image free space exceed all declared floors.
Protected source/recovery views remain read-only. Do not hash live database
files or the mounted image, change frozen inputs or launch another writer.

Target 8,100,000 adds 300,000 historical blocks, bounded by a fresh 67 GiB
sampled ceiling, six-hour cooperative stop, 6h15m Go, 6h30m replay outer and
eight-hour whole-job limits. These are caps, not an ETA. Keep the local
7,170,976 fallback, independent 2,400,000 recovery, backup, archives and existing
reserves. No automatic next range or release selection change.

Runtime status:
`/home/rehearsal/results/restart-ticket-encoder-w-8100000-2026-10-13/status.json`.
Host records: `tmp/replay-w-8100000-2026-10-13/`.
Early dispatcher logs: `tmp/replay-w-8100000-dispatch.stdout.txt` and
`tmp/replay-w-8100000-dispatch.stderr.txt`.
Inspect inner verification/completion, outer `storage-completion.json`, host
exit and actual detach before accepting results. An unrelated Docker ISO may
remain attached; only this job's image attachment must be gone. Seal final
outer records separately without rewriting any earlier manifest.
