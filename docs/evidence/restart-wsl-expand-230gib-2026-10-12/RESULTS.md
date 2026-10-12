# Approved expansion to 230 GiB completed

Peter explicitly approved the 220 to 230 GiB expansion and continued testing.
Native WSL resize succeeded at 05:39:43 UTC on 12 October 2026. The exact
FusionRehearsal registration points to `D:/FusionRehearsal/Ubuntu`; observed
root-device geometry changed from 236,223,201,280 to 246,960,619,520 bytes.
The Docker/WSL fallback was not used; no unrelated service was stopped.

Both bounded preservation checks pass under locks, private mount/network
namespaces and read-only database views. All 16,672 closed working files and
1,383 separate recovery files match their previous hashes before and after.
Replay identity, source, executable and toolchain are unchanged. Original backup
and two baseline metadata inventories match; this is not a new full backup
content hash or independent restore test. The original 6,600,000 failed verifier
and separate successful review retain their sealed evidence (62 files verified).

At 2026-10-12T05:41:19.901342+00:00, Linux has 36,077,268,992
bytes free (33.600 GiB); D: has
73,240,641,536 (68.211 GiB).
The filesystem is ext4 mounted read/write; recorded kernel storage-error
patterns are absent. This health check is not an offline fsck. The verified
W: recovery image, original backup, separate recovery and failed runs remain.
No compaction, deletion, history rerun, mining or release-selection change.

These figures permit a fresh capacity preflight for the proposed 300,000-block
range to 6,900,000, not a guarantee that the remaining history fits.
