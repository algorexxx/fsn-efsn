# W-backed replay verified through 8,100,000

The 300,000-block continuation completed on 13 October 2026 UTC. Inner evidence
verification passed at 21:30:56 UTC; image unmount, read-only filesystem check,
detach and host exit passed by 21:31:18 UTC. The subsequent review verifies all
five prepared/startup/input/output/automatic manifests. The actual-state check
at 22:15:01 UTC finds no test process, loop attachment, matching image mount or
target directory. Original automatic seals remain unchanged; REPORT_SHA256SUMS
covers this review and the late outer records.

All seven commands and ten preservation checks pass. Both cold observers match
the complete backup endpoint at block 8,100,000, hash
`0xfda9bad7c41c5dce6aa75b14e1bb02b0e9a204c47612f88954e75e153332f026`:
state root, ticket commitment, transaction/receipt roots, header/RLP, bloom and
TD, with 4,554 tickets and 116 transactions/receipts. Warm/cold ticket counts
agree. The closed target has 30,407 hashed files; all 27,979 starting file hashes
were checked before replay. Separate recovery retains 1,383 matching hashes.
Backup/baselines and local 7,170,976 fallback metadata remain unchanged, as do
executable/source/toolchain identities. All 2,441 prior evidence files verify.

Replay took 199.801 minutes by wall timestamps and 190.509 by its
recorded monotonic timer. The 9.292-minute difference is preserved;
its cause was not established by this review. Whole host execution took
315.885 wall-clock minutes, including 116.084 minutes outside replay.
Cross-environment timestamps are recorded as observed; the Windows review and
WSL post-state timestamps differ by less than a second despite sequential calls.
No timestamp adjustment is used to claim a faster result. These observations
are not a full-history ETA. Closed allocation is 59.117 GiB
(63,475,888,128 bytes), up 4.094 GiB. Every sampled reserve passed and no
monitor retry was needed. Backing-share changes do not isolate this job from
sparse-image extent retention or unrelated share usage; both backing and image
reserves remain independently checked.

Candidate execution covers 5,420,000 blocks beyond the legacy boundary;
7,030,080 remain to backup tip 15,130,080. F12/G1, final selected-candidate
startup/recovery/handover, independent restore/portable-package acceptance and
consensus review remain open. This does not establish outage durability or
change production release selection. Prior failed/refused jobs remain preserved.

The next justified range is 8,100,000–8,400,000. Keep 300,000 blocks: the latest
replay took about 3h20m by wall timestamps, while the preceding same-size range
took about four hours. Keeping the range leaves room for varying later activity
under the six-hour replay/eight-hour whole-job caps while amortizing cold checks.
A fresh 71 GiB sampled ceiling leaves 11.883 GiB growth headroom, more
than twice either of the last two ranges' net growth (4.094 and 5.511 GiB).
Neither timing nor growth is guaranteed. Keep 6h15m Go, 6h30m replay outer,
30-second resource samples and unchanged 20/50/100 GiB running reserves.
Revalidate local/W: capacity, exact image identity and cold starting inventory
before the next writer. Preserve backup, separate recovery, local fallback and
all sealed/failed records. No runtime change, deletion, D: expansion or unchanged
baseline rerun is needed.
