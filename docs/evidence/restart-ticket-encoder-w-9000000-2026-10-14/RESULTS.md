# W-backed replay verified through 9,000,000

The 300,000-block continuation completed on 14 October 2026 UTC. Inner evidence
verification passed at 14:14:29 UTC; image unmount, read-only filesystem check,
detach and host exit passed by 14:14:56 UTC. The subsequent review verifies all
five prepared/startup/input/output/automatic manifests. The actual-state check
at 14:26:27 UTC finds no test process, loop attachment, matching image mount or
target directory. Original automatic seals remain unchanged; REPORT_SHA256SUMS
covers this review and the late outer records.

All seven commands and ten preservation checks pass. Both cold observers match
the complete backup endpoint at block 9,000,000, hash
`0x772fabc30369f3ff2022a6a3c26432dea4d580258de69f7836d77c36d5f9d32d`:
state root, ticket commitment, transaction/receipt roots, header/RLP, bloom and
TD, with 3,710 tickets and 10 transactions/receipts. Warm/cold ticket counts
agree. The closed target has 36,557 hashed files; all 34,479 starting file hashes
were checked before replay. Separate recovery retains 1,383 matching hashes.
Backup/baselines and local 7,170,976 fallback metadata remain unchanged, as do
executable/source/toolchain identities. All 2,609 prior evidence files verify.

Replay took 189.744 minutes by wall timestamps and 184.792 by its recorded
monotonic timer. The 4.952-minute difference is preserved; its cause was not
established by this review. Whole host execution took 286.196 wall-clock minutes,
including 96.452 minutes outside replay. Cross-environment timestamps are
recorded as observed; no timestamp adjustment is used to claim a faster result.
These observations are not a full-history ETA. Closed allocation is 71.286 GiB
(76,542,504,960 bytes), up 3.984 GiB. Every sampled reserve passed and no monitor
retry was needed. Backing-share changes do not isolate this job from sparse-image
extent retention or unrelated share usage; both backing and image reserves remain
independently checked.

Candidate execution covers 6,320,000 blocks beyond the legacy boundary;
6,130,080 remain to backup tip 15,130,080. F12/G1, final selected-candidate
startup/recovery/handover, independent restore/portable-package acceptance and
consensus review remain open. This does not establish outage durability or
change production release selection. Prior failed/refused jobs remain preserved.

The next justified range is 9,000,000-9,300,000. Keep 300,000 blocks: recent
same-size replays took about three to four hours by wall timestamps, with roughly
1h36m to 2h12m preparation/verification/cleanup overhead across the last three jobs.
This leaves margin under the six-hour replay/eight-hour whole-job caps while
amortizing cold checks. A fresh 83 GiB sampled ceiling leaves 11.714 GiB growth
headroom, over twice the largest net growth in the last five ranges (5.511 GiB).
Neither timing nor growth is guaranteed. Keep 6h15m Go, 6h30m replay outer,
30-second resource samples and unchanged 20/50/100 GiB running reserves.
Revalidate local/W: capacity, exact image identity and cold starting inventory
before the next writer. Preserve backup, separate recovery, local fallback and
all sealed/failed records. No runtime change, deletion, D: expansion or unchanged
baseline rerun is needed.
