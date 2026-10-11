# Cold archive verified; compaction pending

The cold copy finished at 23:26:58 UTC on 10 October 2026. Dispatcher exit is
zero, stderr is empty and no failure record exists. The worker held the source
read lock throughout copying, source re-verification and archive re-verification.
All 211,278,626,816 bytes (196.769 GiB) match on all three SHA256 observations:

`69f181ab44da0f279267524a487cd2f29675165cacb2fcb6cd927aef1ff1f6eb`

The final archive is
`W:/FusionRestart/rehearsal-vhd-before-compact-2026-10-11/ext4.vhdx`.
Source length, modification time and attributes stayed unchanged. Virtual
geometry remains 220 GiB. No source removal or compaction occurred.

Independent record and filesystem verification at 00:02:29 UTC on 11 October
confirmed both archive workers exited, no running distro, the source detached,
matching current source inventory, final archive length, W: mapping, no path
reparse point and an identical archive receipt on W:. Eighteen input/launch/
preparation evidence files verify. This did not repeat the complete image hash.
The worker's final progress record still says `Completed: false`; the successful
archive and dispatcher completion records supersede that intermediate status.

Capacity at verification: C: 13,390,344,192 bytes, D: 59,297,337,344 bytes and
W: 3,644,340,404,224 bytes free. Archival itself does not reclaim D: space.
The archive is required rollback protection through the next storage steps.

Next: run the prepared read-only before checks, preserve their full backup/
baseline inventories and compare working/recovery/source identities. Only a
passing result permits the authorized native compaction. Then repeat logical
preservation and storage health/geometry checks and review actual capacity.
No new replay or release selection is authorized by this storage result.
