# W-backed replay verified through 7,500,000

The 300,000-block continuation completed on 13 October 2026. Inner evidence
verification passed at 09:46:55 UTC; image unmount, read-only filesystem check,
detach and host exit also passed by 09:47:00 UTC. The subsequent review verifies
all prepared, startup, input, output and automatic bundle manifests, and records
no remaining test process, loop attachment or image mount. Original automatic
seals remain unchanged. REPORT_SHA256SUMS covers the review and outer records.

All seven commands and ten preservation checks pass. Both cold observers match
the backup's complete endpoint: block 7,500,000, hash
`0x7bbf45e6fa53717f524b312fc8f5e45dccbc47d2fb2037fc710d71d545fb381c`,
state root, ticket commitment, transaction/receipt roots, header/RLP, bloom and
TD, with 5,248 tickets and six transactions/receipts. Warm/cold ticket counts
agree. The closed target has 25,362 hashed files. Separate recovery retains
1,383 matching hashes; backup/baselines and local 7,170,976 fallback metadata
remain unchanged. Executable/source/toolchain identities pass. The ten checks
omit the prior trial's additional old-STOP comparison because this range resumes
a completed job; earlier failed runs and their STOP records remain preserved.

Replay took 209.188 minutes by recorded wall timestamps and
209.010 minutes by its monotonic timer. Whole host execution took
278.358 minutes, including about 69.2 minutes of preparation,
closed verification and cleanup. These are observed timings, not a full-history ETA.
Closed allocation is 49.512 GiB (53,163,130,880 bytes),
up 4.890 GiB. All sampled reserves passed with no monitor retries.
The backing W: share lost more free space than the live DB grew; sparse-image
extents and unrelated share usage are not distinguished by that measurement.
Both backing-share and mounted-filesystem reserves remain independently checked.

Candidate execution now covers 4,820,000 blocks beyond the legacy boundary;
7,630,080 remain to backup tip 15,130,080. F12/G1, final selected-candidate
startup/recovery/handover, independent restore/portable-package acceptance and
consensus review stay open. This does not establish outage durability or change
the production release selection.

The next justified range is 7,500,000–7,800,000. Retain the same 300,000-block
size: this run took about 3.5 replay hours under a six-hour cap, leaving room
for variable later workload while amortizing about 69 minutes of verification.
A fresh 60 GiB sampled ceiling leaves 10.488 GiB for growth, over twice
this run's observed net growth. Neither growth nor timing is guaranteed.
Keep six-hour clean replay, 6h15m Go, 6h30m replay outer and eight-hour whole-job
limits. Revalidate local/W: capacity, exact image identity and cold starting
inventory before the next writer. Preserve backup, separate recovery, local
fallback and all sealed/failed records. No new runtime change, deletion,
D: expansion or unchanged baseline rerun is needed.
