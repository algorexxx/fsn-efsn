# Proposed archival before the next historical replay

10 October 2026. **Removal approval pending; copy-only preparation launched.**
The standing permission for verified W: archival permits preparing the copies
without deleting their sources. The [four-root Windows copy-only job](evidence/restart-old-fixtures-copy-w-2026-10-10/STATUS.md)
started at 09:45:48 UTC. The two Linux checkpoints remain a later sequential
phase. No source deletion, compaction or replay launch has occurred. The original
storage-review record remains a dated pre-copy observation.
The [stopped checkpoint](evidence/restart-ticket-encoder-stopped-5331360-2026-10-10/RESULTS.md)
passes independent cold checks at 5,331,360. The original requested 5,400,000 job
remains incomplete. Its size stop worked as declared.

D: has approximately 58.64 GiB free, below the unchanged 60 GiB replay starting
floor. Linux has about 21.71 GiB free, leaving little room above its 20 GiB reserve
plus preparation margin. The working target is 11.016 GiB and already exceeds
the old job's 11 GiB ceiling. Do not rerun that job, lower reserves, remove STOP
or reinterpret failure as success.

The Windows copy destination is the new
`W:\FusionRestart\old-fixtures-copy-2026-10-10` archive, on
`\\192.168.1.250\mnemosyne1`. The mapping and about
3.50 TiB free were observed during this review; verify both again before use.
Do not run LevelDB directly on the network share.

## Exact proposed sources

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

## Preservation and approval boundary

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
after Peter approves this specific removal. Check the actual final filesystem
and capacity rather than assuming successful cleanup. Keep finite per-phase
limits and the existing D:/W: reserve checks; use Linux reserve checks too.

The original backup, both baseline comparators, the 2,400,000-v2 recovery
checkpoint, the current 5,331,360 working state, the earlier stopped 2,356,032
attempt, toolchain/executables and all sealed repository evidence remain local.
Existing W: archives remain untouched. Archive references are relocation records;
old evidence retains its historical paths and meaning.

Peter's heartbeat explicitly says **“do not perform destructive cleanup
automatically.”** Earlier authorization covered a different named set of ten
Windows fixtures. That is why removing these six additional local copies needs
one specific approval, despite W: archival itself already being permitted.

After approval and verified reclamation, evaluate the actual new capacity and
prepare a fresh bounded historical continuation from 5,331,360. Require the
stopped-checkpoint inspection's exact hashes/identity, preserve failure records,
and declare new finite growth/time limits before launch. The failed job and its
limits stay immutable. No production activation, real-key use or release
selection is included. Until that storage decision, leave replay stopped and
avoid repeated polling or unchanged acceptance reruns. Preparing and verifying
the W: copies is permitted; deleting any source copy is not yet approved.
