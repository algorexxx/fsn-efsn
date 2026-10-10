# Offline historical continuation is running

Dispatched 10 October 2026 at 18:41:04 UTC from investigation commit e74cd524.
Replay began at 18:45:49 UTC. The four startup commands passed: observer build,
build provenance, cold starting head and fresh backup endpoint reference.
All 10,895 working files, 1,383 separate recovery files and 1,826 prior evidence
files verified. Source, toolchain, replay identity and retained executable match;
the original native-reserve failure records are preserved. No new database copy.

The initial observation at 18:46:14 UTC confirms the live replay wrapper, matching
resume preflight/start at 5,976,864, no reported failure or stop, empty stderr and
a passing allocation sample (22,837,567,488 bytes). It does not yet record the
first progress batch. Samples and log tail have different observation times;
progress remains provisional. Verified history remains 5,976,864 until replay,
both cold checks and evidence verification complete.

Target 6,300,000: up to 323,136 new blocks. The new 28 GiB sampled ceiling allows
about 6.731 GiB growth at the cold start. Size samples remain every 30 seconds;
clean stop 6h, Go timeout 6h15, outer 6h30 plus 20s grace. Per-batch Linux20/D50
GiB reserves are unchanged. Starting capacity was about 34.548 GiB Linux /
62.725 GiB D:. The authorized archive/retirement reclaimed 12.715 GiB on D:.
Private mount/network namespaces, loopback DOWN, protected read-only views and
actual run/database locks remain required. No real keys, public mining/contact,
production activation or release selection change.

Read status/resources only while running; do not hash or open its live LevelDB,
launch another writer or run competing bulk work. Runtime status:
/home/rehearsal/results/restart-ticket-encoder-job-6300000-v3-2026-10-10/status.json.
Host logs: repo tmp/replay-job-6300000-v3-2026-10-10. Dispatcher PID10980; WSL PID49380.
Inspect completion.json, verification.json, run and resource records before the
next dependent step. Preserve failed/stopped attempts and their original limits,
sealed evidence, original backup and separate 2,400,000-v2 recovery. F12/G1 and
final acceptance remain open; avoid repeating unchanged passing tests.
