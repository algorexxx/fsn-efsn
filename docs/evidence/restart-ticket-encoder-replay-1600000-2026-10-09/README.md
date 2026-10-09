# Candidate historical replay through 1,600,000

9 October 2026. **Passed within the declared range.** The retained encoder-candidate
executable resumed a verified copy of the 1,400,000 checkpoint, executed blocks
1,400,001 through 1,600,000 and passed both final cold checks. Its executable,
source and configuration identity was accepted unchanged.

All seven qualification commands exited zero, with no stderr, failed/skipped
tests, monitor retries or stop requests. The replay command ran from
00:02:31 to 00:21:17 UTC (about 18 minutes 46 seconds); preservation checks
finished at 00:21:47. The [specification](spec.md), [plan at start](plan-at-start.md)
and verifier preceded execution. [Evidence verification](verification.json)
passed on its first run; its command, exit status and output are retained.
The initial read-only capacity/process check is retained in [preflight.json](preflight.json).

## Historical result

| Endpoint at 1,600,000 | Observed and matched |
| --- | --- |
| Block hash | `0x473ddba6b04f6b68265158717b4e18ee7b911ed73f065d30d66cf511acd352cb` |
| State root | `0x0d910f543f4b874e3e338671b3a5f8a44ba2b44bb7033ca0800051bd89e703ce` |
| Ticket commitment | `0x4fcdb07d742285698d7b923a39a2290a66c4458120eae575414098ebfdc2966c` |
| Receipt root | `0x836bb84a0fc3ffeba496f7d7d0bbc3ce49ea61977509e6d7638b503a1ca1523b` |
| Cumulative difficulty | `6544924184` |
| Transactions / receipts | `2 / 2` |

Full endpoint header RLP, transaction root and bloom also match the preserved
source reference captured before replay. The cold-details process began with
an empty ticket cache, decoded state tickets and recomputed their commitment.
Its **5,049 tickets** agree with the replay observation; the count is observed,
not assumed from unavailable historical state in the backup. The original
cold-head helper checks all head markers, canonical identity, body/receipt
commitments and TD in a separate process.

Together with the [preceding range](../restart-ticket-encoder-replay-1400000-2026-10-09/README.md),
this establishes sequential candidate execution from genesis through 1,600,000.
These heights retain legacy checkpoint shortcuts through 2,680,000: transaction
execution and state/receipt comparisons run, while ticket-seal and raw-transaction
checks remain subject to those documented shortcuts.

## Inputs and preservation

The replay executable was copied byte-for-byte, not rebuilt. A separate Go 1.27.1
observer uses an overlay changing only the preceding observer's height literal
from 1400000 to 1600000; the [diff](observer-change.patch), overlay and binary hash
are retained. Only its reference and cold-details tests ran; its replay test
was never invoked. The [runner](run.py) imports the sealed first-range runner's
execution, environment, monitoring and preservation helpers, recording its hash.

- Private mount/network namespaces, loopback down, offline Go modules and
  enforced read-only backup/checkpoint mounts were verified.
- All **743 checkpoint files** matched the preceding cold inventory before
  copying. Copied bytes matched, and the original checkpoint remained unchanged.
  Its exact-height cold preflight passed at 1,400,000.
- All **802 stopped-target files** retained their SHA256 during cold inspection.
  The replay identity file remains byte-identical to the checkpoint's.
- Backup metadata for 56,107 files and both baseline metadata inventories are
  unchanged. Neither baseline database was opened. This is a metadata check,
  not a new full-content hash of the 117 GB backup.
- Selected source, prior/copied candidate source, replay binaries, observer,
  overlay and imported runner pass preservation checks. All **1,172 previously
  manifested files** were rechecked.
- Closed target allocation: **1,839,017,984 bytes (1,753.82 MiB)**. Final free space:
  **36.49 GiB Linux / 80.95 GiB D:**. No W: storage or large backup copy was used.

## Retained checkpoint and next boundary

Target: `/home/rehearsal/replay/candidate-ticket-encoding-1600000`.
Replay executable:
`/home/rehearsal/results/restart-ticket-encoder-replay-1600000-2026-10-09/bin/replay-tests`.
SHA256: `b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245`.
Retain this exact binary and the unchanged identity checks for future resume.
The separate observer is specific to 1,600,000 and must not replace it.

Next is a bounded continuation through 1,800,000, preserving this checkpoint.
Keep the 200,000-block range and existing stop limits; the measured duration
does not guarantee future runtime. Fresh capacity checks remain required.
The next range has not started.

F12 remains open for further history, independent codec/consensus/maintenance
review and restored-identity startup refusal. F11 and other findings are
unaffected. No production selection, activation, keys, public peers or mining
were changed.
