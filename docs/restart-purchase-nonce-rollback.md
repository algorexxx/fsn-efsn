# Ticket purchases after nonce rollback and miner competition

25 September 2026, baseline `bcbd1ce`. This continues the
[storage and peer-fork checks](restart-purchase-storage-and-peers.md).
The purchase-policy checks add tests, documentation and evidence. The real-miner
follow-up also reproduced an inherited shared-parent race and led to the separate
[parent isolation correction, P9](restart-parent-isolation.md). Ticket policy,
the pool's one-purchase rule and the automatic controller remain unchanged.

## Confirmed availability boundary

A compatible peer fork can remove more than one confirmed purchase by the same
wallet. Fusion's existing transaction pool retains only one ticket purchase per
owner. Reinserting several displaced purchases therefore does not necessarily
restore the complete nonce sequence. The automatic buyer preserves its latest
saved signed transaction and pauses when an earlier nonce is missing.

The actual-node test demonstrates this sequence:

1. At the common synthetic anchor, wallet 1 has canonical nonce 14. Its local
   branch includes purchases 14 and 15. The controller retires the saved
   nonce-15 record and signs/saves/submits its successor at nonce 16.
2. A heavier branch containing only wallet-2 purchases arrives through devp2p/full sync. It
   contains neither wallet-1 purchase, so wallet 1 returns to canonical nonce 14.
   The local pool reinserts purchase 14 and drops the other ticket purchases
   under its one-per-owner rule. The saved nonce-16 record remains unchanged.
3. The controller pauses because another ticket purchase is pending. A real
   wallet-2 worker includes purchase 14 again. Wallet 1 advances to nonce 15,
   but purchase 15 is missing from the pool. The controller reports that its
   saved purchase needs nonce 16 and does not invent a transaction for nonce 15.
4. A clean process restart with pool journaling disabled retains the same
   nonce-16 bytes and the same unresolved nonce gap.
5. The fixture explicitly resubmits the original signed nonce-15 purchase
   through the ordinary transaction RPC. Wallet 2 mines it; the controller then
   resumes with the exact previously saved nonce-16 bytes.

Checks cover both displaced canonical receipts becoming unavailable, unchanged
saved bytes across each pause, a full retry interval without extra pool entries,
native purchase-result logs for the two repaired nonces, matching peer heads and
state/ticket roots, and exact successor recovery. The two missing-nonce purchases
are taken from the original test blocks; they are not newly signed replacements.

This is safe refusal rather than unattended liveness. Restarting the node alone
does not repair the demonstrated gap. Recovery in this experiment depends on a
second eligible miner remaining available to include the earlier purchases.
It does not prove recovery when no available signer has a usable ticket.

## Operational policy to review before release

Preserve the signed automatic-purchase record, displaced blocks and relevant pool
journal before attempting a repair. Determine the canonical account nonce and
which original signed transactions have become unconfirmed. Inspect their native
payloads, interval validity and current funding/admission requirements before
resubmitting them. A prior receipt on the discarded branch is not current proof
of inclusion.

For the tested case, resubmitting the missing purchases one at a time, in nonce
order, and waiting for canonical native-purchase success restores progress. Bulk
resubmission is unsuitable because the pool can evict another ticket purchase
from the same owner. Do not delete the later saved intent merely to silence its
warning. If old bytes are expired, underpriced, unavailable, or conflict with
another transaction, this tested recovery procedure is insufficient; review the
specific nonce resolution separately.

Before release, decide whether monitored manual repair is acceptable or whether
to add a separately reviewed automatic recovery mechanism for known displaced
transactions. The current candidate does not promise unattended recovery from
every compatible reorganization. No extra finality or reorganization limit is
needed to explain or reproduce this behavior.

The warning text identifies the needed/current nonce, but its current `%s` hash
formatting emits raw hash bytes in some errors. The retained logs demonstrate
this diagnostic limitation. Obtain transaction identity from the retained
record/block data; human-readable hash formatting remains a P4 review item.

## Two real miners

The companion experiment gives separate actual node services public test keys
1 and 2. Both normal miners and automatic buyers run while the nodes are
disconnected. Each node is stopped after its first confirmed purchase, bounding
the discarded purchase history to one per owner. The nodes then connect and
synchronize the heavier branch, restart both normal miners/buyers, and continue
producing on the shared chain.

The checks require distinct worker-produced blocks with a common anchor
parent, at least three further blocks after joining, subsequent purchases from
both wallets, successful native purchase-result receipts, and agreement on the
final persisted heads, account-state root and ticket root. Only after real mining
has finished does the test hold block signatures, allowing a stable inspection
of each next-nonce saved purchase and pool entry across another retry interval.

An initial run passed (77.65 seconds); a repeat converged but exposed the inherited
DaTong global-parent race. That repeat is a failed concurrency check, despite
its successful state/purchase assertions. The narrowly corrected P9 run passes
with race detection (98.37 seconds). The resulting candidate list has nine
permanent rows; this concurrency correction is explicitly separate from P4.

The initial runtime attempt used an existing five-second miner-start check and
timed out after reconnecting. The revised test waits for an explicitly stopped
state before starting again and permits twenty seconds for startup. The worker
can hold its mutex while waiting for its next timestamp; `Miner.SetEtherbase`
needs that mutex before starting. This is a bounded harness readiness allowance,
not a production timing change. The test also stops each isolated miner as soon
as its own purchase is included, separating this case from the multi-purchase
nonce rollback above.

## Fixture and scope

These are sparse synthetic state fixtures. The parent starts with exactly two
explicit public-key tickets and one million synthetic FSN per public account.
Fourteen normally executed/imported blocks buy tickets for both owners and
alternate producers before setting the shared test anchor. The generous funding
isolates concurrency and nonce behavior; it does not validate the real donation
wallet's funding or alter any preserved backup. Earlier
[full-state handover accounting](restart-full-state-handover.md) is separate.

All peer tests run under Linux's race detector, with separate LevelDBs, encrypted
public keystores, private IPC and a network namespace containing only loopback.
The short database paths live in Linux `/tmp`. No real key, public peer, original
backup, complete-state dataset or W: restore is accessed. The source retains its
normal slot timing and ticket economics.

Initial fixture failures are retained: deleting every old ticket before adding
the synthetic tickets caused lazy state loading to restore the old list; taking
the deletion snapshot after insertion also captured a newly inserted ticket;
and a create-only artifact writer refused to overwrite the temporary node
configuration. The final fixture snapshots the old IDs first, inserts the two
new tickets, removes the old IDs, asserts exactly two tickets, and writes the
temporary configuration with the appropriate file operation.

One repeated rollback run required five peer blocks to exceed the local weight.
The downloader then entered a binary ancestor search outside the sparse fixture's
available history and received an empty header response. The final construction
uses the first-ranked eligible public signer for each of three peer blocks,
still buying only for wallet 2. Ordinary `Prepare` determines rank and difficulty;
no weight is fabricated. Three such blocks exceed the two-block local branch,
and the downloader's initial ancestor sample includes the shared anchor. This
keeps the test within its deliberately available history; it is not evidence
for full-history synchronization or a production downloader fix.

This bounded work does not cover every fork depth, multiple successive
partitions, prolonged packet loss, all pool reinjection orders, unavailable
missing transactions, power loss, or independent operator deployment. The
production anchor is still unset and independent review remains required.

Raw logs, scripts and identities are in
[`restart-purchase-rollback-2026-09-25`](evidence/restart-purchase-rollback-2026-09-25).
