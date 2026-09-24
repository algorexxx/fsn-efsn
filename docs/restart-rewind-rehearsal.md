# Interrupted explicit-rewind rehearsal

24 September 2026. Extends the [interrupted-write investigation](restart-crash-rehearsal.md)
on source base `71872b8`. All signing and databases are synthetic and disposable.
The production anchor remains unset; the preserved backup and baseline replay
executable are unchanged.

## Reproduced failures

`BlockChain.SetHead` previously called `HeaderChain.SetHead`, which persisted the
header pointer once per removed height. It then committed accumulated header,
body, difficulty and canonical-index deletions. Only afterwards did it write the
full and fast pointers, separately. A crash could therefore leave the latter
pointers above the header pointer, or referring to data already deleted.

The original client failed 30 of 36 before/after write cuts across three cases:
a rewind above the anchor, a rewind below it, and a rewind with full/header/fast
heads initially at different heights. Sixteen failures had a block pointer above
the header head; twelve had a pointer to a deleted block. The existing anchor
preflight correctly refused these 28 databases. Two other cuts reopened with a
coherent intermediate header head rather than either complete endpoint.

This is an availability and persistence defect during an explicitly requested
rewind, not acceptance of an incompatible anchor. Weakening startup checks would
conceal the interrupted operation rather than prevent it.

Additional fault cases removed a historical state root or body in the disposable
store. State repair could panic when it reached a missing ancestor: its loop
dereferenced the result of `GetBlock` without checking for nil. The retained
`pruned-initial-windows.txt` shows that panic after the atomic rewind correction
but before the separate repair-loop guard was added.

## Correction

The existing deletion batch now also contains all three final head pointers.
`HeaderChain` walks backwards using a local candidate header, stages deletions,
and invokes a private callback to stage full/fast pointers before committing.
The callback uses the existing state-repair and genesis-fallback policy. Memory
heads and cache cleanup follow the commit.

The public `HeaderChain.SetHead` signature is unchanged. Its header-only path
uses the same batch with no block-head callback. Only key/value-store mutations
are made by these paths; this does not add coordinated ancient-store truncation.
The implementation already accumulated the entire deletion set, so this change
does not introduce another large history buffer or a persistent operation journal.

State repair now reports a missing ancestor or unavailable genesis state instead
of dereferencing nil or walking below genesis. `SetHead` retains its existing
fallback to genesis on repair failure. Ordinary startup receives the repair
error; the anchor preflight remains unchanged and still runs before that repair.

No consensus rule, fork weight, balance policy, anchor selection or database
schema changes. Receipt records and raw transaction-lookup metadata left by the
legacy rewind are not newly purged; deleted canonical transactions must stop
resolving, and reimport must restore correct transaction/receipt resolution.

## Rehearsal cases

The existing `TestRestartCrashBoundaries` harness records real LevelDB writes,
exits child processes immediately before or after each write, and verifies the
store in a fresh process. Each rewind now has one database write and two cuts.

Let `A` be the fixed synthetic anchor and `A+1` through `A+4` its accepted suffix.

| Case | Target | Expected full / fast / header after completion |
| --- | --- | --- |
| Ordinary rewind | A+2 | A+2 / A+2 / A+2 |
| Below-anchor rewind | A-1 | A-1 / A-1 / A-1; readiness rejected |
| Split heads, initially A+1 / A+3 / A+4 | A+2 | A+1 / A+2 / A+2; lagging full head is not advanced |
| A+2 state root removed | A+2 | A+1 / A+2 / A+2; nearest available state retained |
| A+2 body removed | A+2 | Genesis / Genesis / A+2; readiness rejected |
| A+2 state root and A+1 body removed | A+2 | Genesis / A+2 / A+2; readiness rejected, no repair panic |

For every cut, persisted and in-memory heads must be either the complete original
set or the complete final set. The test checks canonical indexes, surviving and
deleted headers/bodies, transaction resolution, available full-head state and
anchor readiness. It then repeats the requested rewind and restores the accepted
suffix, verifying heads and canonical transaction/receipt indexes.

The two genesis-fallback cases use an explicit `FastSyncCommitHead` to the retained
state at `A-1` before reimport. This is a fixture limitation: its history starts
at the synthetic backup height, with a gap back to genesis, so ordinary full sync
from genesis cannot be demonstrated here. The retained-state pivot must still
leave readiness rejected until the accepted anchor is imported. This is not proof
of real peer state download or interruption safety inside the pivot operation.

The test suite now has 28 cuts per full run: the previous sixteen import/reorg/
rollback cuts plus twelve rewind cuts. The opt-in remains
`FUSION_RESTART_CRASH_REHEARSAL=1`; use a test filter ending in `/rewind` for only
the six new cases. See the [test instructions](../tests/restart/README.md).

## Evidence and limits

Logs, exact Linux runner, source/binary identities and checksums are retained in
[the evidence directory](evidence/restart-rewind-rehearsal-2026-09-24).
`before-corrected-harness-windows.txt` is the authoritative original-client
reproduction. The first `before-windows.txt` also contains an initial test-helper
mistake: the below-anchor case passed its restored parent block to a suffix-only
index checker. That expectation was corrected before the original-client rerun.
The initial missing-body recovery also failed because the sparse fixture cannot
full-sync from genesis; the explicit retained-state pivot above addresses that
test limitation. Both intermediate logs are retained.

The full Windows restart suite passed in 104.211 seconds with all 28 crash cuts.
The full Linux suite passed under the race detector with the crash and node-service
opt-ins enabled, including all four service/peer scenarios. Two additional Linux
rewind runs passed: 52 Linux crash cuts in this round, of which 36 are rewinds,
with no race report. The complete Linux node binary built successfully. All four
changed/new Go file hashes match between Windows and the Linux source export.
Existing unrelated `miner`/`core/rawdb` package-test compilation failures remain
documented; these restart-package checks are not a whole-repository test claim.

The unchanged historical replay had reached block 2,504,064 at 09:56:46 UTC,
still targeting 2,700,000. The archived progress snapshot records 72,886,886,400
free bytes on Linux and 58,944,876,544 on D:, above the configured reserves. This
is an in-progress observation, not a completed replay checkpoint.

The scope is process exit at database API boundaries with LevelDB and no freezer.
It does not establish power-loss/fsync durability, atomic visibility across all
running RPC readers, reset/genesis rewrite safety, interruption inside a fast-sync
pivot, successful state download, ancient-store rewind consistency, or the cost
of very deep rewinds/reorganizations. Injecting missing historical keys exercises
repair branches, not a complete production pruning lifecycle. The public light
client remains unsupported with an active restart anchor.

The subsequent [reset/pivot rehearsal](restart-reset-pivot-rehearsal.md) covers
reset to the existing genesis and anchored pivot publication, including receipt
import followed by pivot. It needs no further production correction, and retains
the state-download, genesis-resync and freezer limitations above.

These remaining gates, full-state recovery construction, accounting review and
independent operator review remain in the [main plan](restart-plan.md).
