# Offline historical continuation is running

Dispatched 10 October 2026 at 12:50:50 UTC from investigation commit 4b83c16c.
Replay began at 12:53:26 UTC. The four startup commands passed: observer build,
build provenance, cold starting head and fresh backup endpoint reference.
All 5,591 working files, 1,383 separate recovery files and 1,655 prior evidence
files verified. Source, toolchain, replay identity and retained executable match;
the original failed-attempt STOP is preserved. No additional database copy.

The initial observation at 12:54:18 UTC confirms a live replay wrapper, no
reported failure or stop, a passing allocation sample (11,846,160,384 bytes),
and progress beyond 5,335,000. The sampled status and log tail have different
sampling times; both are provisional. Verified history remains 5,331,360 until
replay, both cold checks and independent evidence verification complete.

Target 6,300,000; 15 GiB sampled ceiling; 30-second samples; clean-stop6h,
Go timeout6h15, outer6h30 plus20s grace. Per-batch reserves remain Linux20/D50 GiB.
Fresh launch capacity was about 26.26 GiB Linux / 63.68 GiB D:. Private mount/net
namespaces and loopback DOWN are recorded. Protected backup/recovery views are
read-only. No real keys, public mining, network contact or release change.

Read status/resources only while running; do not hash or open its live LevelDB,
launch a duplicate writer or run competing bulk work. Runtime status:
/home/rehearsal/results/restart-ticket-encoder-job-6300000-2026-10-10/status.json.
Host logs: repo tmp/replay-job-6300000-2026-10-10. Dispatcher PID22504; WSL PID40860.
At the next scheduled check inspect completion.json, verification.json, run and
resource records before deciding the next step. Preserve all failed/stopped
runs, sealed evidence and the separate 2,400,000-v2 recovery. The authorized
six-source cleanup is complete. No additional removal or compaction is needed
for this job. Historical F12/G1 and final restored-startup/recovery/independent
review remain open; do not rerun unchanged passing small acceptance tests.
