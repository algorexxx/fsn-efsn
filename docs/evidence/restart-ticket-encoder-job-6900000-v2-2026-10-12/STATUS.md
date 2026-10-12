# Initial replay observation

Actual replay began at 06:55:04 UTC on 12 October 2026, after the 06:49:35
dispatch from `b256ae6b1f89926f0d9a580bf3533ea0730e9527`. The separate observer
build/build-info, cold start at 6,623,296 and backup reference all exited zero.
Startup verified 16,893 working-file hashes, 1,383 recovery hashes and 2,028
prior evidence files. Executable and replay identity match the retained inputs.
Private network/mount namespaces, loopback DOWN and protected read-only views
are recorded in initial-observation.json.

The one-time observation at 07:37:35 UTC records the live bounded process and
its expected command. The 07:37:09 status has provisional height 6,728,384;
the subsequently read stdout tail reaches 6,729,280. These reads are not atomic
and neither height is accepted cold coverage. No failure, STOP or completion
is recorded, and stderr is empty. The latest allocation sample exited zero
on its first attempt: 37,367,029,760 bytes (34.801 GiB), with no vanished entries
in that sample. It remains below the unchanged 39 GiB sampled ceiling.

This observation reads only process and job records, never the live database.
Its hashes identify the run/status records at observation time, not their later
mutable contents. The earlier LAUNCH.md remains a dated startup observation.

Target remains 6,900,000, at most 276,704 new blocks from the verified checkpoint.
Keep Linux20/D50 GiB reserves and six-hour/6h15/6h30 stop limits. Do not start
another writer or repeat unrelated passing tests while this finite job is healthy.
Both cold endpoint checks and final evidence verification must pass before
adding coverage. Accepted history remains 6,623,296; F12/G1 and final release
acceptance remain open. No release selection or node runtime changed.
