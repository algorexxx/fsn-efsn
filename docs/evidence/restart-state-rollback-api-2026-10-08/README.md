# F11 call, pending-state and tracing rule selection

8 October 2026. Two top-level tests and 84 subtests pass on each of the selected
P1–P17+B1+D1 baseline and the unchanged, unselected F11 candidate, with race
detection. Both runs passed on their first attempt. No production source,
release selection or activation height changes.

## Result

The exercised API paths retain legacy behavior with the correction disabled
or before activation. At and after the synthetic activation height, the
candidate restores the expected ordinary-balance structure. The time lock and
other inspected account fields remain intact. Of 84 paired observations, 42
are identical and 42 differ only in the expected raw child balance arrays.
Recorded execution contexts, gas and return data match across selections.

These are in-process API calls through the actual backend methods. The test
observes the post-call state because gas and returned data alone do not expose
this defect. In all cases, the Go fixture compares a digest of every database
key/value before and after the operation. Pending calls also assert that the
injected snapshot remains unchanged. Those invariants pass; the digests and
snapshot contents are checked in the test rather than emitted in the logs.

| Path | Cases per selection | What is exercised |
| --- | ---: | --- |
| DoCall, public Call, DoEstimateGas, TraceCall | 64 | Number, canonical hash, latest and pending selectors, each disabled/before/at/after activation |
| DoCall with no pending snapshot | 4 | Actual miner/backend fallback to the current block and its state |
| TraceTransaction | 4 | Transaction lookup, replay of its preceding transaction, then the requested transaction |
| TraceBlockByNumber and TraceBlockByHash | 8 | Serial preparation and default structured trace workers for both transactions |
| IntermediateRoots | 4 | Replay with an intermediate root after each transaction |

For numeric/hash calls, the latest synthetic head is later than the requested
header. Pending snapshots use the next header while the current head is one
block behind. Historical queries execute an imported two-transaction block
with a later synthetic head installed afterward. The pre-activation and exact
boundary cases therefore distinguish the requested execution rules from the
latest or parent rules. The fixture schedule is not a production proposal.

## Fixture and observation boundaries

[api_rule_test.go](api_rule_test.go) reuses the immutable
[block fixture](../restart-state-rollback-block-v2-2026-10-07/block_import_test.go)
and its synthetic accounts, transactions, tickets and directly installed
checkpoint. The historical target block passes normal InsertChain. The later
head is installed directly for rule selection; intervening blocks are not
executed. This is not historical-chain compatibility evidence or a continuous
chain crossing activation.

Two added overlay library files initialize otherwise private structs:
[eth_fixture_support.go](eth_fixture_support.go) supplies the real chain,
database, engine, miner and RPC limits to EthAPIBackend;
[miner_fixture_support.go](miner_fixture_support.go) supplies the real chain
and optional pending snapshot to Miner/worker. They add test constructors and
do not replace execution methods. They are absent from the selected source
tree. The observing backend delegates GetEVM, StateAtBlock and
StateAtTransaction to the real implementation, retaining returned state
pointers and context/requested-state heights for assertions.

The pending snapshot is injected. Real Miner.Pending/worker.pending and the
backend selector/copy behavior run, but miner snapshot construction, transaction
pool assembly, ticket buying and the Seal timer do not. The no-snapshot fallback
is covered only through DoCall; other pending fallbacks are not qualified.

For TraceTransaction, the retained state includes the preceding transaction's
replay and the target's trace. For block traces, raw account inspection observes
the serial preparation state, not each worker's copied state. Worker results
are checked for both transactions' gas, success/revert and return data, with
a nonempty structured log for the target. Those outputs alone do not independently
prove each worker's rollback structure. TraceCall and IntermediateRoots inspect
their own returned execution state. TraceNumbers records a state-request height
for StateAtBlock, or an execution-context height for StateAtTransaction; a
parent-state request is not a claim that the EVM executes at the parent height.

Expected child fields come from the earlier literal fixture: ordinary FSN 11
for calls or 12 after the preceding one-unit transfer, nonce 7, preserved code
and storage, and a five-unit future asset time lock. Legacy execution adds an
ordinary nil entry for that asset; active correction prevents it. Expected gas
31,258 and prior transaction gas 21,034 retain the independently derived
[transaction arithmetic](../restart-state-rollback-persistence-v2-2026-10-07/gas-vector.json).
The reverting public Call and estimate paths assert RPC error code 3 and the
exact 32-byte revert payload ending in 01. Their logged Gas=0 means gas usage
is not supplied by those APIs; it is not an assertion of zero gas consumed.

IntermediateRoots returns two nonzero roots, identical across the selections,
although its raw in-memory child differs under the active rule. Source review
explains why this is consistent with the earlier persistence result: this API
calls IntermediateRoot after each transaction, clearing the pending-object set
before the reverted transaction, while normal block execution defers that
flush. It also omits consensus finalization/rewards. These roots are compared
with each other, not an independent root oracle or the accepted block root.
Its Gas/Failed/Return fields are unused placeholders, not transaction outcomes.
Root equality here does not contradict the established accepted-block root
difference or prove historical compatibility.

## Provenance and verification

[run.py](run.py), [launch.py](launch.py) and
[qualification/run.json](qualification/run.json) retain the commands, Go
environment, timestamps, exits, source/overlay hashes and network namespace
identity. The selected recovery source tree contains the node execution paths
and the recovery configuration used by the shared fixture. The baseline and
candidate use the previously recorded overlays; neither edits that tree.

Go 1.27.1 runs with the existing offline cache, two workers, race detection,
two-minute test and seven-minute outer limits. The rehearsal user runs in a
private network namespace with only loopback, down. No real wallet, public
peer or RPC listener is used. Free-space floors were checked; there was no
backup restore or bulk history workload.

[verify.py](verify.py) validates 275 prior evidence files, 35 overlay bindings
(13 baseline, 22 candidate), 35 source/module hashes, the complete test matrix,
literal account/context/return expectations and every cross-selection pair.
It accepts only the specified raw balance difference. It checks intermediate
roots for shape and cross-selection equality without treating an observed hash
as a golden expectation. [verification.json](verification.json) records the
results. SHA256SUMS covers this bundle; logs here are valid UTF-8. Raw logger
trailing spaces are preserved; the bundle attributes exempt only retained logs
and patches from whitespace linting.

## Remaining scope

This is focused replacement coverage under F1, not a pass for the inherited
eth/miner/console/tracer suites. No existing test is replaced with an empty
stub. The earlier recorded state-fixture ports are reused; only the two named
top-level tests execute. Other packages' legacy test files are not invoked.

The following are outside this result: HTTP/WS transport and serialization,
custom JS/native tracers, streaming TraceChain, trace-to-file, raw-RLP and
bad-block entry points, missing-state historical reconstruction, state/block
overrides, full structured-log equivalence, miner-created pending snapshots,
mixed-version peers and final service/artifact rehearsal. Historical tracing
starts from available parent state; F8's sparse-history limitation is unchanged.

Next: reconcile the remaining supported-path/F1 exclusions and startup/F12
compatibility dispositions with the release scope, then the G1 candidate-history
evidence and independent review. These are existing release gates. F11 stays
open, F11-b remains unchanged, and no production fix or schedule is selected.
