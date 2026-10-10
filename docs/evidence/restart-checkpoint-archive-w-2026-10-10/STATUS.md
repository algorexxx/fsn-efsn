# Active finite archival, 10 October 2026

At 10:45:11 UTC, the worker had completed the 2,000,000 checkpoint:
1,004 files, 2,280,498,300 logical bytes, fully checked against its sealed cold
inventory and unchanged source. The 2,200,000 checkpoint is the remaining copy.
The archive worker holds both source locks and protected working/recovery locks.
No replay writer is running. This dated observation is not overall completion.

The preceding four Windows fixture removals completed and independently verified;
their evidence and prepared continuation are committed as `4001feac` on the
existing investigation branch. Peter's current message explicitly authorizes
removing unnecessary copies. The two Linux removals need no further permission,
but require completed archive and full source/archive re-verification first.

## Next scheduled continuation

1. Read `archive-completion.json`, `archive-command.json`, `archive.json`, and
   stderr/resource records. Do not run a duplicate archive or competing bulk job.
2. On exit 0, run this bundle's `verify.py archive` with the bundled Windows
   Python. It checks sealed inputs, complete records, endpoint inventory provenance
   and resources without rehashing a database. If it passes, launch
   `dispatch.py retire` hidden on the Windows host with W: access. It invokes the
   private WSL mount/network launcher and enforces the finite timeout. The worker
   rehashes both complete sources and archives before any allowlisted removal.
   Preserve any failed phase and stop dependent work if a check fails.
3. On verified retirement completion, run `verify.py retire`. Check actual absence
   of just the two source directories, presence of the W: archives, unchanged
   other root names, working/recovery preservation and actual capacity. Seal and
   commit all results and update the three canonical plan/storage/replay documents.
4. The next replay is already prepared in
   `../restart-ticket-encoder-job-6300000-2026-10-10/`. Run its
   `capacity_preflight.py` as rehearsal with a new output filename. It accepts
   the independent cold inspection at 5,331,360 and preserves the failed 5,400,000
   result. Fresh limits: target 6,300,000; 15 GiB sampled ceiling; unchanged
   6h/6h15/6h30 stop limits and 20/50 GiB Linux/D: batch reserves.
5. Only after passing capacity and idle checks, use its copied `replay_dispatch.py`
   with a fresh host output directory. It launches the root private-network
   controller, which locks databases, verifies exact cold inventories/identities,
   source/toolchain and old STOP, then replays with the retained executable.
   Capture launch/initial records, update canonical status and commit. Do not
   change already-sealed prepared inputs or old STOP/failed-run records.

The original backup, all baselines, current 5,331,360 working state, separate
2,400,000-v2 recovery, earlier stopped attempt and sealed evidence remain local.
Do not compact the VHD or remove any further sources as part of this operation.
