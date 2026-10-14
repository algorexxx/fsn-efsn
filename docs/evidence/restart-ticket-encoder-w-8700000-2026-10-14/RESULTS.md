# W-backed replay verified through 8,700,000

The 300,000-block continuation completed on 14 October 2026 UTC. Inner evidence
verification passed at 09:04:43 UTC; image unmount, read-only filesystem check,
detach and host exit passed by 09:04:58 UTC. The subsequent review verifies all
five prepared/startup/input/output/automatic manifests. The actual-state check
at 09:25:44 UTC finds no test process, loop attachment, matching image mount or
target directory. Original automatic seals remain unchanged; REPORT_SHA256SUMS
covers this review and the late outer records.

All seven commands and ten preservation checks pass. Both cold observers match
the complete backup endpoint at block 8,700,000, hash
`0x54d9a0c768554b627766d312980ef240fea0ef586dec52829f6e987592157929`:
state root, ticket commitment, transaction/receipt roots, header/RLP, bloom and
TD, with 3,848 tickets and 258 transactions/receipts. Warm/cold ticket counts
agree. The closed target has 34,479 hashed files; all 32,373 starting file hashes
were checked before replay. Separate recovery retains 1,383 matching hashes.
Backup/baselines and local 7,170,976 fallback metadata remain unchanged, as do
executable/source/toolchain identities. All 2,553 prior evidence files verify.

Replay took 182.190 minutes by wall timestamps and 178.187 by its recorded
monotonic timer. The 4.003-minute difference is preserved; its cause was not
established by this review. Whole host execution took 284.002 wall-clock minutes,
including 101.812 minutes outside replay. Cross-environment timestamps are
recorded as observed; no timestamp adjustment is used to claim a faster result.
These observations are not a full-history ETA. Closed allocation is 67.302 GiB
(72,264,785,920 bytes), up 3.941 GiB. Every sampled reserve passed and no monitor
retry was needed. Backing-share changes do not isolate this job from sparse-image
extent retention or unrelated share usage; both backing and image reserves remain
independently checked.

Candidate execution covers 6,020,000 blocks beyond the legacy boundary;
6,430,080 remain to backup tip 15,130,080. F12/G1, final selected-candidate
startup/recovery/handover, independent restore/portable-package acceptance and
consensus review remain open. This does not establish outage durability or
change production release selection. Prior failed/refused jobs remain preserved.

The next justified range is 8,700,000-9,000,000. Keep 300,000 blocks: recent
same-size replays took about three to four hours by wall timestamps, with roughly
1h42m to 2h12m preparation/verification/cleanup overhead in the last two jobs.
This leaves margin under the six-hour replay/eight-hour whole-job caps while
amortizing cold checks. A fresh 79 GiB sampled ceiling leaves 11.698 GiB growth
headroom, over twice the largest net growth in the last four ranges (5.511 GiB).
Neither timing nor growth is guaranteed. Keep 6h15m Go, 6h30m replay outer,
30-second resource samples and unchanged 20/50/100 GiB running reserves.
Revalidate local/W: capacity, exact image identity and cold starting inventory
before the next writer. Preserve backup, separate recovery, local fallback and
all sealed/failed records. No runtime change, deletion, D: expansion or unchanged
baseline rerun is needed.
