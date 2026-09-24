# Interrupted chain-write rehearsal

24 September 2026. Extends the [node-process rehearsal](restart-node-rehearsal.md)
and [inactive anchor prototype](restart-anchor-implementation.md). The mainnet
anchor remains unset. All databases and signing keys in this experiment are
synthetic and disposable; the baseline historical replay is unchanged.

## Reproduced defect

On source base `c0299b0`, an ordinary compatible reorganization published its new
canonical blocks one at a time through `writeHeadBlock`, then deleted obsolete
transaction lookups in a later batch. Abruptly exiting between those operations
left a partially switched chain on disk.

The fixture has one fixed anchor, four canonical successors and a competing
five-block continuation sharing that anchor. The first four competing blocks
are already stored and executed as a side branch. The fifth has greater total
difficulty and triggers the reorganization. Every block is constructed and
imported through actual DaTong validation with the public key-1 synthetic account.
The seed uses the existing local-preservation callback to retain the old branch
at equal total difficulty; the final successor is explicitly checked to be heavier.

Interruption reproduced two outcomes:

- Eight boundaries left an intermediate new-branch block as the persisted head,
  rather than either the previous head or the complete winning tip. Cold startup
  accepted it, and the restart-readiness check returned success. Canonical entries
  from the old suffix could still remain above that intermediate head.
- Two boundaries had published the final new head but retained obsolete
  transaction lookup entries from the replaced branch. Raw lookup metadata was
  inconsistent with the completed canonical switch.

The old client failed ten of the eighteen before/after cuts around its nine
reorganization writes. Linear successor import and rollback controls passed.
The retained second reproduction opens the blockchain before its assertions,
demonstrating that the partial head can actually pass startup/readiness; this
is not only a hypothetical inspection of keys.

This does not bypass the fixed anchor: both branches share it. It is an inherited
persistence defect during an otherwise permitted fork switch. The anchor alone
cannot establish that an eligible database represents a completed operation.

## Narrow correction

`core/blockchain.go` now stages all changed canonical indexes, new transaction
lookups, removed transaction lookups, canonical-tail cleanup and all three head
markers in one LevelDB batch. The block and state are stored before that batch.
In-memory head publication follows successful batch completion, using a shared
helper also called by ordinary head advancement.

The per-block legacy checkpoint check formerly performed by `writeHeadBlock`
remains in the staging loop. A failure returns before publishing the staged
indexes. An empty replacement chain is rejected instead of indexing an empty
slice. Anchor checks, difficulty comparison, ticket selection, transaction
execution and balances policy are unchanged.

Propagating that existing checkpoint error also closes the previously reproduced
`checkpoint_stored_fork` inconsistency, even with the separate anchor disabled.
The first broader test runs therefore failed an old characterization that still
expected that defect. Its updated regression now requires an error and verifies
all accepted heads, canonical indexes, transaction lookups, linked ancestry and
absence of a head event. This is an intentional correction to ignored-error
handling; no legacy checkpoint height or verification shortcut was extended.
Header-only and other legacy checkpoint gaps still require the separate anchor.

The existing caller subsequently repeats the final-tip index write. That write
is idempotent and remains covered by interruption tests; it is not part of a
second partial chain transition. The reorganization trace is now four writes:
block data, state data, the complete canonical switch, and the repeated tip write.
No database schema, journal or launch checkpoint was added.

## Fault-injection coverage

`TestRestartCrashBoundaries` is explicitly enabled by
`FUSION_RESTART_CRASH_REHEARSAL=1`. A test-only database wrapper records every
`Put`, `Delete` and `Batch.Write` after arming. Each scenario first runs to
completion to enumerate its actual write boundaries. Fresh child processes then
exit with code 86 immediately before and after every boundary, without executing
Go defers or blockchain/database cleanup. A second fresh process reopens each
database and verifies recovery.

The wrapper delegates real writes to LevelDB and uses the existing `HookedBatch`
to label marker/index batches. It does not add production injection points or
write synthetic subsets of a LevelDB batch. A child that misses its requested
boundary, times out, reports a race or exits for another reason fails the test.

| Scenario | Final write boundaries | Abrupt-exit cases per run | Required recovery |
| --- | ---: | ---: | --- |
| Linear block import | 3 | 6 | Old or complete successor head; reimport reaches successor |
| Compatible heavier reorganization | 4 | 8 | Old branch or complete new branch, with matching canonical/transaction/receipt indexes; reimport reaches winning tip |
| Explicit rollback | 1 | 2 | All head markers remain old or move together to the rollback target; reimport restores the original valid suffix |

Checks cover persisted and reopened full/header/fast heads, canonical indexes
through both candidate suffixes, transaction lookup metadata, actual transaction
and receipt resolution, available ticket state, anchor readiness and successful
forward recovery. Rollback intentionally retains its canonical suffix indexes
under the existing API contract; its test distinguishes that behavior from the
canonical replacement performed by a reorganization.

The expectations compare the interrupted store to the separately constructed
complete candidate branches, not to whichever partial head happened to reopen.
They are implementation-to-implementation state checks, not independent golden
vectors for every consensus transition.

## Results and limits

The original failures and corrected Windows/Linux results, source and binary
identities and exact runners belong in the
[evidence directory](evidence/restart-crash-rehearsal-2026-09-24).

The final complete Windows restart suite, including the sixteen crash cuts,
passed in 100.921 seconds. The complete Linux synthetic suite passed with both
the crash and node-service rehearsals enabled under the race detector. Two
additional crash repetitions passed, for 48 successful Linux write-boundary cuts
on the final source with no reported race. The full Linux node binary built
successfully. Existing unrelated miner/rawdb package-test compilation failures
remain documented; this is not a whole-repository test claim.

This establishes process-exit recovery at the observed database API boundaries
for short synthetic chains using archive-style state persistence and LevelDB
without a freezer. It does not establish:

- Persistence through power loss, a torn filesystem write or an interruption
  inside LevelDB's own atomic write implementation; default writes are not being
  upgraded to an fsync durability guarantee.
- Pruned-state recovery, ancient/freezer consistency or full-state mainnet replay.
- Interrupted reset or fast-sync pivot operations. The subsequent
  [explicit-rewind rehearsal](restart-rewind-rehearsal.md) reproduces and corrects
  the separate `SetHead` marker/deletion ordering gap, including six synthetic
  rewind cases. The later [reset/pivot rehearsal](restart-reset-pivot-rehearsal.md)
  covers those publication boundaries too, with state-download/genesis-sync and
  freezer limits retained. The rollback test alone does not cover `SetHead`.
- Very deep reorganizations, a shorter-but-heavier replacement, or the maximum
  memory cost of staging a large canonical switch in one batch. The existing
  reorganization already retains both block lists; the added batch also needs
  measurement under a realistic transaction load. No consensus reorg limit was
  introduced to avoid this work.
- A simultaneous, atomic snapshot across all in-memory/RPC readers while a
  running node changes heads. This experiment asserts durable recovery after exit.

The [main plan](restart-plan.md) retains these gates, full-state bridge construction,
accounting review and independent operator review before production activation.
