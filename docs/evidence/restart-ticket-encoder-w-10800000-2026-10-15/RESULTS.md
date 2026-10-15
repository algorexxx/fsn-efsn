# W-backed replay verified through 10,800,000

The 300,000-block continuation completed on 15 October 2026 UTC. Inner evidence
verification passed at 19:16:00 UTC; image unmount, read-only filesystem check,
detach and host exit passed by 19:17 UTC. The subsequent review verifies all
five prepared/startup/input/output/automatic manifests. The actual-state check
at 20:04:44 UTC finds no test process, loop attachment, matching image mount or
target directory. Original automatic seals remain unchanged; REPORT_SHA256SUMS
covers this review and the late outer records.

All seven commands and ten preservation checks pass. Both cold observers match
the complete backup endpoint at block 10,800,000, hash
`0x8b23015709ec80b1dc889b84711b9dfe2c741ca4242ef494d1e4387ac9add360`:
state root, ticket commitment, transaction/receipt roots, header/RLP, bloom and
TD, with 2,164 tickets and 270 transactions/receipts. Warm/cold ticket counts
agree. The closed target has 45,562 hashed files; all 44,060 starting file hashes
were checked before replay. Separate recovery retains 1,383 matching hashes.
Backup/baselines and local 7,170,976 fallback metadata remain unchanged, as do
executable/source/toolchain identities. All 2,947 prior evidence files verify.

Startup allocation matched the preceding closed measurement. This review also
compares the saved starting and prior closed file-hash maps, which match exactly.
Earlier 4,096-byte allocation differences and the failed supplemental assertion
remain preserved in their original bundles; their cause remains unestablished.
Allocation equality does not replace the unchanged content-verification gate.

Replay took 162.703 minutes by wall timestamps and 153.752 by its recorded
monotonic timer. The 8.952-minute difference is preserved; its cause was not
established by this review. Whole host execution took 305.681 wall-clock minutes,
including 142.977 minutes outside replay. Cross-environment timestamps are
recorded as observed; no timestamp adjustment is used to claim a faster result.
These observations are not a full-history ETA. Closed allocation is 88.792 GiB
(95,340,163,072 bytes), up 3.106 GiB from actual startup allocation.
Every sampled reserve passed and no monitor retry was needed. Backing-share
changes do not isolate this job from sparse-image extent retention or unrelated
share usage; both backing and image reserves remain independently checked.

Candidate execution covers 8,120,000 blocks beyond the legacy boundary;
4,330,080 remain to backup tip 15,130,080. F12/G1, final selected-candidate
startup/recovery/handover, independent restore/portable-package acceptance and
consensus review remain open. This does not establish outage durability or
change production release selection. Prior failed/refused jobs remain preserved.

The next justified range is 10,800,000-11,100,000. Keep 300,000 blocks: recent
same-size replays took about 1h36m to 4h03m by wall timestamps, with roughly
1h36m to 2h23m preparation/verification/cleanup overhead in recent ranges.
This leaves margin under the six-hour replay/eight-hour whole-job caps while
amortizing cold checks. A fresh 101 GiB sampled ceiling leaves 12.208 GiB growth
headroom, over twice the largest net growth among these recent ranges (5.511 GiB).
Neither timing nor growth is guaranteed. Keep 6h15m Go, 6h30m replay outer,
30-second resource samples and unchanged 20/50/100 GiB running reserves.
Fresh local free space is 22.403 GiB Linux / 54.376 GiB D:;
the last W: observation is about 3.02 TiB. Revalidate host/mounted
capacity, exact image identity and cold starting inventory before the next writer.
Preserve backup, separate recovery, local fallback and all sealed/failed records.
No runtime change, deletion, D: expansion or unchanged baseline rerun is needed.
