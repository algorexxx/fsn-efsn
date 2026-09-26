# Controlled recovery funding after two ticket losses

26 September 2026, baseline `ee0165f6134595a4498f1490775f5417581b1ce4`.
Tests and documentation only; the production candidate inventory remains P1–P15.
This follows the [funded live-repair investigation](restart-funded-repair.md).

The same fully executed zero-ticket state now passes four controlled comparisons.
One 5,000-FSN transfer permits repeated purchases if ordinary selection returns
the replacement ticket's usable interval and another producer keeps advancing
the chain. Another first-retreat loss removes that capacity again. Extra funding
and waiting are therefore different parts of recovery; neither repairs a missing
nonce or guarantees unattended production.

## What was controlled

Two public test wallets begin with 12,020.102 synthetic FSN each. A separate
non-producing public test key has 11,000 FSN. All setup purchases have finite
30-day intervals, avoiding the infinite setup-ticket loss in an earlier live
failure. After 24 ordinary executed blocks, all genesis tickets are gone.
Only the healthy wallet then produces, causing exactly two first retreats of
the affected wallet's remaining tickets at blocks 26 and 28.

Every comparison imports this identical genesis-to-28 history into two fresh
independent databases. There is no state edit, fabricated difficulty or free
ticket after genesis. The shared parent is:

| Field | Value |
| --- | --- |
| Height | 28 |
| Hash | `0x75ff1cc93ccda7b14609d406e81d8a15b38887635b1774046f609ea683b5907f` |
| State root | `0x1c5193decdc337409c29535e1479211d329b81df9e7845b5e716b783d91f3f46` |
| Ticket commitment | `0x3b6172fb2dcd65ddee1168bfd0b73a392000d341b90aad814bff4f2487d066c4` |
| Affected public test wallet | `0x2B5AD5c4795c026514f8317c7a215E218DcCD6cF` |
| Nonce / live tickets | 12 / 0 |
| Liquid FSN | 2,045.101915104 |
| Future rights | Two 5,000-FSN locks starting at 1,792,960,671 and 1,792,961,271 |

Those future locks cannot fund the current purchase interval. Ordinary rewards
and fees explain why the synthetic remaining liquid differs from simply
12,020.102 minus 10,000. The inherited first-retreat rule forfeits the ticket's
remaining interval; it does not erase the separate rights after a finite expiry.

Seven purchases, nonces 12–18, are signed once from this parent and reused byte
for byte across the branches. These are synthetic manually prepared purchases,
not transactions recovered from an orphaned branch. The log label `original`
means the common signed sequence in this test. There is no saved automatic
purchase record or automatic-buyer repair in this experiment.

Each admission probe uses the real transaction pool against current canonical
state. After an insufficient-balance rejection, cooperative branches advance
using the first-ranked producer and the healthy wallet's ordinary replenishment,
then retry the unchanged purchase. Every cooperative purchase/wait block must
have no retreats. Signed blocks execute and import independently in both
databases. Timestamps advance 120 seconds per constructed block, starting a day
behind wall clock; this measures funding dependencies, not real mining latency.

## Results

| Branch from the same parent | Transfer | Included purchases | Extra funding-wait blocks | Final height | Observed outcome |
| --- | ---: | ---: | ---: | ---: | --- |
| No funding | 0 FSN | 0 | Not applicable | 40 | All probes remain unfunded through 12 healthy blocks |
| One ticket funded | 5,000 FSN | 7 | 7 | 43 | Ordinary selection returns usable stake between purchases |
| Two tickets funded | 10,000 FSN | 7 | 5 | 41 | More initial capacity, but later purchases still need returns |
| One ticket funded, then missed again | 5,000 FSN | 1 | 0 | 31 | Replacement first-retreats; nonce 13 is unfunded and tickets are zero |

All four characterization tests pass. That includes correctly detecting the two
branches where the affected wallet cannot continue purchasing. The existing
complete-history fixture also passes after its helper refactor. Total parent
test duration is 22.18 seconds, including 17.76 seconds for the comparison and
4.42 seconds for the fixture. Linux Go 1.21.3 race instrumentation reports no
data race; no case is skipped.

In the 5,000-FSN cooperative branch, waits before nonces 12–18 are respectively
0, 1, 1, 1, 2, 1 and 1 blocks. In the 10,000-FSN branch they are 0, 0, 0, 2, 1,
1 and 1. These are one observed pair of controlled trajectories, not expected
network timings or a general performance advantage. Funding changes state and
descendant hashes, so later ticket ordering can differ between branches.

The missed-again branch shares the funded transfer and first purchase with the
5,000-FSN cooperative branch. Its replacement first-retreats at block 31:
`0xea628afb30695a5225f841384697c4ecfc7052778f08b9590b262c86fb91826c`.
The next identical signed purchase is rejected for insufficient balance. This
distinguishes unavailable funding after a loss from temporarily unavailable
stake awaiting normal selection.

Both databases in every branch reopen as actual cold node services and agree
on the expected head and canonical nonce. All included purchases have canonical
successful native receipts. Sponsor nonce and exact remaining balance agree in
both copies: 11,000 FSN without a transfer, 5,999.999979 after transferring 5,000,
or 999.999979 after transferring 10,000. Each transfer costs 21,000 gas at 1 gwei.

Four independent interval-ledger audits cover every block from 25 to each final
head. Liquid, time locks and tickets reconcile at all future interval boundaries
against rewards, fees, transfers and first-retreat losses. The cooperative and
unfunded branches each contain the two prefix losses; the missed-again branch
contains exactly three. Full hashes, roots, transaction identities, logs, build
inputs and verification scripts are in the [evidence directory](evidence/restart-controlled-reserves-2026-09-26).

## Implications for the donation wallet

The [preserved donation account](restart-wallet-handover.md#funding-observation)
has 12,020.102 liquid FSN, nonce zero and no time locks at the accepted candidate
historical parent. The [complete-state handover](restart-full-state-handover.md)
already checks that balance and its short production sequence using audited
public-key substitutions. This new comparison matches its initial balance,
but uses a synthetic low-height chain, different rewards and ordinary 30-day
tickets. It is not a full-state outage replay of the donation wallet or its
long-lived bridge ticket.

For overlapping current intervals, ignoring subsequent rewards and net fees,
the preserved 12,020.102 FSN represents the following capacity:

| Assumed interval losses | Remaining current rights | Meaning |
| --- | ---: | --- |
| None | 12,020.102 FSN | Two 5,000-FSN funding tranches plus 2,020.102 |
| One 5,000-FSN first-retreat loss | 7,020.102 FSN | One tranche remains; reduced replacement capacity |
| Two such losses | 2,020.102 FSN | Cannot fund a fresh 5,000-FSN current interval |
| Two losses, then a 5,000-FSN transfer | 7,020.102 FSN | One tranche restored, conditional rotation demonstrated here |
| Two losses, then a 10,000-FSN transfer | 12,020.102 FSN | Two tranches restored, still subject to selection and purchase ordering |

These are rights across the stated interval, not necessarily liquid balances
or permanent principal losses. Actual tickets, overlapping time locks, fees,
rewards and expiry boundaries must be inspected on the accepted current state.
The test sponsor is invented funding at synthetic genesis; no real reserve
account or permission to spend another owner's FSN has been established.

The agreed sole continuing producer must retain purchase-before-refund capacity.
The existing 5,001-FSN standalone handover failure remains relevant: the ability
to rotate one tranche here depends on another eligible producer. This result
does not make 5,000 FSN plus gas sufficient to sustain the chain alone, nor does
it propose another permanent operator or require extra funding to execute the
already-tested initial handover.

## Remaining operational work

Keep the initial handover unchanged. Before release, specify and rehearse the
monitored manual-repair procedure with checks for canonical nonce, retained
signed bytes, actual usable interval coverage, live ticket count, another
eligible producer and the funding source. Enabled mining or buyer flags and
an advancing common head are insufficient health checks. Stop repair attempts
if those preconditions change; a fixed wait or retry count cannot manufacture
lost rights.

Apply these checks to the complete-state donation handover, including its
long-lived bridge ticket, and verify the eventual ordinary-purchase interval
schedule. Document which outages require external funding and which can recover
with existing returns. This remains open; the controlled comparison does not
choose a reserve amount, resolve the automatic buyer's nonce-gap pause, handle
expired signed transactions or prove recovery if every producer is unavailable.
The earlier failed live experiments remain evidence. No production behavior,
consensus rule, key custody or real chain state changes in this investigation.

The [complete-state funding follow-up](restart-handover-runway.md) now audits
both retained handover sequences: bridge tickets are selected at blocks 2 and
3, ordinary 30-day purchases follow, and each replacement has funding before
the selection refund. This closes the recorded handover's coverage question,
not the live complete-state outage/repair case or real funding availability.
A [manual operator procedure](restart-operator-recovery.md) is now drafted;
adopting it as the supported release policy and deploying monitoring remain open.
