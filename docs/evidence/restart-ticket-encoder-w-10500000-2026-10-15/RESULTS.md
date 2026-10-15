# W-backed replay verified through 10,500,000

The 300,000-block continuation completed on 15 October 2026 UTC. Inner evidence
verification passed at 13:08:21 UTC; image unmount, read-only filesystem check,
detach and host exit passed by 13:09 UTC. The subsequent review verifies all
five prepared/startup/input/output/automatic manifests. The actual-state check
at 14:05:24 UTC finds no test process, replay-image attachment, matching image mount or
target directory. An unrelated Docker read-only ISO remains attached. Original automatic seals remain unchanged; REPORT_SHA256SUMS
covers this review and the late outer records.

All seven commands and ten preservation checks pass. Both cold observers match
the complete backup endpoint at block 10,500,000, hash
`0xbfa5ada6ca8cc6e8d5ada1ca2dbe2b4e96f732148cfc55dcfb92af41d7005e54`:
state root, ticket commitment, transaction/receipt roots, header/RLP, bloom and
TD, with 3,069 tickets and one transaction/receipt. Warm/cold ticket counts
agree. The closed target has 44,060 hashed files; all 42,373 starting file hashes
were checked before replay. Separate recovery retains 1,383 matching hashes.
Backup/baselines and local 7,170,976 fallback metadata remain unchanged, as do
executable/source/toolchain identities. All 2,891 prior evidence files verify.

Startup allocation was 4,096 bytes above the preceding closed measurement;
its cause remains unestablished. All 42,373 starting hashes matched before
replay. This review independently compares the saved starting and prior closed
file-hash maps. The current supplemental capture passed; the earlier failed
allocation assertion remains preserved in its original bundle. No content check
was changed or waived.

Replay took 122.386 minutes by wall timestamps and 118.698 by its recorded
monotonic timer. The 3.689-minute difference is preserved; its cause was not
established by this review. Whole host execution took 254.149 wall-clock minutes,
including 131.763 minutes outside replay. Cross-environment timestamps are
recorded as observed; no timestamp adjustment is used to claim a faster result.
These observations are not a full-history ETA. Closed allocation is 85.687 GiB
(92,005,642,240 bytes), up 3.113 GiB from actual startup allocation.
Every sampled reserve passed and no monitor retry was needed. Backing-share
changes do not isolate this job from sparse-image extent retention or unrelated
share usage; both backing and image reserves remain independently checked.

Candidate execution covers 7,820,000 blocks beyond the legacy boundary;
4,630,080 remain to backup tip 15,130,080. F12/G1, final selected-candidate
startup/recovery/handover, independent restore/portable-package acceptance and
consensus review remain open. This does not establish outage durability or
change production release selection. Prior failed/refused jobs remain preserved.

The next justified range is 10,500,000-10,800,000. Keep 300,000 blocks: recent
same-size replays took about 1h36m to 4h03m by wall timestamps, with roughly
1h36m to 2h12m preparation/verification/cleanup overhead in recent ranges.
This leaves margin under the six-hour replay/eight-hour whole-job caps while
amortizing cold checks. A fresh 98 GiB sampled ceiling leaves 12.313 GiB growth
headroom, over twice the largest net growth among these recent ranges (5.511 GiB).
Neither timing nor growth is guaranteed. Keep 6h15m Go, 6h30m replay outer,
30-second resource samples and unchanged 20/50/100 GiB running reserves.
Fresh local free space is 22.311 GiB Linux / 56.528 GiB D:;
the last W: observation is about 3.03 TiB. Revalidate host/mounted
capacity, exact image identity and cold starting inventory before the next writer.
Preserve backup, separate recovery, local fallback and all sealed/failed records.
No runtime change, deletion, D: expansion or unchanged baseline rerun is needed.
