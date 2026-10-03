# Durable observer history and incident review

27 September 2026, baseline `b13c92c`. The external `fsn-observe` command now has
opt-in local history and incident review. Raw observations and explicit operator
reviews are retained; status is reconstructed from those records each time.
The chain RPC allowlist, node runtime and P1–P15 are unchanged. No notification,
scheduler, recovery action or automatic incident resolution is introduced.

Snapshot-only operation implements **durable snapshot history** and reports
`snapshots_only_no_block_backfill`. The subsequent [bounded block backfill](restart-observer-backfill.md)
adds an explicit separate operation for complete supported block/receipt ranges,
per-node coverage and retained displaced branches. Neither operation proves it
has seen every temporary fork or establishes complete wallet accounting.

## Operator commands

Choose a separate new directory under an existing parent. Never use a node
datadir. Initialization requires the same explicit observer identity/configuration
as a collection, but makes no RPC calls:

```sh
fsn-observe --config observer.json --history /absolute/observer-history --init-history --history-budget 67108864
fsn-observe --config observer.json --timeout 10s --history /absolute/observer-history
fsn-observe --history /absolute/observer-history --history-status
fsn-observe --history /absolute/observer-history --history-export > history.jsonl
```

On Windows use the `.exe` and an absolute Windows path, for example a new leaf
under an existing `D:\FusionObserver` directory. The example 64 MiB logical
budget and ten-second RPC timeout are illustrative, not production settings.
Without `--history`, the existing one-observation JSON behavior is unchanged.
With history, the same report fields remain at the top level and an additional
`History` object describes the committed status. No report is emitted as a
successful history collection until its event write succeeds.

For launch, acquire and preserve both wallets' anchor inventories before
production, then verify their baselines after reopening this history. The
[real-backup probe and procedure](restart-observer-preserved-inventory.md#launch-procedure-consequence)
show why historical availability cannot be assumed even for every recent block.

History status contains its chain/anchor/named-wallet scope, sequence, latest
event/report times, logical byte usage, coverage limitation and incident list.
To acknowledge or resolve a reviewed incident, use its ID and the current
sequence from that status:

```sh
fsn-observe --history /absolute/observer-history --history-action acknowledge --incident INCIDENT_ID --at-sequence SEQUENCE --reason "Operator has inspected the evidence."
fsn-observe --history /absolute/observer-history --history-action resolve --incident INCIDENT_ID --at-sequence SEQUENCE --reason "Record the reviewed outcome and evidence reference here."
```

These commands append a local review record. **Resolution is an operator
assertion, not proof that the command verified recovery.** Follow the
[response policy's closure requirements](restart-monitoring-response.md#alert-ownership-timing-and-closure)
and [recovery procedure](restart-operator-recovery.md), including fresh native
purchases and production where applicable. Acknowledgement does not resolve an
incident. A review from an old sequence is rejected, so inspect status again if
another observation arrived. A condition observed again after resolution
reopens the same incident, retaining the previous review.

Status, export, initialization and review contact no node. Endpoint URLs and
credentials are not stored in history metadata. Reports retain public signed
bytes, receipts and wallet state; review reasons are user-provided text. Keep
the directory/export access controlled and do not put secrets in review reasons.

## State transitions and scope

| Incident kind | Evidence used |
| --- | --- |
| `node_observation` | Reported identity/read/snapshot/producer-flag issues for a named node |
| `branch_divergence` | Differing canonical hashes at a stable common height; no branch selection |
| `purchase_attention` | Supplied purchase bytes with an observed nonce gap, conflicting pool nonce, invalid/currently unusable payload, insufficient free-backing estimate, failed/unverified native outcome, or consumed nonce without confirmed purchase |
| `receipt_change` | A previously observed canonical success later missing/noncanonical/failed, or found at a different canonical location |
| `block_coverage` | Incomplete or unavailable bounded block backfill; see the backfill guide |
| `canonical_history_change` | Backfill replaces or rewinds an already retained branch |

These are observed conditions needing review, not timed severity alerts. In
particular, a supplied purchase ahead of the canonical nonce does not prove it
is the controller's saved intent. Saved intent still remains unknown.

Incident IDs are stable within the fixed history scope. Repeated observations
update the same incident rather than creating duplicates. `Status` is `open`,
`acknowledged` or `resolved`; independently, `Observation` is `present`,
`not_observed` or `unknown`. Details refer to the last positive detection,
identified by sequence and UTC time. An open/acknowledged incident remains
unresolved when the condition is no longer observed. A single successful receipt,
quiet log, advancing unrelated wallet or enabled flag cannot resolve it.

Missing RPC data, retiring a node or removing a tracked transaction produces
unknown coverage for relevant prior incidents; it does not erase those incidents
or invent receipt disappearance. Previously observed receipt locations survive
these gaps. A later usable observation can establish recurrence and reopen a
resolved incident. A receipt that moves remains a reviewable change even if its
native outcome is successful at the new location. Later matching observations
do not automatically clear that review requirement.

History is bound to chain/network IDs, genesis, anchor and the mapping of node
names to monitored wallets. Changed chain/anchor/wallet scope is rejected before
collection. Endpoints may change and roles/tracked inputs may change without
rewriting earlier records. Earlier tracked bytes and diagnoses remain in the
original reports. Changing an expected identity to fit a surprising node must
not silently reuse or reset the old history.

## Storage behavior and limits

[history.go](../internal/observe/history.go) uses the repository's existing
LevelDB dependency in a separate marked directory. Initialization only accepts
a new leaf directory. Opening requires the observer format marker and existing
metadata; it does not initialize an unmarked directory or invoke database
repair. OS-backed database locking prevents concurrent opens, while in-process
operations are serialized. Samples, reviews and backfill batches each use one synchronous event
write. There is no separate mutable incident/status cache to become inconsistent
with the original evidence.

Replay checks the format, sequence, timestamps, scope, report structure and
tracked signed bytes. Malformed records, missing sequence entries, missing
metadata and exceeded bounds fail closed. Backward/overlapping observation
times are rejected; inspect clock/order instead of editing the history. A write
error may be ambiguous: inspect persisted status before retrying. Output failure
after a committed event also does not undo that event.

The explicit budget bounds logical key/value bytes, with a maximum 16 MiB per
event and accepted total budgets from 1 KiB through 1 GiB. **It is not a physical
disk quota**: database journals/compaction and exports need additional space.
At exhaustion the append fails and existing evidence is retained. There is no
automatic pruning, rotation, budget expansion or migration command. Do not
start an empty history to make an unresolved incident disappear. An approved
retention/capacity and migration procedure is still required before deployment.

Each operation reconstructs status from the bounded event history. The RPC
timeout does not bound this local replay. There is no claim of sustained-load
readiness. Sync-acknowledged writes survive the tested abrupt process exit;
power-loss/filesystem durability has not been demonstrated. No external signed
checkpoint detects replacing the directory with an older internally valid copy.
This remains local operational evidence, not chain consensus or finality.

## Validation

The [evidence directory](evidence/restart-observer-history-2026-09-27/)
contains cross-platform test output, source/input identities and exported replay
histories. The transition test uses actual IPC service reports from the
[previous service rehearsal](restart-observer-services.md), with explicit fixed
test times and controlled recurrence/missing-data variants. It does not claim
that a new live chain followed that sequence.

Both Go 1.21.3 builds and both package suites passed: 52 test/subtest results on
Windows and 52 on Linux with race detection in a loopback-only namespace.
Verification matched all 590 pinned inputs and the two platforms' nine-event
exports byte for byte; see [checks.json](evidence/restart-observer-history-2026-09-27/checks.json).

Checks cover repeated-condition deduplication, acknowledgement across reopen,
convergence with a displaced purchase receipt, no closure from one successful
receipt, explicit review, unknown coverage, recurrence, removed tracking inputs,
exported evidence, scope mismatch, stale review, timestamp ordering, byte-budget
failure, exclusive opening, unmarked directories, corruption and abrupt exit
after a sync-acknowledged write. CLI tests exercise initialization, collection,
status, export, acknowledgement, resolution and reopening with failed local HTTP
reads; offline operations issue no node RPCs and exports omit endpoint secrets.

The [backfill extension](restart-observer-backfill.md) now passes bounded range,
fork/reopen and actual-service checks. The [ordinary-mining follow-up](restart-observer-mining.md)
now passes moving-head collection, catch-up, cold rechecks and test-only ticket
inventory reconstruction. The [offline wallet ticket timeline](restart-observer-tickets.md)
now derives native events without adding stored inventory or changing history
format. [Historical anchor acquisition](restart-observer-anchor.md) subsequently
adds an immutable `AnchorInventory` event, accepted by the updated reader and
rejected by older readers. It leaves live incidents and block coverage unchanged.
Live competing reorganizations, representative storage/load, production historical
state availability and complete financial accounting remain to validate.
Notification routing, timing, acknowledgements in
the delivery system and a separately checked lost-monitor heartbeat remain
undeployed. The [main plan](restart-plan.md) retains those release gates.
