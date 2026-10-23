# Tracing historical blocks

Investigated on 25 September 2026 from the fsnex-rebirth explorer, which wants
internal transactions (value-carrying calls inside a transaction). Only a trace
RPC produces those: they are not in blocks, receipts or logs.

**Status: the `debug` API works, but tracing any block older than the node's
most recent saved state fails. Replaying history breaks on block 2 with a
consensus error. The cause is one line in `eth/state_accessor.go` (below).**

**Fixed on 11 October 2026** in Fusion-Community/efsn `feature/historical-tracing`
(`aae15bf`, one commit on `develop`): the proposed line below plus integration
regressions in `tests/tracing`. The regressions fail without the fix and pass with
it; read-only mainnet probes trace blocks 256 and 4096 and replay from stored
block 3001, and baseline and fixed code import blocks 1–4096 identically. Its
commit message has the full validation. Full-history tracing has not been run.
The sections below are the investigation as it stood before the fix.

## What was enabled

The node container was recreated with `debug` on the HTTP API:

```text
--http --http.addr 0.0.0.0 --http.port 9000 --http.api eth,net,web3,fsn,debug
```

`rpc_modules` then answered `debug, eth, fsn, net, rpc, web3`. An earlier attempt
also served WebSocket on the same port 9000 (`--ws --ws.port 9000 --ws.api
eth,debug`). It never worked: a WebSocket upgrade to `ws://127.0.0.1:9000`
through the tunnel got a plain `200` instead of `101`. If WebSocket is needed
(for `debug_traceChain`), give it its own port and its own tunnel forward.

## What was observed

All calls went through the SSH tunnel to `http://127.0.0.1:9000`, using
`debug_traceBlockByNumber` with `{"tracer":"callTracer"}`.

| Block | Options | Result |
|---|---|---|
| `latest` (15,130,080) | none | Works. One trace: a `CALL` from `0x0aef49b7…` to `0xffff…ffff` (the native call address), `gas` and `gasUsed` 0, input `0xcd048bca…` |
| 1 | none | `[]`, correct, since the block has no transactions |
| 1,000,295 and 5,926,479 | none | `required historical state unavailable (reexec=128)` |
| 256 | `reexec: 5000` | `processing block 2 failed: MixDigest mismatch, have:0x8a27…, want:0x8345…, header:2` |
| 4,096 | `reexec: 5000` | `processing block 3002 failed: MixDigest mismatch, have:0x01cc…, want:0xbd2d…, header:3002` |

The node is a full node, not an archive node. It keeps state at genesis, at a
few saved points (evidently including block 3001) and near the head. Tracing an
older block therefore means replaying forward from the nearest saved state. That
replay fails on the first block after the one it started from: from genesis it
gets through block 1 and fails on block 2; from block 3001 it fails on 3002.

The error comes from `consensus/datong/consensus.go:454`. `Finalize` recomputes
the ticket set's hash with `headerState.UpdateTickets` and compares it to
`header.MixDigest`. During replay the two differ, so the tracer rejects the
chain's own blocks.

## Likely cause

`eth/state_accessor.go`, in `stateAtBlock`'s replay loop, reopens the state after
each replayed block with an empty ticket hash:

```go
// eth/state_accessor.go:144
statedb, err = state.New(root, common.Hash{}, database)
```

In efsn the second argument of `state.New` is the block's `MixDigest`, and it
becomes `StateDB.ticketsHash` (`core/state/statedb.go:191-206`). That hash
matters because `AllTickets` (`core/state/statedb.go:1282`) looks the ticket set
up in a process-wide cache, `cachedTicketSlice`, keyed by `ticketsHash`, before
it reads the ticket blob from the trie at `common.TicketKeyAddress`:

```go
key := s.ticketsHash
ts := cachedTicketSlice.Get(key)
if ts != nil {
	s.tickets = ts.DeepCopy()
	return s.tickets, nil
}
```

With an empty hash, every replayed block after the first uses the same all-zero
cache key. It can get back whichever ticket set was cached under that key: the
first replayed block's, or one from an unrelated state opened with an empty
hash. `UpdateTickets` then hashes the wrong set, and `Finalize` fails the
`MixDigest` check. The first block after the start point opens its state with
the real `MixDigest` (lines 67, 87 and 103 pass `current.MixDigest()`), which is
why it succeeds and the next one fails.

The normal import path does not hit this: `BlockChain` opens each state with the
parent's `MixDigest`.

## Proposed fix

One line. It is not built, run or reviewed yet:

```go
// eth/state_accessor.go:144
statedb, err = state.New(root, current.MixDigest(), database)
```

`current` is the block just replayed, so its `MixDigest` is the hash of the ticket
set its state now holds. `UpdateTickets` caches the new set under exactly that
hash (`cachedTicketSlice.Add(hash, …)`). Both `traceBlock` and `traceChain` replay
through `stateAtBlock`, so the one line covers both.

A search for `state.New(..., common.Hash{}` finds no other replay path. The other
matches create empty states (genesis, the `evm` tools, tests) or open a state
only for `dump` in `cmd/efsn/chaincmd.go:396`.

## How to verify

1. Build the node with the fix and trace the two failing cases again:
   `debug_traceBlockByNumber` on `0x100` with `{"tracer":"callTracer","reexec":5000}`,
   then on `0x1000`. Both should return traces instead of `MixDigest mismatch`.
2. Replay across a stretch with ticket churn: pick a block a few thousand past
   genesis that is not near a saved state, and confirm replay reaches it.
3. Check the result against something independent. For a block whose internal
   calls are known from the legacy explorer or a contract's own events, the
   traced calls should match.
4. `debug_traceChain` (WebSocket only, on its own port) should then stream the
   whole chain from genesis in one pass. Replay cost is linear there. With
   `traceBlockByNumber` it grows with the distance to the nearest saved state.

## Constraints on any fix

Agreed with the owner on 9 October 2026, when the explorer recorded how it will take
Fusion's internal transactions (fsnex-rebirth, `docs/PLAN.md` §6.7, "Trace sources and
node types", and §10.1 #14):

- **Do not weaken consensus to make replay pass.** The `MixDigest` comparison in
  `consensus/datong/consensus.go:454` is the check that rejects a block whose ticket set
  is wrong; it must stay exactly as it is for normal block import, and so must every other
  check `Finalize` and header verification make. The mismatch is a symptom: the proposed
  fix above corrects the state the replay opens (`eth/state_accessor.go:144`), which normal
  import never uses. Skipping, relaxing or special-casing the check for replay is not a fix:
  a trace taken through it would no longer prove the replayed state is the chain's.
- **If the state-accessor fix does not hold** (replay still fails the check, or passes
  only with the check changed), stop and work out why before going further, rather than
  loosening anything. A real disagreement between replay and import would mean the replayed
  state is wrong, and every trace taken from it with it.
- **Prove normal import is unchanged.** Besides the checks under "How to verify", sync a
  stretch of blocks from a saved state with the fixed build and confirm it imports them with
  the same results as before, including the blocks whose replay failed.
- **Expose tracing, not `debug`.** The gateway dropped the `debug` namespace on 3 October
  2026, because it also carries `debug_setHead` and the file-reading and file-writing trace
  methods. The explorer should reach only a thin trace service: `traceBlockByNumber`,
  `traceBlockByHash`, `traceTransaction`, `traceCall` and `traceChain`, with the
  JavaScript tracers left out so only the native ones resolve (fsnex-rebirth
  `docs/PLAN.md` §10.1 #151 has the file and line references). `traceChain` is a
  subscription: over HTTP it answers `ErrNotificationsUnsupported`, so it needs a
  WebSocket (or IPC) endpoint, on a port of its own, since WebSocket on 9000 beside
  HTTP never upgraded (above).

## How the explorer will use it

The chain is halted at block 15,130,080, so there is nothing new to trace at the head. The
explorer's internal-transaction lane will walk the history once: `debug_traceChain` from
genesis to the halt, through the trace service above, storing each block's internal calls
as it goes. That needs no archive re-sync: `traceChain` opens the start block's state
(genesis, or a stored state up to `reexec` blocks back) and executes each later block on
the previous one's state in memory, through `stateAtBlock`, exactly the path this fix
repairs. A walk cut short restarts by replaying, untraced, from genesis or the nearest
stored state up to where it stopped, so the lane resumes from its checkpoint at that cost.
Neither the fix nor `traceChain` has been run yet. The same lane traces new blocks at the
head with `debug_traceBlockByNumber` if the chain ever restarts.

## What the explorer needs from a trace

- `callTracer` output per transaction, with nested `calls`, `type`, `from`,
  `to`, `value` and `error`.
- Native calls show up as a `CALL` to `0xffffffffffffffffffffffffffffffffffffffff`
  with zero gas. The explorer already decodes native calls from input and logs,
  so it can skip that frame.
- Internal transactions are the nested frames that carry value, plus contract
  creations. They are captured once, in their own lane, and are never
  re-derivable from stored data.

The alternative to the fix is an archive re-sync (`--gcmode archive`). It stores
state at every block, so tracing needs no replay. It costs a full re-sync of
about 15 M blocks and an unmeasured, large amount of disk.
