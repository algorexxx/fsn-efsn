# Authorized archival before the next historical replay

10 October 2026. **All six authorized obsolete-copy retirements passed.**
The subsequent replay stopped at its declared allocation ceiling and its saved
state is [verified at 5,600,032](evidence/restart-ticket-encoder-stopped-5600032-2026-10-10/RESULTS.md).
Peter approved the subsequent [200 to 220 GiB expansion](restart-storage-capacity-review.md).
It is complete with passing preservation checks and unchanged reserves. A fresh
finite continuation was dispatched at 15:14:00 UTC after passing capacity; no
more cleanup is needed.
His message was: "If there is something not needed any more you can delete it."
The [four-root copy](evidence/restart-old-fixtures-copy-w-2026-10-10/RESULTS.md)
completed at 09:52:08 UTC. The [separate retirement](evidence/restart-old-fixtures-retire-w-2026-10-10/RESULTS.md)
reverified every source/archive file and removed only those four D: roots at
10:37:32 UTC. All other root names remain present. D: free increased by
4,714,328,064 bytes to 68,385,763,328 bytes (63.689 GiB).
The [two-checkpoint archive](evidence/restart-checkpoint-archive-w-2026-10-10/spec.md)
completed at 10:52:40 UTC, after Windows verification: 2,161 files /
4,874,392,642 logical bytes. Its full byte checks and independent provenance
verification pass; see [archive results](evidence/restart-checkpoint-archive-w-2026-10-10/ARCHIVE-RESULTS.md).
The separate [authorized retirement](evidence/restart-checkpoint-archive-w-2026-10-10/RESULTS.md)
completed at 11:52:51 UTC after rechecking both complete copies, reclaiming
4,878,532,608 bytes (4.544 GiB) inside Linux. Independent record verification and
an actual-filesystem check confirm the intended source directories absent and
archives/retained database directories present. No compaction occurred.
The prepared continuation's fresh capacity preflight passes at 12:49:43 UTC,
with about 26.26 GiB Linux / 63.68 GiB D: free. The prepared offline continuation
was dispatched at 12:50:50 UTC and began replay at 12:53:26 UTC after passing
inventory/identity checks. Earlier storage records remain
dated observations, not current capacity claims.
The [stopped checkpoint](evidence/restart-ticket-encoder-stopped-5331360-2026-10-10/RESULTS.md)
passed independent cold checks at 5,331,360. The original requested 5,400,000 job
remains incomplete. Its size stop worked as declared.

D: was at approximately 58.64 GiB free during that earlier stopped-state inspection,
below the unchanged 60 GiB replay starting floor. Linux then had about 21.71 GiB free, leaving little room above its 20 GiB reserve
plus preparation margin. The working target then occupied 11.016 GiB and exceeded
the old job's 11 GiB ceiling. Do not rerun that job, lower reserves, remove STOP
or reinterpret failure as success.

The Windows copy destination is the new
`W:\FusionRestart\old-fixtures-copy-2026-10-10` archive, on
`\\192.168.1.250\mnemosyne1`. The mapping and about
3.50 TiB free were observed during this review; verify both again before use.
Do not run LevelDB directly on the network share.

## Exact authorized sources

| Source | Measured bytes | Effect of retiring the verified local copy |
| --- | ---: | --- |
| `D:\FusionRehearsal\abandonment-reorg-2026-09-27` | 1,185,671,227 logical; 1,149 files | Host D: space |
| `D:\FusionRehearsal\equal-weight-2026-09-27` | 1,182,987,280 logical; 740 files | Host D: space |
| `D:\FusionRehearsal\stale-intent-2026-09-27` | 1,183,572,109 logical; 815 files | Host D: space |
| `D:\FusionRehearsal\live-abandonment-repair-2026-09-27` | 1,185,425,749 logical; 1,001 files | Host D: space |
| `/home/rehearsal/replay/candidate-ticket-encoding-2000000` in FusionRehearsal | 2,282,467,328 allocated | Linux filesystem space |
| `/home/rehearsal/replay/candidate-ticket-encoding-2200000` in FusionRehearsal | 2,596,163,584 allocated | Linux filesystem space |

The four Windows roots total 4,737,656,365 logical bytes (4.412 GiB). The two
Linux roots total 4,878,630,912 allocated bytes (4.544 GiB). These are sizing
observations, not guaranteed free-space gains or archive hashes. Removing Linux
files does not promise a smaller VHDX or more host D: space. No VHD compaction
is proposed. Exact inventories and archive requirements must be captured cold.

## Preservation boundary

Reuse the established verified-copy-then-retire procedures, with these exact
six source roots as the entire allowlist. Preserve every diagnostic and failed
fixture file within each root, not merely its database. Keep source and archive
phases separate; refuse existing archive destinations and unexpected paths,
symlinks/reparse points, changed files or competing writers.

Before retirement, hold the applicable database/run locks, prove the sources
are idle, verify their sealed evidence and full cold inventories, and copy to W:.
Flush/read back and fully hash the archive; compare it with the unchanged source
again. Save checksummed relocation records and an exact restore map. Stop on any
failure without removing source bytes. Retire only verified allowlisted copies
under Peter's current removal authorization. Check the actual final filesystem
and capacity rather than assuming successful cleanup. Keep finite per-phase
limits and the existing D:/W: reserve checks; use Linux reserve checks too.

The original backup, both baseline comparators, the 2,400,000-v2 recovery
checkpoint, the current 5,600,032 working state, the earlier stopped 2,356,032
attempt, toolchain/executables and all sealed repository evidence remain local.
Existing W: archives remain untouched. Archive references are relocation records;
old evidence retains its historical paths and meaning.

Peter's later explicit message authorizes removing unnecessary test copies.
Apply that permission to these six already-reviewed sources, after verified W:
archival. It does not justify deleting backup, evidence or recovery data.

After verified reclamation, the fresh capacity and exact cold inventory/identity
checks passed. The [continuation toward 6,300,000](evidence/restart-ticket-encoder-job-6300000-2026-10-10/RESULTS.md)
ran with a fresh 15 GiB sampled ceiling and unchanged time/reserve limits. It
stopped at that ceiling and its saved state is independently verified at 5,600,032.
Closed allocation is now 15.028 GiB; free capacity is 22.177 GiB Linux / 63.653 GiB
D:. Both failed jobs and their original STOP/limits remain immutable.

No further archival/removal is proposed. The approved disk expansion now provides
about 40.87 GiB Linux / 63.64 GiB D: free. The fresh 6,300,000-v2 job's capacity
preflight passes with a 26 GiB sampled ceiling. Existing reserves/time limits
remain unchanged. No production activation, real-key use or release selection is
included. Do not repeat unchanged acceptance checks.
