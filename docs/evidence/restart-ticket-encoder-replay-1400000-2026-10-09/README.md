# Candidate historical replay through 1,400,000

9 October 2026 (Europe/Stockholm). **Passed within the declared range.**
The retained encoder-candidate executable resumed a verified copy of the
1,200,000 checkpoint, executed blocks 1,200,001 through 1,400,000 and passed
both final cold checks. Its executable, source and configuration identity
was accepted unchanged.

All seven qualification commands exited zero, with no stderr, failed/skipped
tests, monitor retries or stop requests. The replay command ran from
22:45:11 to 23:03:44 UTC on 8 October (about 18 minutes 33 seconds);
preservation checks finished at 23:04:08 UTC. The 200,000-block range left
more margin under the unchanged 30-minute allowance than the preceding
300,000-block range.

The [specification](spec.md), [plan at start](plan-at-start.md) and verifier
preceded execution. [Evidence verification](verification.json) passed on its
first run; its command, exit status and output are retained. Before launch,
an inline Python read-only capacity check failed to parse because of shell
quoting. Direct read-only commands then confirmed capacity and no conflicting
process; the launcher repeated the capacity/path checks. This preparation
error is recorded in [preflight-note.json](preflight-note.json); no replay
was started by that failed command.

## Historical result

| Endpoint at 1,400,000 | Observed and matched |
| --- | --- |
| Block hash | `0x85b500fe1186cb8a4140beb38e50c6dd9e4f7efa53e7703741d3781455cc71c1` |
| State root | `0x3187a039f732f31bb9003793ceb26b3fbf55617158165f0933e4ef21a3525339` |
| Ticket commitment | `0x2806ef3d360f701f257c38b85dbbc13a3aea8eec10454c358ef032847b677328` |
| Receipt root | `0x474f1d25f07161b0b7d37ddfd1dc1fbb8513a25e9240087dddcb0919bd81cf9f` |
| Cumulative difficulty | `5541204113` |
| Transactions / receipts | `2 / 2` |

Full endpoint header RLP, transaction root and bloom also match the preserved
source reference captured before replay. The cold-details process began with
an empty ticket cache, decoded state tickets and recomputed their commitment.
Its **4,814 tickets** agree with the replay observation; the count is observed,
not assumed from unavailable historical state in the backup. The original
cold-head helper checks all head markers, canonical identity, body/receipt
commitments and TD in a separate process.

Together with the [preceding range](../restart-ticket-encoder-replay-1200000-2026-10-08/README.md),
this establishes sequential candidate execution from genesis through 1,400,000.
These heights retain legacy checkpoint shortcuts through 2,680,000: transaction
execution and state/receipt comparisons run, while ticket-seal and raw-transaction
checks remain subject to those documented shortcuts.

## Inputs and preservation

The replay executable was copied byte-for-byte, not rebuilt. A separate Go 1.27.1
observer uses an overlay changing only the preceding observer's height literal
from 1200000 to 1400000; the [diff](observer-change.patch), overlay and binary hash
are retained. Only its reference and cold-details tests ran; its replay test
was never invoked. The [runner](run.py) imports the sealed first-range runner's
execution, environment, monitoring and preservation helpers, recording its hash.

- Private mount/network namespaces, loopback down, offline Go modules and
  enforced read-only backup/checkpoint mounts were verified.
- All **586 checkpoint files** matched the preceding cold inventory before
  copying. Copied bytes matched, and the original checkpoint remained unchanged.
  Its exact-height cold preflight passed at 1,200,000.
- All **743 stopped-target files** retained their SHA256 during cold inspection.
  The replay identity file remains byte-identical to the checkpoint's.
- Backup metadata for 56,107 files and both baseline metadata inventories are
  unchanged. Neither baseline database was opened. This is a metadata check,
  not a new full-content hash of the 117 GB backup.
- Selected source, prior/copied candidate source, replay binaries, observer,
  overlay and imported runner pass preservation checks. All **1,135 previously
  manifested files** were rechecked.
- Closed target allocation: **1,647,353,856 bytes (1,571.04 MiB)**. Final free space:
  **38.26 GiB Linux / 84.44 GiB D:**. No W: storage or large backup copy was used.

## Retained checkpoint and next boundary

Target: `/home/rehearsal/replay/candidate-ticket-encoding-1400000`.
Replay executable:
`/home/rehearsal/results/restart-ticket-encoder-replay-1400000-2026-10-09/bin/replay-tests`.
SHA256: `b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245`.
Retain this exact binary and the unchanged identity checks for future resume.
The separate observer is specific to 1,400,000 and must not replace it.

Next is a bounded continuation through 1,600,000, preserving this checkpoint.
Keep the 200,000-block range and existing stop limits; the measured duration
does not guarantee future runtime. Fresh capacity checks remain required.
The next range has not started.

F12 remains open for further history, independent codec/consensus/maintenance
review and restored-identity startup refusal. F11 and other findings are
unaffected. No production selection, activation, keys, public peers or mining
were changed.
