# Automatic ticket purchase runtime investigation — 23 September 2026

This report preserves the baseline behavior before the purchase-controller
correction. Current code and test expectations are described in
[the implementation report](restart-purchase-controller.md).

## Result

The source-level stall concern is now reproduced with the real miner and
auto-buy loop on synthetic state. Starting the miner with one surviving ticket
and an empty pool does not submit an initial replacement. After an explicitly
delivered notification, an injected submission failure receives no automatic
retry during the observation window. A direct purchase retry restores mining;
the subsequent canonical-head notification triggers another successful purchase.

Both newly mined blocks pass execution/import in a second in-memory chain.
This supports fixing purchase orchestration without changing ticket consensus.
It does not yet establish a production-ready retry implementation.

## Test and evidence

`TestAutoBuyRuntime` in [the restart tests](../tests/restart/autobuy_test.go) runs
in a child process because the existing auto-buy service uses global state and
has no shutdown API. It exercises:

- The ordinary miner, including preparation, finalization, signing, sealing,
  transaction-pool events, and canonical-head notification.
- The real Fusion transaction API, default ticket arguments, gas estimation,
  nonce selection, raw transaction submission, and real pool admission.
- A temporary keystore containing only the existing public synthetic test key;
  the account manager and wallet perform transaction signing.
- Independent RLP round-trip and `InsertChain` execution of the mined blocks.

The test constructs fourteen setup blocks so the sealer has the ten-header
history its delay calculation requires. It adapts the jump timestamp to one
hour before the test's wall clock and uses perpetual setup tickets to keep the
fixture usable after October 2026. These are synthetic fixture inputs, not a
proposed mainnet recovery sequence or endorsement of perpetual launch tickets.
Neither system time nor production code is changed.

| Stage | Observed result |
| --- | --- |
| Start actual miner and enable auto-buy; pool empty | Mining flag true, zero purchase builds, no head advance for three seconds |
| Deliver one notification; inject one temporary failure at `SendTx` | Default purchase reaches estimation and wallet signing, then submission fails |
| Leave miner and auto-buy running | No further purchase build, pool remains empty, no head advance for three seconds |
| Call the existing purchase API explicitly again | Purchase accepted; miner produces height 15,130,095; verifier imports it and finds the replacement ticket |
| Allow ordinary head-change notification | Automatic purchase accepted and mined at height 15,130,096; verifier imports it and finds the next ticket |

The baseline run is recorded in
[the complete test output](evidence/restart-2026-09-23/synthetic-autobuy-baseline-tests.txt).
The [parent-time overlay run](evidence/restart-2026-09-23/synthetic-autobuy-parent-time-tests.txt)
also exercises this runtime scenario alongside the reconstruction correction.
The suite now has ten top-level tests covering 22 leaf cases. Earlier defect
characterizations remain intentionally passing when they reproduce known
reconstruction failures. This is not an audit-completion or launch-readiness claim.

Three seconds is a bounded runtime observation, spanning several configured
one-second miner recommit intervals. The stronger explanation comes from source:
the auto-buy loop has a channel receive and no retry timer; enabling only sets
the flag, and head writes are the notification producer. The test does not prove
that every external system or future client can never retry.

## Limits and remaining cases

The initial run used Windows amd64, Go 1.21.3, CGO disabled. Subsequent
[Linux/CGO and race runs](restart-linux-investigation.md) reproduce the behavior
and identify a separate miner receipt-log race. The revised fixture stops the
producer before importing both mined blocks in the verifier, avoiding concurrent
two-chain access to process-global parent headers. It uses an adapter over the
real in-memory chain/pool, rather than the full `eth.Ethereum` service or JSON-RPC
transport. The cold-start condition is a newly created miner and empty pool on
existing state; it is not a disk-database restart or journal recovery test. The
second verifier shares a process with the producer and therefore the global
ticket cache. No public network, recovered database, or real staking key is used.

The original runtime test injects submission failure. Locked-wallet, estimation, insufficient
funding, nonce conflict, dropped purchase, same-height reorganization, journal
restoration, and long outage/expiry cases remain. The current purchase cache is
keyed by block number and owner; successful submission is not the same as
inclusion, so retry behavior must account for it rather than blindly resubmit.

The follow-up `TestSubmittedTicketReplacementBlocksBuilderRetry` now confirms
one non-inclusion case using the real API, wallet and pool: a synthetic purchase
is accepted, then a higher-fee same-nonce ordinary transfer replaces it. The old
purchase disappears from the pool, but a new purchase request at the unchanged
head still fails with `Purchase of BuyTicket for this block already submitted`.
All three Linux race-detector repetitions reproduced this. The miner is not
started in this bounded cache test; it establishes retry rejection, not that
every chain with additional producers would stall. See
[the raw result](evidence/restart-integrity-2026-09-23/purchase-replacement.txt).

## Required operational behavior

An initial purchase check must run when mining is enabled or resumed. Retry
recoverable failures without requiring the chain to advance. Confirm actual
pending transaction and ticket state, classify terminal errors, preserve nonce
and one-purchase-per-owner constraints, and expose failures to the operator.
Evaluate a small purchase controller/watchdog before changing consensus rules.

After a successful submission, track inclusion and the surviving ticket rather
than treating the returned transaction hash as completion. Test recovery when
submission succeeds but the transaction later leaves the pool. Adequate ticket
runway and independent producers remain separate launch requirements.

Before implementing a retry timer, resolve the accepted-but-not-included state.
The controller must distinguish its exact pending transaction from another
transaction consuming the nonce, and re-evaluate after a head-hash change even
when the height is unchanged. A boolean keyed by owner and height cannot answer
either question. Preserve the consensus one-purchase-per-owner constraint;
submission throttling is a separate client concern.

For the historical bridge, use the explicit reviewed sequence and transaction
arguments, with auto-buy disabled until the head reaches the agreed transition.
For ordinary operation, run an initial evaluation when mining starts, then
reconcile head/tickets, the submitted transaction and pool/nonce state before
retrying. Surface wallet/funding/nonce conflicts; do not silently produce new
signed alternatives. Durable transaction recovery and journal/reorg tests remain
implementation gates. The three narrow corrections do not claim to solve these.
