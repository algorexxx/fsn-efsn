# Archive and compaction verified; replay held for host space

Completed on 11 October 2026. The stopped disk was archived to
`W:/FusionRestart/rehearsal-vhd-before-compact-2026-10-11/ext4.vhdx` and all
211,278,626,816 bytes matched both source rereads. The approved native compaction
succeeded and retained the 220 GiB virtual geometry. Before/after checks pass.
No runtime, release selection, chain data semantics or reserve limit changed.

All **77,856 protected database files** verify: 56,107 original-backup files,
3,026 and 3,546 baseline files, 13,794 working files and 1,383 recovery files.
Backup/baseline full inventories are identical across storage operations;
working/recovery hashes match the sealed 6,300,000 result. Metadata, source,
executables, toolchain and replay identities remain unchanged. Independent
verification of both output manifests and inventory contents passes.
The mounted filesystem was ext4/rw with no observed kernel storage-error
patterns. This was not an offline fsck or independent image-restore rehearsal.

The unused-block trim reported 38.1 GiB, but native compaction reclaimed only
**279,969,792 file bytes (267 MiB)**. The file grew by 32 MiB during subsequent
verification startup; final length is 211,032,211,456 bytes, a net reduction of
235 MiB from the archived source. These are measured results, not a promise
that all free ext4 space becomes reclaimable host storage.

Fresh capacity at 00:20:18 UTC:

- Working allocation: 29,064,523,776 bytes (27.068 GiB), unchanged.
- Linux available: 30,817,837,056 bytes (about 28.70 GiB).
- D: available: 59,506,003,968 bytes (about 55.42 GiB).
- Proposed next range: 6,300,000 to 6,600,000; sampled ceiling 34 GiB.
- The unchanged controller refuses D: capacity: it requires strictly more than
  64,424,509,440 bytes (60 GiB). The shortfall is about 4.58 GiB; freeing roughly
  10 GiB would provide useful starting margin. Linux passes its proposed floor.

No next job was prepared or launched. No repeated compaction, zero fill,
smaller replay solely to bypass the floor, new storage method or reserve
reduction is selected. All workers exited; the rehearsal distro is stopped
and its disk is detached. Ask Peter about freeing more D: space or revising the
storage arrangement; keep dependent replay held. Do not keep rerunning this
unchanged failing gate without evidence that capacity has changed.

Keep the W: archive: it remains a separate complete disk recovery copy of the
original backup, current checkpoint and retained evidence. No other separately
qualified complete image has been established in this storage operation.
Deleting it would save W: space but would not resolve the D: blocker. The
independent restore/portable backup package acceptance remains open under G1;
this verified copy does not silently close those requirements. All earlier
failed runs and sealed evidence remain preserved.

Relevant records: `ARCHIVE_OUTPUT_SHA256SUMS`, `BEFORE_OUTPUT_SHA256SUMS`,
`TRIM_OUTPUT_SHA256SUMS`, `NATIVE_OUTPUT_SHA256SUMS`, `AFTER_OUTPUT_SHA256SUMS` and
`RESULTS_SHA256SUMS`. Earlier preparation/status files are dated evidence,
superseded by these completed records. F12/G1 history and final selected-binary
startup/recovery/handover remain open. No production activation is authorized.
