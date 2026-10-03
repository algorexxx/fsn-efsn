# Reset and fast-sync pivot interruption rehearsal

24 September 2026, source base `6dce20d`. This extends the
[rewind correction](restart-rewind-rehearsal.md). It adds tests and evidence;
no production code change was needed. The mainnet anchor remains unset.

## Observed persistence behavior

Reset to the existing genesis now makes three writes: the atomic rewind to
genesis, a rewrite of genesis block/difficulty data, and a rewrite of its canonical
index/full-head pointer. The latter two writes are idempotent. Every interrupted
store reopened with either the original heads and suffix or the complete genesis
heads with that suffix removed. Repeating reset is safe in these fixtures.
Readiness stays rejected at genesis, and replacing genesis with a different
block is still rejected without changing database keys.

With an active anchor, `FastSyncCommitHead` checks eligibility, canonical status
and the state root before persisting its single full-head pointer. Memory updates
follow that write. Header and fast heads remain at their existing positions.
The direct pivot tests start with the full head at genesis and the header/fast
heads at a fully stored accepted tip. This deliberate marker setup represents
the boundary after state data has arrived; it does not simulate its download.

The receipt/pivot case exercises the same public-method sequence used by the
downloader's `commitPivotBlock`: `InsertReceiptChain`, then `FastSyncCommitHead`.
The target header/state are present, while its body, receipts and transaction
lookups are initially absent. The full head is below the anchor and the fast head
is the preceding block. Its three writes persist body/receipts/lookups together,
advance the fast head, and finally advance the full head. Intermediate stores are
valid: readiness remains disabled until the full head crosses the anchor. Repeating
the sequence finishes it without requiring database repair.

## Coverage

The existing opt-in crash harness terminates child processes before and after
every observed database write and reopens in a fresh process. It verifies actual
LevelDB data, rather than replacing writes with in-memory mock results.

| Added case | Writes | Crash cuts per run | Expected recovery |
| --- | ---: | ---: | --- |
| Reset to existing genesis | 3 | 6 | Original or complete reset state; repeat reset, keep readiness disabled and reject a replacement genesis |
| Pivot below anchor | 1 | 2 | Original or target full head; readiness remains disabled |
| Pivot exactly to anchor | 1 | 2 | Original or anchor full head; readiness enabled only after commit |
| Pivot to accepted tip | 1 | 2 | Original or tip full head; header/fast heads retained |
| Receipt import followed by pivot | 3 | 6 | Body/receipt/lookup batch consistent, heads never ahead of required data; repeat sequence and continue |

The four pivot cases reimport the accepted suffix after resuming and verify all
heads and canonical transaction/receipt resolution. Fresh target state must open
and expose the expected ticket count. Reset verifies the genesis identity,
configured anchor, deleted canonical data and transaction resolution, and checks
that rejected genesis replacement changes no key/value.

Two additional anchor-enforcement cases remove a compatible target's state root
or body before reopening. Both reject the pivot with the appropriate storage
error while preserving all keys, persisted/in-memory heads and the head-event
stream. There are now 36 anchor-enforcement cases.

The crash suite now has 46 cuts per full run across fourteen scenarios: the
previous 28 plus these eighteen. Enable `FUSION_RESTART_CRASH_REHEARSAL=1`; filter
`TestRestartCrashBoundaries/(reset|pivot)` for the five new scenarios.

## Results and limits

The full Windows restart suite passed in 110.437 seconds, including all 46 cuts.
The full Linux suite passed with race detection and the crash/service opt-ins,
including all 36 anchor cases and four node/peer scenarios. Two additional runs
of the five new cases passed: 82 Linux crash cuts this round, including 54 reset/
pivot cuts, with no race report. The complete Linux node binary built successfully.
All three changed/new test files match their recorded Linux source hashes byte
for byte. The two unchanged core files came from the Git archive with CRLF line
endings; their contents match the Windows working files exactly after LF
normalization, as verified separately in `source-comparison.txt`. Both original
byte hashes are retained. The inherited miner/rawdb package-test compilation
failures remain separately documented; this is not a whole-repository test claim.
Results, source/binary identities and exact runners are in the
[evidence directory](evidence/restart-reset-pivot-rehearsal-2026-09-24).
The first focused Windows log contains a test expectation error: the common
anchor assertion expected an anchor error after the new cases had correctly
reported missing state/body. The assertion now accepts each case's explicitly
specified error. The original and corrected logs are retained; this was not a
client failure.

The full-service negative startup test intentionally emits one nested child
failure for an incompatible anchor, then checks that startup was refused and the
logical database digest did not change. Its parent test passes; that expected
child exit is not a failed verification run.

The unchanged historical replay reached block 2,557,952 at 10:15:21 UTC, still
targeting 2,700,000. The progress snapshot records 72,494,329,856 free bytes on
Linux and 57,014,775,808 on D:, above the configured reserves. This remains an
in-progress observation rather than a closed replay checkpoint.

These are anchored, synthetic, archive-style LevelDB experiments with the public
test key. They do not establish power-loss/fsync durability, a crash inside a
LevelDB write, successful network state download, ancient/freezer consistency,
or simultaneous atomic reads across every in-memory/RPC observer. The receipt
experiment invokes the downloader's public-method sequence directly; it does not
run the downloader's complete fast-sync scheduling or state acquisition loop.
State-root availability alone is not proof that every descendant trie node and
code blob exists; complete state traversal is a separate requirement.

The reset fixture has a gap between genesis and the synthetic backup height.
It proves a coherent, non-ready genesis database and repeatable reset, not a
subsequent genesis-to-tip sync. Changing genesis is intentionally unsupported
under the anchor rule. The unanchored client's legacy in-memory-only pivot
behavior is outside these anchored persistence claims.

The unchanged node code still needs full-state recovery, accounting review,
supported-mode decisions and independent operator rehearsal before activation.
The next practical step is the bounded full-state extraction described in the
[main plan](restart-investigation-record.md#full-state-rehearsal-with-limited-disk-space).
