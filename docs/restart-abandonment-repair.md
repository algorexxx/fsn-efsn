# Exact transaction recovery after abandonment rollback

Status: complete-state synthetic pass, 27 September 2026. On fresh copies of
the [preserved rollback](restart-abandonment-reorg.md), the original self-transfer
and three displaced purchases execute again without re-signing. The unchanged
saved purchase then executes automatically, followed by two fresh successors
and actual production by both owners. Both cold 86-block ledgers agree.

## Starting state and scope

The source is `D:\FusionRehearsal\abandonment-reorg-2026-09-27`, at block
**15,130,148**, hash
`0xd20a058d9830fb8b93df0e4ecb0874132c40254020ae3ea3d0ed646434ab3347`.
The fresh target is `D:\FusionRehearsal\abandonment-repair-2026-09-27`.
All **618 source files / 1,148,513,319 bytes** are hash-checked before/after
copying and again after the experiment. The source remains unchanged.

Donation starts at canonical nonce **39**, with zero tickets,
**5021.976763487999978776 FSN** liquid and its original saved nonce **43**:

```text
0xddb72dc7336546fdbe48be0570dca20587a77c51aa5e61d3664d468e7f04097a
```

Entrant starts at nonce 63 with one ticket and existing time-lock backing.
Its inherited saved nonce-43 record is already canonically consumed and is
reconciled normally when its buyer starts. Both nodes' preflight inventories
match their preserved cold inventories exactly.

Fresh services use synthetic keys 2 and 3, initially empty pools and the existing
loopback-only harness. They connect through ordinary peers and start their real
miners and buyers once. No held signer, new partition, forced synchronization,
new funding, account edit or manual purchase-record edit is used. This is a
restarted continuation of the rollback result; it does not combine the earlier
reorganization and this repair in one uninterrupted service session.

## Sequential recovery

Before submission, existing block-hash/index RPC recovers all four displaced
transactions byte-for-byte. Their canonical lookups and receipts are absent.
The test submits the existing nonce-39 self-transfer to donation's pool:

```text
0xdfe37cb273c558caad05568f61fc1096f8b1752af99dddf80e9c8adcad19fd83
```

It succeeds at **15,130,149**, on both nodes, with 21,000 gas, no logs and no
ticket creation. Its 2-gwei gas price yields **0.000042 FSN** in canonical fees.
Donation advances to nonce 40 while its saved nonce-43 record remains unchanged.
This replays the prior decision to abandon nonce 39; it does not sign another
abandonment transaction or revive the previously retired stale purchase.

The existing manual-repair helper then retrieves and checks purchases 40–42,
submits them one at a time and requires matching canonical native success on
both nodes before proceeding. Purchases 41 and 42 initially fail for insufficient
available stake while the preceding ticket is live. Normal ticket selection
returns the needed time-lock rights, after which the same bytes are admitted.
No principal is added and validation is not relaxed.

| Donation nonce | New inclusion height | Action |
| --- | --- | --- |
| 39 | 15,130,149 | Original zero-value self-transfer, manually replayed |
| 40 | 15,130,150 | Original purchase, manually replayed |
| 41 | 15,130,153 | Original purchase, manually replayed after ticket return |
| 42 | 15,130,156 | Original purchase, manually replayed after ticket return |
| 43 | 15,130,160 | Exact saved purchase, automatically submitted |
| 44 | 15,130,162 | Fresh automatic purchase |
| 45 | 15,130,164 | Fresh automatic purchase |

All four replayed transactions retain their original hashes and signed fields;
their new canonical receipts point to different blocks from the displaced
history. Existing direct-delivery assistance is available only for a manual
predecessor that remains locally pending and absent remotely. **No direct
delivery is needed in this run.** Saved 43 receives no manual submission.

The live acceptance point is shared block **15,130,164**. Donation has made six
purchases and produced five blocks; entrant has made eleven purchases and
produced eleven blocks. Both buyers and miners remain enabled throughout repair
and continuation. No further start command is needed.

## Shutdown and independent accounting

After stopping both workers, observing a stable common head for 35 seconds and
closing both services, the final head is **15,130,166**:

```text
hash:    0xf3ce6a477394ee65876edc6e331addfce50bf3124967558a1301a744820522be
state:   0x18d3ed963a365edb0e0afdd303431f42550c81864aaedb985c6cc8edceaed80e
tickets: 0x61372addbf3fc56a1de8f4c08da57e47f85a8c482a1b65c50eeab7739d753e18
```

The full eighteen-block continuation has donation purchases 40–45, entrant
purchases 63–74, six donation-produced blocks and twelve entrant-produced
blocks. No new retreat occurs. The sole ordinary transaction added after the
starting head is the original self-transfer. The earlier 33 ordinary transactions
remain at their original heights; the cold audit's inherited `AdditionalFunding`
map now contains 34 entries, without any new positive funding transfer.

The race-enabled live test passes in **248.05 seconds**. The separate cold
audit passes in **52.52 seconds**, with no race warnings. Both complete
**86-block** ledgers reconcile account differences, gas, rewards, receipts,
tickets and future time-lock rights. Their **344 JSON/RLP artifacts** match
exactly. The **272 artifacts** covering the original 68-block prefix remain
identical to the source. The backup inventory is unchanged and it signs nothing.

| Synthetic owner | Final nonce | Tickets | Liquid FSN | Own saved intent |
| --- | --- | --- | --- | --- |
| Backup | 233430 | 0 | 5.752721845480158626 | Not used |
| Donation | 46 | 0 | 23.851721487999978776 | Nonce 46, pending |
| Entrant | 75 | 1 | 242.915864776000021224 | None |

Donation's next purchase is saved and pending at the deliberate shutdown. Its
time-lock rights remain in the cold inventory. A zero ticket count at this
stopped checkpoint does not erase the observed production or demonstrate a live
funding failure. Cold nonces and saved bytes match the stopped services.

The [397-file evidence bundle and verifier](evidence/restart-abandonment-repair-2026-09-27/)
retain source identities, raw predecessor bytes, admission/propagation logs,
native inclusion observations, complete cold ledgers and exact stopped records.
Verification checks source hashes, independent RLP fields, changed receipt
locations, canonical ordering, native owners, unchanged prefixes, no new funding,
no direct delivery and staged Git bytes. The outer `Final` in `repair-result.json`
records the settled head; the nested reusable helper's unused `Final` is zero.

All test processes are stopped. D: has about **136.0 GB** free; WSL has about
**63.9 GB**. No W: workload was used. Logs use UTC+02; structured observations use
UTC. Production P1–P15 and consensus rules remain unchanged.

## What this closes

The retained rollback now has a demonstrated manual recovery using existing
transactions and existing funds: repair the self-transfer's canonical inclusion,
replay the missing purchases in order, let the buyer execute its saved intent,
then require fresh automatic purchases and actual production. It does not make
the original pause automatic or establish a universal reserve.

For an operator, a changed branch means checking current nonces, receipts,
pending transactions, interval validity and funding again. A previously signed
self-transfer may already be pending or included. Preserve and verify its bytes
before deciding whether to replay it. Waiting for a ticket return is appropriate
only while that live ticket and its usable rights are actually present; the
earlier first-retreat funding failures remain relevant.

The remaining integration distinction is a live compatible rollback followed by
this recovery without stopping services or holding a signer. Keep that timing
case separate from the passing restarted continuation. Release review still
needs the chosen monitored/manual policy, alert delivery and response ownership,
real-address funding checks and independent review of the minimal patch set.
