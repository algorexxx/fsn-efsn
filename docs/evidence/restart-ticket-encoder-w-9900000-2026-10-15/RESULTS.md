# W-backed replay verified through 9,900,000

The 300,000-block continuation completed on 15 October 2026 UTC. Inner evidence
verification passed at 04:01:37 UTC; image unmount, read-only filesystem check,
detach and host exit passed by 04:02 UTC. The subsequent review verifies all
five prepared/startup/input/output/automatic manifests. The actual-state check
at 04:49:18 UTC finds no test process, loop attachment, matching image mount or
target directory. Original automatic seals remain unchanged; REPORT_SHA256SUMS
covers this review and the late outer records.

All seven commands and ten preservation checks pass. Both cold observers match
the complete backup endpoint at block 9,900,000, hash
`0x3aeaf11645f7636cc84bb534454f300d783f9c85f900d2539f68c2945f9e5dca`:
state root, ticket commitment, transaction/receipt roots, header/RLP, bloom and
TD, with 1,206 tickets and two transactions/receipts. Warm/cold ticket counts
agree. The closed target has 41,121 hashed files; all 39,752 starting file hashes
were checked before replay. Separate recovery retains 1,383 matching hashes.
Backup/baselines and local 7,170,976 fallback metadata remain unchanged, as do
executable/source/toolchain identities. All 2,779 prior evidence files verify.

Startup allocation matched the preceding closed measurement. This review also
independently compares the saved starting and prior closed file-hash maps.
The earlier supplemental 4 KiB allocation discrepancy and failed observer remain
preserved in their original bundle; no content check was changed or waived.

Replay took 133.316 minutes by wall timestamps and 123.690 by its recorded
monotonic timer. The 9.626-minute difference is preserved; its cause was not
established by this review. Whole host execution took 252.302 wall-clock minutes,
including 118.986 minutes outside replay. Cross-environment timestamps are
recorded as observed; no timestamp adjustment is used to claim a faster result.
These observations are not a full-history ETA. Closed allocation is 79.906 GiB
(85,798,092,800 bytes), up 2.563 GiB from actual startup allocation.
Every sampled reserve passed and no monitor retry was needed. Backing-share
changes do not isolate this job from sparse-image extent retention or unrelated
share usage; both backing and image reserves remain independently checked.

Candidate execution covers 7,220,000 blocks beyond the legacy boundary;
5,230,080 remain to backup tip 15,130,080. F12/G1, final selected-candidate
startup/recovery/handover, independent restore/portable-package acceptance and
consensus review remain open. This does not establish outage durability or
change production release selection. Prior failed/refused jobs remain preserved.

The next justified range is 9,900,000-10,200,000. Keep 300,000 blocks: recent
same-size replays took about 2h06m to 4h03m by wall timestamps, with roughly
1h36m to 2h12m preparation/verification/cleanup overhead in recent ranges.
This leaves margin under the six-hour replay/eight-hour whole-job caps while
amortizing cold checks. A fresh 92 GiB sampled ceiling leaves 12.094 GiB growth
headroom, over twice the largest net growth among these recent ranges (5.511 GiB).
Neither timing nor growth is guaranteed. Keep 6h15m Go, 6h30m replay outer,
30-second resource samples and unchanged 20/50/100 GiB running reserves.
Fresh local free space is 22.449 GiB Linux / 56.531 GiB D:;
the last W: observation is about 3.03 TiB. Revalidate host/mounted
capacity, exact image identity and cold starting inventory before the next writer.
Preserve backup, separate recovery, local fallback and all sealed/failed records.
No runtime change, deletion, D: expansion or unchanged baseline rerun is needed.
