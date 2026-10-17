# W-backed replay verified through 12,900,000

The 300,000-block continuation completed on 17 October 2026 UTC. Inner evidence
verification passed at 16:30:58 UTC; image unmount, read-only filesystem check,
detach and host exit passed by 16:32 UTC. The subsequent review verifies all
five prepared/startup/input/output/automatic manifests. The actual-state check
at 16:48:27 UTC finds no test process, loop attachment, matching image mount or
target directory. Original automatic seals remain unchanged; REPORT_SHA256SUMS
covers this review and the late outer records.

All seven commands and ten preservation checks pass. Both cold observers match
the complete backup endpoint at block 12,900,000, hash
`0x71d79c50c8c2511e261f8dd10f37685dedcbc5fcd74bf301c17b0e9cdb1342e9`:
state root, ticket commitment, transaction/receipt roots, header/RLP, bloom and
TD, with 4,486 tickets and one transaction/receipt. Warm/cold ticket counts
agree. The closed target has 54,324 hashed files; all 54,009 starting file hashes
were checked before replay. Separate recovery retains 1,383 matching hashes.
Backup/baselines and local 7,170,976 fallback metadata remain unchanged, as do
executable/source/toolchain identities. All 3,363 prior evidence files verify.

Startup allocation matched the preceding closed measurement. This review also
compares the saved starting and prior closed file-hash maps, which match exactly.
Earlier allocation differences and the failed supplemental assertion remain
preserved in their original bundles; their cause remains unestablished.
Allocation equality does not replace the unchanged content-verification gate.
The preceding preflight refusal and earlier WSL monitoring interruption/recovery
remain sealed in their original bundles. No controller gate or limit changed,
no duplicate writer was launched and no forced restart was performed.

Replay took 80.552 minutes by wall timestamps and 78.132 by its recorded
monotonic timer. The 2.420-minute difference is preserved; its cause was not
established by this review. Whole host execution took 346.993 wall-clock minutes,
including 266.441 minutes outside replay. Cross-environment timestamps are
recorded as observed; no timestamp adjustment is used to claim a faster result.
These observations are not a full-history ETA. Closed allocation is 105.075 GiB
(112,823,578,624 bytes), up 0.876 GiB from actual startup allocation.
Every sampled reserve passed and no monitor retry was needed. Backing-share
changes do not isolate this job from sparse-image extent retention or unrelated
share usage; both backing and image reserves remain independently checked.

Candidate execution covers 10,220,000 blocks beyond the legacy boundary;
2,230,080 remain to backup tip 15,130,080. F12/G1, final selected-candidate
startup/recovery/handover, independent restore/portable-package acceptance and
consensus review remain open. This does not establish outage durability or
change production release selection. Prior failed/refused jobs remain preserved.

The next justified range is 12,900,000-13,200,000. Keep 300,000 blocks: this run
used about 1h21m for replay and 4h26m for preparation/verification/cleanup,
leaving about 133 minutes under the eight-hour whole-job cap. Recent ranges
left as little as 81 minutes, and earlier same-size replays reached four replay
hours. Do not increase the range or any time limit. A fresh 118 GiB sampled
ceiling leaves 12.925 GiB growth headroom, over twice the largest net growth
among these recent ranges (5.511 GiB). This adds new historical evidence while
amortizing the costly closed checks. Neither timing nor growth is guaranteed.
Keep six-hour clean replay, 6h15m Go, 6h30m replay outer, 30-second resource
samples and unchanged running reserves. Fresh local free space is 21.964 GiB
Linux / 53.026 GiB D:; the last W: observation is about 2.90 TiB. Revalidate
host/mounted capacity, exact image identity and cold starting inventory before
the next writer. Preserve backup, separate recovery, local fallback and all
sealed/failed records. No runtime change, deletion, D: expansion or unchanged
baseline rerun is needed.
