# Bounded observer block backfill

27 September 2026, baseline `4edd015`. The external observer can now retain a
contiguous block/receipt history for each configured node, starting immediately
after its explicit anchor. This extends [snapshot history](restart-observer-history.md)
without changing node runtime, consensus, P1–P15 or the RPC method allowlist.
It does not select a winning network branch or perform recovery actions.

## Operation and coverage

Initialize a separate observer history as described in the history guide. Then
select one configured node and an explicit batch bound:

```sh
fsn-observe --config observer.json --history /absolute/observer-history --timeout 10s --backfill-node donation --backfill-blocks 32
fsn-observe --history /absolute/observer-history --history-status
fsn-observe --history /absolute/observer-history --history-export > history.jsonl
```

Use an absolute Windows path and `.exe` on Windows. The example timeout and batch
size are illustrative. The node name must match the config, and the config must
match the history's chain/network/genesis/anchor/named-wallet scope. This is a
separate collection operation, not a flag that silently expands every snapshot.
Run it for each relevant node and repeat to fill any remaining range. A successful
process exit means its observation was persisted; inspect coverage for success,
partial progress or failure of the actual reads.

Status reports `Coverage: bounded_block_history_see_nodes` after the first
attempt and lists each node under `Blocks`:

- `StoredThrough` identifies the retained contiguous branch from the anchor.
  Under an error status, it is the last accepted prefix, not a claim that the
  endpoint still serves it as canonical.
- `ObservedHead` identifies the target read at the start of that attempt.
- `CheckedUTC` timestamps that attempt, not a finality or freshness guarantee.
- `Status` states the result. `complete_at_observation` means every block after
  the anchor through that particular head has been retained and checked.
  `batch_limit`, `data_limit` and `block_unavailable_or_invalid` leave explicit
  incomplete coverage. When the observed head is higher, the first missing
  height is `StoredThrough.Number + 1`.

`unavailable`, `identity_mismatch` and `unstable` do not replace the retained
prefix. `retired` makes no RPC calls. A second configured node begins as
`not_requested` until its own backfill. Later snapshot collection marks existing
block coverage `not_rechecked`, keeping its prior head and check time: reading a
current wallet snapshot does not prove that intervening blocks were collected.

Complete coverage refers only to the endpoint's observed canonical branch after
the anchor. It excludes earlier history, forks that arose and disappeared between
observations, unseen peers and any new blocks produced after the target was read.
There is no continuous scheduler or lost-monitor heartbeat yet.

## Retrieval and reorganization

The command verifies chain/network IDs, genesis and anchor before fetching body
data. It rechecks the retained tip against the endpoint; if necessary, a binary
search over retained ancestor hashes locates a common ancestor, bounded by the
anchor. It then fetches a contiguous replacement/extension in ascending order.
A head that has moved backward is handled explicitly. A missing ancestor read
stops the attempt rather than guessing a new cursor.

Before accepting any prefix, it rereads the common ancestor, collected endpoint
and original target head at their explicit heights. Changed/unavailable boundary
reads discard the proposed prefix and record `unstable`. Ordinary advancement
beyond the pinned target is allowed. These checks are RPC consistency checks,
not an atomic snapshot or proof that an endpoint is honest.

Each event contains the observed identity/target, base, complete accepted block
RLPs and receipts, times and outcome. Cursor and canonical hash path are derived
by replaying those events; no second mutable cursor/index is persisted. Replacing
the derived branch leaves all older events and displaced block bytes intact.
The event and resulting progress use the existing single synchronous history
write. Failed storage does not publish successful progress.

The `block_coverage` incident records incomplete/unavailable observations.
`canonical_history_change` records replacement or rewind of a retained branch.
These use the existing acknowledgement/resolution rules: catching up does not
automatically resolve an incident, and recurrence after resolution reopens it.
Backfill does not refresh wallet/pool diagnoses or automatically classify every
retained native purchase. Continue snapshot/receipt monitoring as well.

## What is checked

Retrieval uses existing read methods only: `eth_chainId`, `net_version`,
`eth_getBlockByNumber`, `eth_getRawTransactionByBlockHashAndIndex` and
`eth_getTransactionReceipt`. It does not require `debug`, subscriptions or new
node APIs. Explicit transaction hashes and signed bytes must agree.

For each accepted block, both collection and history replay check:

- Block height, parent continuity and header hash; complete transaction count
  and transaction trie root.
- Every transaction's receipt, including block/hash/index/type identity,
  status/post-state representation, cumulative and individual gas consistency.
- Log identities and order, receipt/header blooms, total gas and receipt root.

The original headers retain Fusion ticket selection/retreat data in `extraData`.
Native receipt logs remain intact. This step retains the evidence; it does not
execute transactions, validate state/ticket roots or signatures as a full node,
prove ticket ownership/accounting, or add a native outcome/selection timeline.
The existing tracked-purchase classifier still has its separate checks.

Fusion uses `sha3Uncles` as a proof-of-stake commitment after its relevant fork;
Ethereum's usual uncle-root equality would incorrectly reject these blocks.
The observer preserves that header field. It currently supports only an empty
uncle body and reports nonempty bodies as unsupported/incomplete. The inherited
DaTong `VerifyUncles` method does not reject them, so this observer restriction
must not be presented as a new consensus rule.

## Bounds and compatibility

One invocation collects one named node with a required limit of 1–128 blocks.
Each block is limited to 4,096 transactions. Accepted block/receipt JSON is
bounded to 8 MiB per batch; the existing 16 MiB event and explicit history budget
remain additional limits. Header/ancestor reads and per-transaction reads share
one RPC deadline. HTTP response limits and IPC transport limits remain in force.
Local decoding, commitment checks and history replay are not bounded by that RPC
deadline. Large valid blocks may remain an explicit gap under these limits.

The existing physical-space, replay-cost, power-loss and retention limitations
still apply. There is no pruning, repair, export import or silent history reset.
This version reads earlier snapshot/review events. Earlier binaries reject the
new backfill event field rather than silently ignoring it; retain a compatible
binary with the history. No node database is opened by this command.

## Validation and remaining work

See the [evidence bundle](evidence/restart-observer-backfill-2026-09-27/).
Both Go 1.21.3 builds and package suites passed, with 78 test/subtest results on
each platform and Linux race detection. The actual-service rehearsal also passed
with race detection in 25.99 seconds. Its 18 CLI invocations preserved the checked
node state. Verification matched 713 pinned inputs, identical platform exports,
all six service backfill results and retained original/replacement blocks; see
[checks.json](evidence/restart-observer-backfill-2026-09-27/checks.json).

Cross-platform tests use retained actual-service block RLPs and receipts with
controlled RPC responses. They cover a replacement branch, bounded catch-up
across close/reopen, shorter-head recurrence, missing data, wrong identity,
timeouts, changing boundaries, bad transaction/receipt commitments, receipt/log
metadata, budget refusal, disconnected replay and snapshot invalidation. Export
checks retain both branches, with no endpoint credentials.

An opt-in extension of the isolated service rehearsal exercises the external
command over actual IPC/HTTP, including persistent snapshots, branch replacement,
bounded resume and endpoint loss. Every invocation compares node state before
and after. Its nodes use compact complete synthetic history and public test keys
1 and 2; controlled synchronization is performed by the test harness. This does
not exercise ordinary live mining, deeper arbitrary forks or production load.

The [ordinary-mining follow-up](restart-observer-mining.md) now passes with one
producer and one verifier, including reads deliberately spanning natural head
advancement, bounded catch-up, cold rechecks and test-only native inventory
reconstruction. It changes no observer or node runtime source. Live competing
reorganizations and representative backlog, storage and receipt-index availability
remain to validate. Triage the documented snapshot decoder concern and add the
derived native timeline with explicit starting inventory and accounting coverage
before asserting complete wallet progress. Delivery, operational timings,
lost-monitor checks and release review remain open in the [main plan](restart-plan.md).
