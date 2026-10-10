# Expansion and preservation checks passed

Peter approved the 200 to 220 GiB expansion on 10 October 2026. Native WSL
completed the exact 236,223,201,280-byte expansion at 15:08:55 UTC. The actual
Linux block device now reports that size; the filesystem reports 231,379,542,016
usable total bytes. Linux available space is 43,879,849,984 bytes (40.866 GiB),
with 68,333,772,800 bytes (63.641 GiB) free on D: at the post-expansion check.

The first distro-only attempt refused with `WSL_E_DISTRO_NOT_STOPPED` before
resizing. Its logs remain intact. The VHD was still attached while Docker's
backend was running. Fresh `docker ps --quiet` returned zero running containers,
and the running-distro allowlist contained only FusionRehearsal/docker-desktop.
The subsequent supported operation stopped the idle Docker backend, shut down
WSL, expanded only FusionRehearsal's disk and restarted Docker. Docker's final
status is checked separately; no running container workload was interrupted.
This operational adjustment was necessary to finish the approved expansion.

Read-only preservation checks passed before and after. The post-expansion check
ran 15:09:20 to 15:10:01 UTC, with private mount/network namespaces, loopback DOWN,
read-only bind views and actual database/run locks. All 7,625 working-checkpoint
and 1,383 recovery-file hashes match the sealed inventories. Backup metadata
(56,107 files / 117,170,022,674 bytes), baseline metadata, replay identities,
selected/candidate source, executable, toolchain and original STOP all match.
All 83 files in the immediate inspection/attempt manifests verified. The original
117 GB backup was checked by metadata; no fresh full-backup hash is claimed.

The original backup, separate 2,400,000-v2 recovery, failed runs, working state and
sealed evidence remain preserved. No cleanup, VHD compaction or runtime/release
change occurred. Free-space reserves remain Linux20/D50 GiB. Expanding the
virtual limit does not reserve host D: space or prove all history will fit.

The fresh 6,300,000-v2 replay preflight subsequently passed at 15:10:44 UTC with
the independently verified 5,600,032 checkpoint and a new finite 26 GiB sampled
ceiling. The older job's 15 GiB limit and STOP remain immutable. Preparation and
capacity are not replay completion; consult that job's launch/completion records.
