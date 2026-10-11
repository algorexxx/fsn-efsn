# Native compaction completed; insufficient reclaimed capacity

The one native operation completed at 00:13:19 UTC on 11 October 2026, exit zero.
Installed DiskPart help was qualified before execution. Normal Windows elevation
succeeded; no UAC bypass was used. The detached disk retained its 220 GiB virtual
geometry. The worker held the W: rollback image read-only throughout.

File length changed from 211,278,626,816 to 210,998,657,024 bytes: only
279,969,792 bytes (267 MiB) reclaimed. Native execution took 109.963 seconds.
A separate check confirmed the worker exited, the disk remained detached and
its geometry/file length matched the successful record. D: has 59,577,307,136
bytes free (about 55.49 GiB), below the next replay's strict 60 GiB starting floor.
The earlier 38.1 GiB trim report measures discarded filesystem ranges, not host
space reclaimed. No inference about why more space was not recovered is made.

The original backup, W: archive and all evidence remain retained. No repeat
compaction, zero fill, capacity shrink, new storage method or reserve reduction
is selected. Complete the prepared after-preservation check and inspect mounted
filesystem/kernel health. A successful native command alone does not establish
logical data preservation. The next replay stays blocked by host capacity.
