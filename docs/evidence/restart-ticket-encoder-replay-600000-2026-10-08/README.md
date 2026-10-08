# Candidate historical replay through 600,000

8 October 2026. **Passed within the declared range.** The retained encoder-candidate
executable resumed a verified copy of the 300,000 checkpoint, executed blocks
300,001 through 600,000 and passed both final cold checks. The saved executable,
source and configuration identity was accepted unchanged.

All seven commands exited zero, with no stderr, failed/skipped tests, monitor
retries or stop requests. The replay command ran from 16:50:37 to 17:10:43 UTC
(20 minutes 6 seconds); final preservation checks finished at 17:11:00.
The [specification](spec.md), [plan at start](plan-at-start.md) and verifier
preceded execution. [Evidence verification](verification.json) passed on its
first run; its command, exit status and output are retained.

## Historical result

| Endpoint at 600,000 | Observed and matched |
| --- | --- |
| Block hash | `0xf211256464eea17ef5f70beca19412714aa0ab1efe1daacee14d767f7a4d9727` |
| State root | `0x4f358efc875a6fde257842ea0bc2a7eab737b3f2b0ca511451378b86097f98db` |
| Ticket commitment | `0x673523ef6886b2b90aa10aabd8df338e99557d279312379d1c46cf4fddeebe91` |
| Receipt root | `0xad07a6a4b6d83e1f8fa95e6148b86245a62bfebd5470842c8f27c97484387975` |
| Cumulative difficulty | `1894872741` |
| Transactions / receipts | `1 / 1` |

The full endpoint header RLP, transaction root and bloom also match the preserved
source reference captured before replay. The cold-details process began with
an empty ticket cache, decoded state tickets and recomputed the commitment.
Its **3,498 tickets** agree with the replay observation; the count is observed,
not an assumed expectation from unavailable historical state in the backup.
The original cold-head helper checks all head markers, canonical identity,
body/receipt commitments and TD in a separate process.

Together with the [preceding range](../restart-ticket-encoder-replay-300000-2026-10-08/README.md),
this establishes sequential candidate execution from genesis through 600,000.
These heights retain legacy checkpoint shortcuts through 2,680,000: transaction
execution and state/receipt comparisons run, while ticket-seal and raw-transaction
checks remain subject to those documented shortcuts.

## Inputs and preservation

The replay executable was copied byte-for-byte, not rebuilt. A separate Go 1.27.1
observer uses an overlay changing only the previous observer's height literal
from 300000 to 600000; the [diff](observer-change.patch), overlay and binary hash
are retained. Only its reference and cold-details tests ran. Its replay test
was never invoked. The [runner](run.py) imports the sealed first-range runner's
execution, environment, monitoring and preservation helpers, recording its hash.

- Private mount/network namespaces, loopback down, offline Go modules and
  enforced read-only backup/checkpoint mounts were verified.
- All **161 checkpoint files** matched the preceding cold inventory before
  copying. Copied bytes matched, and the original checkpoint remained unchanged.
  Its exact-height cold preflight passed at 300,000.
- All **297 stopped-target files** retained their SHA256 during cold inspection.
  The replay identity file remains byte-identical to the checkpoint's.
- Backup metadata for 56,107 files and both baseline metadata inventories are
  unchanged. Neither baseline database was opened. This is a metadata check,
  not a new full-content hash of the 117 GB backup.
- Selected source, prior/copied candidate source, replay binaries, observer,
  overlay and imported runner pass preservation checks. All **1,027 previously
  manifested files** were rechecked.
- Closed target allocation: **739,811,328 bytes (705.54 MiB)**. Final free space:
  **42.35 GiB Linux / 88.51 GiB D:**. No W: storage or large backup copy was used.

## Retained checkpoint and next boundary

Target: `/home/rehearsal/replay/candidate-ticket-encoding-600000`.
Replay executable:
`/home/rehearsal/results/restart-ticket-encoder-replay-600000-2026-10-08/bin/replay-tests`.
SHA256: `b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245`.
Retain this exact binary and the unchanged identity checks for future resume.
The separate observer is specific to 600,000 and must not replace it.

Next is a bounded continuation through 900,000 with fresh capacity checks and
the same stop limits, preserving this checkpoint. It has not started.
F12 remains open for further history, independent codec/consensus/maintenance
review and restored-identity startup refusal. F11 and other findings are
unaffected. No production selection, activation, keys, public peers or mining
were changed.
