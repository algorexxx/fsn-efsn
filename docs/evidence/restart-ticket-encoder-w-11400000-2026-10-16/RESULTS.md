# W-backed replay verified through 11,400,000

The 300,000-block continuation completed on 16 October 2026 UTC. Inner evidence
verification passed at 07:54:49 UTC; image unmount, read-only filesystem check,
detach and host exit passed by 07:55:12 UTC. The subsequent review verifies all
five prepared/startup/input/output/automatic manifests. The actual-state check
at 08:26:25 UTC finds no test process, loop attachment, matching image mount or
target directory. Original automatic seals remain unchanged; REPORT_SHA256SUMS
covers this review and the late outer records.

All seven commands and ten preservation checks pass. Both cold observers match
the complete backup endpoint at block 11,400,000, hash
`0xb3c644d3b564774124099d43beb4ba78a0d6397f92531cebe57a26c37e0fa7c6`:
state root, ticket commitment, transaction/receipt roots, header/RLP, bloom and
TD, with 4,769 tickets and zero transactions/receipts. Warm/cold ticket counts
agree. The closed target has 49,313 hashed files; all 46,997 starting file hashes
were checked before replay. Separate recovery retains 1,383 matching hashes.
Backup/baselines and local 7,170,976 fallback metadata remain unchanged, as do
executable/source/toolchain identities. All 3,059 prior evidence files verify.

Startup allocation matched the preceding closed measurement. This review also
compares the saved starting and prior closed file-hash maps, which match exactly.
Earlier allocation differences and the failed supplemental assertion remain
preserved in their original bundles; their cause remains unestablished.
Allocation equality does not replace the unchanged content-verification gate.

The [02:18 monitoring interruption](monitoring-2026-10-16T0218/README.md) and
[06:17 recovered access](monitoring-2026-10-16T0616/README.md) remain sealed and
are included in the 62-file automatic manifest. Two status requests timed out;
access later returned without a forced restart or duplicate writer. Low host
memory was observed, but the cause was not established. This monitoring failure
did not become a replay failure; final verification and cleanup passed.

Replay took 199.523 minutes by wall timestamps and 186.758 by its recorded
monotonic timer. The 12.765-minute difference is preserved; its cause was not
established by this review. Whole host execution took 398.671 wall-clock minutes,
including 199.149 minutes outside replay. Cross-environment timestamps are
recorded as observed; no timestamp adjustment is used to claim a faster result.
These observations are not a full-history ETA. Closed allocation is 95.369 GiB
(102,401,626,112 bytes), up 3.855 GiB from actual startup allocation.
Every sampled reserve passed and no monitor retry was needed. Backing-share
changes do not isolate this job from sparse-image extent retention or unrelated
share usage; both backing and image reserves remain independently checked.

Candidate execution covers 8,720,000 blocks beyond the legacy boundary;
3,730,080 remain to backup tip 15,130,080. F12/G1, final selected-candidate
startup/recovery/handover, independent restore/portable-package acceptance and
consensus review remain open. This does not establish outage durability or
change production release selection. Prior failed/refused jobs remain preserved.

The next justified range is 11,400,000-11,700,000. Keep 300,000 blocks: this run
used about 3h20m for replay and 3h19m for preparation/verification/cleanup,
leaving about 81 minutes under the eight-hour whole-job cap. Earlier same-size
replays reached about four replay hours. Do not increase the range or any time
limit. A fresh 108 GiB sampled ceiling leaves 12.631 GiB growth headroom, over
twice the largest net growth among these recent ranges (5.511 GiB). This adds
new historical evidence while amortizing the costly closed checks. Neither
timing nor growth is guaranteed. Keep six-hour clean replay, 6h15m Go, 6h30m
replay outer, 30-second resource samples and unchanged running reserves.
Fresh local free space is 22.282 GiB Linux / 53.816 GiB D:;
the last W: observation is about 3.02 TiB. Revalidate host/mounted
capacity, exact image identity and cold starting inventory before the next writer.
Preserve backup, separate recovery, local fallback and all sealed/failed records.
No runtime change, deletion, D: expansion or unchanged baseline rerun is needed.
