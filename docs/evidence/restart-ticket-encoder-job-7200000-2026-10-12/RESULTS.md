# Declared allocation stop before 7,200,000

The finite job stopped at 12:32 UTC on 12 October 2026 at its unchanged 44 GiB
sampled allocation limit. The triggering successful sample measured
47,262,625,792 bytes, above the 47,244,640,256-byte ceiling. The small overshoot
reflects sampled accounting; the limit was not adjusted during the run.

The log reports a stop before block 7,170,977 and normal cleanup to persist state.
This proposes 7,170,976 for a separate cold inspection, not accepted coverage.
The original exit-1 completion, STOP, failed replay and sealed automatic outputs
remain unchanged. No consensus mismatch was reported. All nine additional
preservation checks and protected backup/baseline/source/input checks passed.
The original backup, separate recovery, failed run and W: archive are retained.

No replay process remains. The last finalization record shows free space of
23,574,089,728 bytes Linux and 60,557,066,240 bytes D:, above the 20/50 GiB running
reserves. A new writer must pass the separate starting gate. Growth was greater
than the prior range's estimate; do not reuse that estimate as a guarantee.
Accepted history remains 6,900,000 until the stopped checkpoint verifies.
