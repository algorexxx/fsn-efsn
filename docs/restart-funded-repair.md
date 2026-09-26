# Funding manual purchase recovery

26 September 2026, baseline `950f682`. Investigation tests and documentation only;
production candidates remain P1–P15. This follows the
[small-reserve failures](restart-small-reserve-and-retrieval.md).

## Accounting question

A ticket represents 5,000 FSN over a specified interval. For a purchase funded
from liquid FSN, `core/state_transition.go` subtracts 5,000 liquid and preserves
the unused intervals as time locks. The default automatic purchase spans 30 days
(`common/fsnargs.go`). Rights after its end therefore survive independently of
the ticket.

`consensus/datong/consensus.go` returns a selected non-genesis ticket's remaining
interval as time locks. It removes the first retreated ticket without returning
that interval; later retreated non-genesis tickets are returned. Expired
intervals have no future value to return. With two ticket owners, an absent
owner's eligible ticket can be the first retreat, and repeated blocks can remove
more than one of that owner's tickets. This is inherited behavior, not a restart
patch. A future 5,000-FSN time lock is not necessarily usable stake today.

The new ledger uses the existing independent interval-accounting helpers from
the full-state handover investigation. At every interval boundary from each
block's timestamp onward, it totals liquid FSN, time locks and live tickets for
each known owner. Differences must equal ordinary rewards, transaction fees,
simple transfers and the first-retreat interval loss. Purchases and selected
ticket returns must conserve these rights. The synthetic low-height reward is
checked against an explicit 2.5 FSN, not the production reward function.

## Experiment

Two public test wallets still begin with 12,020.102 synthetic FSN each and one
or two tickets at the fully executed block-24 setup boundary. Public test key 3
has 6,000 synthetic FSN in genesis and never mines or buys tickets. Its inclusion
changes the synthetic genesis and descendant hashes; this is a new experiment,
not an exact replay of an earlier failed run.

The two real services mine through a 90-second packet-loss outage and ordinary
reconnection. The ledger checks both isolated branches before reconnection and
the common branch before repair. The affected owner's first original purchase
must be rejected for insufficient funds before the sponsor sends exactly one
ordinary 5,000-FSN transfer through the existing raw-transaction RPC. Both nodes
must confirm its successful canonical receipt.

The repair then attempts the original missing purchases in nonce order without
changing the saved automatic intent. Acceptance requires that intent, at least
two fresh automatic successor purchases, agreement after cold restart, and the
same funding receipt in both cold databases. The sponsor must have nonce 1 and
exactly 999.999979 FSN left: 6,000 minus 5,000 minus 21,000 gas at 1 gwei.
No post-genesis state adjustment, free ticket, real key or backup is used.

After the first experiment, the funded variant initially allowed up to 60
seconds per purchase for ordinary ticket funding to become available; the final
diagnostic increases that bound to 120 seconds and audits the ledger after each
included repair purchase and on a funding timeout. It retries only an
insufficient-balance rejection, using identical signed bytes, while requiring
the same canonical nonce, unchanged saved intent, empty pool and enabled miners
and buyers. Other errors or changed preconditions fail immediately. It sends no
second transfer or additional start/stop command. This is an operator-procedure
experiment, not a change to the automatic buyer.

## Results

The initial experiment fails after 190.48 seconds because it attempts the second
missing purchase immediately after the first. Both isolated branch ledgers pass
for blocks 25–32, and the common branch ledger passes through block 35. On that
common branch, wallet 1 loses first-retreat intervals at blocks 29 and 32; each
has value 5,000 FSN. Their expiry times are 1,793,043,411 and 1,793,043,400. The
account retains matching future 5,000-FSN locks beginning at expiry plus one.
All interval rights reconcile; there is no unexplained balance loss.

Wallet 1 has canonical nonce 19 and saved nonce 26. Its 2,067.602042576 liquid
FSN cannot fund the first missing purchase. The ordinary 5,000-FSN transfer
succeeds at block 37 and raises its liquid balance to 7,067.602042576. The exact
nonce-19 purchase succeeds at block 38, leaving 2,067.602000128 liquid FSN after
the ticket cost and 0.000042448 FSN fee. A new future 5,000-FSN time lock begins
after that purchase's expiry; the current interval is in its live ticket.
Immediate nonce-20 submission is therefore rejected. This is a failed repair,
not proof that a second transfer is necessary: ticket selection has not yet
returned the first repaired ticket's interval.

The 60-second-wait experiment also fails, after 299.11 seconds. The affected
wallet has canonical nonce 14 and saved nonce 21. One 5,000-FSN transfer succeeds
at block 37; original purchases 14 and 15 execute at blocks 38 and 42. Purchase
15 was admitted after a 38.08-second wait for funding. Purchase 16 remains
unfunded for the full 60-second bound, with 2,057.602000128 liquid FSN at block 46
and no covering time lock. The chain continues advancing. Neither saved-intent
completion, automatic successors nor cold acceptance is claimed.

The pre-funding ledger in that run identifies two first retreats: a normal
30-day ticket at block 31 and a setup ticket whose expiry is `TimeLockForever`
at block 33. The latter loss covers all future times, so it has no later
principal rights to recover. That setup ticket is a material synthetic-fixture
difference from normal 30-day automatic purchases. The ledger still reconciles
exactly. This result cannot be translated into the real donation wallet's
reserve requirement.

The longer diagnostic passes in 445.66 seconds. Its 90.41-second outage drops
44 packets and produces isolated heads 33 and 35. On the common branch, wallet 1
has canonical nonce 13 and saved nonce 19. An unfunded submission is rejected at
block 38. The sponsor's single 5,000-FSN transfer executes at block 39, then
original purchases 13–18 execute at blocks 40, 41, 44, 46, 48 and 49. Purchases
15, 16 and 17 require waits of 26.07, 14.03 and 14.03 seconds. No wait exceeds the
earlier 60-second bound: this is not proof that extending the timeout fixed the
previous failure.

The exact saved nonce-19 intent executes at block 50. Four new automatic
successors follow. Both cold databases agree at block 56:

- Block: `0x49dc91008832b3dc922ab7ab9e3adb91d7a9bcc5c82c25d43d98f727184ac31d`
- State: `0xfa620d138d30dfda14f0ebfceed2e334ec51d3dd495a68d4353f2f7a11cd43b0`
- Tickets: `0xedcfc74940f2e5417b81c869c8fa307599571331c2a62e310093b6e723655eb9`

Each cold node retains all eleven checked native-success receipts and the
funding receipt. Wallet nonces are 24 and 33. Their saved records retain exactly
their pre-shutdown contents: empty for wallet 1, 118 bytes for wallet 2. Both
cold pools are empty. Sponsor nonce 1 and the exact 999.999979 FSN balance pass
on both nodes. Two head changes are observed after `miner_stop` before the
required 35-second quiet period, reinforcing the existing clean-shutdown
requirement for key handover.

The ledger passes for both isolated branches, before funding, after all six
repaired purchases and finally through block 56. The final canonical suffix has
only one first-retreat loss, at block 34, for a 30-day ticket. At block 37 the
affected wallet still has a usable 5,000-FSN time-lock interval as well as the
future rights from the lost ticket; later purchases/returns redistribute those
rights. This starting inventory differs materially from the two-loss failures.
The successful transfer restores one lost interval's current funding; it does
not establish zero-ticket recovery after two losses with the same transfer.

| Run | Result |
| --- | --- |
| Immediate sequential repair | Fail, 190.48 s; second missing purchase is unfunded |
| Up to 60 s between purchases | Fail, 299.11 s; two included, third remains unfunded |
| Up to 120 s, per-purchase ledger | Pass, 445.66 s; six originals, saved intent, four successors, both cold nodes |
| Existing complete-history fixture | Pass, 4.45 s using the diagnostic binary |

No run reports a data race. These are Linux service experiments, not a broad
suite or native Windows test pass. Raw attempts, the earlier harness sources,
three executable identities, source identities and checksums are retained in
[the evidence directory](evidence/restart-funded-repair-2026-09-26).

## Limits

This is an isolated, synthetic two-owner scenario, not a full-state replay of
the donation address. Its sponsor funds must exist somewhere in a real launch;
the test does not identify such an available account. It does not establish a
universal reserve requirement or cover another outage during repair, longer
absence, expired signed purchases or loss of every eligible producer. Manual
nonce repair and usable funding remain separate requirements. No automatic
recovery mechanism or consensus rule is introduced.

Next use controlled starting inventories to resolve recovery after two
first-retreat losses with zero usable tickets, including whether waiting alone
can suffice and how much additional funding permits purchase-before-refund
operation. Preserve both failed live attempts as counterexamples to assuming
instant or fixed-time recovery. Then evaluate the real donation wallet against
complete-state accounting and choose an operator monitoring/repair policy.
The initially agreed backup-to-donation handover sequence is unchanged.
