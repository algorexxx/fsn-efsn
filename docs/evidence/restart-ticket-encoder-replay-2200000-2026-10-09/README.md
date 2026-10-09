# Candidate historical replay through 2,200,000

9 October 2026. **Passed within the declared range.** The retained encoder-candidate
executable resumed a verified copy of the 2,000,000 checkpoint, executed blocks
2,000,001 through 2,200,000 and passed both final cold checks. Its executable,
source and configuration identity was accepted unchanged.

All seven qualification commands exited zero, with no stderr, failed/skipped
tests, monitor retries or stop requests. The recorded command timestamps span
01:53:59 to 02:20:59 UTC (1,619.61 seconds, about 27 minutes); the Go test
separately reports 1,487.81 seconds (24 minutes 48 seconds). Preserve both
measurements; the cause of their difference is not established. The unchanged
runner uses a monotonic clock for its 30-minute clean-stop limit. Preservation
checks finished at 02:21:29. The [specification](spec.md), [plan at start](plan-at-start.md)
and verifier preceded execution. [Evidence verification](verification.json)
passed on its first run; its command, exit status and output are retained.
The initial read-only capacity/process check is retained in [preflight.json](preflight.json).

## Historical result

| Endpoint at 2,200,000 | Observed and matched |
| --- | --- |
| Block hash | `0xfb434cd67f91ec47cb6fc6eef629493b8ae2b38bf98d1e81b5ae6fc51d60f308` |
| State root | `0x86f23b7891c3f9381d9575352d02728104188bbcf6ec89782a9198e58a87a71b` |
| Ticket commitment | `0xf02885da3009aacab9309ccc90ee1368bff55d936d870ca8fb1d4c5e00e063bf` |
| Transaction root | `0x15cdec93f32d9921963612b70dc41e04b7d7079f1acd6a328ad6e7c9ee8ce5f0` |
| Receipt root | `0x0043627246f29a6f86796fd275575acb12d68e7fadff407de5dfefbca165f9b5` |
| Cumulative difficulty | `9815661760` |
| Transactions / receipts | `2 / 2` |

Full endpoint header RLP and bloom also match the preserved source reference
captured before replay. The cold-details process began with an empty ticket
cache, decoded state tickets and recomputed their commitment. Its **6,220
tickets** agree with the replay observation; the count is observed, not assumed
from unavailable historical state in the backup. The original cold-head helper
checks all head markers, canonical identity, body/receipt commitments and TD
in a separate process.

Together with the [preceding range](../restart-ticket-encoder-replay-2000000-2026-10-09/README.md),
this establishes sequential candidate execution from genesis through 2,200,000.
These heights retain legacy checkpoint shortcuts through 2,680,000: transaction
execution and state/receipt comparisons run, while ticket-seal and raw-transaction
checks remain subject to those documented shortcuts.

## Inputs and preservation

The replay executable was copied byte-for-byte, not rebuilt. A separate Go 1.27.1
observer uses an overlay changing only the preceding observer's height literal
from 2000000 to 2200000; the [diff](observer-change.patch), overlay and binary hash
are retained. Only its reference and cold-details tests ran; its replay test
was never invoked. The [runner](run.py) imports the sealed first-range runner's
execution, environment, monitoring and preservation helpers, recording its hash.

- Private mount/network namespaces, loopback down, offline Go modules and
  enforced read-only backup/checkpoint mounts were verified.
- All **1,004 checkpoint files** matched the preceding cold inventory before
  copying. Copied bytes matched, and the original checkpoint remained unchanged.
  Its exact-height cold preflight passed at 2,000,000.
- All **1,157 stopped-target files** retained their SHA256 during cold inspection.
  The replay identity file remains byte-identical to the checkpoint's.
- Backup metadata for 56,107 files and both baseline metadata inventories are
  unchanged. Neither baseline database was opened. This is a metadata check,
  not a new full-content hash of the 117 GB backup.
- Selected source, prior/copied candidate source, replay binaries, observer,
  overlay and imported runner pass preservation checks. All **1,283 previously
  manifested files** were rechecked.
- Closed target allocation: **2,596,163,584 bytes (2,475.89 MiB)**. Final free space:
  **29.89 GiB Linux / 66.82 GiB D:**. No W: storage or large backup copy was used.

## Retained checkpoint and next boundary

Target: `/home/rehearsal/replay/candidate-ticket-encoding-2200000`.
Replay executable:
`/home/rehearsal/results/restart-ticket-encoder-replay-2200000-2026-10-09/bin/replay-tests`.
SHA256: `b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245`.
Retain this exact binary and the unchanged identity checks for future resume.
The separate observer is specific to 2,200,000 and must not replace it.

**Resolve storage before another range.** Linux is 0.11 GiB below the unchanged
30 GiB starting floor, although this run finished above its 20 GiB continuation
reserve. Preserve the checkpoint and all evidence. Assess additional Linux
capacity or verified archival to the already-authorized W: storage before any
move or new copy; do not lower the reserve or delete preserved evidence.
No storage migration has been performed.

After resolving capacity, the next bounded endpoint is 2,400,000. Keep the
200,000-block range and existing stop limits; measured durations do not
guarantee future runtime. Require fresh path/capacity checks and a new declared
specification before launch. The next range has not started.

F12 remains open for further history, independent codec/consensus/maintenance
review and restored-identity startup refusal. F11 and other findings are
unaffected. No production selection, activation, keys, public peers or mining
were changed.
