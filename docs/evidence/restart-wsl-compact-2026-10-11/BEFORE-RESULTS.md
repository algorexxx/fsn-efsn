# Before-compaction preservation passed

The isolated read-only check completed at 00:08:22 UTC on 11 October, exit zero.
All 13,794 working files and 1,383 recovery files match the sealed 6,300,000 run.
Backup/baseline metadata matches that run; full content inventories are now
recorded for the 56,107 backup files and 3,026/3,546 baseline files. Those full
inventories are the reference for post-compaction checks. No metadata-only
claim is substituted for content preservation.

Actual database and run locks, private mount/network namespaces, loopback down
and read-only bind views were verified. Source, candidate, replay/observer
executables, overlay, toolchain and both replay identities remain unchanged.
All 53 completed-replay evidence files verify. The before output manifest and
its compressed inventory counts were independently checked; stderr is empty.

Virtual geometry remains 220 GiB. Linux/D:/C: remaining bytes are respectively
30,819,483,648 / 59,259,588,608 / 13,367,791,616. No trim, compaction or replay
occurred in this check. The approved next step is the bounded unused-block trim,
then cold native compaction. Keep the verified W: rollback image throughout.
