# Complete integrity checks and replay — 23 September 2026

The Linux investigation was committed as `bf71410` on
`codex/restart-investigation-wip`. This follow-up adds read-only full-data checks
and a bounded historical replay runner, committed as `d82a229`. All baseline
data checks and replay use unchanged production code. The subsequent
[corrections](restart-corrections.md) are tested in a separate source tree.

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
The complete current-state scan passed in 1,287.81 seconds: 801,355 accounts,
2,886,305 storage leaves, and 33,437 code/native-data references totalling
262,368,983 referenced bytes. The rebuilt root matches the observed head and
no missing/corrupt reachable data was reported. References can share blobs;
these are not unique code-size totals. The complete history scan is still in
progress; that separate gate remains open.

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
checks the resulting ticket commitment. The initial pilot accepted only a new
output directory; the later validated resume mode is described below. Before each 128-block
batch it checks reserves of 50 GiB on the Windows host drive and 20 GiB inside
Linux. Cleanup stops the chain and closes the output database so a controlled
test failure does not intentionally discard pending state.

D: is a Samsung SSD 970 EVO 500GB NVMe device, reported healthy by Windows.
The pilot left 78,689,280,000 bytes available in Linux and 151,710,142,464 bytes
on D:. The 200 GB virtual-disk capacity is a separate limit from host free space.
No additional full database, network archive, or long replay has been assumed
to fit. The existing C: preservation copy and explorer gateway remain intact.

A second fresh replay through 100,000 blocks passed in 397.06 seconds
(20:46:38–20:53:15 UTC). Its closed database occupies 227,214,790 bytes.
The final hash is `0x0e4a4045c06984472f86bb8f1e40bb70dee87b6227877ffcaeab7624db745cd2`,
root `0x95697b558879524bead323328c9e97adce259ac7047a2140107704bf930d4741`,
and ticket commitment `0x1860459771b267e3b319ed899deb55a4ab973562f0d923309263244e1630020d`
with 2,630 tickets. Both pilot databases are retained. The smaller incremental
growth illustrates why a fixed bytes-per-block estimate from the first pilot
would have been misleading; it still does not establish the full replay size.

## Replay continuation and active long run

The later runner records the exact executable hash, source genesis/head and
source/replay configurations in a target manifest. Reuse requires explicit
`FUSION_RESTART_REPLAY_RESUME=1` and an identical manifest. Before writable open,
it checks the target's genesis/configuration, all three head pointers, head body
and receipt commitments, cumulative difficulty and available head ticket state
against the preserved source. Startup must retain that validated head. A missing
state after an unclean termination fails preflight; it does not authorize a
silent rewind or manual manifest rewrite.

Continuation testing created a fresh database through 1,024, rejected accidental
reuse and an end below the existing head, stopped through the explicit stop-file
path, then resumed to 10,000 with the same hash/root/ticket commitment as the
original fresh pilot. A deliberately mismatched executable identity was also
rejected; the test restored the original manifest afterward. These intentional
nonzero test exits are expected rejection evidence, not successful replays.

At 21:02:03 UTC the first million-block baseline phase started in a new database:

- Source: `/home/rehearsal/data/efsn/chaindata`, read-only mount in a private
  mount/network namespace.
- Retained executable: `/home/rehearsal/replay-resume-tests`, compiled from the
  baseline production tree with the updated replay harness.
- Target: `/home/rehearsal/replay/baseline-mainnet`.
- Results: `/home/rehearsal/results/restart-replay-million-2026-09-23`.
- End height: 1,000,000. This is a bounded first phase, not a full-chain success.
- Stop file: `/home/rehearsal/replay/STOP-baseline-mainnet`. Creating it requests
  a controlled test failure at the next batch boundary, followed by normal
  chain/database cleanup. Do not terminate WSL to pause a replay.

Do not run two writers or edit this running executable. A later extension must
first confirm completion/clean shutdown and use that same retained executable
with explicit resume and a newly chosen end. The old 10,000/100,000 pilot targets
predate the identity manifest and are not eligible for automatic resume.
Full replay remains conditional on continued storage checks and results.

The exact machine-specific runner scripts are archived in
[the evidence runners](evidence/restart-integrity-2026-09-23/runners). Invoke
isolation scripts through `wsl -d FusionRehearsal -u root --exec unshare --mount
--net --propagation private -- bash <script-path>`. Review their target/result
paths before reusing them; most intentionally reject an existing target.

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
