# Candidate historical replay through 1,200,000

8 October 2026. **Passed within the declared range.** The retained encoder-candidate
executable resumed a verified copy of the 900,000 checkpoint, executed blocks
900,001 through 1,200,000 and passed both final cold checks. Its saved executable,
source and configuration identity was accepted unchanged.

All seven commands exited zero, with no stderr, failed/skipped tests, monitor
retries or stop requests. The replay command ran from 18:20:36 to 18:47:30 UTC
(about 26 minutes 54 seconds); preservation checks finished at 18:48:04.
The [specification](spec.md), [plan at start](plan-at-start.md) and verifier
preceded execution. [Evidence verification](verification.json) passed on its
first run; its command, exit status and output are retained.

## Historical result

| Endpoint at 1,200,000 | Observed and matched |
| --- | --- |
| Block hash | `0x1af01e640756161654ae77d6de3d0e256928d9c1ea65f049a527aed2241cf8c3` |
| State root | `0x94d4862011241075088efdd4cbb86c8e036d027b4617a93750cee922d2ce09e5` |
| Ticket commitment | `0x95c20c40a3f8d603aa7c1dc34dbc1b720e6fd83a229e9632770364c8cc9e5608` |
| Receipt root | `0x4a1305fea6ba53740f12a3348cfb9d54f623ca35cba17a026eb88a1c435e936b` |
| Cumulative difficulty | `4521667037` |
| Transactions / receipts | `1 / 1` |

Full endpoint header RLP, transaction root and bloom also match the preserved
source reference captured before replay. The cold-details process began with
an empty ticket cache, decoded state tickets and recomputed their commitment.
Its **4,948 tickets** agree with the replay observation; the count is observed,
not assumed from unavailable historical state in the backup. The original
cold-head helper checks all head markers, canonical identity, body/receipt
commitments and TD in a separate process.

Together with the [preceding range](../restart-ticket-encoder-replay-900000-2026-10-08/README.md),
this establishes sequential candidate execution from genesis through 1,200,000.
These heights retain legacy checkpoint shortcuts through 2,680,000: transaction
execution and state/receipt comparisons run, while ticket-seal and raw-transaction
checks remain subject to those documented shortcuts.

## Inputs and preservation

The replay executable was copied byte-for-byte, not rebuilt. A separate Go 1.27.1
observer uses an overlay changing only the preceding observer's height literal
from 900000 to 1200000; the [diff](observer-change.patch), overlay and binary hash
are retained. Only its reference and cold-details tests ran; its replay test
was never invoked. The [runner](run.py) imports the sealed first-range runner's
execution, environment, monitoring and preservation helpers, recording its hash.

- Private mount/network namespaces, loopback down, offline Go modules and
  enforced read-only backup/checkpoint mounts were verified.
- All **436 checkpoint files** matched the preceding cold inventory before
  copying. Copied bytes matched, and the original checkpoint remained unchanged.
  Its exact-height cold preflight passed at 900,000.
- All **586 stopped-target files** retained their SHA256 during cold inspection.
  The replay identity file remains byte-identical to the checkpoint's.
- Backup metadata for 56,107 files and both baseline metadata inventories are
  unchanged. Neither baseline database was opened. This is a metadata check,
  not a new full-content hash of the 117 GB backup.
- Selected source, prior/copied candidate source, replay binaries, observer,
  overlay and imported runner pass preservation checks. All **1,099 previously
  manifested files** were rechecked.
- Closed target allocation: **1,446,739,968 bytes (1,379.72 MiB)**. Final free space:
  **39.85 GiB Linux / 86.53 GiB D:**. No W: storage or large backup copy was used.

## Retained checkpoint and next boundary

Target: `/home/rehearsal/replay/candidate-ticket-encoding-1200000`.
Replay executable:
`/home/rehearsal/results/restart-ticket-encoder-replay-1200000-2026-10-08/bin/replay-tests`.
SHA256: `b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245`.
Retain this exact binary and the unchanged identity checks for future resume.
The separate observer is specific to 1,200,000 and must not replace it.

Next is a bounded continuation through 1,400,000, preserving this checkpoint.
Use 200,000 blocks for the next range because this 300,000-block command took
26 minutes 54 seconds, leaving only about three minutes under the existing
30-minute allowance. This reduces the planned workload without changing the
stop limits; it is not a runtime guarantee. Fresh capacity checks remain required.
The next range has not started.

F12 remains open for further history, independent codec/consensus/maintenance
review and restored-identity startup refusal. F11 and other findings are
unaffected. No production selection, activation, keys, public peers or mining
were changed.
