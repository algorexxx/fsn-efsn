# W-backed trial verified through 7,200,000

The 29,024-block continuation completed on 12 October 2026. Inner evidence
verification passed at 20:28:42 UTC; image unmount, read-only filesystem check,
detach and host exit also passed. The 13 October review verifies all prepared,
startup, input, output and automatic bundle manifests and records no remaining
test process, loop attachment or image mount. The original automatic seals
are unchanged; REPORT_SHA256SUMS covers this review and outer completion.

All seven commands and eleven preservation checks pass. Both cold observers
match the backup's complete endpoint: block 7,200,000, hash
`0x5fdd73b6b6749a406da95c3735a95a3eb8c5667a4e69d8386b9b6a53ba2615a7`,
state root, ticket commitment, transaction/receipt roots, header/RLP, bloom and
TD, with 5,053 tickets and 30 transactions/receipts. Warm/cold ticket counts
agree. The closed target has 22,859 hashed files. Separate recovery retains
1,383 matching hashes; original backup/baselines and local 7,170,976 fallback
metadata remain unchanged. Executable/source/toolchain identities pass.

Replay took 22.131 minutes by recorded wall timestamps,
versus 20.302 minutes from the monotonic timer.
These clocks differ; retain both. Whole host execution was about 87.5 minutes,
including approximately 65 minutes of preparation and cold verification.
Closed database allocation is 44.622 GiB,
up 0.589 GiB. All sampled reserves passed,
and no size-monitor retry was needed. Backing-share allocation can grow faster
than live database allocation as the sparse image touches previously unused
extents; this is separately guarded by the W: reserve.

Candidate execution now covers 4,520,000 blocks beyond the legacy boundary;
7,930,080 remain to the backup tip. This is a successful W: replay trial, not
all-history acceptance or power-loss durability evidence. The earlier failed
local 7,200,000 attempt and STOP remain unchanged. F12/G1 and final
startup/recovery/handover, independent restore and consensus review stay open.

The next justified range is 7,200,000–7,500,000. A 54 GiB sampled ceiling gives
about 9.38 GiB remaining growth, more than the roughly 6.09 GiB implied by
scaling this short trial. That illustration is not a size guarantee. Use six
hours clean replay, 6h15m Go and 6h30m replay outer limits, plus an eight-hour
whole-job cap for W: preparation/cold checks. Keep all reserves, the independent
recovery and local fallback. Revalidate mounted capacity and exact closed
inventory before the next writer. No new runtime change or baseline rerun.
