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
these are not unique code-size totals.

The complete history scan also passed, finishing at 23:28:23 UTC on 23 September.
It checked 15,130,081 blocks including genesis, 419,409,946 transactions and the
same number of receipts, with no absent empty-block receipt records. The final
hash matches `B`, and accumulated difficulty is 63,370,514,513. The history phase
took 9,928.76 seconds. Its calculated block-stream RLP size is 76,291,252,333
bytes (about 71.05 GiB); this excludes receipt/state/database overhead and is
not an export artifact or a complete backup-size estimate. Completed logs and
isolation/exit records are in [the follow-up evidence](evidence/restart-validation-2026-09-24).

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

## Replay continuation and bounded long runs

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
- End height: 1,000,000. This bounded first phase completed successfully, not a full-chain replay.
- Stop file: `/home/rehearsal/replay/STOP-baseline-mainnet`. Creating it requests
  a controlled test failure at the next batch boundary, followed by normal
  chain/database cleanup. Do not terminate WSL to pause a replay.

The first million-block phase finished at 22:14:08 UTC on 23 September after
4,324.80 seconds. Its closed database occupies 1,158,354,931 bytes (about 1.08
GiB), with 4,598 tickets. The resulting commitments are:

- Block: `0x4b0d0d5a0739c801c3d4fe91258d3b9ddf81f471464e221921442ea503d711a6`.
- State: `0x882b7092542a98dfd38dcc253304b17e7d713dcc2aed65222399e0042ec81ad3`.
- Tickets: `0xe8850a91eff584a180740c12f9279a5ce973fb57884c43b75466fbe9d3c3b614`.

After confirming exit code zero, no remaining writer and the retained executable
identity, continuation to **2,000,000** started at 05:40:23 UTC on 24 September.
The preflight successfully reopened and validated height 1,000,000 before
resuming. This phase completed at 07:22:21 UTC, with exit zero after 5,928.57
seconds. It remains within the original checkpoint shortcut range. Its result directory is
`/home/rehearsal/results/restart-replay-two-million-2026-09-24`; the source,
target, executable and stop-file paths above are unchanged. The runner adds
a writer lock and preserves the existing 20 GiB Linux / 50 GiB Windows reserves.
At launch Linux had 76,551,995,392 free bytes and D: had 87,101,820,928 free bytes.
Available host space had fallen since the previous phase, so capacity is checked
throughout instead of assuming the full replay fits.

At 06:42:36 UTC on 24 September, while the separate anchor prototype was being
tested, this replay had reached 1,604,288 with no reported import failure.
Linux had 75,352,391,680 free bytes and D: had 79,522,516,992. The retained replay
executable still matched its original digest. This is an intermediate observation,
not phase-completion evidence; see the [sampled log and capacity record](evidence/restart-anchor-implementation-2026-09-24/replay-progress.txt).

Do not run two writers or edit the retained executable. Any later extension must
first confirm completion/clean shutdown and use that same executable with
explicit resume and a newly chosen end. The old 10,000/100,000 pilot targets
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
[the original evidence directory](evidence/restart-integrity-2026-09-23) and
[the completed-scan/continuation evidence](evidence/restart-validation-2026-09-24).
The completed two-million phase is archived in the
[node rehearsal evidence](evidence/restart-node-rehearsal-2026-09-24).
The closed replay database occupies 2,261,867,399 bytes (about 2.11 GiB), with
5,449 tickets. All final commitments match the source:

- Block: `0x4592c42db8ddf3343dc242770d13de5d158c5e7fc1120870805b1e8731ed43cf`.
- State: `0x3c3a1d38a0f4022f738b8e494becb823867562b7424166043e76df69543f04a2`.
- Tickets: `0x5ec663a1a3e90d9270733d5aa20d99108f4d0d12e5e2c99e71a5a87bf666ba5b`.

At completion Linux had 74,905,395,200 free bytes and D: had 74,497,351,680.
Continuation to the next bounded target, 2,700,000, started at 08:00:40 UTC on
24 September. The read-only preflight validated the complete 2,000,000 head
before writable resume. This phase is running; its results directory is
`/home/rehearsal/results/restart-replay-checkpoint-boundary-2026-09-24` and its
[exact runner](evidence/restart-node-rehearsal-2026-09-24/run-replay-checkpoint-boundary.sh)
is archived. Do not rerun it while the writer is active. This crosses the last legacy checkpoint at
2,680,000; it does not retroactively remove verification shortcuts from earlier
blocks. The source, retained executable, target, identity manifest and per-batch
20 GiB Linux / 50 GiB Windows reserves remain unchanged. Full historical execution
remains pending.

## Next gates

1. Continue bounded execution replay, investigating any failure. Current-state
   traversal and complete structural history validation have both passed;
   neither substitutes for full historical execution.
2. Use the measured export size and progressively measured replay growth to
   choose the full replay layout. W: remains available for verified sequential
   exports/preservation; active LevelDB storage remains on local Linux ext4.
3. Retain explicit distinction between replay with historical checkpoint
   shortcuts and any subsequent stricter verification experiment.
4. Prepare the demonstrated corrections and then the full-state recovery and
   restart-anchor rehearsals under the signing/artifact policy in the main plan.
