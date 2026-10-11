# Initial running observation

Observed 11 October 2026 at 21:51:51 UTC (23:51:51 Europe/Stockholm).
The hidden dispatcher launched at 21:45:40 UTC from commit `b34152ff`;
the retained replay process started at 21:51:47 UTC after successful startup
qualification. Requested interval: 6,300,000 through 6,600,000.

All four startup commands passed: observer build/build information, read-only
starting head, and backup endpoint reference. Exact verification covered all
13,794 working files, 1,383 separate recovery files and 1,879 prior evidence
files. Source/toolchain and executable identities passed the unchanged runner.
Replay identity remains
733848a7e2aaed7027305d21aacdd46cf84c48d363bc505c2dc25dd9fb163b11.

The process was alive at observation, with no recorded failure or stop reason.
The first size measurement passed at 29,064,523,776 allocated bytes. Launch
capacity was about 29.51 GiB Linux / 72.26 GiB D:. Private network/mount
namespaces, loopback DOWN and all three read-only preparation views are recorded.
No database files were read or hashed by this status observation.

The 34 GiB sampled ceiling, 20/50 GiB Linux/D: per-batch reserves, six-hour clean
stop, 6h15 Go timeout and 6h30 outer timeout plus 20-second grace remain unchanged.
No further writer, bulk archival, deletion or release-selection change started.

Verified historical coverage remains 6,300,000. The initial log only establishes
test startup, not newly verified blocks or a completed endpoint. Both endpoint
cold checks and the automatic evidence verifier must pass before a continuation
can count as complete. A stopped/failed job needs separate diagnosis and cold
inspection; do not rerun it blindly.

Runtime status:
/home/rehearsal/results/restart-ticket-encoder-job-6600000-2026-10-11/status.json.
Host dispatch records: repo tmp/replay-job-6600000-2026-10-11. Preserve this dated
observation; later completion/verification supersedes it.
