# Replay verified through 6,900,000

The continuation from 6,623,296 completed and its automatic verifier passed at
09:00:57 UTC on 12 October 2026. All seven commands, both cold endpoint checks,
ten additional preservation checks and protected backup/baseline/source/input
checks pass. The first 6,900,000 attempt's failed completion and STOP remain
unchanged; its separately verified checkpoint supplied this continuation.

The full header/RLP, state root, ticket/transaction/receipt commitments, bloom
and total difficulty match the preserved backup. Warm and cold ticket counts
agree at 5,304; the endpoint has 12 transactions and 12 receipts. Exact endpoint
values are in verification.json. The retained replay executable is unchanged.
The controller recorded 6,713.369 monotonic seconds for replay; its UTC timestamps
span 06:55:04 to 08:58:21. These are separate recorded time measurements.

Startup verified 16,893 working files, 1,383 separate recovery files and 2,028
prior evidence files. The final 19,533-file working inventory is unchanged across
the two read-only cold checks. Private mount/network namespaces and protected
read-only views were retained. All 224 allocation measurements passed on their
first attempt: 223 live scanner samples and the final closed GNU du measurement.
No vanished entry was observed in those live samples. Closed allocation is
40,776,675,328 bytes (37.976 GiB). Final recorded free space is 28.064 GiB Linux
and 59.554 GiB D:, both above the 20/50 GiB running reserves. A new job still
needs its own stricter starting-capacity gate; these values are not that gate.

This adds 276,704 verified blocks, reaching 4,220,000 beyond the 2,680,000 legacy
boundary. Another 8,230,080 blocks remain to the 15,130,080 backup tip. F12/G1,
final selected-binary restored startup/recovery/handover, independent complete
restore/portable-package acceptance and independent consensus review remain open.

All 57 entries in the automatic root manifest were independently checked after
completion. Its SHA256 is
`a02ec219a07b89a6f07f0bdbb87681f834ebe38eaa41583a996155d2ef745d4f`.
That manifest and the automatic outputs remain unchanged. REPORT_SHA256SUMS
separately binds this later human-readable report. No database replay, release
selection, storage expansion or cleanup was performed to produce this report.
