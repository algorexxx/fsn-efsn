# Capacity after the approved WSL expansion

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

## Authorized next finite replay

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

No further cleanup or disk expansion is authorized by this completed operation.
W: remains available for verified cold archival; do not run live LevelDB on SMB.
The separate complete-backup package remains a G1 preservation gap. Review
capacity and evidence value again on verified completion or a finite stop.
G1/F12 and final selected-binary startup/recovery/handover acceptance remain open.
