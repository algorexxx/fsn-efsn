# W-backed continuation dispatched

Started 13 October 2026 at 05:08:37 UTC from prepared commit
`1073039b6ef84d070885b6141de7b9787921e195`, hidden host PID 38684.
Frozen input manifest:
`c1474c45a5f146322ea24f60b10a65a00f0267f93dbd82ebc736750be4f8ccb0`.
The host also verifies the prior trial's sealed outer review before dispatch.

Actual startup at 05:08:44 UTC passes mounted capacity and distinct private
mount/network namespaces with only loopback down. The correct W-backed image
is attached as `/dev/loop0`; protected source/recovery views are read-only.
The job is checking the closed 7,200,000 checkpoint before its replay writer.
There is one attachment owner and no competing test. Do not hash live database
files or the mounted image, change frozen inputs or launch another writer.

Target 7,500,000 adds 300,000 blocks, bounded by 54 GiB sampled allocation,
six-hour cooperative replay stop, 6h15m Go, 6h30m replay outer and eight-hour
whole-job limits. Those are caps, not an ETA. Keep local fallback, independent
recovery, backup, archives and existing reserves. No automatic next range.

Runtime status:
`/home/rehearsal/results/restart-ticket-encoder-w-7500000-2026-10-13/status.json`.
Host completion/logs: `tmp/replay-w-7500000-2026-10-13/`.
Inspect inner completion/verification, outer `storage-completion.json`, host
exit and actual detach before accepting results. Seal final outer records
separately from the inner automatic manifest. This startup adds no coverage.
