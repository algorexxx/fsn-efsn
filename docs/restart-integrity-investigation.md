# Complete integrity checks and replay — 23 September 2026

The Linux investigation was committed as `bf71410` on
`codex/restart-investigation-wip`. This follow-up adds read-only full-data checks
and a bounded historical replay runner. Production node code is unchanged.

## Complete-data checks

`TestPreservedStateIntegrity` traverses every reachable account and its storage,
rebuilds their Merkle roots using a separate stack trie, and checks every
referenced code/native-data blob against its committed Keccak hash. Iterator
errors are checked for each trie. This is stronger than opening the root or
looking up selected accounts, but still depends on this client's trie/RLP
implementation. Address-preimage coverage and unreachable database records are
not included.

`TestPreservedHistoryIntegrity` scans canonical heights zero through 15,130,080.
It checks canonical block identity, number indexes, parent links, transaction
commitments, decoded receipt commitments/blooms, and accumulated difficulty. It
also totals the RLP block-stream size to inform export/replay capacity planning.
An absent receipt record is allowed only for a transaction-free block with an
empty receipt root, and is counted explicitly. Malformed stored receipt data
does not take that exception.

The history scan does not execute transactions, verify signatures/ticket
selection, validate every historical state, or inventory transaction lookup
indexes. Fusion uses the header's uncle-hash field for its PoS commitment;
ordinary Ethereum uncle-root validation would be inappropriate here. Its
`VerifyUncles` currently returns nil. These checks must not be described as full
independent consensus verification.

Checker tests exercise intact in-memory data and deliberately missing/corrupt
account roots, storage roots, code, bodies, receipts, total difficulty,
transactions and parent links. All eleven cases passed before the real scan.

The full scan started at 20:21:26 UTC in a private mount/network namespace,
with the verified database mounted read-only. Its live log is
`/home/rehearsal/results/restart-integrity-2026-09-23/full-integrity.txt`.
Completion is not yet established; results must be recorded before closing this
validation gate.

## Replay pilot

The unchanged client replayed genesis through block 10,000 in a newly created
database at `/home/rehearsal/replay/baseline-10000`. The source remained mounted
read-only, with no network, node service, or signing key involved.

| Item | Observed |
| --- | --- |
| Runtime | 71.95 seconds, while the separate state scan was active |
| Logical database size after clean shutdown | 117,083,563 bytes |
| Final block hash | `0x1830e440e17cda3a26d02ea650331a584d58a499cbbd3821c622568c8de9b470` |
| Final state root | `0xc85623ffdf98796fb39d437ceff4626b7aa56bb5ee12c8b1491a7524ad85cfbf` |
| Ticket commitment | `0x0f8a8be52d2df5f43c50a33049c1594252d48c6fb523fc35adac5c27750c5456` |
| Tickets | 1,817 |
| Legacy checkpoint range retained | Through height 2,680,000 |

This is a successful baseline execution pilot. The legacy checkpoint range
still skips normal ticket-seal checks and raw-transaction validation, while
retaining the checks the old code performs before that shortcut. The pilot
therefore does not establish independent verification of ticket consensus.
Later transaction volume and state size can differ sharply; do not extrapolate
its runtime or bytes per block into a reliable full-replay estimate.

The existing CLI import handler logs `ImportChain` errors but can return nil.
The rehearsal runner instead fails on an import error or unexpected head and
checks the resulting ticket commitment. It accepts only a new output directory;
existing databases cannot be overwritten by this runner. Before each 128-block
batch it checks reserves of 50 GiB on the Windows host drive and 20 GiB inside
Linux. Cleanup stops the chain and closes the output database so a controlled
test failure does not intentionally discard pending state.

D: is a Samsung SSD 970 EVO 500GB NVMe device, reported healthy by Windows.
The pilot left 78,689,280,000 bytes available in Linux and 151,710,142,464 bytes
on D:. The 200 GB virtual-disk capacity is a separate limit from host free space.
No additional full database, network archive, or long replay has been assumed
to fit. The existing C: preservation copy and explorer gateway remain intact.

## Historical reconstruction check

The read-only `TestPreservedTicketReconstruction` validates the signatures and
ticket selection of actual headers 15,129,955 through 15,130,080, then repeats
each validation with its parent state deliberately unavailable and the ticket
cache evicted. At the final header it also forces reconstruction across 16 and
126 missing state roots, back to retained state 15,129,953. All 128 cases pass
on the unchanged client, with identical selected/retreated tickets. These recent
heights are outside the legacy checkpoint range. No blocks are signed or written.
This is real historical reconstruction coverage; it does not include an expiry
boundary, for which the synthetic tests remain the demonstrated regression.

The existing miner package tests do not compile on the baseline: they reference
removed `ethash`/`clique` symbols, the old `newWorker` signature and old balance
APIs. DaTong has no package tests. This pre-existing test-suite gap is recorded
in `baseline-package-tests.txt`; the dedicated restart tests exercise the actual
miner through an external test package without silently repairing or excluding
those stale files.

Completed logs, isolation records and source hashes are preserved in
[the evidence directory](evidence/restart-integrity-2026-09-23). The complete
integrity scan's final evidence remains pending.

## Next gates

1. Finish the state and complete-history scans; investigate any failure instead
   of treating a partial traversal as success.
2. Use the measured export size and progressively measured replay growth to
   choose the full replay layout. W: remains available for verified sequential
   exports/preservation; active LevelDB storage remains on local Linux ext4.
3. Retain explicit distinction between replay with historical checkpoint
   shortcuts and any subsequent stricter verification experiment.
4. Prepare the demonstrated corrections and then the full-state recovery and
   restart-anchor rehearsals under the signing/artifact policy in the main plan.
