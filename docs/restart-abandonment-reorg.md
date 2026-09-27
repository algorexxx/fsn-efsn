# Compatible rollback after purchase abandonment

Status: complete-state characterization passed, 27 September 2026. A heavier
compatible branch removes the nonce-abandonment transaction and three later
purchases. The account nonce rolls back from 43 to 39 while the exact saved
nonce-43 intent survives. The buyer pauses across an empty-pool restart. This
is a verified pause and retained-data result, not automatic recovery or resumed
block production.

## Preserved inputs and competing history

The local source is the [stale-intent recovery result](restart-stale-intent.md)
at `D:\FusionRehearsal\stale-intent-ordered-2026-09-27`, block **15,130,140**:

```text
hash: 0x81678c972fdd0e173589b25e7f7868833b9a65407218b88ad5925ca20762a061
total difficulty: 63370514801
```

It contains the successful nonce-39 zero-value self-transfer, successful native
purchases 40–42 and the saved nonce-43 successor. This is the same input used by
the independently passing [normal restart](restart-recovered-buyer-restart.md),
not a copy of that later 72-block result. Donation has zero tickets, canonical
nonce 43 and 22.914221463999978752 liquid FSN before this rollback.

The competing source is the earlier verifier at block 15,130,130 in
`D:\FusionRehearsal\expired-nonce-neutralization-2026-09-27`. Its existing genuine
historical bodies remain available. The test imports the exact original blocks
15,130,131 and 15,130,132, preserving both ordinary funding transfers. It then
constructs and validates **16** alternative blocks using synthetic key 3,
existing stake, ordinary purchases and the existing consensus rules. Only the
entrant purchases on this alternative suffix, at nonces 47–62. No donation
nonce is consumed. All constructed timestamps precede the actual wall clock.

Both branches share the recovery anchor and the exact prefix through
**15,130,132**. The competing source does not contain the old recovered tip.
No head is rewound, account state edited, new funding added or durable purchase
record injected. The earlier stale-record injection remains part of the local
source's provenance; it is not repeated in this test.

The disposable root is `D:\FusionRehearsal\abandonment-reorg-2026-09-27`.
All **605 source files / 1,148,293,681 bytes** are hash-checked before and after
copying and again after the experiment. Both source databases remain unchanged.

## Live rollback and cold restart

Fresh real services start with empty pools and pool journaling disabled, as in
the existing test harness. Only synthetic keys 2 and 3 are loaded. The donation
buyer restores the exact saved purchase and holds it unchanged for six seconds:

```text
nonce: 43
hash:  0xddb72dc7336546fdbe48be0570dca20587a77c51aa5e61d3664d468e7f04097a
```

The existing test-only held signing worker enables purchase reconciliation but
withholds block signatures. The entrant's miner and buyer remain disabled.
An explicit downloader request over the real loopback peer connection imports
the heavier branch. This tests compatible reorganization through the downloader,
not unattended peer discovery or competing live production. The downloader log
records an eight-block removal and thirteen-block adoption at the first heavier
tip, followed by the remaining three blocks.

The canonical donation nonce becomes **39**. The old self-transfer and purchases
40–42 have no canonical receipts. Existing block-hash/index RPC still returns
their exact signed bytes, checked throughout both twelve-second observation
windows before and after restart.

| Observation | Canonical nonce | Saved intent | Own pool | Buyer result |
| --- | --- | --- | --- | --- |
| Before peer import | 43 | Exact nonce 43 | Purchase 43 | Normal rebroadcast |
| After rollback | 39 | Same bytes | Self-transfer 39 and purchase 40 | Another ticket purchase is pending |
| Restart with empty pool | 39 | Same bytes | Empty | Needs nonce 43; current nonce is 39 |

The pool's existing one-ticket-purchase rule leaves purchase 40 rather than all
three displaced purchases. The self-transfer is an ordinary transaction and can
coexist with it. Neither pending status nor the buyer's enabled flag establishes
nonce repair. The cold restart deliberately removes transient pool assistance:
both services are stopped, only donation is restarted, and no journal or peer
restores the pool. The saved record alone does not reconstruct predecessors.

No transaction is manually submitted or newly signed during the live rollback
or cold observation. The held worker signs no block. The retired stale purchase
does not return as the donation node's saved intent or acquire a canonical receipt.

## Ledger and evidence checks

Both services finish at **15,130,148**, total difficulty **63370514808**:

```text
hash:    0xd20a058d9830fb8b93df0e4ecb0874132c40254020ae3ea3d0ed646434ab3347
state:   0x4e976c2d136266880aa3ff4c4acbdc3626f81fd23419576f6b4136082a96af90
tickets: 0x70e877e2091c463a5f727d3ba5e18bb0e8e4b44172590d4048a9a933dccf8746
```

The race-enabled live test passes in **70.22 seconds**, including the old and
competing branch audits. The separate cold audit passes in **34.46 seconds**.
There are no race warnings. Both **68-block** canonical ledgers reconcile all
account differences, receipts, rewards, gas, tickets and future time-lock
boundaries. Their **272 JSON/RLP artifacts** match exactly and also match the
prepared competing branch. The old 60-block ledger matches the source's 120
artifacts; the 52-block common prefix remains identical in every history.

The cold canonical ledger retains the preceding 31 self-transfers
and two funding transfers, all at their original heights. Only the latest
nonce-39 abandonment disappears. No new retreat occurs on the alternative suffix.

| Synthetic owner | Final nonce | Tickets | Liquid FSN |
| --- | --- | --- | --- |
| Backup | 233430 | 0 | 5.752721845480158626 |
| Donation | 39 | 0 | 5021.976763487999978776 |
| Entrant | 63 | 1 | 239.165822776000021224 |

Donation's original pre-abandonment funds and interval rights return because its
later purchases and rewards are rolled back. Both cold inventories exactly
match the independently prepared competing state. The backup inventory is
unchanged from the local source. Node-local purchase records are not consensus
state: donation retains its saved 43, while the never-enabled peer retains its
older inherited records. They are captured separately from canonical accounts.

The [563-file evidence bundle and verifier](evidence/restart-abandonment-reorg-2026-09-27/)
retain both histories, both cold ledgers, source hashes, raw RPC observations,
exact saved bytes, raw logs and source/binary identities. Verification checks
independent RLP fields, canonical receipts, native purchase owners, unchanged
prefixes, restored balances, retained raw predecessors and staged Git bytes.
All test processes are stopped. D: has about **137.3 GB** free; WSL has about
**63.9 GB**. No W: workload was used. Logs use UTC+02; observation times use UTC.

## Operational meaning and next test

An abandonment receipt can disappear in a compatible reorganization, like an
ordinary purchase receipt. The restart anchor protects the agreed ancestry;
both branches in this test contain that ancestry. This result calls for receipt
and nonce diagnosis after a branch change, not another consensus exception.

Preserve the saved successor and the original self-transfer/purchase bytes.
Recheck the current nonce, canonical receipts, pending transactions, interval
validity and funding. Do not clear the saved record, re-sign a successor or send
an additional abandonment just because the wallet is behind. The live pool may
already contain the original self-transfer; an empty-pool restart may contain
neither it nor the displaced purchases.

The next distinct rehearsal is to recover from a fresh copy of this paused
result: validate and resubmit the **same** nonce-39 self-transfer, require its
new canonical receipt, then recover purchases 40–42 in order, the saved 43 and
fresh automatic successors with actual production. Recheck funding and interval
admission at each stage; this test does not prove that continuation or a universal
reserve. Keep unattended equal-weight convergence, crash/power-loss boundaries
and operator monitoring responsibilities separate. Production P1–P15 and
consensus rules are unchanged; this batch adds tests and investigation evidence.
