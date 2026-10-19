# Candidate replay verified at backup tip 15,130,080

The final 130,080-block continuation completed on 19 October 2026 UTC.
Evidence verification passed at 19:51:17 UTC; image unmount, read-only
filesystem check, detach and host exit passed by 19:51:31 UTC. Post-completion
review verifies all five prepared/startup/input/output/automatic manifests.
The actual-state check at 20:43:22 UTC finds no test process, loop attachment,
matching mount or target directory. REPORT_SHA256SUMS seals this review and
late outer records without changing the original automatic seals.

All seven commands and ten preservation checks pass. Both cold observers match
the complete backup at block 15,130,080, hash
`0xe93ffded087a79097d4309c7831690161db6ed136f4b1a22c4c83a99db80f99f`:
state root `0x1526799d6f10f4a4467e4dd4f3b1f81ca1479822bb2c24aa541ac66f889ccffc`,
ticket commitment `0xe4e079c525c189eb30ca22ba57bbd4af8b44050e2fc1618c2157107b00820e2c`,
transaction/receipt roots, header/RLP, bloom and TD 63,370,514,513.
Warm/cold counts agree at 491 tickets and one transaction/receipt.

The closed target has 55,903 hashed files. All 55,796 starting hashes match the
preceding closed checkpoint exactly. Separate recovery retains 1,383 matching
hashes; backup/baseline/local fallback metadata and executable/source/toolchain
identities remain unchanged. All 3,829 prior evidence files verify. Startup
allocation matches the preceding closed measurement. Earlier allocation
anomalies, failed supplemental assertions, preflight refusals and monitoring
interruptions remain preserved. No failed completion is rewritten.

Replay took 9.098 wall-clock minutes and 8.647 monotonic minutes; their
0.451-minute difference remains unexplained. Whole host execution took
369.630 wall-clock minutes, including 360.532 minutes outside replay, leaving
110.370 minutes under the eight-hour cap. Cross-environment timestamps are
recorded as observed. Closed allocation is 115,887,316,992 bytes (107.928 GiB),
up 109,727,744 bytes (0.102 GiB). All sampled reserves pass; minimum free bytes
were 23,060,000,768 Linux, 56,143,138,816 D:, 3,190,789,049,344 W: and
432,379,772,928 inside the image. No STOP, retry or duplicate writer occurred.

Candidate replay now reaches the complete available backup tip, with 12,450,080
blocks beyond the legacy shortcut boundary at 2,680,000. There is no further
historical range to launch. Earlier consensus shortcuts remain in this client's
replay; this is not independent validation of every early rule or global chain
canonicality. The unchanged baseline remains a diagnostic comparator. Missing
17 exported ticket samples are not recovered by this result. F12/G1 require
independent codec/consensus review, exact source/shortcut acceptance and an
explicit accepted-parent/trust record; release selection is unchanged.

The next useful acceptance question is full writable restored startup and fresh
restart on a disposable complete backup copy using the already qualified
unselected startup guard and encoder. Preserve this final replay checkpoint,
the original backup, separate recovery, local fallback, archives and all failed
or sealed records. Fresh Linux/D: free space is 21.476/52.681 GiB, unsuitable
for a complete local copy; the W: image has about 402.7 GiB free and the backing
share about 2.90 TiB. A distinct W: copy can fit while retaining reserves, but
must have finite copy/verification/runtime limits and one image owner.
Do not reuse the final checkpoint as a writable startup fixture. The test-only
anchor must remain separate from production selection. Recovery/handover,
independent complete restore/portable-package acceptance and final selected
candidate rehearsal remain open. No unchanged passing small test needs rerunning.
