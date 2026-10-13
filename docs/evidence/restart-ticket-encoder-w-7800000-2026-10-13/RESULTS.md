# W-backed replay verified through 7,800,000

The 300,000-block continuation completed on 13 October 2026. Inner verification
passed at 15:51:41 UTC; image unmount, read-only filesystem check, detach and host
exit passed by 15:52:06 UTC. The subsequent review verifies six manifests:
prepared, startup, input, output, automatic bundle and the corrected dispatcher.
The actual-state check at 16:10:58 UTC finds no test process, loop attachment,
matching image mount or target mount directory. Original automatic seals remain
unchanged; REPORT_SHA256SUMS covers this review and the late outer records.

All seven commands and ten preservation checks pass. Both cold observers match
the complete backup endpoint at block 7,800,000, hash
`0xa51edadce589d7bd27751b64545b1341179310279d03370fef7e9f5fb89fc22c`:
state root, ticket commitment, transaction/receipt roots, header/RLP, bloom and
TD, with 4,804 tickets and 135 transactions/receipts. Warm/cold ticket counts
agree. The closed target has 27,979 hashed files; all 25,362 starting file hashes
were checked before replay. Separate recovery retains 1,383 matching hashes.
Backup/baselines and local 7,170,976 fallback metadata remain unchanged, as do
executable/source/toolchain identities. All 2,378 prior evidence files verify.

Replay took 242.953 minutes by wall timestamps and
235.471 by its recorded monotonic timer. The timers
differ by 7.481 minutes; the cause was not established by this review.
Whole host execution took 341.799 wall-clock minutes,
including 98.846 minutes outside replay. These are observations, not a
full-history ETA. Closed allocation is 55.023 GiB (59,080,257,536 bytes),
up 5.511 GiB. Every sampled reserve passed, with no monitor retries.
Backing-share free-space changes do not isolate this job from sparse-image
extent retention or unrelated share usage. Both backing and image reserves
remain independently checked.

The original preflight's refusal of an unrelated Docker read-only ISO and the
first host dispatch's existing-log-directory refusal remain preserved. Neither
started replay. The corrected preflight and dispatcher led to this completed
run; see PREFLIGHT-NOTE.md and DISPATCH-NOTE.md. The report checker initially had
a manifest-key typo, corrected before its first result was written; this did
not modify any test output or frozen input. Its current source and result are
included in the supplemental seal.

Candidate execution now covers 5,120,000 blocks beyond the legacy boundary;
7,330,080 remain to backup tip 15,130,080. F12/G1, final selected-candidate
startup/recovery/handover, independent restore/portable-package acceptance and
consensus review remain open. This does not establish outage durability or
change production release selection.

The next justified range is 7,800,000–8,100,000. Keep 300,000 blocks: replay took
about four wall-clock hours with about 99 additional minutes outside replay,
leaving margin under six-hour replay/eight-hour whole-job caps. A fresh 67 GiB
sampled ceiling leaves 11.977 GiB of net growth headroom, over twice this
range's observed 5.511 GiB net growth. Neither timing nor growth is guaranteed.
Keep six-hour clean replay, 6h15m Go, 6h30m replay outer and eight-hour whole-job
limits. Revalidate local/W: capacity, exact image identity and cold starting
inventory before the next writer. Preserve backup, separate recovery, local
fallback and all sealed/failed records. No new runtime change, deletion,
D: expansion or unchanged baseline rerun is needed.
