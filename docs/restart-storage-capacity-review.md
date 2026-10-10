# Capacity decision after the 5,600,032 checkpoint

10 October 2026. **Awaiting Peter's decision. No resize or new replay has started.**

The [6,300,000 attempt](evidence/restart-ticket-encoder-job-6300000-2026-10-10/RESULTS.md)
stopped at its declared sampled 15 GiB allocation ceiling. The separate
[cold inspection](evidence/restart-ticket-encoder-stopped-5600032-2026-10-10/RESULTS.md)
verifies the saved checkpoint at **5,600,032**. All five inspection commands,
twelve preservation checks and evidence verification pass. The requested range
remains incomplete; its completion record, STOP, logs and limits stay immutable.

The [six obsolete test copies](restart-storage-next-step.md) have already been
archived, fully verified and retired under Peter's authorization. That reclaimed
4.391 GiB on D: and 4.544 GiB inside Linux. Do not repeat that cleanup.

## Measured constraint and proposed change

The [geometry observation](evidence/restart-ticket-encoder-stopped-5600032-2026-10-10/storage-geometry.json)
and [capacity review](evidence/restart-ticket-encoder-stopped-5600032-2026-10-10/storage-review.json)
record these values; they are observations, not reservations:

| Item | Observed value |
| --- | ---: |
| FusionRehearsal virtual disk capacity | 200 GiB (214,748,364,800 bytes) |
| Linux available space after cold inspection | 22.177 GiB |
| D: available space | 63.653 GiB |
| Working replay allocation | 15.028 GiB |
| Growth across the latest 268,672 blocks | 4.012 GiB |
| Existing per-batch Linux / D: reserves | 20 / 50 GiB |
| Existing preparation margin | 1 GiB |

Only about 1.177 GiB of Linux growth fits above the reserve and preparation
margin. Another tiny continuation would provide little progress before another
capacity stop. The virtual disk limit is currently tighter than host D: capacity.

**Proposal:** expand only FusionRehearsal's virtual disk from **200 to 220 GiB**
(236,223,201,280 bytes), keeping all existing reserve checks. Its backing file is
`D:\FusionRehearsal\Ubuntu\ext4.vhdx`. This is a capacity change to the shared
rehearsal disk containing the preserved data, beyond the completed removal of
obsolete test copies; obtain Peter's decision before performing it.

The dynamically allocated VHDX's recorded host file length is 194,186,838,016
bytes, distinct from its virtual capacity. A larger virtual capacity does not
reserve host space. D:'s 50 GiB reserve will still limit actual future growth.
Recheck both filesystems before declaring another finite job. This proposal
does not establish that all remaining history through 15,130,080 will fit.

## Execution boundary if approved

1. Recheck that the replay, observers, archival and retirement jobs have ended.
   Verify sealed checkpoint/evidence identities and hold the existing run/database
   locks for any cold inventory checks. Preserve the original backup, failed runs,
   current working checkpoint, separate 2,400,000-v2 recovery and baseline data.
2. Capture current disk geometry, D: capacity and the exact distro/VHDX mapping.
   The installed `wsl.exe --help` exposes `--manage <Distro> --resize <MemoryString>`.
   Use that distro-specific supported operation, with an exact 220 GiB target;
   verify the accepted size syntax before mutation. The intended command family
   is `wsl.exe --manage FusionRehearsal --resize ...`.
3. Stop only the idle FusionRehearsal distro as required by that operation.
   Do not globally shut down WSL, stop Docker, compact or move the VHDX, reduce
   filesystem reserves or introduce network access. If the supported operation
   requires disrupting another distro/service, stop and ask before that change.
4. Record the command, exit status and actual post-operation block-device and
   filesystem sizes. Require the intended 236,223,201,280-byte virtual capacity
   and a usable filesystem; verify the preserved checkpoint identities before
   any writer resumes. A failed resize is not permission to repair destructively.
5. Prepare a **fresh** bounded continuation from 5,600,032, using the verified
   stopped-checkpoint inspection and retaining the failed 6,300,000 attempt as
   its provenance. Re-evaluate capacity and evidence value. Preserve the retained
   executable, offline isolation, separate recovery, finite timeout and
   per-batch 20/50 GiB reserve checks. Do not edit or reuse the old STOP/limits.

A possible next envelope is a 26 GiB sampled target ceiling and the same
6,300,000 endpoint: about 10.972 GiB of remaining allocation growth from the
current checkpoint. This is only a sizing illustration, not a prepared or
authorized job. It would require Linux free above 31.972 GiB and D: free above
62.972 GiB under the existing starting rules. Select the actual finite bounds
only after the approved resize and fresh capacity measurements. Keep the
six-hour clean stop and existing outer deadlines unless separately justified.

W: remains suitable for verified cold archives. Do not run live LevelDB on SMB
or relocate the original backup/baselines as an automatic alternative. No further
cleanup is proposed here. The missing separate complete-backup package remains
an open G1 preservation issue; checkpoint archives do not replace that package.

## While the decision is pending

Keep replay stopped. Do not retry the failed job, lower reserves, launch another
tiny range, resize the disk, or repeat unchanged passing acceptance tests. The
heartbeat should stay quiet while this decision remains unanswered; elapsed time
is not approval. If Peter declines expansion, review storage placement or the
historical acceptance basis with him before dependent work. G1/F12 and the final
selected-binary startup/recovery/handover review remain open.
