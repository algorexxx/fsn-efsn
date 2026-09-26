# Donation handover funding coverage

26 September 2026, baseline `ed7229591ab635203e5412b2d027444c9d2f518b`.
Investigation tests and documentation only; production candidates remain P1–P15.

The preserved donation balance funds the recorded transition from long-lived
bridge purchases to ordinary 30-day purchases without needing an external
transfer. The new audit verifies replacement capacity before each selected-ticket
refund and after every recorded block. It supports the existing initial handover,
not a reserve guarantee for arbitrary later outages or losses.

## Evidence and method

The [complete-state handover](restart-full-state-handover.md) retained ten signed
blocks and complete account-difference ledgers from each Windows and Linux run.
Both used audited public-key substitutions, including an exact debit/credit of
the donation address's 12,020.102 liquid FSN, without duplicated funding.
The new test reads those committed artifacts; it opens no chain database and
does not copy or replay the backup.

For both sets, the existing independent audit rechecks block/receipt identities,
native purchase success, unrelated account-field preservation and every future
interval boundary against rewards, fees and first-retreat penalties. The new
check then verifies continuous exact successor-account RLP before/after all ten
blocks and examines the decoded purchase intervals and ticket selection.

An independent boundary calculation finds the minimum FSN time-lock coverage
through each entire purchase interval and compares it with the native
`TimeLock.GetSpendableValue` result. Live tickets are excluded from spendable
funding. The parent-state builder interval is checked, which can start earlier
than the eventual execution interval. Liquid must cover the signed transaction's
full gas limit times gas price, plus 5,000 FSN when locks cannot cover the whole
interval. Ticket purchases have no additional native-call fee in this source.
Partial time-lock coverage is not combined with a partial liquid payment by the
ordinary purchase path. This is an accounting check, not a new pool submission.

## Results

Both retained handovers produce the same balance schedule despite their later
worker timestamps and hashes differing. The first six constructed blocks match.

| After block | Purchase / selected ticket | Liquid FSN | Minimum free locks for next 30-day interval |
| --- | --- | ---: | ---: |
| Historical parent | Donation nonce zero, no locks | 12,020.102 | 0 FSN |
| 1: backup-signed block | First long purchase funded from liquid | 7,020.101957552 | 0 FSN |
| 2: donation jump | Second long purchase funded from liquid; first bridge selected | 2,020.414457552 | 5,000 FSN |
| 3: cleanup | Ordinary 30-day purchase funded from locks; second bridge selected | 2,020.726957552 | 5,000 FSN |
| 6: constructed suffix | Ordinary replacement rotation | 2,021.664457552 | 5,000 FSN |
| 10: worker/restart suffix | Donation nonce ten, one ordinary ticket | 2,022.914457552 | 5,000 FSN |

The two long purchases end at Unix time 1,792,713,600. Their respective starts
are 1,759,826,630 and 1,759,826,750. They are selected at blocks 2 and 3, so no
long-lived bridge ticket remains after cleanup. Purchases 3–10 each end exactly
30 days after their parent timestamp. Returned and retained time locks provide
continuous replacement coverage as the requested end moves beyond the original
bridge end; those rights are not stranded merely because the ticket was long-lived.

The first purchase fee leaves the donation wallet for the backup signer.
For the remaining nine blocks the donation signer receives the ordinary
0.3125-FSN reward and its own transaction fees. The final liquid amount follows
12,020.102 − 10,000 − 0.000042448 + 9 × 0.3125 = 2,022.914457552 FSN.
The two 5,000-FSN liquid debits became interval rights, not a 10,000-FSN loss.

Historical blocks 1–3 contain respectively six, five and four retreats of other
owners' tickets. No successor ticket is retreated. The full interval audit
continues to reconcile those historical effects, including expiry, rather than
assuming the recovery sequence has no retreats.

Frozen-state projections at 0, 1, 7 and 29 days after each final head still find
5,000 FSN of free locks covering a new 30-day interval. At 30 and 31 days they
find 10,000 FSN but zero tickets whose intervals remain live. These projections
execute no blocks, select no ticket and do not prove mining can restart after
expiry. Funding and an available eligible producer remain separate requirements.

The final race-instrumented Linux audit passes in 1.12 seconds: Windows artifacts
0.58 seconds, Linux artifacts 0.54 seconds. It checks 20 linked block ledgers and
12 frozen-state samples, with no skips or reported data races. This is not a
fresh native Windows execution or another live outage rehearsal.

An initial audit failed in 0.99 seconds because its new assertion prohibited
all retreats. The retained artifacts already contained the historical retreats
above; the existing conservation audit passed. The corrected assertion checks
that each retreat refers to a known parent ticket belonging to another owner.
The failed log, source and executable identity remain in the
[evidence directory](evidence/restart-handover-runway-2026-09-26).

## Operator consequence

The agreed one-backup-block startup remains unchanged. The records establish a
funded transition to ordinary purchases and one available replacement tranche.
They do not promise that 2,022.914 FSN of liquid can replace a lost 5,000-FSN
interval. Use the [controlled loss comparisons](restart-controlled-reserves.md)
to distinguish temporary waiting for a selected-ticket return from forfeited
coverage. Any external repair funding must come from an identified, authorized
account; none is established by the synthetic sponsor tests.

The [manual recovery runbook](restart-operator-recovery.md) now collects the
demonstrated retrieval, nonce, interval, funding and acceptance checks. Its use
as the supported release policy remains a decision. A live complete-state
outage/repair rehearsal, unavailable or expired original bytes, real signing
custody, final recovery parameters and monitoring deployment remain open.
