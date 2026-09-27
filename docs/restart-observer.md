# Read-only restart observer

27 September 2026. The external `fsn-observe` command implements a single RPC
observation for one or two explicitly configured nodes. It supports the
[monitoring proposal](restart-monitoring-response.md) and
[operator recovery procedure](restart-operator-recovery.md). It does not yet
implement a continuous monitor, history backfill, incident lifecycle or alert
delivery. A report is evidence for diagnosis, not a launch approval.

The implementation is confined to [cmd/fsn-observe](../cmd/fsn-observe/main.go)
and [internal/observe](../internal/observe/collect.go). The ordinary node does
not import this package. P1–P15, consensus, discovery, transaction admission and
automatic buying are unchanged. The collector opens no chain database and has
no signing, submission, mining-control, peer-management or service-control path.

## Running one observation

Build with the repository's supported Go toolchain:

```sh
go build -o fsn-observe ./cmd/fsn-observe
./fsn-observe --config observer.json --timeout 10s > observation.json
```

On Windows use `fsn-observe.exe`. Both arguments are required. The example
deadline is illustrative, not an approved production setting or alert threshold.
The deadline applies separately to each node and once to a two-node comparison;
two nodes can therefore take approximately three deadlines plus local work.
Interrupting cancels outstanding reads. Output is versioned JSON with UTC start
and finish times. **Exit code zero means a report was emitted, not that a node
is healthy.** Configuration/output errors return nonzero; RPC failures appear
inside the report as missing values and issues.

Prepare a local JSON configuration with these fields. Obtain the accepted
identity from the reviewed release/recovery manifest, not from an unverified
node being evaluated. No production identity or endpoint is supplied here.

| Field | Required value |
| --- | --- |
| `ChainID`, `NetworkID` | Canonical decimal strings; positive chain ID and nonnegative network ID |
| `Genesis` | Full `0x` genesis block hash |
| `AnchorNumber`, `AnchorHash` | Nonzero integer height and full accepted restart block hash |
| `Nodes` | One or two objects described below |
| `Tracked` | Optional array of exact signed transaction bytes as `0x` hexadecimal strings; at most 64, each at most 4,096 bytes |

Each node object contains `Name`, `Endpoint`, `Role` and `Wallet`. Names and
endpoint strings must be unique. Wallets are explicit nonzero public addresses.
Endpoints are absolute Unix IPC paths, Windows named pipes such as
`\\.\pipe\efsn.ipc` (escape backslashes in JSON), or HTTP(S) URLs. WebSockets are
not supported by this command. Tracked transactions must carry a valid signature
for the configured chain, recover a configured wallet and have unique hashes.
They are optional tracking inputs, not evidence of a controller's saved record.

Supported roles are `producer`, `verifier`, `maintenance` and `retired`.
Producer flags and configured coinbase are checked only for `producer`.
Maintenance/verifier observations still retain read errors. A retired endpoint
is not contacted and has `Consistency: "not_applicable"`. If either of two
configured nodes is retired/unavailable, comparison is unavailable. Zero peers
alone is not an issue in the agreed initial single-producer arrangement.

Keep endpoint credentials in the local configuration. The collector omits
endpoint URLs and transport error text from reports. Reports contain public
wallets, signed bytes, receipts and account state, and should have controlled
storage/retention. No private key or unlocked wallet is needed. IPC permissions
still confer the server's administrative access; the allowlist is enforced by
this executable, not by a read-only IPC account.

## What is collected and checked

The command reads node/version/chain identity, genesis and accepted anchor,
latest header and cumulative difficulty, synchronization, mining and auto-buy
flags, coinbase and peer count. Canonical nonce, liquid FSN, raw time locks and
ticket inventory are read at that explicit latest height. The canonical hash at
that height is read again after the remaining work. Returned headers must hash
to the supplied block hash and match requested heights.

`Identity` is `matches`, `mismatch` or `unknown`. `Consistency: "stable"` means
the sampled canonical height still had the same hash on reread. If identity or
consistency fails, tracked inclusion, payload, funding and nonce diagnoses become
`unknown`; raw observations remain available. This is a collection time window,
not an atomic state snapshot. Pool and control flags cannot be pinned to the
sampled block. A later reorganization can invalidate a previously stable sample.

Numeric balances/coverage are exact decimal wei strings; Ethereum RPC quantities
retain their hexadecimal form where applicable. Do not parse large values
through floating point. Unknown pointer fields serialize as `null`. Check
`TicketsKnown` and `PoolKnown` before interpreting collections as empty: a
successful null ticket response means no tickets, while a failed ticket read
does not. Empty `Issues` is not a general health verdict.

Two nodes are compared at the lower sampled tip height, rereading each hash.
The report distinguishes `same_at_common_height`, `divergent_at_common_height`,
`unstable`, `unavailable` and single-node `not_requested`. Different tip heights
with the same prefix do not establish a fork. Neither agreement nor disagreement
automatically selects a branch. Both tips and their reported difficulties remain
in the report.

For each configured signed transaction belonging to a sampled wallet:

- Report canonical nonce relation (`current`, `ahead`, `consumed` or `unknown`)
  and exact pool presence, absence or conflicting nonce. Failed/incomplete pool
  reads stay unknown.
- Decode native BuyTicket payloads and check their interval against the sampled
  head and wall-clock expiry. Estimate backing over the interval beginning at
  the later of payload start and observation time. Full ticket-value time locks
  or full ticket-value liquid FSN are required, plus liquid gas budget; partial
  locks and partial liquid do not combine into ticket backing.
- Bind receipts to the requested hash, canonical block and exact signed bytes at
  the reported transaction index. Require an explicit valid status. For native
  success, additionally require the correctly bound BuyTicket log, expected
  ticket ID/owner and matching historical ticket state. Ordinary self-transfers
  consuming a nonce are classified separately from ticket purchases.

`canonical_native_success` is a historical inclusion observation. Payload and
funding fields describe hypothetical suitability **at the sampled time**, even
for a transaction already consumed. Insufficient current funding does not undo
an earlier successful purchase. These estimates do not cover every admission,
gas, ticket-eligibility or economic rule. They cannot authorize repair signing.

`SavedIntent` is always `unknown`: the production RPC has no live saved-record
endpoint. The command never calls the test-only `lab_*` APIs or reads a running
writer's LevelDB. Resample and follow the operator procedure before taking any
action. This component does not automatically clear or close incidents.

## Transport and work bounds

The explicit allowlist in [rpc.go](../internal/observe/rpc.go) contains only the
16 read methods used by the collector. Tests reject submission, signing, buyer
and miner controls, peer changes, account unlock and test methods before reaching
transport. Unknown methods are rejected by default.

Configuration input is limited to 1 MiB. HTTP response reads are capped at 8 MiB,
redirects are refused, collection uses context deadlines and only 256 pool entries
for a monitored wallet are retained. A truncated/invalid pool is marked unknown.
The node still produces the entire `txpool_content` response; the cap does not
reduce server work. The inherited IPC JSON codec has no observer-specific message
size cap. Use controlled local/private endpoints; this is not a hardened scanner
for arbitrary untrusted public RPC servers. Malicious RPC data can still lie
consistently: these checks do not validate consensus, attest the executable or
establish finality.

## Validation and remaining work

The [evidence directory](evidence/restart-observer-2026-09-27/) retains commands,
toolchain identities, input hashes, test logs and representative JSON reports.
Both Windows Go 1.21.3 tests/build and Linux Go 1.21.3 tests with race detection
and build passed. The Linux checks ran in an isolated network namespace. The
initial null-receipt failure and its correction are retained, not overwritten.
Tests use real local HTTP and IPC transports with adapters serving preserved
synthetic block headers, signed bytes, receipts, historical tickets and account
state. They do not open a database or run a new miner rehearsal. Adapter genesis,
status flags and default pool/total difficulty are synthetic; the equal-weight
case supplies the original recorded difficulties and both genuine branch heads.
Controlled fault variants do not modify the preserved inputs.

Coverage includes the recorded rollback nonce gap, funding exhaustion, automatic
reinclusion and repaired native receipt; actual equal-weight divergence; normal
tip-height lag; expired payloads; partial backing; queued exact bytes; native
failure despite receipt status one; wrong transaction/receipt binding; unknown
reads, malformed time locks, absent receipt status, deadlines, retired roles,
zero peers and endpoint credential omission. It checks classification of snapshots,
not elapsed incident behavior or notification delivery.

Next run this executable against actual isolated node services, then implement
durable observation/history coverage and incident transitions. Select operational
timings, retention and notification destinations before deployment; demonstrate
actual delivery, acknowledgement, loss of the collector, and receipt rollback
reopening an incident. Continuous block backfill, saved-intent visibility, real
funding/custody and independent release review remain separate gates. No public
monitor has been deployed.
