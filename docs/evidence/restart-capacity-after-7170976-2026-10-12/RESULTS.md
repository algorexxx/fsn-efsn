# Capacity decision after 7,170,976

The checkpoint is verified; no replay writer is running. Linux has 21.937
GiB free and D: has 57.054 GiB. Current closed working allocation is
44.033 GiB. The host metadata record also shows about 60.6 GiB on C:
and 3.31 TiB on the expected W: share; the full rehearsal VHD would not fit C:.
Only swap and Ubuntu remain under D:\FusionRehearsal. All previously identified
standalone obsolete test fixtures have already been archived and retired.
No additional disposable D: fixture was identified by this top-level inventory.
Unrelated personal/Docker/game folders were not inspected or changed.

An illustrative useful continuation to 7,500,000 (329,024 blocks) with a fresh
53 GiB sampled ceiling would leave 8.967 GiB growth. The unchanged
controller requires Linux >29.967 GiB and
D: >60.000 GiB. Both gates currently fail. capacity-review.json
records the existing helper's refusal; it is not a prepared or launched job.
The remaining 29,024 blocks to the old endpoint would not solve the capacity
problem; D: remains below the 60 GiB starting floor even for a tiny range.
No old limits, reserves, STOP, or evidence were altered.

A concrete limited continuation option is for Peter to free at least 20 GiB
more on D: and explicitly approve expanding FusionRehearsal from 230 to 250 GiB.
The previously approved 230 GiB expansion is complete; it does not authorize
250 GiB. Reuse the existing preservation/resize/verification procedure only
after approval, with fresh host capacity, cold locks and before/after identities.
This would fund further bounded work, not guarantee completion of all history.

Recent net growth was 6.057 GiB per 270,976 blocks. A linear illustration
over the remaining 7,959,104 blocks is about 178 GiB
more working storage. Growth varies with historical activity and compaction;
this is not a measured total requirement. A larger local working volume may
be a better long-term decision. Extending W: beyond its established cold-archive
role would need a separately reviewed storage plan; do not run writable LevelDB
directly on SMB or silently move the protected VHD. Repeating the earlier
267 MiB compaction gain does not resolve these gates.

Keep the original backup, independent recovery, baseline comparisons, failed
runs, sealed evidence and verified W: image. Dependent replay is held pending
the storage decision. No further unchanged small test is needed for this hold.
F12/G1 and the final acceptance gaps remain open; no trust waiver is inferred.
