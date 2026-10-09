# Candidate continuation through 2,400,000

9 October 2026. **Passed within the declared 43,968-block continuation.**
The unchanged encoder-candidate executable resumed a verified copy of the
cold-checked 2,356,032 checkpoint and completed through exactly 2,400,000.
Both fresh-process cold checks matched the backup reference captured before
this continuation. All seven commands and the first-run evidence verifier pass,
with no stderr, failed/skipped tests, monitor retries or new stop request.

The preceding [200,000-block attempt](../restart-ticket-encoder-replay-2400000-2026-10-09/README.md)
remains recorded as incomplete at its 30-minute limit. Its [stopped checkpoint
inspection](../restart-ticket-encoder-stopped-2356032-2026-10-09/README.md)
and original STOP are retained unchanged. This new result finishes the remaining
work without rewriting that attempt or extending its allowance.

Replay command timestamps span 07:37:16.401545 to 07:48:19.795684 UTC
(663.394139 seconds, about 11 minutes). The Go test reports 658.05 seconds.
These distinct measurements are retained without attributing their difference
to an unverified cause. Final preservation checks completed at 07:48:35 UTC.
The [specification](spec.md), [plan at start](plan-at-start.md), observer and
verifier preceded execution. [Verification](verification.json), its invocation
and outputs are retained alongside the raw qualification record.

## Historical result

| Endpoint at 2,400,000 | Observed and matched |
| --- | --- |
| Block hash | 0x92765e9c935c6d4ae34011520aa2a8818db9302c2eabc1ac5ea4ce8d25bc60d0 |
| State root | 0x4eb9d6f422b857ef563a780d5f066e5586446a0b71f5e38883263d07c32b15bb |
| Ticket commitment | 0x0cd3ba434244580a38508f6af9efd7b06bd7240f29b9b2aff9a80ef8ad5021c5 |
| Transaction root | 0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421 |
| Receipt root | 0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421 |
| Cumulative difficulty | 11115990864 |
| Transactions / receipts | 0 / 0 |

Complete header RLP and bloom also match. The cold-details process began with
an empty ticket cache, decoded state tickets and recomputed their commitment.
Its **6,425 tickets** agree with the final replay observation; this count is
observed rather than assumed from unavailable historical state in the backup.
The original cold-head helper separately verifies canonical/header/full/fast
heads, body/receipt commitments, cumulative difficulty and state availability.

Together with preceding completed ranges and the preserved partial replay,
this establishes sequential candidate execution through 2,400,000. Legacy
checkpoint shortcuts remain active through 2,680,000: transaction execution and
state/receipt comparisons run, while documented ticket-seal and raw-transaction
shortcuts still apply. This is bounded compatibility evidence, not all-history
qualification or independent consensus review.

## Inputs and preservation

- Private mount/network namespaces, loopback down, offline Go modules and
  enforced read-only backup/checkpoint/closed-target mounts were verified.
- All **1,384 previously manifested files** verify, including the stopped
  attempt and its separate inspection.
- All **1,299 checkpoint files** matched the stopped cold inventory before
  copying. Copied bytes matched, and the original checkpoint remained unchanged.
  Its fresh exact-height cold preflight passed at 2,356,032.
- All **1,383 closed-target files** retained their hashes during inspection.
  The replay identity file remains byte-identical to the checkpoint's.
- Selected and prior/copied candidate source inventories, replay binaries,
  observer, overlay, imported runner and original STOP pass preservation checks.
- Backup metadata for 56,107 files and both baseline metadata inventories are
  unchanged. This is not a new full-content hash of the 117 GB backup. Neither
  baseline database nor the original 2,200,000 checkpoint was opened.
- Closed allocation is **3,035,418,624 bytes (2,894.80 MiB)**. Final free capacity
  is **33.10 GiB Linux / 66.97 GiB D:**, above the unchanged starting floors.
  No W: access or backup-scale copy was performed.

The replay executable was copied byte-for-byte, without rebuilding:
b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245.
The separate Go 1.27.1 observer changes only the stopped observer's height
literal from 2356032 to 2400000; see [observer-change.patch](observer-change.patch).
Its source is also byte-identical to the first attempt's endpoint observer.
Observer SHA256:
668a4e5bb1d6a523ea9adb9c2e824db6e60f4c2608b6b25a837aaf7ba3c6e9e1.
Only the original retained executable performs replay.

## Retained checkpoint and next boundary

Verified target:
/home/rehearsal/replay/candidate-ticket-encoding-2400000-v2.
Original executable copy:
/home/rehearsal/results/restart-ticket-encoder-replay-2400000-v2-2026-10-09/bin/replay-tests.

Preserve both these inputs and the older stopped target, whose name ends in
2400000 but whose actual head is 2,356,032. No older checkpoint was deleted.

Next planned endpoint is **2,500,000**, a 100,000-block interval. This reduces
the former 200,000-block request after its measured time stop; the latest
43,968-block continuation took about 11 minutes. Future runtime still depends
on historical workload and is not guaranteed. Recheck paths/capacity and declare
a new specification before copying. Retain the 30-minute monotonic allowance,
4 GiB sampled target stop, 30/60 GiB starting floors, 20/50 GiB continuation
reserves, exact replay executable and unchanged identity checks. No further
range has started.

F12 remains open for further history, independent codec/consensus/maintenance
review and restored-identity startup refusal. F11 and other findings are
unaffected. Production selection, runtime patches, keys and activation are
unchanged. This work adds only investigation scripts, evidence and documentation.
