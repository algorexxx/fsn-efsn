# Recovery of an unsuitable saved ticket purchase

Status: funded synthetic recovery passes, 27 September 2026. An explicitly
signed self-transfer consumes the stale purchase's nonce; the existing
controller retires its record as **unconfirmed**, then creates fresh purchases
and resumes actual mining. A failed funding-order attempt is retained alongside
the pass. Only a new test and investigation documents are added. Production
P1–P15 and consensus rules remain unchanged.

## Source and deliberately seeded condition

Both attempts copy the stopped [nonce-abandonment result](restart-expired-nonce-neutralization.md)
from `D:\FusionRehearsal\expired-nonce-neutralization-2026-09-27`. They start at
block **15,130,130**, hash
`0x1c856076d9f7d8ab6f426a50684e581f48688e5dc41bb4bc81cee0f4d0d977cc`.
Donation has canonical/saved nonce 39, zero tickets and
2,021.976763487999978776 liquid FSN. Entrant has canonical nonce 44, an already
included saved purchase at nonce 43, one ticket and about 2,033.54 liquid FSN.

The original saved donation purchase is still within its native validity
window. To test the stale-record condition without changing clocks or creating
future blocks, the fixture signs a different nonce-39 purchase using the public
synthetic key. Its 30-day interval begins two days before the source head and
ends 28 days after that head, so it fails the existing 29-day remaining-window
check. The fixture preserves the original bytes and records both transactions,
then writes the stale bytes to the copied donation database **once before
starting either node**. It verifies that the canonical head is unchanged.

This record injection is test setup, not a production recovery instruction or
proof that the real controller previously created this exact transaction. The
subsequent recovery does not manually delete or rewrite the record. No state
balance, block, ticket or consensus parameter is edited. Both services use real
miners, ordinary peer networking and local RPC inside a loopback-only namespace;
the held-signature worker is not used. Only public synthetic keys 1–3 sign.

Each fresh copy contains **599 source files / 1,148,250,467 bytes**, with hashes
checked before/after copying and again after the attempt. All source files
remain unchanged. Attempts and results are kept separately:

| Attempt | D: directory suffix | Live result | Cold result |
| --- | --- | --- | --- |
| Transfer takes entrant's next purchase nonce | `stale-intent-2026-09-27` | Fails after 76.74 s | Pass, 22.49 s; unchanged 50-block suffix |
| Transfer follows entrant's pending purchase | `stale-intent-ordered-2026-09-27` | Pass, 159.75 s | Pass, 35.96 s; matching 60-block suffixes |

## Funding order matters when only one eligible ticket remains

The initial attempt starts donation's real miner/buyer with the stale record.
For 12 seconds the saved bytes and canonical nonce remain unchanged, the owner's
pool stays empty, and actual pool RPC on both nodes rejects the transaction for
its encoded end time. It then submits two planned ordinary transfers: 1,200 FSN
from synthetic backup nonce 233429 and 1,800 FSN from entrant nonce 44.

Entrant's controller retires its already confirmed nonce-43 record, sees the
pending transfer at 44, and correctly avoids signing a purchase over it. Its
existing sole ticket cannot seal a continuation containing only those transfers:
finalization rejects a block that would leave no ticket. Logs retain both
`account has another pending transaction` and
`Next block doesn't have ticket, wait buy ticket`.

Neither transfer executes within 60 seconds. The separate cold audit confirms
the same head, all account inventories and every one of the **200 JSON/RLP
canonical artifacts** are unchanged. The stale donation record survives. This
is an actual sequencing failure, not an expired-purchase recovery pass or a
reason to relax ticket validation.

On a fresh copy, the corrected attempt starts entrant's buyer first and waits
for its ordinary automatic nonce-44 purchase to be saved and pending. It then
places the 1,800-FSN transfer at **nonce 45**, after that purchase. The existing
funding helper checks the donor's saved/pending state before submission. Both
transfers and the unchanged automatic purchase execute at **15,130,131**.

| Synthetic sender | Amount | Sender nonce | Gas cost |
| --- | --- | --- | --- |
| Backup | 1,200 FSN | 233429 | 0.000042 FSN |
| Entrant | 1,800 FSN | 45, after purchase 44 | 0.000042 FSN |

These are transfers of existing balances, not minting. Synthetic backup signs
only its transfer and produces no block. This experiment does not establish
available real funding or authorize spending the borrowed real wallet's funds.
The 3,000-FSN amount works for this exact state and schedule, not every future
retreat or funding requirement.

## Funding does not cure an unsuitable interval

After canonical funding, donation has exactly
**5,021.976763487999978776 liquid FSN**, sufficient for a 5,000-FSN purchase and
the tested gas budget. Nevertheless, another 12-second observation window
retains the same stale bytes, nonce 39 and empty donation pool. Both nodes
continue to reject the same signed transaction with:

```text
BuyTicket end must be greater than latest block time + 1 month
```

There are **48 recorded real RPC expiry rejections** in the passing attempt:
two nodes at each of 12 observations before and after funding. Donation's miner
and buyer remain enabled throughout. The controller never renews the interval,
signs around the record or admits it simply because funds have arrived.

## Explicit nonce consumption and automatic continuation

The owner then uses existing `eth_signTransaction` to sign a nonce-39 ordinary
self-transfer: zero value, empty data, 21,000 gas at 2 gwei. Its exact raw bytes
are submitted directly to entrant through `eth_sendRawTransaction`. Both nodes
confirm canonical success at **15,130,133**, with no BuyTicket log. The cost is
**0.000042 FSN**; it creates no ticket and refunds no stake.

The controller observes the canonical nonce advance, finds no canonical receipt
for the stale purchase, and logs exactly one
`Automatic ticket nonce consumed without a confirmed purchase` event. It
retires the stale record through its existing reconciliation path and starts a
fresh automatic purchase. No new miner/buyer start command, manual purchase
submission, durable-record edit or funding transfer follows abandonment.

Both nodes verify successful native receipts for fresh donation purchases:

| Donation nonce | Canonical inclusion |
| --- | --- |
| 40 | 15,130,134 |
| 41 | 15,130,136 |
| 42 | 15,130,138 |

Donation signs blocks **15,130,135**, **15,130,137** and **15,130,139** using the
ordinary worker. Entrant also continues automatic purchases and signs seven
of the ten new blocks. The stale purchase never acquires a canonical receipt.
After disabling both buyers/miners, observing a stable common head and cleanly
stopping the services, both finish at **15,130,140**:

```text
hash:    0x81678c972fdd0e173589b25e7f7868833b9a65407218b88ad5925ca20762a061
state:   0xa6e8dd84ed55a5654a0ace9169797dc8b739d01f0b2c091f563bdbca40aa3b38
tickets: 0x9f611beb2c2583742ecede7089d054f6ed9f3d4d38c0f29d01b8b2cd170435ed
```

## Cold accounting, scope and next case

Both complete 60-block ledgers reconcile all accounts, receipts, purchases,
ordinary transfers, rewards, gas and future time-lock boundaries. Their 240
canonical JSON/RLP artifacts match byte-for-byte; the preceding 200 artifacts
also match the source. No new retreat occurs in the ten-block continuation.
All race-enabled runs are free of race warnings, including the retained live
failure. Cold intent bytes and nonces match the stopped-service observations.

| Synthetic owner | Final nonce | Tickets | Liquid FSN |
| --- | --- | --- | --- |
| Backup | 233430 | 0 | 5.752721845480158626 |
| Donation | 43 | 0 | 22.914221463999978752 |
| Entrant | 52 | 1 | 235.728364800000021248 |

Donation's next nonce-43 purchase is saved and pending at shutdown. Its last
ticket has been selected, leaving free time locks sufficient for the pending
interval. Its zero ticket count at this deliberately stopped point does not
erase the observed fresh purchases and canonical mining, or establish an
unattended funding failure. Continued operation after restarting this particular
saved successor remains the next bounded lifecycle check.

The inherited `AdditionalFunding` audit map contains 34 allowlisted ordinary
transactions: 31 prior self-transfers, two funding transfers and the new
self-transfer. Only the two positive transfers add funds to donation. The
independent verifier checks both attempts, exact signed inputs, all inclusion
identities, original-prefix equality, expiry observations, no false stale
receipt, fresh native purchases, source hashes and staged Git bytes.

This is a conditional manual recovery on a shared branch with an eligible
funded surviving producer. It does not establish automatic replacement, a
universal reserve, power-loss durability or safety against a later rollback of
the abandonment. Keep the earlier equal-weight first-contact failure separate.
Real funding, monitoring and responsibility for owner-approved abandonment
remain release decisions.

All processes are stopped. D: has about **139.7 GB** free and the WSL filesystem
about **63.9 GB**. No W: workload was required. Native logs use UTC+02; structured
observations use UTC. The [failed-attempt evidence](evidence/restart-stale-intent-2026-09-27/)
retains its original test source snapshot, because the final test implements
the corrected sequence. The [passing evidence and joint verifier](evidence/restart-stale-intent-ordered-2026-09-27/)
check manifests of **232** and **279** files respectively. No production file
changes in this batch.
