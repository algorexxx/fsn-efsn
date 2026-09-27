# Uninterrupted complete-state partition and funded repair

27 September 2026. Production baseline `b2e3ab5`. The
[previous funded continuation](restart-funded-gap.md) passed after restarting a
preserved failure. This experiment keeps both services, miners and automatic
buyers running from the initial partition through funding and manual repair.
Only test harness and documentation files change.

## Setup and acceptance

Fresh copies of the retained participant checkpoint contain 560 verified files /
1,040,745,262 bytes. They reside at
`D:\FusionRehearsal\live-funded-partition-2026-09-27`; the source remains at
`tmp/full-state-participant-2026-09-26-attempt-03`. Both copies start at
15,130,090, hash
`0x71fda3d5913b4f0ae5ea48fb1512bf3f1706a2b42a4d9358b1cd890f95ff8674`.
The previously verified genuine historical segment is installed below the
synthetic parent without changing active heads. No original backup restore is
performed. D: has about 159.1 GB free after copying.

The live test checks each producer's ticket eligibility and next-purchase
backing before injecting 90 seconds of kernel packet loss. It preserves branch
bodies under their original hashes throughout reconnection, waits for ordinary
convergence and a stable saved-purchase nonce gap, and retrieves all missing
original signatures through the existing production RPC before repair.

For an unfunded first purchase, the planned ordinary transfers are 1,200 FSN
from the synthetic backup and 1,800 FSN from the continuing producer to the
stalled producer. The continuing producer's transfer is sequenced after its
exact pending automatic purchase. A changed donor nonce/intent stops the
attempt; there is no replacement signature, manual saved-record clearing,
miner restart or consensus change. Both transfers require successful canonical
receipts on both nodes before repair proceeds. The synthetic backup mines no
further block or ticket and its test signature authorizes no real spending.

Acceptance requires sequential native success for every missing original,
automatic execution of the unchanged saved intent, two fresh automatic
purchases, continuing donor purchases, stable matching shutdown heads and cold
accounting of both canonical histories and both isolated branches. The separate
cold audit also runs if the live phase fails. Funding is a conditional experiment,
not an approved real reserve or unattended-recovery policy.

## Result

The live race-enabled test **fails after 562.48 seconds**. The separate cold audit
**passes in 30.53 seconds**, and the historical pool-admission diagnostic
**passes in 0.14 seconds**. There is no race report. An initial test-only compile
error (`head.Hash` is a field, not a method) was corrected before starting any
node; the failed build log and source hashes remain retained.

Both producers pass the reserve gate at 15,130,093. Kernel packet loss drops
44 packets, and both isolated branches reach 15,130,099, diverging at 15,130,095.
They keep producing during reconnection. Ordinary heavier-branch synchronization
converges on the entrant's branch; no manual reconnect, downloader call, mining
restart or fork-choice override is used. This reverses the winning/losing roles
from the previous restarted repair.

The donation fixture now has canonical nonce **10**, saved nonce **17** (hash
`0xe8d24daf9dabf9ee5bb2e3ee11b54165c2aa84fd11f3ee6a0fea499379e627ff`)
and an empty pool. Its two first retreats occur at 15,130,096 and 15,130,099.
It has no tickets, 2,022.603065487999978776 liquid FSN and only future rights
covering the original purchase's missing interval. The unfunded submission is
rejected. The observer recovers all seven original nonces **10–16**, including
three in blocks mined after packet flow resumed (15,130,100–102). Existing
block-hash/index RPC returns their exact signatures; no cold restart is needed
to recover those block locations.

The synthetic backup's nonce-233429 transfer and entrant's nonce-16 transfer
execute at **15,130,104**, after the entrant's saved nonce-15 purchase. Both
funding receipts are canonical on both nodes; their total is 3,000 FSN. Miners
and buyers remain enabled. No donor nonce is replaced or saved intent cleared.

| Repaired donation nonce | Successful canonical height |
| --- | --- |
| 10 | 15,130,105 |
| 11 | 15,130,108 |
| 12 | 15,130,112 |
| 13 | 15,130,114 |
| 14 | 15,130,117 |
| 15 | 15,130,120 |

Intervening purchase admission waits rely on ordinary selection/return. The last
rejected samples are about 12–38 seconds after the individual waits begin; the
two-second retry interval bounds the sampling delay. No additional retreat occurs
during funding and repair.

## Remaining manual transaction stalls

Donation's ticket is selected at **15,130,121**. At 11:56:51 local log time
(09:56:51 UTC) its node admits
the unchanged nonce-16 purchase
`0xb48486a5a0d79ba11ed9c67107e7e83aa886c3309fbb9785fc7cbe21fd9b0e61`.
The purchase remains pending locally while the entrant advances the common
chain. It never obtains a canonical receipt within the test's 60-second bound.
Donation still has canonical nonce 16 and saved automatic nonce 17. The saved
purchase and fresh automatic successors are therefore **not reached**.

A fresh, checksummed diagnostic copy of the entrant database tests this exact
signed transaction through the real remote pool using retained historical
states:

| State used for remote admission | Result |
| --- | --- |
| 15,130,120, before donation selection | Insufficient balance |
| 15,130,121, after donation selection | Accepted and pending |
| 15,130,125, final cold head | Accepted and pending |

The diagnostic does not mine, rewind or move the canonical head. It rules out a
persistent funding/validity rejection at those later states. It does not prove
the exact wire-level reason the live receiving node did not include the purchase.
The live debug log samples the entrant pool as empty after local submission;
per-hash recipient admission and peer-known-set decisions were not captured.

Source review identifies a relevant limit of P4: its repeated send applies to
the saved current-nonce automatic purchase. Here the saved intent is nonce 17,
so reconciliation pauses at canonical nonce 16 before reaching that resend.
The manual predecessor's ordinary broadcast uses `PeersWithoutTx`; local
duplicate submission returns `already known`. Stale peer knowledge or an early
remote rejection is consistent with the symptom, but is not established by this
run's wire evidence. Increasing the receipt timeout alone is not a demonstrated
repair.

## Cold accounting and preservation

After test cleanup, both databases end at **15,130,125**, hash
`0x93ccd33c56bcdff1a572b381887f99eb0ca349af63b63ecffa63858b7cffef77`,
state root
`0x095be7b1b6b1d61ceee4794d44cea52183d39d498ee9bf19cb41101230061b0a`.
Both complete 45-block canonical JSON/RLP suffixes match. Both original
19-block isolated branches also pass independent accounting. The 35 new
canonical blocks include eight donation signatures and 27 entrant signatures;
there is no additional backup block.

| Synthetic owner | Cold canonical nonce | Tickets | Liquid FSN |
| --- | ---: | ---: | ---: |
| Backup | 233430 | 0 | 5.752721845480158626 |
| Donation | 16 | 0 | 24.478065487999978776 |
| Entrant | 32 | 1 | 229.477020776000021224 |

The ledger accounts for every purchase, ordinary transfer, reward, fee, selected
return, first-retreat interval loss and future boundary. Donation's exact saved
nonce-17 bytes remain unchanged. Entrant's own saved nonce-32 purchase remains
retained at shutdown. The failure occurs before the normal stopped-purchase
snapshot, so that particular live-versus-cold byte comparison is not claimed.

All 560 original source files and the initial ten canonical blocks remain
unchanged. The diagnostic copies 300 files / 574,033,058 bytes and independently
rechecks that its failed-run source remains unchanged. Both copies are stopped;
no rehearsal process remains. Final D: free space is about 158.2 GB. Preserve
both result directories and use fresh copies for any continuation.

Evidence: [runner, copy proof, source identities and logs](evidence/restart-live-funded-partition-2026-09-27/).

## Boundaries

The harness observes the saved automatic intent through its test-only
`lab_purchaseState` interface. Original displaced-transaction retrieval,
submission and receipt verification use existing production RPC, but this is
not yet a complete operator workflow using only production interfaces. The
[operator procedure](restart-operator-recovery.md) still requires offline
inspection if the exact saved intent was not retained beforehand. Head polling
also does not guarantee capture of every unobserved fork.

Repeated-loss recovery, connected equal-weight branches, actual authorized
reserves, monitoring/response coverage and independent release review remain
separate gates. The possible [surviving node](restart-surviving-node.md) remains
unverified while its enode is pending. No real keys or public network are used by
this rehearsal, and no additional production patch is introduced.

The [manual-predecessor follow-up](restart-manual-purchase-delivery.md) now
captures remote rejection, known-peer suppression and successful exact-byte
retry/reconnect in controlled protocol cases. Direct delivery on fresh restarted
copies also recovers this predecessor, both saved intents and fresh automatic
successors without new funding. Its first shorter-window attempt remains a
failure. Keep these results separate from this failed uninterrupted run; its
exact wire-level sequence was not recorded. No additional runtime patch follows
from the controlled reproduction or restarted recovery.
