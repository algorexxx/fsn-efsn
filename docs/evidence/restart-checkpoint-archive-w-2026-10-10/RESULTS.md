# Completed verified checkpoint retirement

Both finite phases passed. The archive completed at 10:52:40 UTC on 10 October
2026. Retirement completed at 11:52:51 UTC in the Linux worker (host process exit0).
Their independent record/provenance verifiers pass. Full source/archive bytes
were rechecked before removing only the 2,000,000 and 2,200,000 local checkpoints.
The archives contain 2,161 files / 4,874,392,642 logical bytes and match the
original sealed cold inventories. archive.json is the complete restore map,
including original file metadata and SHA256 values.

Linux free space increased by 4,878,532,608 bytes (4.543 GiB), to
28,200,284,160 bytes. Host D: free did not change
during retirement: 68,354,744,320 bytes. No VHD compaction ran.
The filesystem check at 2026-10-10T12:48:54.670592+00:00 independently confirms both
source directories absent, both W: archive directories present, identical
archive/retirement records in W: and the repo, retained backup/working/recovery
database directories and no active node/replay process. See its captured root
inventory and fresh free-space measurements.

Working/recovery metadata and every other replay root name remained unchanged
under locks during each phase. Exact working/recovery content and original
backup/baseline preservation are checked again by the prepared replay before
its writer starts. This post-removal check did not hash any live LevelDB.

The current 5,331,360 working state, separate 2,400,000-v2 recovery, earlier
stopped 2,356,032 attempt, baselines, original backup and all sealed evidence
remain. Only the six specifically documented obsolete local copies were retired
across the Windows and Linux operations. Older status/preparation records remain
immutable and are superseded by completion, verification and this result.
The next step is fresh capacity/preflight and the prepared bounded continuation
toward 6,300,000. No efsn runtime or release selection changed.
