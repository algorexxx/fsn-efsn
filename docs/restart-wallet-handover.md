# Recovery signer to continuing operator

On 24 September 2026 Peter selected a two-node launch: the backup wallet
`0x9fc4c40e50f902b9aa641b4a32ebaafa5c9386a1` signs one recovery block and buys
no new tickets; the donation wallet
`0xa3ce60d2dbf51afa0ab106df1c44a2e48853817a` then continues production and
replenishment. Both initial nodes are operated by Peter. Stop our use of the
backup owner's key after verified handover and return operation to him. He
remains free to run a node and buy tickets later. No account restriction, balance
confiscation or permanent dependence on the borrowed key is part of this plan.

This selects the launch arrangement. Exact real-signer recovery blocks,
accounting, runtime behavior and the accepted anchor still need rehearsal and
review before production signing or public use. No real keys have been used.

## Funding observation

The public donation address supplied by Peter is
`0xa3ce60d2dbf51afa0ab106df1c44a2e48853817a`. A native Windows read-only lookup
against the verified compact state at block 15,130,080 found:

| Field | Preserved value |
| --- | --- |
| Liquid FSN | 12,020.102 |
| Liquid wei | 12020102000000000000000 |
| Time-lock balances | None |
| Nonce | 0 |
| Code | Empty |

The source is the preserved 7 October 2025 block
`0xe93ffded087a79097d4309c7831690161db6ed136f4b1a22c4c83a99db80f99f`.
This is not a balance claim for any unknown continuation after that block.
Only public state was read. No donation key was requested, read, unlocked or
used, and no transfer or purchase was submitted. Peter subsequently selected
this donation wallet as the continuing producer; no transfer from the backup
owner's balance is required by this arrangement.

The 10,001-FSN synthetic successor budget succeeds: 5,000 for the first ticket,
5,000 available for replacement before the selection refund, and 1 for gas.
A separate case with exactly the donation wallet's observed 12,020.102-FSN
balance also succeeds. Relative to 10,000 FSN of staking/replacement capacity,
that balance leaves 2,020.102 FSN before transaction fees. These are short
rehearsal budgets, not an audited minimum for every time-lock schedule or
arbitrarily long operation. The stake becomes time-bound ticket rights; this is
not a claim that 10,000 FSN is consumed as a recurring operating expense.

A 5,001-FSN test funds the first ticket but fails its replacement with
`not enough time lock or asset balance`. Purchases execute before the selected
ticket refund. With only the successor's ticket remaining, the chain cannot
simply consume it and leave zero tickets. This demonstrates why funding one
ticket plus gas is insufficient for this particular standalone successor setup.

## Selected one-block startup

1. Prepare two nodes with separately writable, verified copies of the accepted
   data and one active signer per key. Keep the backup wallet's automatic
   purchases disabled from the outset, including after restart. Inventory and
   reconcile any existing pending purchases, nonces and purchase journals.
2. Construct the donation wallet's first funded ticket purchase before mining.
   Its start must fit the historical parent timestamp and its end must extend
   beyond the planned present-day jump, with the required ticket duration and
   operating margin. An ordinary 30-day purchase based on the old timestamp
   expires before that jump. Explicitly construct and submit this first purchase;
   the donation node cannot mine before its ticket exists in parent state.
3. The backup wallet signs exactly one historically timed recovery block,
   containing that donation purchase and no purchase from the backup wallet.
   Its selected historical ticket receives the normal remaining-interval refund.
4. The donation signer produces the next block at the planned jump timestamp,
   including a replacement purchase, and continues producing/replenishing.
   Clear the expired historical ticket set under existing rules and verify the
   complete recovery sequence independently. The jump block's purchase also
   needs an explicit interval spanning the jump; do not rely on the automatic
   buyer's historical 30-day default. After the head reaches the present-day
   timestamp, demonstrate ordinary automatic replenishment and cold restart.
5. Verify there are no backup-wallet purchases still capable of being included
   from the recovery operation. Stop the recovery instance/signing access and
   provide its owner current data, configuration and the accounting record.
   Coordinate custody so our signer and his node never sign concurrently using
   the same key. Returning a copied key does not revoke other copies.
6. Publish the release and recovery data enforcing the accepted restart anchor
   before opening ordinary economic use. Keep the donation producer running;
   other holders may join and stake normally. Neither a second permanent
   producer nor another organization is required for this initial arrangement.

The backup wallet has **two** historical tickets at the preserved head. One
backup block consumes only one by selection. Its other ticket has expired by
the jump and is removed by retreat or expiry processing, without a refund of
that expired interval. This is different from the earlier proposal to mine the
owner's final remaining ticket after a longer recovery bridge. Existing future
time-lock rights are not transferred to Peter; exact original-owner accounting
must accompany the real sequence. If refunding both selected historical tickets
before the jump is required, the one-backup-block constraint must be reconsidered.

`TestSingleBackupBlockHandover` demonstrates this shorter sequence with public
keys 1 and 2 and synthetic successor funding equal to the observed donation
balance. It uses the RPC purchase builder for the first long-lived ticket,
imports the sole original-signer block at 15,130,081, then imports five successor
blocks independently. The first successor block jumps to 23 September 2026;
the second clears the remaining expired ticket set, leaving one successor
ticket. No original-wallet transaction is submitted, and the original account
is byte-identical throughout successor-only production after its first refund.
In this fixture its other ticket is retreated in the jump block without a refund.
Real addresses alter ticket ordering, so that particular retreat slot is not a
production prediction. `TestSingleBackupBlockRejectsShortSuccessorTicket`
confirms that a first ticket ending 30 days after the old timestamp cannot seal
the jump and that rejecting it leaves the canonical head unchanged.

These sparse core tests pass on Windows and twice on Linux with race detection.
The subsequent [full-state handover rehearsal](restart-full-state-handover.md)
also passes complete-state independent imports, owner-by-owner accounting,
actual worker/automatic-buyer production, a failed submission and process
restart on both platforms. The [guarded two-node follow-up](restart-recovery-construction.md)
now also passes actual service/IPC/peer handover, ordinary mining immediately
after cleanup, SIGKILL restart and independent cold ledgers. Actual backup-wallet
purchase drain, production signing custody and supported data distribution remain open. The fixture's fixed dates and synthetic roots are
test inputs, not launch dates or a production anchor. Evidence:
[single-block rehearsal](evidence/restart-single-block-handover-2026-09-24).

**Mandatory jump purchase:** the follow-up also reproduces an accepted jump
block with only expired tickets remaining when the donation replacement is
omitted. Require that replacement and a usable successor ticket before signing
or publishing the recovery block. Keep the initial handover/jump/cleanup
construction controlled until those checks pass. The cleanup block rejects a
missing replacement, but the jump itself does not provide that protection.
The earlier worker run starts after cleanup and additional constructed donation
blocks. The two-node follow-up starts ordinary production directly after cleanup.
Neither permits unattended worker startup at the old historical head.

## Earlier final-ticket handover alternative

The earlier tested construction below uses four backup-signer bridge blocks
before its final handover block. It remains useful as a comparison, but is not
the selected one-backup-block startup.

1. Complete the historical bridge with the backup owner's authorized signer.
   Prepare Peter's separate node/wallet and prove its funding and purchase
   construction before draining the old signer. Keep one active signer per key.
2. Disable the backup owner's new automatic purchases, while allowing its
   already-owned tickets to produce blocks. Inventory its pending and queued
   purchases, automatic-purchase journal, nonce and canonical receipts. Resolve
   already signed purchases before declaring the ticket set drained. Clearing a
   local pool or journal cannot revoke a signed transaction known to peers.
3. Arrange the final-ticket boundary with the new wallet's funded purchase.
   One demonstrated form has only the old owner's final ticket in parent state:
   that owner mines a block containing the successor's first purchase. Execution
   creates the new ticket before finalization consumes the old one, so the block
   leaves one successor ticket. The old ticket's remaining time-lock value is
   refunded to its original owner under ordinary rules.
4. Have the successor produce and replenish without any new old-wallet
   transactions or signatures. Verify its blocks independently, restart it and
   demonstrate recovery. Check the original owner has no remaining tickets or
   unresolved purchases attributable to the recovery operation.
5. Stop the recovery instance/signing access and provide the owner current data,
   configuration and a record of transactions, rewards, refunds and any remaining
   time locks. Remove temporary key access under the agreed custody procedure;
   no deletion or key handling is performed by this investigation. Returning a
   copied key does not cryptographically revoke other copies. Coordinate the
   change so our recovery signer and his own node never sign concurrently with
   the same key. He can subsequently use ordinary staking on his own terms.

The final-ticket boundary is one tested construction, not a promise that every
overlapping-miner schedule consumes the old ticket through selection. If both
owners already have tickets, ordering, missed slots, expiry and retreats can
change which tickets survive and whether remaining time-lock value is refunded.
An exact accepted sequence must check those effects and the successor's remaining
tickets. Do not force the old owner to seal over a higher-priority successor
ticket and assume that successor ticket survives retreat processing.

`miner_stopAutoBuyTicket` currently changes the process flag. It does not remove
pending/queued transactions or the saved automatic ticket, and is not a durable
stop configuration. Launch flags such as `--autobt` can enable purchases again
after restart. A call already past its enabled check can also still be in flight.
The real-node rehearsal must cover shutdown/drain, restart with purchases
disabled, existing signed transactions and canonical reconciliation. Do not
claim the handover is complete from the RPC return value alone.

## Earlier final-ticket test result and scope

`TestLastTicketHandover` uses public keys 1 and 2 with the existing sparse
restart fixture. It explicitly installs synthetic funding for key 2 in that
fixture; it does not transfer the real donation balance or duplicate funding in
the preserved full-state artifact. The four-block bridge leaves the first key
with one ticket. Its final block, 15,130,085, includes only key 2's purchase.
The test checks:

- Selection of the first key's final ticket, without any retreat tickets.
- Zero tickets for the original signer and one for the successor after import.
- Exactly 5,000 FSN of additional time-lock coverage returned to the original
  owner over its ticket's remaining interval; the original nonce is unchanged.
- Four successor-only blocks with replacement purchases, independently imported
  into a second database with matching roots.
- Byte-identical original account state throughout that successor-only phase.
- Failure to fund a replacement with the deliberately insufficient budget.

The funded cases end at 15,130,089. The donation-balance case's final state root
is `0x19433a869668651aeb2dfbc4dcb6054ab08cc04bc7baf9dbad77992bd65147ef`.
This is an explicitly synthetic identity, not a proposed production anchor.
The existing last-ticket/no-purchase rejection is tested alongside it.

Windows passes the three handover cases and existing negative case. Linux runs
the same set twice with race detection in a private network namespace. This
earlier sparse result alone does not prove complete-state operation or key
custody. Complete-state execution, peer propagation and process restart are now
covered by the later reports linked above; actual backup-wallet purchase drain
and key-custody cleanup remain open. This earlier experiment changed no
production code or consensus rules.

Evidence: [restart-handover-2026-09-24](evidence/restart-handover-2026-09-24).
