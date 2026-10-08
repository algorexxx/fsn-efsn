# Candidate historical replay through 900,000

8 October 2026. **Passed within the declared range.** The retained encoder-candidate
executable resumed a verified copy of the 600,000 checkpoint, executed blocks
600,001 through 900,000 and passed both final cold checks. Its saved executable,
source and configuration identity was accepted unchanged.

All seven commands exited zero, with no stderr, failed/skipped tests, monitor
retries or stop requests. The replay command ran from 17:47:25 to 18:10:42 UTC
(about 23 minutes 17 seconds); preservation checks finished at 18:11:06.
The [specification](spec.md), [plan at start](plan-at-start.md) and verifier
preceded execution. [Evidence verification](verification.json) passed on its
first run; its command, exit status and output are retained.

## Historical result

| Endpoint at 900,000 | Observed and matched |
| --- | --- |
| Block hash | `0x1e75da884b3673a3baef096fe43b4df93c4c4911cfaf79770da9ec8dbd5bd7c1` |
| State root | `0x7f7cc37f43d212924c68a8f4bcb295aa7726e8a16ceb9811135e570ba7a81785` |
| Ticket commitment | `0xe70762294e2636c3b0900ddd25c909ecdd77202f2b301c90c57b73edfa49bf06` |
| Receipt root | `0x8787cd0c17daa542fd4da49510c77e3ce601672a0dfb8595acf27fc534470f54` |
| Cumulative difficulty | `3049755450` |
| Transactions / receipts | `2 / 2` |

Full endpoint header RLP, transaction root and bloom also match the preserved
source reference captured before replay. The cold-details process began with
an empty ticket cache, decoded state tickets and recomputed their commitment.
Its **4,032 tickets** agree with the replay observation; the count is observed,
not assumed from unavailable historical state in the backup. The original
cold-head helper checks all head markers, canonical identity, body/receipt
commitments and TD in a separate process.

Together with the [preceding range](../restart-ticket-encoder-replay-600000-2026-10-08/README.md),
this establishes sequential candidate execution from genesis through 900,000.
These heights retain legacy checkpoint shortcuts through 2,680,000: transaction
execution and state/receipt comparisons run, while ticket-seal and raw-transaction
checks remain subject to those documented shortcuts.

## Inputs and preservation

The replay executable was copied byte-for-byte, not rebuilt. A separate Go 1.27.1
observer uses an overlay changing only the preceding observer's height literal
from 600000 to 900000; the [diff](observer-change.patch), overlay and binary hash
are retained. Only its reference and cold-details tests ran; its replay test
was never invoked. The [runner](run.py) imports the sealed first-range runner's
execution, environment, monitoring and preservation helpers, recording its hash.

- Private mount/network namespaces, loopback down, offline Go modules and
  enforced read-only backup/checkpoint mounts were verified.
- All **297 checkpoint files** matched the preceding cold inventory before
  copying. Copied bytes matched, and the original checkpoint remained unchanged.
  Its exact-height cold preflight passed at 600,000.
- All **436 stopped-target files** retained their SHA256 during cold inspection.
  The replay identity file remains byte-identical to the checkpoint's.
- Backup metadata for 56,107 files and both baseline metadata inventories are
  unchanged. Neither baseline database was opened. This is a metadata check,
  not a new full-content hash of the 117 GB backup.
- Selected source, prior/copied candidate source, replay binaries, observer,
  overlay and imported runner pass preservation checks. All **1,063 previously
  manifested files** were rechecked.
- Closed target allocation: **1,112,977,408 bytes (1,061.42 MiB)**. Final free space:
  **41.25 GiB Linux / 87.19 GiB D:**. No W: storage or large backup copy was used.

## Retained checkpoint and next boundary

Target: `/home/rehearsal/replay/candidate-ticket-encoding-900000`.
Replay executable:
`/home/rehearsal/results/restart-ticket-encoder-replay-900000-2026-10-08/bin/replay-tests`.
SHA256: `b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245`.
Retain this exact binary and the unchanged identity checks for future resume.
The separate observer is specific to 900,000 and must not replace it.

Next is a bounded continuation through 1,200,000 with fresh capacity checks
and the same stop limits, preserving this checkpoint. It has not started.
F12 remains open for further history, independent codec/consensus/maintenance
review and restored-identity startup refusal. F11 and other findings are
unaffected. No production selection, activation, keys, public peers or mining
were changed.
