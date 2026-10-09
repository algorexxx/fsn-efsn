# Verified replay through 4,500,000

Completed 9 October 2026 at 19:20:56 UTC (21:20:56 Europe/Stockholm).
Replay from 3,600,000 took 181.781 minutes. All seven commands and all nine
additional preservation checks passed. Both fresh-process cold checks agree
with the independently captured backup reference, including the complete header,
state/ticket commitments, transaction/receipt roots, bloom and total difficulty.
Warm/cold ticket counts agree at 6,995; the endpoint has one transaction/receipt.

All 4,182 closed-target file hashes stayed unchanged during inspection. The
separate 2,400,000 recovery checkpoint, backup/baseline metadata and exact retained
source/executable identities passed preservation checks. The 1,519 preceding
evidence files verified. Input, output and full bundle manifests were independently
rechecked after completion: 11, 29 and 53 entries respectively.

Closed allocation is 8,907,165,696 bytes (8.295 GiB), up about 1.24 GiB over this
900,000-block interval. Final free space is 24.45 GiB Linux / 63.68 GiB D:.
No monitor retries, stop request or failure occurred. F12 now has 1,820,000
candidate-executed blocks beyond the legacy boundary at 2,680,000; the complete
15,130,080 history and G1/F12 release decisions remain open.

Prepared and running-status files remain immutable historical records; their
pending wording is superseded by completion.json, verification.json and this
result. A host-side verification recheck passed but its JSON writer introduced
Windows CRLF; the exact original LF bytes were restored and matched the already
sealed SHA256 before preservation. No result content or sealed hash changed.

Next perform the planned bounded read-only startup-candidate check against the
complete backup. Then prepare 4,500,000–5,400,000 in place using the identical
replay executable, six-hour clean stop and existing 11 GiB sampled ceiling.
Fresh capacity checks and all preceding completion/identity checks are mandatory;
the observed growth is a planning input, not a guarantee. Preserve the separate
recovery checkpoint and avoid any competing historical writer.
