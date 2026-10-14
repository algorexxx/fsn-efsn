# W-backed replay verified through 8,400,000

The 300,000-block continuation completed on 14 October 2026 UTC. Inner evidence
verification passed at 03:50:44 UTC; image unmount, read-only filesystem check,
detach and host exit passed by 03:51:05 UTC. The subsequent review verifies all
five prepared/startup/input/output/automatic manifests. The actual-state check
at 04:17:17 UTC finds no test process, loop attachment, matching image mount or
target directory. Original automatic seals remain unchanged; REPORT_SHA256SUMS
covers this review and the late outer records.

All seven commands and ten preservation checks pass. Both cold observers match
the complete backup endpoint at block 8,400,000, hash
`0x8a4e52a26fee0a83b3a911991a873f4dd278d28aa7ff3860f5d7d7ed0aeb7ff1`:
state root, ticket commitment, transaction/receipt roots, header/RLP, bloom and
TD, with 1,857 tickets and 736 transactions/receipts. Warm/cold ticket counts
agree. The closed target has 32,373 hashed files; all 30,407 starting file hashes
were checked before replay. Separate recovery retains 1,383 matching hashes.
Backup/baselines and local 7,170,976 fallback metadata remain unchanged, as do
executable/source/toolchain identities. All 2,497 prior evidence files verify.

Replay took 184.764 minutes by wall timestamps and 172.659 by its recorded
monotonic timer. The 12.105-minute difference is preserved; its cause was not
established by this review. Whole host execution took 317.249 wall-clock minutes,
including 132.485 minutes outside replay. Cross-environment timestamps are
recorded as observed: the Windows review timestamp precedes the sequential WSL
post-state capture timestamp by about 1.7 seconds. No timestamp adjustment is
used to claim a faster result. These observations are not a full-history ETA.
Closed allocation is 63.361 GiB (68,033,474,560 bytes), up 4.245 GiB. Every sampled
reserve passed and no monitor retry was needed. Backing-share changes do not
isolate this job from sparse-image extent retention or unrelated share usage;
both backing and image reserves remain independently checked.

Candidate execution covers 5,720,000 blocks beyond the legacy boundary;
6,730,080 remain to backup tip 15,130,080. F12/G1, final selected-candidate
startup/recovery/handover, independent restore/portable-package acceptance and
consensus review remain open. This does not establish outage durability or
change production release selection. Prior failed/refused jobs remain preserved.

The next justified range is 8,400,000-8,700,000. Keep 300,000 blocks: recent
same-size replays took about 3h05m to four hours by wall timestamps, and the latest
cold preparation/verification/cleanup added about 2h12m. This leaves margin under
the six-hour replay/eight-hour whole-job caps while amortizing cold checks.
A fresh 75 GiB sampled ceiling leaves 11.639 GiB growth headroom, over twice the
largest net growth in the last three ranges (5.511 GiB). Neither timing nor growth
is guaranteed. Keep 6h15m Go, 6h30m replay outer, 30-second resource samples and
unchanged 20/50/100 GiB running reserves. Revalidate local/W: capacity, exact image
identity and cold starting inventory before the next writer. Preserve backup,
separate recovery, local fallback and all sealed/failed records. No runtime
change, deletion, D: expansion or unchanged baseline rerun is needed.
