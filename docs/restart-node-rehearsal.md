# Restart service and peer rehearsal

24 September 2026. This extends the [inactive anchor prototype](restart-anchor-implementation.md).
The production mainnet anchor remains unset. No operator key, preserved database,
public network or production transaction is used in these experiments.

## What was exercised

`tests/restart/node_rehearsal_linux_test.go` starts separate operating-system
processes containing the actual `node.Node` and `eth.Ethereum` service. Each has
its own LevelDB, transaction pool, consensus engine, miner, RPC server and peer
manager. The test executable supplies the synthetic anchor programmatically;
there is no added production CLI, JSON or RPC override for the anchor.

The following four cases passed:

| Case | Observation |
| --- | --- |
| Readiness, mining and committed-head crash | Below the anchor, `eth_syncing` does not report ready; `miner_start` and `eth_sendRawTransaction` return anchor errors, with no admitted transaction or head change. A test-only direct worker start reports mining active but produces zero signatures or new blocks during observation. Importing the accepted sequence through `admin_importChain` restores readiness. A purchase submitted through RPC is mined through the actual wallet/miner path, then independently re-executed by a verifier. After stopping mining and killing the node with SIGKILL, reopening preserves the full/header/fast heads, state and ticket commitments and successful receipt. |
| Compatible peer | Two independently running services connect over loopback devp2p. The receiver executes and adopts the source's four valid successor blocks, crossing the anchor with matching full/header/fast heads and state/ticket commitments. |
| Heavier incompatible peer | The receiver has four accepted successor blocks and two previously stored side-branch blocks. An unanchored returning peer presents five valid foreign successors with greater total difficulty. The actual downloader finds the stored side ancestry, rejects the continuation at the anchor, and retains the accepted head and transaction lookup. Clean reopen preserves the accepted commitments. |
| Incompatible database startup | A service opening a database whose canonical head descends from the foreign anchor refuses startup. A digest of every logical LevelDB key/value before and after the attempted service construction is identical. |

All accepted and foreign fixture blocks are constructed and imported using the
actual DaTong validation/execution code and public synthetic key `1`. The peer
case compares total difficulty explicitly; an extra block alone is not treated
as proof of greater weight. Competing signatures never involve the operator's key.

The separate-process network is isolated by `unshare --net`. Only loopback is
enabled. The test itself refuses any other interface. Nodes disable discovery,
use no bootnodes or NAT mapper, restrict peers to `127.0.0.0/8`, and expose IPC
only. HTTP and WebSocket listeners are disabled. All disposable databases and
generated P2P identities are owned by the test and cleaned up after its children.

## Changes justified by this run

Anchor errors previously formatted `common.Hash` with `%s`, which this fork
renders as raw bytes. `core/restart_anchor.go` now uses explicit `.Hex()` values.
The returning-peer test requires both the rejected and expected anchor hashes
in the error. This changes diagnostics, not eligibility or fork choice.

The first complete Linux race run also exposed a timing assumption in the older
`TestAutoBuyRuntime`: `Miner.Start` hands a request to its goroutine before the
worker is necessarily marked active. If the purchase controller observes that
short interval, it correctly waits for its five-second retry. The test's own
five-second initialization timeout raced that retry. The retained failure says
`auto-buy did not initialize`, followed immediately by purchase processing.

The test now waits for the existing atomic `Mining()` state before starting the
controller. Its purchase initialization timeout and economic assertions are
unchanged. No production controller timing or miner lifecycle was changed.
The process harness also scans child logs for race reports, including the child
deliberately killed before a normal race-runtime exit.

## Scope and interpretation

These are real services and peer messages, but the history/state fixture is
synthetic. It contains genesis, a snapshot based on selected observations at
`B = 15,130,080`, and a constructed continuation. It lacks the intervening
historical chain and the complete mainnet state. Consequently:

- The bloom indexer logs `canonical block #1 unknown`. That is an expected
  fixture limitation, not a successful log-index rebuild or a full-history test.
- The heavier-peer case deliberately includes a stored foreign ancestor. This
  lets the real downloader locate that branch without binary-searching absent
  pre-`B` history, and exercises the stored-ancestry bypass of concern. A completely
  unknown long fork still requires a complete-history rehearsal.
- An IPC method included only in the test executable triggers
  `Downloader.Synchronise` with the connected peer's advertised head and weight.
  Header/body requests, validation and insertion use the actual network stack.
  This does not prove the timing of the ordinary automatic sync scheduler.
- Checkpoint initialization follows the existing CLI order: construct the service,
  then call `datong.InitCheckPoints`, then start the node. The protocol manager
  captures the legacy checkpoint at construction; this harness does not relocate
  initialization or claim to test a new handshake challenge for the restart anchor.
- SIGKILL occurs after a successfully observed committed head, with mining stopped.
  It proves that case of process recovery. It does not simulate power loss,
  interrupted individual database batches, filesystem faults or torn disk writes.
- The independent verifier executes the mined block after production is stopped;
  it is a separate chain instance using the same implementation, not an independent
  consensus implementation or a golden vector for every state transition.
- The service harness does not start the CLI's automatic ticket buyer or illegal
  mining report loop. Automatic purchasing has separate synthetic coverage;
  simultaneous real services with both features enabled remain a later rehearsal.

The one fixed anchor does not grant ongoing finality. Competing descendants of
that same anchor still follow ordinary Fusion fork choice. Existing entry-point
tests continue to require a heavier compatible fork to win.

## Evidence and next gates

Exact commands, source/binary identities, the initial diagnostic/timing failures,
and final platform/race results are in the
[evidence directory](evidence/restart-node-rehearsal-2026-09-24).
The complete ordinary Windows restart suite passed in 97.445 seconds. The complete
Linux synthetic suite passed with the race detector and the service harness
enabled. Two additional runs of the service scenarios and auto-buy runtime also
passed, giving twelve service-subcase passes on the final source without a race
report. The full Linux node binary also built successfully. This does not change
the previously documented inherited compile failures in the miner/rawdb package
tests; it is not a whole-repository test claim.
It also retains the completed two-million-block baseline replay, which used its
separate unchanged executable and source database. No synthetic result is counted
as preserved-history execution.

Next cover interrupted head/index writes, deep unknown ancestry, ordinary sync
scheduling, concurrent peer mining/reorganizations and supported fast/freezer
modes. Full-state bridge construction, complete accounting, controlled production
signing and independent operator review remain required before selecting or
activating the production anchor. See the [main plan](restart-plan.md).
