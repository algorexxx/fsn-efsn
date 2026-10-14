# W-backed replay verified through 9,600,000

The 300,000-block continuation completed on 14 October 2026 UTC. Inner evidence
verification passed at 23:38:21 UTC; image unmount, read-only filesystem check,
detach and host exit passed by 23:38:48 UTC. The subsequent review verifies all
five prepared/startup/input/output/automatic manifests. The actual-state check
at 23:46:39 UTC finds no test process, loop attachment, matching image mount or
target directory. Original automatic seals remain unchanged; REPORT_SHA256SUMS
covers this review and the late outer records.

All seven commands and ten preservation checks pass. Both cold observers match
the complete backup endpoint at block 9,600,000, hash
`0xd2e2de7fe44a1bc7a7f9195f8de2bbf8b64b3c4a2e12012cdc5f104582facc9f`:
state root, ticket commitment, transaction/receipt roots, header/RLP, bloom and
TD, with 3,467 tickets and zero transactions/receipts. Warm/cold ticket counts
agree. The closed target has 39,752 hashed files; all 38,445 starting file hashes
were checked before replay. Separate recovery retains 1,383 matching hashes.
Backup/baselines and local 7,170,976 fallback metadata remain unchanged, as do
executable/source/toolchain identities. All 2,723 prior evidence files verify.

Startup allocation matched the preceding closed measurement. This review also
independently compares the saved starting and prior closed file-hash maps.
The prior run's supplemental 4 KiB allocation discrepancy and failed observer
remain preserved in that bundle; no content check was changed or waived.

Replay took 126.077 minutes by wall timestamps and 117.996 by its recorded
monotonic timer. The 8.082-minute difference is preserved; its cause was not
established by this review. Whole host execution took 236.429 wall-clock minutes,
including 110.351 minutes outside replay. Cross-environment timestamps are
recorded as observed; no timestamp adjustment is used to claim a faster result.
These observations are not a full-history ETA. Closed allocation is 77.342 GiB
(83,045,781,504 bytes), up 2.578 GiB from actual startup allocation.
Every sampled reserve passed and no monitor retry was needed. Backing-share
changes do not isolate this job from sparse-image extent retention or unrelated
share usage; both backing and image reserves remain independently checked.

Candidate execution covers 6,920,000 blocks beyond the legacy boundary;
5,530,080 remain to backup tip 15,130,080. F12/G1, final selected-candidate
startup/recovery/handover, independent restore/portable-package acceptance and
consensus review remain open. This does not establish outage durability or
change production release selection. Prior failed/refused jobs remain preserved.

The next justified range is 9,600,000-9,900,000. Keep 300,000 blocks: recent
same-size replays took about 2h06m to 4h03m by wall timestamps, with roughly
1h36m to 2h12m preparation/verification/cleanup overhead in recent ranges.
This leaves margin under the six-hour replay/eight-hour whole-job caps while
amortizing cold checks. A fresh 90 GiB sampled ceiling leaves 12.658 GiB growth
headroom, over twice the largest net growth among these recent ranges (5.511 GiB).
Neither timing nor growth is guaranteed. Keep 6h15m Go, 6h30m replay outer,
30-second resource samples and unchanged 20/50/100 GiB running reserves.
Fresh local free space is 22.514 GiB Linux / 56.523 GiB D:;
the last W: observation is about 3.04 TiB. Revalidate host/mounted
capacity, exact image identity and cold starting inventory before the next writer.
Preserve backup, separate recovery, local fallback and all sealed/failed records.
No runtime change, deletion, D: expansion or unchanged baseline rerun is needed.
