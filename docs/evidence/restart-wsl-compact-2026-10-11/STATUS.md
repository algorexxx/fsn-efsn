# Cold archive started; compaction pending

The hidden dispatcher launched at 22:11:02 UTC on 10 October (00:11 on
11 October in Europe/Stockholm), from commit `86874249`. The worker verified
all 53 completed-replay evidence files, found the 220 GiB virtual disk detached,
and opened the 211,278,626,816-byte source with a read lock that refuses writers.
The first phase copies and hashes it to W:, followed by full independent
source and archive rereads. Its finite limit is ten hours plus ten minutes
of outer grace. Initial progress is recorded in `initial-observation.json`.

Archive completion and whole-image equality are not yet established.
No trim, compaction, deletion or replay has started. Do not start
FusionRehearsal or a competing storage workload during the archive. Preserve
the incomplete file if it fails; do not overwrite or silently retry this run.

Docker's backend was observed running immediately before dispatch, although
it had been stopped at preparation. The rehearsal disk remained detached.
No Docker service action was performed. Recheck actual service state before
any later stop/detach requirement; do not apply the old observation blindly.

Next: verify archive completion and hashes, commit evidence, then perform the
approved pre-compaction logical preservation checks, native compaction and
post-compaction checks. Retain the rollback archive through qualification.
