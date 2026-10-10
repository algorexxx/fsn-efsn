# Stopped checkpoint verified at 5,600,032

The independent read-only inspection passes all five commands and its evidence
verifier. The saved endpoint is 5,600,032; the requested 6,300,000 job remains
incomplete after its declared sampled 15 GiB allocation stop. No writer resumed.

Fresh backup and cold target agree on the complete header/RLP, state and ticket
commitments, transaction/receipt roots, bloom and total difficulty. Cold ticket
count is 2,370, with 1 transaction/1 receipt. There is no final warm ticket
count from the stopped attempt.

- Block hash: `0x4fc7c1548035526ea0bb573128b79f16cdf9e0ba99a9888cecc17be619364102`
- State root: `0x457db01c6e2656fa4a16176602c2caeb0124aac217f2e20ee00b0285e3bba7c4`
- Ticket commitment: `0x3570533e4dce89d338a92a806f97b182e79449860c3b225c7bf3d0e3c21347fc`
- Total difficulty: `27949610873`

All twelve preservation checks pass. All 7,625 working-file hashes remain
unchanged during inspection, all 1,383 recovery hashes match the sealed 2,400,000-v2
checkpoint, and 1,698 prior evidence files verify. Backup/baseline metadata,
selected/candidate source, executable/toolchain, observer/input bytes and original
STOP remain unchanged. Metadata checks do not claim a fresh hash of the117GB backup.
Private network/mount namespaces, loopback DOWN, read-only views, exclusive run
locks and shared actual LevelDB locks preceded all cold hashing and inspection.

Inspection ran 2026-10-10T14:52:26.250790+00:00 to 2026-10-10T14:54:18.054439+00:00. Closed
allocation is 16,136,085,504 bytes (15.028 GiB). Free space is approximately
22.177 GiB Linux / 63.653 GiB D:.
This adds 268,672 verified candidate blocks and 2,920,032 post-legacy blocks in total.
The last fully completed requested interval remains4,500,000; baseline remains
3,600,000. F12/G1 and final restored-startup/recovery/independent review stay open.

The latest 268,672 blocks grew allocation by 4.012 GiB. This is an observation,
not a whole-history size forecast. Only about1.2GiB remains above the Linux
20GiB reserve plus1GiB preparation margin. Another tiny interval is not justified
without addressing capacity. The installed WSL exposes --manage/--resize;
its virtual disk is200GiB. A proposed expansion to220GiB would retain the existing
20/50GiB Linux/D: reserves, subject to actual post-expansion checks. It has not
been performed and needs Peter's decision. See ../../restart-storage-capacity-review.md.
The original backup, failed runs, sealed evidence and separate recovery remain.
