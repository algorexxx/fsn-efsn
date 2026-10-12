# Finite continuation from 6,900,000 to 7,200,000

Resume the automatically verified 6,900,000 checkpoint for at most 300,000 new
blocks. The original backup and separate 2,400,000-v2 recovery remain protected.
Replay executable stays b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245.
All five controller files are byte-identical to the successful preceding job.
Only the observer's height literal changes; the canonical a/b diff is checked.

Declare a fresh 44 GiB sampled allocation ceiling for this job only; do not
change the preceding job's 39 GiB limit. Current closed allocation is
40,776,675,328 bytes (37.976 GiB), leaving 6.024 GiB growth. The preceding
276,704 blocks added 5.008 GiB, implying about 5.43 GiB for 300,000 at the same
rate. This estimate is not a guaranteed growth bound. The existing controller
must pass a fresh gate of Linux >27.024 GiB and D: >60 GiB, again at startup.
Keep Linux20/D50 GiB per-batch reserves, 30s allocation sampling, six-hour clean
stop, 6h15 Go / 6h30 outer timeout and 20s outer kill grace. Each allocation
worker keeps its 15s timeout plus 2s kill grace and three-attempt failure limit.
Stop and preserve evidence if a bound is reached; never adjust limits in flight.

Require private network/mount namespaces and loopback DOWN; read-only protected
views; exclusive run/actual database locks; all cold working/recovery hashes,
prior manifests, source/toolchain/executable and replay identity. Both final
cold checks and automatic evidence verification must pass before new coverage
is accepted. The qualified scanner remains sampled, non-atomic accounting;
closed allocation uses GNU du. No live database hashes or duplicate writers.

This extends the open F12/G1 historical compatibility evidence. It does not
close independent review, restored startup/recovery/handover or portable restore
acceptance. No production activation, real keys, public peers/mining, release
selection changes, additional disk expansion or cleanup. Preserve the W: archive,
baselines, failed attempts and all sealed evidence. Review capacity/value again
after completion before preparing any further range.
