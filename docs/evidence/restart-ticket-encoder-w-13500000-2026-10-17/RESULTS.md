# W-backed replay verified through 13,500,000

The 300,000-block continuation completed on 18 October 2026 UTC. The evidence
verifier exited successfully at 04:55:19 UTC; image unmount, read-only filesystem
check, detach and host exit passed by 04:56 UTC. The subsequent review verifies
all five prepared/startup/input/output/automatic manifests. The actual-state
check at 05:57:34 UTC finds no test process, loop attachment, matching image
mount or target directory. Original automatic seals remain unchanged;
REPORT_SHA256SUMS covers this review and the late outer records.

All seven commands and ten preservation checks pass. Both cold observers match
the complete backup endpoint at block 13,500,000, hash
`0xe5e3ad02245e8b484d1b10ebe05b6f4631bb9139ff0942cbd6252d1c73069eec`:
state root, ticket commitment, transaction/receipt roots, header/RLP, bloom and
TD, with 3,647 tickets and two transactions/receipts. Warm/cold ticket counts
agree. The closed target has 54,852 hashed files; all 54,351 starting file hashes
were checked before replay. Separate recovery retains 1,383 matching hashes.
Backup/baselines and local 7,170,976 fallback metadata remain unchanged, as do
executable/source/toolchain identities. All 3,493 prior evidence files verify.

Startup allocation matched the preceding closed measurement. This review also
compares the saved starting and prior closed file-hash maps, which match exactly.
Earlier allocation differences and the failed supplemental assertion remain
preserved in their original bundles; their cause remains unestablished.
Allocation equality does not replace the unchanged content-verification gate.
Earlier filename/line-ending preflight refusals and WSL monitoring interruption/
recovery remain sealed in their original bundles. No controller gate or limit
changed, no duplicate writer was launched and no forced restart was performed.

Replay took 62.263 minutes by wall timestamps and 58.413 by its recorded
monotonic timer. The 3.850-minute difference is preserved; its cause was not
established by this review. Whole host execution took 364.904 wall-clock minutes,
including 302.640 minutes outside replay. Cross-environment timestamps are
recorded as observed; no timestamp adjustment is used to claim a faster result.
These observations are not a full-history ETA. Closed allocation is 106.233 GiB
(114,067,230,720 bytes), up 0.594 GiB from actual startup allocation.
Every sampled reserve passed and no monitor retry was needed. Backing-share
changes do not isolate this job from sparse-image extent retention or unrelated
share usage; both backing and image reserves remain independently checked.

Candidate execution covers 10,820,000 blocks beyond the legacy boundary;
1,630,080 remain to backup tip 15,130,080. F12/G1, final selected-candidate
startup/recovery/handover, independent restore/portable-package acceptance and
consensus review remain open. This does not establish outage durability or
change production release selection. Prior failed/refused jobs remain preserved.

The next justified range is 13,500,000-13,800,000. Keep 300,000 blocks: this run
used about 1h02m for replay and 5h03m for preparation/verification/cleanup,
leaving about 115 minutes under the eight-hour whole-job cap. Recent ranges
left as little as 81 minutes, and earlier same-size replays reached four replay
hours. Do not increase the range or any time limit. A fresh 119 GiB sampled
ceiling leaves 12.767 GiB growth headroom, over twice the largest net growth
among these recent ranges (5.511 GiB). This adds new historical evidence while
amortizing the costly closed checks. Neither timing nor growth is guaranteed.
Keep six-hour clean replay, 6h15m Go, 6h30m replay outer, 30-second resource
samples and unchanged running reserves. Fresh local free space is 21.855 GiB
Linux / 52.953 GiB D:; the last W: observation is about 2.90 TiB. Revalidate
host/mounted capacity, exact image identity and cold starting inventory before
the next writer. Preserve backup, separate recovery, local fallback and all
sealed/failed records. No runtime change, deletion, D: expansion or unchanged
baseline rerun is needed.
