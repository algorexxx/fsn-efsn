# Offline historical continuation is running

Dispatched 10 October 2026 at 15:14:00 UTC from investigation commit 40551639.
Replay began at 15:17:23 UTC. The four startup commands passed: observer build,
build provenance, cold starting head and fresh backup endpoint reference.
All 7,625 working files, 1,383 separate recovery files and 1,738 prior evidence
files verified. Source, toolchain, replay identity and retained executable match;
the original failed-attempt STOP is preserved. No additional database copy.

The initial observation at 15:18:41 UTC confirms a live replay wrapper, no
reported failure or stop, and a passing allocation sample (16,163,786,752 bytes).
The 15:18:29 status reports height 5,602,080. Samples and log tail have different
observation times; progress remains provisional. Verified history remains
5,600,032 until replay, both cold checks and evidence verification complete.

Target 6,300,000; new 26 GiB sampled ceiling; 30-second samples; clean stop6h,
Go timeout6h15, outer6h30 plus20s grace. Per-batch Linux20/D50 GiB reserves remain.
Starting capacity was about 40.86 GiB Linux / 63.64 GiB D:. The approved disk
expansion to 220 GiB passed geometry and preservation checks before launch.
Private mount/network namespaces, loopback DOWN, protected read-only views and
actual run/database locks remain required. No real keys, public mining/contact,
production activation or release selection change.

Read status/resources only while running; do not hash or open its live LevelDB,
launch a duplicate writer or run competing bulk work. Runtime status:
/home/rehearsal/results/restart-ticket-encoder-job-6300000-v2-2026-10-10/status.json.
Host logs: repo tmp/replay-job-6300000-v2-2026-10-10. Dispatcher PID24780; WSL PID17704.
Inspect completion.json, verification.json, run and resource records before the
next dependent step. Preserve failed/stopped attempts, their original STOPs and
limits, sealed evidence, the original backup and separate 2,400,000-v2 recovery.
Six-source cleanup and disk expansion are complete. F12/G1 and final acceptance
remain open; do not repeat unchanged passing tests or expand dashboard scope.
