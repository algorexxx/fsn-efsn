# W-backed replay verified through 15,000,000

The 300,000-block continuation completed on 19 October 2026 UTC. Evidence
verification passed at 13:16:04 UTC; image unmount, read-only filesystem check,
detach and host exit passed by 13:16:17 UTC. The post-completion review verifies
all five prepared/startup/input/output/automatic manifests. The actual-state
check at 13:38:14 UTC finds no test process, loop attachment, matching image
mount or target directory. Original automatic seals remain unchanged;
REPORT_SHA256SUMS covers this review and the late outer records.

All seven commands and ten preservation checks pass. Both cold observers match
the complete backup endpoint at block 15,000,000, hash
`0x04c0b58ad890a69513b3e2dce6a9889d455eb7adccbb1c89d30e0eeccd4dce39`:
state root, ticket commitment, transaction/receipt roots, header/RLP, bloom and
TD, with 520 tickets and one transaction/receipt. Warm/cold ticket counts agree.
The closed target has 55,796 hashed files; all 55,695 starting file hashes were
checked before replay. Separate recovery retains 1,383 matching hashes.
Backup/baselines and local 7,170,976 fallback metadata remain unchanged, as do
executable/source/toolchain identities. All 3,773 prior evidence files verify.

Startup allocation matched the preceding closed measurement. This review also
compares the saved starting and prior closed file-hash maps, which match exactly.
Earlier allocation differences and the failed supplemental assertion remain
preserved in their original bundles; their cause remains unestablished.
Allocation equality does not replace the unchanged content-verification gate.
Earlier filename/line-ending preflight refusals and WSL monitoring interruption/
recovery remain sealed. No controller gate or limit changed, no duplicate writer
was launched and no forced restart was performed.

Replay took 15.935 minutes by wall timestamps and 15.596 by its recorded
monotonic timer. The 0.338-minute difference is preserved; its cause was not
established by this review. Whole host execution took 353.692 wall-clock minutes,
including 337.758 minutes outside replay. Cross-environment timestamps are
recorded as observed; no timestamp adjustment is used to claim a faster result.
These observations are not a full-history ETA. Closed allocation is 107.826 GiB
(115,777,589,248 bytes), up 0.254 GiB from actual startup allocation.
Every sampled reserve passed and no monitor retry was needed. Backing-share
changes do not isolate this job from sparse-image extent retention or unrelated
share usage; both backing and image reserves remain independently checked.

Candidate execution covers 12,320,000 blocks beyond the legacy boundary;
130,080 remain to backup tip 15,130,080. F12/G1, final selected-candidate
startup/recovery/handover, independent restore/portable-package acceptance and
consensus review remain open. This does not establish outage durability or
change production release selection. Prior failed/refused jobs remain preserved.

The next justified range is the final 130,080 blocks, 15,000,000-15,130,080.
It reaches the preserved backup tip without extending beyond available history.
This completed 300,000-block range used about 15.9 minutes for replay and
337.8 for preparation/verification/cleanup, leaving 126.3 minutes under
the eight-hour whole-job cap. Recent ranges left as little as 81 minutes.
The final range is smaller; keep all time limits. A fresh 120 GiB sampled
ceiling leaves 12.174 GiB growth headroom, over twice the largest recent
net growth (5.511 GiB). Timing and growth are not guaranteed. Keep six-hour
clean replay, 6h15m Go, 6h30m replay outer, 30-second resource samples and
unchanged running reserves. Fresh free space is 21.536 GiB Linux /
52.320 GiB D:; the last W: observation is about 2.90 TiB. Revalidate
host/mounted capacity, exact image identity and cold starting inventory before
the next writer. Preserve backup, separate recovery, local fallback and all
sealed/failed records. No runtime change, deletion, D: expansion or unchanged
baseline rerun is needed. Once the tip is verified, review the remaining
restored-startup, identity-refusal, recovery and handover acceptance gaps.
