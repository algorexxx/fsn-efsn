# Exact pending-purchase delivery

27 September 2026, baseline `7f7697b`. Tests and evidence only; production
candidates remain P1–P15 and the selected launch sequence is unchanged.

Later follow-up: the [peer retry investigation](restart-peer-purchase-retry.md)
captures known-peer suppression and successful same-byte retransmission through
the actual handler. A two-process reconnect recovers the original purchase but
fails again on its automatic successor; the complete forty-four-block cold
audit passes. The new failure narrows the remaining P4 delivery work.

The [existing-funds experiment](restart-existing-funds.md) ended at block
15,130,111 with the donation's correctly numbered purchase pending locally.
This follow-up demonstrates recovery by submitting its **unchanged signed
bytes** directly to the surviving producer. Both owners then replenish under
their ordinary workers and automatic buyers. No additional funding, nonce
repair, replacement signature or state injection is used.

The Linux race-instrumented live test passes in **159.29 seconds**, including
shutdown and complete cold accounting. This is a bounded delivery/replenishment
result, not a completed partition/nonce-rollback rehearsal or a general guarantee
that peer propagation recovers automatically.

## Preserved input

The stopped failure starts at block 15,130,111, hash
`0xec993b33d085d74c03256109c866e825b7609a64a1a55a94b70a12daf27e54f9`.
The saved donation purchase is nonce 8, hash
`0xdfea27eab0a6b3cd87782ff072176c2daa98222c9e764fdcf30c0fc75f30737f`.
The entrant's saved purchase is nonce 26, hash
`0x2c58e7707f4b2ed8150b162e1cec9036fccb92eb68a2fe378e80030d185d5120`.
The exact public signed bytes remain in the preceding evidence directory and
the new historical-admission evidence.

A fresh C: copy uses 1,147,817,023 bytes across 612 files, including the required
manifests. Every copied file is hashed, and the source files are rechecked
unchanged afterward. Both services use public synthetic keys 2 and 3 in a
private network namespace with loopback only. No real keys, public peers or
additional original-backup copy are involved.

## Admission changes at the first live block

The actual transaction pool is initialized against three retained canonical
states without rewinding the database. A test-only chain view selects the
historical head while the database supplies its genuine retained state and
ticket commitments. Each fresh pool receives the same donation nonce-8 bytes
through `AddRemotes`, with ordinary remote pricing constraints.

| Recipient head | Canonical nonce | Remote admission |
| --- | --- | --- |
| 15,130,098 | 8 | Rejected: purchase start exceeds head time plus three hours |
| 15,130,099 | 8 | Accepted and pending |
| 15,130,111 | 8 | Accepted and pending |

The historical check passes in **0.23 seconds**. At the earlier head, time is
1,790,459,840; the purchase starts at 1,790,488,672, which is 28,832 seconds later.
`BuyTicketParam.Check` rejects that difference before funding validation. The
next block advances time to the purchase start and refunds the donation's
selected ticket. The previous report's funding-rejection hypothesis therefore
does not describe the first validation error in this reproduced pre-import state.

This demonstrates a specific admission race: a node that already imported the
new block can send a valid purchase to a peer that has not imported it yet, and
that peer can reject it. Source inspection also shows that the handler marks
transactions as known before calling `AddRemotes` and ignores the returned
errors; the sending peer records them as known when queueing transmission.
The automatic buyer returns without submitting again while the same hash
remains in its local pool. These behaviors explain why local pending status is
insufficient evidence of delivery.

The original connection's acceptance flag and exact rejection were not captured.
This historical admission check does not retroactively prove that connection's
packet order. A deterministic protocol-level reproduction is still needed before
selecting any automatic retry change.

## Direct delivery and live continuation

Both actual services reopen with empty transaction pools, the exact saved
records and matching canonical nonces. Before connecting peers or enabling
mining, the test submits the donation's saved bytes through
`eth_sendRawTransaction` on the entrant. The returned hash and the recipient's
pending transaction must match the original. The originating node's record
remains byte-identical and its pool remains empty at this checkpoint.

This RPC submission treats the transaction as local to the recipient. It is
therefore an explicit delivery experiment, not proof of successful P2P admission.
The separate historical `AddRemotes` checks cover remote admission at the
specified heads.

Both mining services are enabled before either automatic buyer. The two original
saved purchases execute in the first new block, 15,130,112. The entrant continues
buying automatically through nonce 32; the donation's fresh nonce 9 executes at
15,130,118. Every required receipt is checked on both canonical chains for
successful native ticket creation, including owner and ticket identity.

The test records thirteen changes in observed pool/head state, including the
donation's fresh nonce 9 being present in both pools before inclusion. These are
periodic observations, not a packet trace or atomic snapshots of every subsystem.

After stopping the buyers and workers, two additional head changes occur while
previously scheduled work finishes. The test waits for a shared head unchanged
for 35 seconds, then cleanly terminates both services before opening their
databases independently. `miner_stop` alone remains insufficient as a custody or
handover barrier.

Final block: **15,130,120**, hash
`0x6150f27eca48b41ee3878462d677c46be40a497e3c2c0ba0390cad2601fad34a`.
Both databases agree on all forty suffix blocks, receipts, tickets and complete
account differences. The earlier thirty-one blocks match their retained artifacts
byte for byte. The nine new blocks contain nine successful purchases and no new
retreat; the last block is empty. Independent accounting checks every future
time-lock interval, rewards, fees, prior ordinary contributions and the previously
identified mature-lock conversion. Saved-record presence and bytes survive the
cold reopen unchanged.

| Synthetic account | Canonical nonce | Liquid FSN | Tickets |
| --- | --- | --- | --- |
| Donation | 10 | 22.603001816 | 0 |
| Entrant | 33 | 229.789584448 | 1 |
| Backup | 233,430 | 5.752721845480158626 | 0 |

The donation's last ticket is consumed during shutdown; its free 5,000-FSN rights
are returned. The complete remaining intervals are in `accounts-final.json`.
This short successful run does not create a reserve against another retreat.

## Failures retained and next boundary

The first launcher stopped before building because it did not request the root
WSL user needed to create a network namespace. The first historical test then
failed an incorrect expectation of an insufficient-balance error; the timestamp
error occurs first. After correcting that expectation, a second attempt was
refused by the immutable evidence writer because the initial output file already
existed. Giving each historical observation its own output path resolved the
harness issue. Both failed tests, their source snapshots, the launcher failure,
all executable hashes and the successful runs are retained in
[the evidence directory](evidence/restart-purchase-delivery-2026-09-27).

Next reproduce transaction-before-block delivery through the actual peer handler,
capture its admission result and known-transaction state, and test bounded
same-byte retry or reconnection. Do not delete the saved record or sign a new
nonce merely because a purchase remains pending. Preserve the timestamp rule and
funding checks; the evidence does not justify changing consensus validation.

The complete-state live nonce rollback/repair rehearsal, explicit reserves for
another partition, equal-weight convergence and independent release review remain
separate open gates. No production source or dependency changed in this follow-up.
