# F11 block construction, import and fresh-process reopening

7 October 2026. One top-level test and 16 subtests pass on each of the selected
P1–P17+B1+D1 baseline and the unchanged, unselected F11 candidate. Each case
uses a fresh import subprocess and another fresh reopen subprocess: 64 receiver
processes total. Race detection is enabled. No production selection or
activation height changes.

## What this establishes

The inherited dirty-account case can produce a block accepted by the normal
blockchain importer in this synthetic fixture. Its extra ordinary zero entry
survives a new process opening the receiver's database. With the correction
active, that entry is absent and the accepted state root differs. The time
lock remains intact. This extends the earlier transaction-persistence evidence
through block validation, consensus finalization and canonical storage.

| Case | Baseline / inactive candidate after import and reopening | Active candidate | Cross-selection result |
| --- | --- | --- | --- |
| Clean child; reverted deletion; ordinary entry absent | Original account; no extra persisted entry | Same | Identical block bytes |
| Earlier transaction changed child; reverted deletion; ordinary entry absent | Extra ordinary zero entry | Extra entry prevented | State root and signed block differ |
| Earlier transaction changed child; ordinary zero pre-exists | Original zero entry retained | Same | Identical block bytes |
| Earlier transaction changed child; successful deletion | Child absent; beneficiary receives its ordinary FSN | Same | Identical block bytes |

Each case runs disabled, immediately before, at and immediately after the
synthetic activation height. Fourteen baseline/candidate pairs have identical
serialized blocks and observations. The only two differences are the dirty
absent-entry cases at/after activation. Receipt roots, ticket roots, selected
tickets, gas, transfers, miner rewards and the other recorded account fields
match across all pairs. These results require preserving pre-activation
execution; they do not identify any occurrence in Fusion's historical chain.

## Execution path and assertions

[block_import_test.go](block_import_test.go) seeds matching producer and receiver
databases independently. The parent at the fixture height is installed directly,
as in the existing restart fixture approach; it is a synthetic checkpoint, not
an executed prefix from genesis. Four synthetic tickets belong to public test
scalar one. Transaction sender scalar two has disposable synthetic funds.

The producer uses actual DaTong.Prepare, core.ApplyTransaction and
DaTong.Finalize. It signs the returned SigningPayload with the synthetic key
and serializes the block. This exercises the block-assembly calls used by the
miner; it does not run the miner worker, ticket autobuyer or Seal timer.

A new process opens the receiver database at the unchanged checkpoint and
passes the serialized block to the normal BlockChain.InsertChain. The default
header/body/state validators, StateProcessor and DaTong finalization remain
installed. A second new process opens the database after the importer stops
and closes it. Both subprocesses assert that the parent/result ticket hashes
are absent from the process-wide ticket cache before chain startup, preventing
the producer or importer cache from supplying the cold receiver's ticket data.

Both receiver phases check:

- Canonical checkpoint and new head, all three in-memory and stored head
  markers, total difficulty, and account state from the head root.
- Raw child balance/time-lock arrays, code, storage and nonce; sender balance
  and nonce; beneficiary transfer; miner fees plus reward.
- Receipt status, gas, cumulative gas, block/transaction identity, empty logs
  and bloom, receipt commitment, and canonical transaction lookup entries.
- Three surviving tickets: the selected input ticket is removed, every other
  ticket's complete body is unchanged, no retreat occurs, and stored ticket
  bytes hash to the header's ticket commitment.

Ticket conservation and commitments are checked; this is not a new independent
test of which of the four equal-owner tickets should win the selection score.

Expected gas remains 31,258 for the tested transaction and 21,034 for the prior
one, from the [transaction fixture's arithmetic](../restart-state-rollback-persistence-v2-2026-10-07/gas-vector.json).
The block fixture uses one-gwei gas price/base fee and 10^15 base units of sender
funding. Clean/prior sender balances are 968742000000000 and 947707999999999.
The one-unit prior transfer is unchanged. At these heights the reward is
2.5 × 10^18 / 2^3 = 312500000000000000 base units. Adding fees gives miner
balances 312531258000000000 and 312552292000000000. Four tickets/one owner imply
difficulty five, order zero and parent TD one plus block difficulty = TD six.
These expectations are literals in the fixture and independently recalculated
by the Python verifier; no observed state root is used as a golden constant.

## Evidence and retained failure

[run.py](run.py), [launch.py](launch.py) and qualification/run.json retain the
actual commands, source/overlay hashes, environment, timestamps, namespace IDs
and exits. Go 1.27.1 uses the existing cache, two workers, two-minute test limits
and seven-minute outer limits. The unprivileged rehearsal user runs in a private
network namespace with only loopback, down. Every recorded child process is in
that same namespace. No real key, public peer or RPC endpoint is involved.
Free-space floors were checked; no large restore or replay workload was used.

The [first attempt](../restart-state-rollback-block-2026-10-07/README.md) is
preserved: all 16 imports failed header validation because the fixture wrongly
carried forward a zero base fee. Fusion requires one gwei for this parent.
[fixture-correction.patch](fixture-correction.patch) changes only fixture fees,
sender funding and independently derived balance expectations. Runtime checks
remain intact. The candidate was not run in that failed attempt.

The raw Go logs are retained byte-for-byte. One informational log formats
common.Hash with %s, which writes raw bytes rather than hexadecimal; those log
segments are not UTF-8 text. The per-case JSON artifacts contain correctly
encoded roots, serialized blocks, literal expectations, process identities,
receiver observations and child logs. They are the authoritative hash records;
no log output was reconstructed. The verifier reads raw logs as bytes.

[verify.py](verify.py) checks 230 prior evidence files, 29 overlay-input bindings,
27 source/module hashes, the exact fixture correction, all process results,
independent fee/reward arithmetic and independently decoded block RLP fields.
It compares all 16 pairs and permits only the two intended account/root
differences. [verification.json](verification.json) records its results.
SHA256SUMS covers this bundle. Selected runtime files and prior evidence remain
unchanged; additions are test fixtures, runner/verifier files and documentation.

## Remaining scope

These are isolated one-block descendants of synthetic checkpoints. This does
not prove historical compatibility, a continuous chain crossing activation,
mixed-version peer behavior, public-network liveness, service startup with the
final release artifact, or power-loss safety. Both producer and receiver use
the same rule schedule in each case; baseline/candidate comparison happens
between retained runs. Logical account deletion is not physical erasure of
historical database data. F11-b remains unchanged.

Next: qualify rule selection for supported RPC calls, pending execution and
historical tracing, retaining any F1 coverage exclusions. Candidate historical
compatibility, independent consensus review and the final release/service
rehearsal remain open. This synthetic accepted-block result closes none of
those release gates and selects no production schedule.
