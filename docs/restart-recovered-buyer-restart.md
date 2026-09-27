# Normal restart after stale-purchase recovery

Status: complete-state synthetic pass, 27 September 2026. Fresh services restore
the exact saved donation purchase from an empty transaction pool, execute it
through ordinary propagation, and continue automatic purchasing and mining.
Both cold 72-block ledgers agree. No new funding, manual transaction submission,
record injection or production change is made in this follow-up.

## Preserved starting point

The source is the stopped [stale-intent recovery result](restart-stale-intent.md)
at `D:\FusionRehearsal\stale-intent-ordered-2026-09-27`. The new disposable copy
is `D:\FusionRehearsal\recovered-buyer-restart-2026-09-27`. It contains **606
files / 1,148,381,204 bytes**, verified before/after copying and rehashed after
the experiment. All source files remain unchanged.

Both databases start at block **15,130,140**, hash
`0x81678c972fdd0e173589b25e7f7868833b9a65407218b88ad5925ca20762a061`.
Donation has canonical nonce 43, zero tickets, 22.914221463999978752 liquid FSN
and free time locks backing its saved purchase. Entrant has canonical nonce 52,
one ticket and no saved intent. The donation intent is:

```text
nonce: 43
hash:  0xddb72dc7336546fdbe48be0570dca20587a77c51aa5e61d3664d468e7f04097a
```

The earlier stale nonce-39 intent has already been retired. Its prior fixture
injection and the earlier 3,000-FSN funding remain part of the preserved
experiment's provenance; neither is repeated here. No balances, tickets,
blocks or durable purchase records are edited to prepare this continuation.

The test starts two new real services using the copied chain databases and
the existing synthetic harness configuration. Both transaction pools are
initially empty; no old pool journal is supplied. Only synthetic keys 2 and 3
sign. Networking is confined to a loopback-only namespace. This tests recovery
from a cleanly stopped database, not deployment configuration, machine reboot,
power loss or production key custody.

## Exact-byte recovery and ordinary continuation

Both startup heads and own-wallet records must match the stopped source.
Cold preflight inventories also match the preceding cold inventories exactly.
The services connect through their normal peer interface. Donation's miner and
buyer start first; entrant remains stopped as a producer during the observation.

Donation's buyer restores the exact nonce-43 transaction to its pool. Its saved
and pending bytes remain identical for **six seconds**, covering the existing
five-second retry interval. Both canonical heads remain unchanged. Donation
has no ticket yet, so its enabled mining flag alone is not counted as successful
production. No held-signature worker or manual raw transaction submission is
used.

Entrant's miner and buyer then start normally. The saved purchase propagates
and executes at **15,130,141** with matching successful native BuyTicket receipts
on both nodes. Its hash, nonce and raw signed bytes are unchanged. The controller
then creates and executes two fresh donation successors:

| Donation nonce | Inclusion height | Origin |
| --- | --- | --- |
| 43 | 15,130,141 | Exact saved transaction |
| 44 | 15,130,145 | Fresh automatic purchase |
| 45 | 15,130,150 | Fresh automatic purchase |

Donation signs blocks **15,130,144** and **15,130,149**. Entrant also continues
automatic purchases and mining. Both miners and buyers remain enabled during
the live continuation; there is no further start command or recovery action.
The live acceptance point is shared block 15,130,150, by which donation has
made three purchases and entrant eight.

After stopping the workers, observing a stable common head for 35 seconds and
cleanly closing the services, both finish at **15,130,152**:

```text
hash:    0x16fca2965fd9e86bf2bb90b7300928af94300da4080f7f57c90466bcd6159175
state:   0xdfd44f507cb0acf2ec98f8db5cb9172b4935cdaaaf3dec10458175268323c94a
tickets: 0x6fabbec11eb5baceb99e9d35779cbde5a1b025914a71932f83f7e8bd1a8494d5
```

The entire twelve-block continuation contains only ordinary ticket purchases:
donation nonces 43–45 and entrant nonces 52–60. Donation produces two blocks and
entrant ten. No new retreat occurs. The abandoned stale purchase still has no
canonical receipt; the restored nonce-43 purchase remains canonically included.

## Independent cold checks

The race-enabled live test passes in **179.83 seconds** and the separate cold
audit in **47.36 seconds**, without race warnings. Both **72-block** canonical
suffixes reconcile complete account differences, native receipts, tickets,
rewards, gas and future time-lock boundaries. Their **288 JSON/RLP artifacts**
match byte-for-byte. The **240 artifacts** covering the original 60-block
prefix remain byte-for-byte identical to the source.

The ordinary-transaction audit allowlist remains exactly the prior 34 entries,
all included before this restart. No new funding transfer or nonce-abandonment
transaction appears. The synthetic backup's complete inventory remains
unchanged, and it signs no transaction or block in this run.

| Synthetic owner | Final nonce | Tickets | Liquid FSN | Own saved intent |
| --- | --- | --- | --- | --- |
| Backup | 233430 | 0 | 5.752721845480158626 | Not used |
| Donation | 46 | 1 | 23.539200239999957528 | None |
| Entrant | 61 | 0 | 238.853386024000042472 | Nonce 61 |

Entrant's nonce-61 purchase is saved and pending at the deliberate shutdown;
its free time locks are retained in the cold inventory. Cold nonces and exact
saved bytes match the stopped-service observations. A zero ticket count at this
stopped point is not evidence of an observed live buyer failure.

The [324-file evidence bundle and verifier](evidence/restart-recovered-buyer-restart-2026-09-27/)
retain copy proofs, startup state, restored bytes, retry-window observations,
native inclusion, live progress, final inventories and both ledgers. The
verifier independently compares RLP transactions and canonical receipts,
checks sequential purchase nonces and ticket owners, confirms unchanged backup
inventory and historical prefix, and verifies source and staged Git hashes.

## What this closes and what remains

This closes the clean-restart continuation of the previously recovered buyer:
the durable successor survives, does not require re-signing or manual delivery,
and leads to further purchases and real block production with existing funds.
It does not establish indefinite unattended operation or a universal reserve.
The earlier funding-order failure and equal-weight first-contact failure remain
preserved and relevant.

The separate [abandonment rollback](restart-abandonment-reorg.md) now removes
the self-transfer and purchases 40–42 on fresh copies of this run's input.
It verifies canonical nonce 39, unchanged saved nonce 43, exact displaced-byte
retrieval and an explicit nonce-gap pause after an empty-pool restart. Both
68-block cold ledgers agree. This is a pause/data-preservation result with a
held signer and explicit downloader request, not another mining-continuation
pass. The subsequent [exact-transaction repair](restart-abandonment-repair.md)
now passes that sequential recovery on restarted copies, including unchanged
saved-intent execution, automatic successors, actual production and both
86-block cold ledgers. No new funds or direct delivery are needed. Combining
the rollback and repair in one uninterrupted live session, crash/power-loss
boundaries and operator response responsibility remain separate concerns.

All rehearsal processes are stopped. D: has about **138.5 GB** free and the WSL
filesystem about **63.9 GB**. No W: workload was needed. Native logs use UTC+02;
structured observations use UTC. This batch adds only a test and investigation
documents; production P1–P15 and consensus rules remain unchanged.
