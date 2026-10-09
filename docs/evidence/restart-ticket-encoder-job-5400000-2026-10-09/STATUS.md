# Finite job dispatched

Dispatched 9 October 2026 at 19:32:26 UTC (21:32:26 Europe/Stockholm),
following verified completion through 4,500,000, passing complete-backup
read-only startup preflight and fresh capacity checks. Target: 5,400,000.

The hidden dispatcher owns the existing offline launcher. Starting identity,
closed-inventory, executable and capacity checks must pass before replay.
Initial runtime status exists; completion is pending. Do not start another writer
or hash the working database while this job is active. Use live status.json,
completion.json, verification.json and resource records before subsequent work.

Source/release selection, replay executable, six-hour clean stop, 11 GiB sampled
ceiling and 20/50 GiB per-batch reserves remain unchanged. The verified 2,400,000
recovery checkpoint is preserved. Prepared files remain immutable.

The initial observation at 19:33:54 UTC records all four preparation commands
passing: observer build, executable identity inspection, starting cold head and
backup reference. All 1,572 prior evidence files verified; the replay executable
hash is unchanged. Final resume validation was still pending at that observation.
See initial-observation.json; this is not a new verified historical endpoint.

Active observation at 19:34:44 UTC confirms replay began at 19:34:33 UTC
(PID 635), with a passing first allocation sample of 8,907,165,696 bytes and
no failure or stop reason. See active-observation.json. Completion remains pending.
