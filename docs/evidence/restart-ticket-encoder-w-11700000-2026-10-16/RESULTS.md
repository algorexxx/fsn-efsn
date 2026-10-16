# W-backed replay verified through 11,700,000

The 300,000-block continuation completed on 16 October 2026 UTC. Inner evidence
verification passed at 14:45:21 UTC; image unmount, read-only filesystem check,
detach and host exit passed by 14:46:10 UTC. The subsequent review verifies all
five prepared/startup/input/output/automatic manifests. The actual-state check
at 15:29:35 UTC finds no test process, loop attachment, matching image mount or
target directory. Original automatic seals remain unchanged; REPORT_SHA256SUMS
covers this review and the late outer records.

All seven commands and ten preservation checks pass. Both cold observers match
the complete backup endpoint at block 11,700,000, hash
`0x639809ae1f22f8bf29ad4b338da1cd8132b54b2dac0bbb508b1c88993103d5bf`:
state root, ticket commitment, transaction/receipt roots, header/RLP, bloom and
TD, with 4,581 tickets and one transaction/receipt. Warm/cold ticket counts
agree. The closed target has 51,371 hashed files; all 49,313 starting file hashes
were checked before replay. Separate recovery retains 1,383 matching hashes.
Backup/baselines and local 7,170,976 fallback metadata remain unchanged, as do
executable/source/toolchain identities. All 3,121 prior evidence files verify.

Startup allocation matched the preceding closed measurement. This review also
compares the saved starting and prior closed file-hash maps, which match exactly.
Earlier allocation differences and the failed supplemental assertion remain
preserved in their original bundles; their cause remains unestablished.
Allocation equality does not replace the unchanged content-verification gate.

The [first preflight refusal](preflight-refusal-1/FAILURE.md) remains sealed and
is included in the 74-file automatic manifest. It caught changed observer line
endings before any image attachment or writer. Byte-preserving correction and
repeated preflight passed before the single actual dispatch. No controller gate
or finite limit changed. The earlier WSL monitoring interruption and recovered
access remain in their original sealed bundle; no forced restart was performed.

Replay took 189.514 minutes by wall timestamps and 184.380 by its recorded
monotonic timer. The 5.134-minute difference is preserved; its cause was not
established by this review. Whole host execution took 373.136 wall-clock minutes,
including 183.622 minutes outside replay. Cross-environment timestamps are
recorded as observed; no timestamp adjustment is used to claim a faster result.
These observations are not a full-history ETA. Closed allocation is 99.830 GiB
(107,191,193,600 bytes), up 4.461 GiB from actual startup allocation.
Every sampled reserve passed and no monitor retry was needed. Backing-share
changes do not isolate this job from sparse-image extent retention or unrelated
share usage; both backing and image reserves remain independently checked.

Candidate execution covers 9,020,000 blocks beyond the legacy boundary;
3,430,080 remain to backup tip 15,130,080. F12/G1, final selected-candidate
startup/recovery/handover, independent restore/portable-package acceptance and
consensus review remain open. This does not establish outage durability or
change production release selection. Prior failed/refused jobs remain preserved.

The next justified range is 11,700,000-12,000,000. Keep 300,000 blocks: this run
used about 3h10m for replay and 3h04m for preparation/verification/cleanup,
leaving about 107 minutes under the eight-hour whole-job cap. The preceding
range left about 81 minutes, and earlier same-size replays reached four replay
hours. Do not increase the range or any time limit. A fresh 112 GiB sampled
ceiling leaves 12.170 GiB growth headroom, over twice the largest net growth
among these recent ranges (5.511 GiB). This adds new historical evidence while
amortizing the costly closed checks. Neither timing nor growth is guaranteed.
Keep six-hour clean replay, 6h15m Go, 6h30m replay outer, 30-second resource
samples and unchanged running reserves. Fresh local free space is 22.217 GiB
Linux / 53.603 GiB D:; the last W: observation is about 3.01 TiB. Revalidate
host/mounted capacity, exact image identity and cold starting inventory before
the next writer. Preserve backup, separate recovery, local fallback and all
sealed/failed records. No runtime change, deletion, D: expansion or unchanged
baseline rerun is needed.
