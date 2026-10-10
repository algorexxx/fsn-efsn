# Authorized rehearsal-disk archival and compaction

Peter approved on 11 October 2026 (Europe/Stockholm):
"Archive to W and compact. If the backup is needed, otherwise delete."
This supersedes the pending storage question. No further permission is needed
for this reviewed operation. Preserve the original node backup and the working/
recovery evidence. The disk archive is needed as rollback until full post-storage
qualification succeeds; assess its future recovery value before deleting it.

The latest completed replay is verified through 6,300,000, manifest SHA256
e99e6f4b516e9119f9ffc18a5ac1519ab613e96203ba395c971fba5f8ed83845.
Working allocation is 27.068 GiB; further replay awaits the host capacity gate.
The next tentative range remains 6,300,000–6,600,000 with a 34 GiB ceiling and
unchanged finite time/reserve rules. It has not been prepared or launched.

## Phase 1 — cold rollback archive

Source D:/FusionRehearsal/Ubuntu/ext4.vhdx is already stopped/detached, with
211,278,626,816 file bytes and 236,223,201,280 virtual bytes (220 GiB). Docker
was also already stopped; do not start it merely for this operation. Native
Get-DiskImage confirmed detached state and geometry. Both source and archive
must remain outside reparse paths. Windows source FileShare.Read prevents any
writer or deletion while copying and verifying. Do not start FusionRehearsal,
hash a live LevelDB or run another storage workload during this phase.

Destination W:/FusionRestart/rehearsal-vhd-before-compact-2026-10-11/ext4.vhdx
is on the existing mapped share. Require a fresh destination and at least the
source size plus 100 GiB free on W:; retain C: 5 GiB and W: 100 GiB reserves.
The copy reads D: but does not change it. A 10-hour monotonic deadline plus
10-minute outer grace bounds copy/verification, with progress at most once per
minute. Preserve an incomplete copy on failure; never silently retry/overwrite.

archive.ps1 adapts the existing cold-fixture copy helper's guards, path checks,
flush, read locks and record conventions. SHA256 of the locked source is
computed during the copy, then the full source and full flushed destination are
independently reread and compared. This avoids an extra source-only hash pass
while proving complete copy equality. Only verified bytes are renamed from
ext4.vhdx.incomplete to ext4.vhdx using exact validated PowerShell paths.
Source length/mtime/attributes and detached state must remain unchanged.

Since the disk is already cold, archive it before booting it for filesystem
inventory checks. This preserves the current image immediately. The subsequent
read-only pre-compaction checks still occur before any trim/compaction mutation.
The dispatcher does not compact, trim, delete data or automatically continue.

## Phase 2 — verify, compact and qualify

Only after completed archive and whole-image equality are verified: establish
private mount/network namespaces, loopback DOWN, actual database/run locks and
read-only protected views. Reuse the previous disk-preservation helper, adapted
to the 6,300,000 checkpoint, and add full protected-backup/baseline content hashes
before and after compaction. Compare working/recovery hashes and all source,
executable/toolchain/identity evidence with the sealed completed job.

Then stop/detach the rehearsal disk. Native diskpart is present; the current
Windows token is not administrator. Qualify the installed native command/help;
request Windows elevation only if required. Keep all native command/output
records. Any trim is limited to unused filesystem blocks after the verified
archive exists; no zero fill, capacity shrink or database pruning. Do not kill
a native rewrite merely because a tool call yields. Check exit status and actual
disk/file capacity, then repeat the full protected-data preservation checks.
The virtual size stays 220 GiB. Keep failed states and rollback archive on error.

The archive image and byte equality preserve the original cold source; full
logical file inventories taken before mutation provide the reference for
post-compaction comparison without requiring a live database on W:. Restore
only deliberately stopped services; Docker was already stopped at preparation.
Do not infer success or reclaimable space from preparation. After qualification,
record capacity and run the unchanged replay gate before preparing another job.
