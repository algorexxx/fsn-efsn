# W-backed replay verified through 12,000,000

The 300,000-block continuation completed on 16 October 2026 UTC. Inner evidence
verification passed at 20:48:59 UTC; image unmount, read-only filesystem check,
detach and host exit passed by 20:49:51 UTC. The subsequent review verifies all
five prepared/startup/input/output/automatic manifests. The actual-state check
at 21:33:02 UTC finds no test process, loop attachment, matching image mount or
target directory. Original automatic seals remain unchanged; REPORT_SHA256SUMS
covers this review and the late outer records.

All seven commands and ten preservation checks pass. Both cold observers match
the complete backup endpoint at block 12,000,000, hash
`0x6025d10eb6a23788d96d2e5824a4d5077e54a9fa18e3d276b4bedba42f2aa854`:
state root, ticket commitment, transaction/receipt roots, header/RLP, bloom and
TD, with 5,054 tickets and one transaction/receipt. Warm/cold ticket counts
agree. The closed target has 52,179 hashed files; all 51,371 starting file hashes
were checked before replay. Separate recovery retains 1,383 matching hashes.
Backup/baselines and local 7,170,976 fallback metadata remain unchanged, as do
executable/source/toolchain identities. All 3,195 prior evidence files verify.

Startup allocation matched the preceding closed measurement. This review also
compares the saved starting and prior closed file-hash maps, which match exactly.
Earlier allocation differences and the failed supplemental assertion remain
preserved in their original bundles; their cause remains unestablished.
Allocation equality does not replace the unchanged content-verification gate.
The preceding preflight refusal and earlier WSL monitoring interruption/recovery
remain sealed in their original bundles. No controller gate or limit changed,
no duplicate writer was launched and no forced restart was performed.

Replay took 123.138 minutes by wall timestamps and 117.030 by its recorded
monotonic timer. The 6.108-minute difference is preserved; its cause was not
established by this review. Whole host execution took 315.408 wall-clock minutes,
including 192.270 minutes outside replay. Cross-environment timestamps are
recorded as observed; no timestamp adjustment is used to claim a faster result.
These observations are not a full-history ETA. Closed allocation is 101.489 GiB
(108,973,027,328 bytes), up 1.659 GiB from actual startup allocation.
Every sampled reserve passed and no monitor retry was needed. Backing-share
changes do not isolate this job from sparse-image extent retention or unrelated
share usage; both backing and image reserves remain independently checked.

Candidate execution covers 9,320,000 blocks beyond the legacy boundary;
3,130,080 remain to backup tip 15,130,080. F12/G1, final selected-candidate
startup/recovery/handover, independent restore/portable-package acceptance and
consensus review remain open. This does not establish outage durability or
change production release selection. Prior failed/refused jobs remain preserved.

The next justified range is 12,000,000-12,300,000. Keep 300,000 blocks: this run
used about 2h03m for replay and 3h12m for preparation/verification/cleanup,
leaving about 165 minutes under the eight-hour whole-job cap. Recent ranges
left as little as 81 minutes, and earlier same-size replays reached four replay
hours. Do not increase the range or any time limit. A fresh 114 GiB sampled
ceiling leaves 12.511 GiB growth headroom, over twice the largest net growth
among these recent ranges (5.511 GiB). This adds new historical evidence while
amortizing the costly closed checks. Neither timing nor growth is guaranteed.
Keep six-hour clean replay, 6h15m Go, 6h30m replay outer, 30-second resource
samples and unchanged running reserves. Fresh local free space is 22.157 GiB
Linux / 53.676 GiB D:; the last W: observation is about 3.01 TiB. Revalidate
host/mounted capacity, exact image identity and cold starting inventory before
the next writer. Preserve backup, separate recovery, local fallback and all
sealed/failed records. No runtime change, deletion, D: expansion or unchanged
baseline rerun is needed.
