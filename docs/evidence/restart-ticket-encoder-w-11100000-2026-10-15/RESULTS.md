# W-backed replay verified through 11,100,000

The 300,000-block continuation completed on 16 October 2026 UTC. Inner evidence
verification passed at 00:53:17 UTC; image unmount, read-only filesystem check,
detach and host exit passed by 00:54 UTC. The subsequent review verifies all
five prepared/startup/input/output/automatic manifests. The actual-state check
at 01:13:10 UTC finds no test process, replay-image attachment, matching image mount or
target directory. An unrelated Docker read-only ISO remains attached. Original automatic seals remain unchanged; REPORT_SHA256SUMS
covers this review and the late outer records.

All seven commands and ten preservation checks pass. Both cold observers match
the complete backup endpoint at block 11,100,000, hash
`0xe48092f20d13a5d5dfbad604b952140c7e06a00ec64a3a6ba1afb21613e04a6d`:
state root, ticket commitment, transaction/receipt roots, header/RLP, bloom and
TD, with 4,865 tickets and one transaction/receipt. Warm/cold ticket counts
agree. The closed target has 46,997 hashed files; all 45,562 starting file hashes
were checked before replay. Separate recovery retains 1,383 matching hashes.
Backup/baselines and local 7,170,976 fallback metadata remain unchanged, as do
executable/source/toolchain identities. All 3,003 prior evidence files verify.

Startup allocation matched the preceding closed measurement. This review also
compares the saved starting and prior closed file-hash maps, which match exactly.
Earlier 4,096-byte allocation differences and the failed supplemental assertion
remain preserved in their original bundles; their cause remains unestablished.
Allocation equality does not replace the unchanged content-verification gate.

Replay took 143.577 minutes by wall timestamps and 133.508 by its recorded
monotonic timer. The 10.069-minute difference is preserved; its cause was not
established by this review. Whole host execution took 285.434 wall-clock minutes,
including 141.857 minutes outside replay. Cross-environment timestamps are
recorded as observed; no timestamp adjustment is used to claim a faster result.
These observations are not a full-history ETA. Closed allocation is 91.514 GiB
(98,262,872,064 bytes), up 2.722 GiB from actual startup allocation.
Every sampled reserve passed and no monitor retry was needed. Backing-share
changes do not isolate this job from sparse-image extent retention or unrelated
share usage; both backing and image reserves remain independently checked.

Candidate execution covers 8,420,000 blocks beyond the legacy boundary;
4,030,080 remain to backup tip 15,130,080. F12/G1, final selected-candidate
startup/recovery/handover, independent restore/portable-package acceptance and
consensus review remain open. This does not establish outage durability or
change production release selection. Prior failed/refused jobs remain preserved.

The next justified range is 11,100,000-11,400,000. Keep 300,000 blocks: recent
same-size replays took about 1h36m to 4h03m by wall timestamps, with roughly
1h36m to 2h23m preparation/verification/cleanup overhead in recent ranges.
This leaves margin under the six-hour replay/eight-hour whole-job caps while
amortizing cold checks. A fresh 104 GiB sampled ceiling leaves 12.486 GiB growth
headroom, over twice the largest net growth among these recent ranges (5.511 GiB).
Neither timing nor growth is guaranteed. Keep 6h15m Go, 6h30m replay outer,
30-second resource samples and unchanged 20/50/100 GiB running reserves.
Fresh local free space is 22.338 GiB Linux / 53.007 GiB D:;
the last W: observation is about 3.02 TiB. Revalidate host/mounted
capacity, exact image identity and cold starting inventory before the next writer.
Preserve backup, separate recovery, local fallback and all sealed/failed records.
No runtime change, deletion, D: expansion or unchanged baseline rerun is needed.
