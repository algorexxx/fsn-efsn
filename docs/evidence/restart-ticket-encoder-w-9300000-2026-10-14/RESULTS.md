# W-backed replay verified through 9,300,000

The 300,000-block continuation completed on 14 October 2026 UTC. Inner evidence
verification passed at 18:58:55 UTC; image unmount, read-only filesystem check,
detach and host exit passed by 18:59:26 UTC. The subsequent review verifies all
five prepared/startup/input/output/automatic manifests. The actual-state check
at 19:39:20 UTC finds no test process, loop attachment, matching image mount or
target directory. Original automatic seals remain unchanged; REPORT_SHA256SUMS
covers this review and the late outer records.

All seven commands and ten preservation checks pass. Both cold observers match
the complete backup endpoint at block 9,300,000, hash
`0xf802a2ca4e60858ef77c9bbf6cfc3c86145a8f7c4c38e31fad979db1e275a81a`:
state root, ticket commitment, transaction/receipt roots, header/RLP, bloom and
TD, with 3,850 tickets and 275 transactions/receipts. Warm/cold ticket counts
agree. The closed target has 38,445 hashed files; all 36,557 starting file hashes
were checked before replay. Separate recovery retains 1,383 matching hashes.
Backup/baselines and local 7,170,976 fallback metadata remain unchanged, as do
executable/source/toolchain identities. All 2,665 prior evidence files verify.

The supplemental startup allocation equality assertion failed on a 4,096-byte
difference. The failed observer and its record remain sealed. The revised
observer recorded both allocation measurements without changing frozen runtime
checks. All 36,557 starting checkpoint file hashes subsequently matched the
prior closed inventory before replay; this review independently compares those
saved maps. The allocation difference's cause remains unestablished. Allocation
equality is not a substitute for content identity, and no content check was waived.

Replay took 163.436 minutes by wall timestamps and 156.306 by its recorded
monotonic timer. The 7.130-minute difference is preserved; its cause was not
established by this review. Whole host execution took 268.904 wall-clock minutes,
including 105.468 minutes outside replay. Cross-environment timestamps are
recorded as observed; no timestamp adjustment is used to claim a faster result.
These observations are not a full-history ETA. Closed allocation is 74.764 GiB
(80,277,336,064 bytes), up 3.478 GiB from actual startup allocation.
Every sampled reserve passed and no monitor retry was needed. Backing-share
changes do not isolate this job from sparse-image extent retention or unrelated
share usage; both backing and image reserves remain independently checked.

Candidate execution covers 6,620,000 blocks beyond the legacy boundary;
5,830,080 remain to backup tip 15,130,080. F12/G1, final selected-candidate
startup/recovery/handover, independent restore/portable-package acceptance and
consensus review remain open. This does not establish outage durability or
change production release selection. Prior failed/refused jobs remain preserved.

The next justified range is 9,300,000-9,600,000. Keep 300,000 blocks: recent
same-size replays took about 2h43m to 4h03m by wall timestamps, with roughly
1h36m to 2h12m preparation/verification/cleanup overhead across the last four jobs.
This leaves margin under the six-hour replay/eight-hour whole-job caps while
amortizing cold checks. A fresh 87 GiB sampled ceiling leaves 12.236 GiB growth
headroom, over twice the largest net growth in the last six ranges (5.511 GiB).
Neither timing nor growth is guaranteed. Keep 6h15m Go, 6h30m replay outer,
30-second resource samples and unchanged 20/50/100 GiB running reserves.
Revalidate local/W: capacity, exact image identity and cold starting inventory
before the next writer. Preserve backup, separate recovery, local fallback and
all sealed/failed records. No runtime change, deletion, D: expansion or unchanged
baseline rerun is needed.
