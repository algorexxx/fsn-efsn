# Candidate historical replay through 2,000,000

9 October 2026. **Passed within the declared range.** The retained encoder-candidate
executable resumed a verified copy of the 1,800,000 checkpoint, executed blocks
1,800,001 through 2,000,000 and passed both final cold checks. Its executable,
source and configuration identity was accepted unchanged.

All seven qualification commands exited zero, with no stderr, failed/skipped
tests, monitor retries or stop requests. The replay command ran from
01:27:25 to 01:46:55 UTC (about 19 minutes 30 seconds); preservation checks
finished at 01:47:22. The [specification](spec.md), [plan at start](plan-at-start.md)
and verifier preceded execution. [Evidence verification](verification.json)
passed on its first run; its command, exit status and output are retained.
The initial read-only capacity/process check is retained in [preflight.json](preflight.json).

## Historical result

| Endpoint at 2,000,000 | Observed and matched |
| --- | --- |
| Block hash | `0x4592c42db8ddf3343dc242770d13de5d158c5e7fc1120870805b1e8731ed43cf` |
| State root | `0x3c3a1d38a0f4022f738b8e494becb823867562b7424166043e76df69543f04a2` |
| Ticket commitment | `0x5ec663a1a3e90d9270733d5aa20d99108f4d0d12e5e2c99e71a5a87bf666ba5b` |
| Receipt root | `0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421` |
| Cumulative difficulty | `8599107474` |
| Transactions / receipts | `0 / 0` |

Full endpoint header RLP, transaction root and bloom also match the preserved
source reference captured before replay. The cold-details process began with
an empty ticket cache, decoded state tickets and recomputed their commitment.
Its **5,449 tickets** agree with the replay observation; the count is observed,
not assumed from unavailable historical state in the backup. The original
cold-head helper checks all head markers, canonical identity, body/receipt
commitments and TD in a separate process.

Together with the [preceding range](../restart-ticket-encoder-replay-1800000-2026-10-09/README.md),
this establishes sequential candidate execution from genesis through 2,000,000.
These heights retain legacy checkpoint shortcuts through 2,680,000: transaction
execution and state/receipt comparisons run, while ticket-seal and raw-transaction
checks remain subject to those documented shortcuts.

## Inputs and preservation

The replay executable was copied byte-for-byte, not rebuilt. A separate Go 1.27.1
observer uses an overlay changing only the preceding observer's height literal
from 1800000 to 2000000; the [diff](observer-change.patch), overlay and binary hash
are retained. Only its reference and cold-details tests ran; its replay test
was never invoked. The [runner](run.py) imports the sealed first-range runner's
execution, environment, monitoring and preservation helpers, recording its hash.

- Private mount/network namespaces, loopback down, offline Go modules and
  enforced read-only backup/checkpoint mounts were verified.
- All **941 checkpoint files** matched the preceding cold inventory before
  copying. Copied bytes matched, and the original checkpoint remained unchanged.
  Its exact-height cold preflight passed at 1,800,000.
- All **1,004 stopped-target files** retained their SHA256 during cold inspection.
  The replay identity file remains byte-identical to the checkpoint's.
- Backup metadata for 56,107 files and both baseline metadata inventories are
  unchanged. Neither baseline database was opened. This is a metadata check,
  not a new full-content hash of the 117 GB backup.
- Selected source, prior/copied candidate source, replay binaries, observer,
  overlay and imported runner pass preservation checks. All **1,246 previously
  manifested files** were rechecked.
- Closed target allocation: **2,282,467,328 bytes (2,176.73 MiB)**. Final free space:
  **32.36 GiB Linux / 69.97 GiB D:**. No W: storage or large backup copy was used.

## Retained checkpoint and next boundary

Target: `/home/rehearsal/replay/candidate-ticket-encoding-2000000`.
Replay executable:
`/home/rehearsal/results/restart-ticket-encoder-replay-2000000-2026-10-09/bin/replay-tests`.
SHA256: `b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245`.
Retain this exact binary and the unchanged identity checks for future resume.
The separate observer is specific to 2,000,000 and must not replace it.

Next is a bounded continuation through 2,200,000, preserving this checkpoint.
Keep the 200,000-block range and existing stop limits; the measured duration
does not guarantee future runtime. Fresh capacity checks remain required.
The next range has not started.

F12 remains open for further history, independent codec/consensus/maintenance
review and restored-identity startup refusal. F11 and other findings are
unaffected. No production selection, activation, keys, public peers or mining
were changed.
