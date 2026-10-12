# Capacity after separately verified replay through 6,600,000

**Current observation, 12 October 2026 at 00:23 UTC:** the
[verification follow-up](evidence/restart-ticket-encoder-6600000-verification-followup-2026-10-12/RESULTS.md) passes. The original replay and both cold
checks succeeded; its automatic-verifier failure concerned only patch filename
labels and remains sealed. No replay, observer or node process remains.

Fresh free capacity is 26,039,566,336 bytes (24.251 GiB) in Linux and
72,288,534,528 bytes (67.324 GiB) on D:. Closed working allocation is
34,987,921,408 bytes (32.585 GiB), up 5.517 GiB in 300,000 blocks.
The proposed next 300,000 blocks to 6,900,000 with a 39 GiB sampled ceiling
allows 6.415 GiB growth and requires Linux >27.415 GiB / D: >60 GiB.
The existing gate fails Linux. Only 3.251 GiB remains above the Linux reserve
and preparation margin; repeating tiny ranges is not justified.

## Pending capacity decision

Propose expanding only `D:/FusionRehearsal/Ubuntu/ext4.vhdx`, belonging to
FusionRehearsal, from 220 to 230 GiB virtual capacity. The earlier explicit
expansion approval covered 200 to 220 GiB; the further expansion is pending.
This grows its virtual limit, not immediately its physical allocation. Actual
host capacity must still pass the 50 GiB reserve and starting gate. No claim
that the remaining 8,530,080 historical blocks will fit follows from this step.

The reviewable proposed operation is:

1. Reuse the qualified native expansion and preservation procedure. Validate
   exact distro/disk identity, completed/follow-up evidence, current working and
   separate recovery inventories, original-backup/baseline metadata and retained
   executable/source/toolchain identities, under the existing locks/isolation.
2. Stop and detach the rehearsal disk. Only stop an idle Docker/WSL backend if
   needed and no unrelated workload is active; otherwise hold that step. Expand
   this disk alone to 230 GiB. No compaction, deletion, repartitioning or pruning.
3. Verify actual geometry/filesystem health, working/recovery file hashes and
   protected metadata/identities afterward. Retain the W: image as recovery and
   restore any deliberately stopped idle service. Record actual free capacity.
4. Before any resumed writer, explicitly qualify the separate successful
   evidence verification without overwriting the original failed completion.
   The existing controller currently refuses it. Only after this and fresh
   capacity/inventory checks pass, prepare a new finite range with unchanged
   20/50 GiB reserves and timeouts. Preserve all failed/sealed evidence.

No expansion or next replay has been launched. Do not lower reserves, repeat
compaction, delete protected data or rerun passing small tests while waiting.
The earlier W: archive/compaction is complete, with 77,856 protected files
verified. Its 267 MiB reclamation (32 MiB later reused) is not worth repeating.
Independent complete restore/portable-package acceptance remains open.

All obsolete fixture roots under D:/FusionRehearsal were already archived and
retired. Ubuntu and swap remain; the 36 MiB swap file is not a solution to this
Linux-capacity shortfall. No unrelated user folders were inspected or selected.

## Earlier completed capacity actions

Peter's freed D: space after the reboot enabled the 6,300,000 to 6,600,000 job.
Its 21:43 UTC 11 October preflight passed at about 29.51 GiB Linux / 72.26 GiB D:
free. Those starting values are historical and superseded by the review above.

The earlier choice, resolved in favor of option 2 and now completed:

1. Peter frees about 10 GiB elsewhere on D:, after which the existing controller
   can recheck capacity for the proposed bounded continuation. This avoids a
   large rehearsal-disk archive and compaction operation.
2. Archive a byte-verified copy of the stopped rehearsal virtual disk to W:,
   then attempt offline compaction of unused virtual-disk storage. This may
   reclaim host space, but the amount has not been established and success is
   not promised. This changes the disk containing the preserved backup and
   requires a separate storage decision. The previous expansion authorization
   explicitly excluded compaction; permission to retire obsolete folders does
   not by itself approve rewriting this protected disk.

### Approved offline-compaction scope (completed)

- Exact source/target: D:/FusionRehearsal/Ubuntu/ext4.vhdx. Preserve its 220 GiB
  virtual geometry; no shrinking partition/filesystem capacity, distro removal,
  reinstallation, database pruning, evidence deletion or release change.
- Require current manifests/identities, no rehearsal writer, actual run/database
  locks before shutdown and zero active container workloads. Stop only the
  rehearsal distro; if its disk stays attached, an idle Docker/WSL shutdown is
  allowed only after confirming no other active workload would be interrupted.
  Active unrelated workloads require a separate decision.
- Use a fresh cold destination
  W:/FusionRestart/rehearsal-vhd-before-compact-2026-10-11/ext4.vhdx at the verified
  W: mapping to `\\192.168.1.250\mnemosyne1`. Check exact paths/reparse points and
  at least 100 GiB of archive-volume reserve beyond the actual source size.
  Copy only while the disk is stopped and detached. Record source size, geometry
  and SHA256, flush the copy, and rehash the complete source and destination.
  Any mismatch or space failure stops the operation with both copies retained.
  The approximately 197 GiB copy and verification may take hours on the slow share.
- Only after the full cold archive verifies, qualify the installed native
  compaction command against its local help and device state. diskpart.exe is
  present; Optimize-VHD was not found in this session. A discard/trim step, if
  the native method needs it, is limited to unused filesystem blocks after the
  archive exists; then stop and detach again. Retain the command and output.
  Never use a zero-fill operation that consumes the remaining host reserve.
- Perform one native offline compaction of that exact VHD, retaining logs and
  its exit status. Do not kill a storage rewrite merely because a tool call
  yields. Failure blocks further mutation and replay; preserve the archived
  disk and the failed compacted result for diagnosis. Restoring over the original
  is a separate recovery action, not an automatic cleanup.
- Recheck actual geometry, filesystem health, full protected-backup content
  against the verified archive and the sealed working/recovery hashes, identities,
  toolchain and source. Reuse existing preservation helpers where they cover
  these checks. Do not equate unchanged metadata with full content equality.
  Keep the W: rollback copy; it is a cold archive, never a live LevelDB on SMB.
- Restart any idle service deliberately stopped, record actual D:/Linux free
  space, and rerun the existing capacity/provenance gate. Only a passing gate
  permits preparing the next finite offline replay. If compaction gains too
  little space, report that result and hold further testing rather than reduce
  reserves or run repeated tiny jobs.

The [completed operation](evidence/restart-wsl-compact-2026-10-11/RESULTS.md)
preserves the original backup, working state, recovery and evidence. Its limited
space gain does not meet the next replay gate. Retain the W: recovery image.
The next history range still has evidence value; no snapshot-trust waiver or
release acceptance follows from this capacity hold. All currently passing small
startup/refusal fixtures remain valid and do not need blanket reruns.

## Earlier completed archival and retirement

**Earlier completion, 10 October 2026:** [archival](evidence/restart-remaining-fixtures-copy-w-2026-10-10/RESULTS.md)
and [separate local retirement](evidence/restart-remaining-fixtures-retire-w-2026-10-10/RESULTS.md)
passed. The exact 14 D: roots are absent, all 9,191 files remain on W:, other root
names are unchanged and protected-VHD metadata stayed unchanged during both
operations. D: gained **12.715 GiB**, leaving **62.100 GiB free** at completion.
That immediate capacity blocker was resolved for the v3 run. The [bounded cold inspection](evidence/restart-ticket-encoder-stopped-reserve-2026-10-10/spec.md)
passed at 5,976,864, with 21.269 GiB closed working allocation and 62.100 GiB
still free on D:. The fresh 6,300,000-v3 continuation uses a 28 GiB ceiling
(6.731 GiB remaining growth). Its required starting floors were Linux >27.731 GiB
and D: >60 GiB. Fresh preflight passed at 18:40:20 UTC with about 34.548/62.725 GiB
free; the dispatcher launched at 18:41:04 UTC and replay began at 18:45:49 UTC
after passing startup checks. The job subsequently completed at 21:24:13 UTC;
the next capacity decision is now recorded above.

**Earlier reserve-stop observation, 10 October 2026, after 17:45 UTC:** the
[6,300,000-v2 replay](evidence/restart-ticket-encoder-job-6300000-v2-2026-10-10/RESULTS.md)
stopped at the unchanged 50 GiB D: reserve. D: now has 53,026,660,352 bytes
(49.385 GiB) free; Linux's final record has 37,115,981,824 bytes (34.567 GiB).
The expansion succeeded, but expanding virtual capacity again would not supply
host space. Cold inspection requires more than 51 GiB on D:; a resumed writer
requires more than max(60 GiB, 51 GiB plus remaining allowed growth).

The last live working allocation was 21.235 GiB. Since launch it increased by
about 6.207 GiB, while host free space decreased by about 14.255 GiB. The current
VHD file length is 205,171,720,192 bytes. Dynamic VHD allocation, compaction churn
and other host use can differ from the measured live database size; the records
do not attribute the whole host-space decrease to the working database. No
reliable full-history storage forecast follows from these observations.

## Completed archival and reclaim scope

The [read-only inventory](evidence/restart-ticket-encoder-job-6300000-v2-2026-10-10/capacity-review.json)
identified these exact folders formerly under `D:\FusionRehearsal`, totaling **9,191 files /
13,630,973,746 logical bytes (12.695 GiB)**. These are old fixtures, including
failed attempts whose contents must remain preserved. Evidence mappings are
recorded. Both complete copies passed byte verification during archival and
again before retirement. No root or descendant reparse entries were observed. W: has about
3.49 TiB free at the expected share.

| Folder under D:\FusionRehearsal | Logical bytes |
| --- | ---: |
| delivered-partition-2026-09-27 | 1,182,070,861 |
| delivered-partition-2026-09-27-attempt-02 | 1,181,917,028 |
| delivered-partition-2026-09-27-attempt-03 | 1,182,960,561 |
| delivered-partition-2026-09-27-attempt-04 | 1,186,616,109 |
| injected-manual-delivery-2026-09-27 | 1,186,537,103 |
| live-funded-partition-2026-09-27-admission | 607,706,428 |
| manual-purchase-live-2026-09-27 | 1,184,067,299 |
| manual-purchase-live-2026-09-27-attempt-02 | 1,184,042,076 |
| manual-purchase-protocol-2026-09-27 | 593,796,391 |
| manual-purchase-protocol-2026-09-27-attempt-02 | 593,848,584 |
| peer-purchase-retry-2026-09-27 | 574,038,931 |
| retry-partition-2026-09-27 | 1,181,907,368 |
| retry-partition-2026-09-27-attempt-02 | 1,183,508,673 |
| retry-partition-2026-09-27-displaced | 607,956,334 |

Verified archive destination: `W:\FusionRestart\remaining-fixtures-copy-2026-10-10`.
Require a fresh destination, bounded copy operation, stopped rehearsal services,
actual database locks, exact path/reparse checks, source and destination SHA256
verification, preserved evidence manifests and a separate final re-verification
before any D: removal. Keep the backup, VHD, swap, current replay, separate
recovery and all other paths. W: is cold storage, not a live LevelDB location.

**Completed under explicit authorization.** Peter said: "Archive whatever folders
you think is necessary. If they arent needed for future testing you can outright
remove them." The copy completed at 18:26:32 UTC and the separately verified
retirement at 18:31:52 UTC. Preserve the W: archive and all evidence. No additional
cleanup is currently needed for the prepared continuation; re-evaluate actual
capacity at its fresh preflight and completion. Do not ask for the same cleanup permission again.

The earlier copy helper required 50 GiB on D: despite only reading there. This
explicit replacement reads D: and writes only to C:/W:, reserving 5/100 GiB on
those output volumes. It requires the rehearsal distro stopped and records
unchanged protected-VHD metadata. It leaves the original 20/50 GiB replay
reserves and cold-inspection starting floors intact. Both operations are complete; their stopped-distro requirement has been
satisfied. Database work now follows its own unchanged isolation/capacity gates.

The measured 12.715 GiB gain differs from 12.695 GiB of logical file sizes because
filesystem allocation differs. Cold inspection has passed; declare
another replay only after fresh capacity passes for its documented finite bounds.
This does not establish a full-history size requirement or guarantee the next
requested endpoint will fit. Keep the finite stops and separate recovery copy.

## Earlier approved expansion and launch

10 October 2026. **Expansion to 220 GiB and preservation checks passed.** Peter
approved the proposal: "question somehow went away bet yes, feel free to expand it".
The [execution evidence](evidence/restart-wsl-expand-220gib-2026-10-10/RESULTS.md)
records the native operation, first refusal, actual geometry and protected-data
checks. No release selection or node runtime changed.

The replay is cold-verified through **5,600,032**. Its preceding requested
6,300,000 attempt remains incomplete after reaching its declared sampled 15 GiB
ceiling. Preserve that attempt's original STOP, limits, logs and manifests.
The [fresh continuation](evidence/restart-ticket-encoder-job-6300000-v2-2026-10-10/README.md)
uses a new job directory and the verified stopped-checkpoint provenance.

## Why expansion was useful

The [six obsolete test copies](restart-storage-next-step.md) were already
archived, fully verified and retired under Peter's authorization, reclaiming
4.391 GiB on D: and 4.544 GiB inside Linux. That cleanup is complete.

The latest 268,672 replayed blocks added 4.012 GiB of working allocation. Before
expansion, Linux had only 22.177 GiB free inside its 200 GiB virtual disk, leaving
about 1.177 GiB above its 20 GiB reserve plus 1 GiB preparation margin. Another
tiny range would have been poor value. D: still had about 63.65 GiB free.

| Item | After expansion / fresh preflight |
| --- | ---: |
| FusionRehearsal virtual disk | 220 GiB (236,223,201,280 bytes) |
| Linux filesystem total | 231,379,542,016 bytes |
| Linux available space at preflight | 43,870,941,184 bytes (40.858 GiB) |
| D: available space | 68,333,772,800 bytes (63.641 GiB) |
| Current working allocation | 16,136,085,504 bytes (15.028 GiB) |
| Per-batch Linux / D: reserves | 20 / 50 GiB, unchanged |
| Preparation margin | 1 GiB, unchanged |

The dynamic VHDX remains at `D:\FusionRehearsal\Ubuntu\ext4.vhdx`. Expanding its
virtual capacity does not reserve host space or prove that all history through
15,130,080 will fit. D:'s reserve continues to constrain actual growth.

## Operation and preservation

The initial distro-only termination left the disk attached. Native resize
refused with `WSL_E_DISTRO_NOT_STOPPED` before mutation; the failure is preserved.
A fresh check found zero running Docker containers and no running distributions
outside FusionRehearsal/docker-desktop. The idle Docker backend was briefly
stopped, WSL shut down, only FusionRehearsal's disk expanded with the exact byte
size, and Docker restarted. Its final status is running, still with zero running
containers. This was the necessary operational adjustment to the initial
proposal's distro-only stop. No container workload was interrupted.

Post-expansion checks verified all 7,625 working and 1,383 recovery-file hashes
against sealed inventories, plus unchanged original-backup/baseline metadata,
replay identity, source, executable, toolchain and STOP. Checks used private
mount/network namespaces, loopback DOWN, actual database/run locks and read-only
views. Metadata verification is not a fresh full hash of the 117 GB backup.
No cleanup, VHD compaction, data relocation or reserve reduction occurred.

## Earlier finite replay after expansion

The fresh 6,300,000-v2 job was dispatched at 15:14:00 UTC from commit `40551639`.
It starts at 5,600,032: up to 699,968 additional blocks.
Its preflight passed at 15:10:44 UTC with no active node/replay process and valid
stopped-checkpoint provenance. A 26 GiB sampled ceiling permits about 10.972 GiB
remaining allocation growth. The actual required starting floors are
34,329,780,224 bytes Linux (31.972 GiB) and 66,542,034,944 bytes D: (61.972 GiB).
The earlier proposal's 62.972 GiB D: illustration was an arithmetic error; the
unchanged controller correctly applies 51 GiB plus remaining growth.

Keep the retained executable, private offline isolation, separate 2,400,000-v2
recovery and original failed records. Keep the six-hour clean stop, 6h15 Go
and 6h30 outer deadline plus 20-second grace, with 30-second size samples and
per-batch 20/50 GiB reserve checks. Preparation/capacity are not launch or verified
completion. Inspect the job's launch, completion and verification records before
any dependent action; no duplicate writer or hashing of a live LevelDB.

The expansion approval itself did not authorize further cleanup. Peter later
explicitly authorized obsolete-folder archival/removal; the 14-folder operation
summarized above completed under that authorization. No further disk expansion
has been performed. W: remains available for verified cold archival; do not run
live LevelDB on SMB.
The separate complete-backup package remains a G1 preservation gap. Review
capacity and evidence value again on verified completion or a finite stop.
G1/F12 and final selected-binary startup/recovery/handover acceptance remain open.
