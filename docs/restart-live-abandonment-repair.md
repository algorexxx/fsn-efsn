# Live recovery after abandonment rollback

Status: complete-state synthetic pass, 27 September 2026. Both the live test
and separate 90-block cold audits pass. Production P1–P15 remain unchanged.

This report covers the uninterrupted counterpart to the
[restarted repair](restart-abandonment-repair.md): ordinary peer synchronization
reorganizes the donation node, its existing pool automatically recovers part of
the discarded history, and manual recovery addresses only the remaining gap.

## Starting state and controls

Fresh copies use the donation producer from
`D:\FusionRehearsal\stale-intent-ordered-2026-09-27` and the heavier entrant
verifier from `D:\FusionRehearsal\abandonment-reorg-2026-09-27`.
The target is `D:\FusionRehearsal\live-abandonment-repair-2026-09-27`.
The copy manifest covers **616 files / 1,148,421,808 bytes**. Original databases
remain separate from the experiment; all 616 source hashes still match after
the completed run.

Donation starts at block **15,130,140**, canonical nonce 43, zero tickets and
saved purchase 43. Entrant starts at **15,130,148**, nonce 63 and one ticket.
The branches share the accepted restart anchor and history through 15,130,132.
Their initial total difficulties are 63,370,514,801 and 63,370,514,808.
Both preflight inventories match their respective preserved source inventories.

The services start with empty pools. Donation's real buyer restores its exact
saved nonce-43 transaction and holds it unchanged for six seconds. Entrant's
real miner and buyer then start, and ordinary peer connection begins the test.
The harness uses public synthetic keys 2 and 3, loopback-only networking and
its existing disabled pool journal. No held signer, explicit downloader RPC,
operator pause, service restart, new funds or manual record edit is used during
rollback and repair. Normal downloader behavior remains enabled.

## Automatic and manual recovery

Ordinary synchronization adopts the heavier compatible branch. Pool reset
reinjects the original zero-value self-transfer at nonce 39 and ticket purchase
40. They propagate normally and both execute in **15,130,149**, before any
manual submission. The self-transfer has a successful 21,000-gas receipt with
no native ticket log. Purchase 40 has canonical native ticket success.

The diagnostic waits for a stable ten-second gap on the advancing common
chain, checks matching receipts on both nodes and finds canonical nonce **41**,
an empty donation pool and the original saved nonce **43**. Its signed hash is:

```text
0xddb72dc7336546fdbe48be0570dca20587a77c51aa5e61d3664d468e7f04097a
```

Only originals 41 and 42 are retrieved through existing old-block RPC,
validated and submitted manually. Neither the self-transfer nor purchase 40
is submitted again. The repair helper waits for actual ticket selection to
return usable rights when pool admission reports insufficient funding. It adds
no funds and relaxes no validation.

| Donation nonce | Inclusion height | Action |
| --- | --- | --- |
| 39 | 15,130,149 | Original self-transfer, automatically reincluded |
| 40 | 15,130,149 | Original purchase, automatically reincluded |
| 41 | 15,130,155 | Original purchase, manually replayed |
| 42 | 15,130,158 | Original purchase, manually replayed |
| 43 | 15,130,161 | Exact saved purchase, automatically submitted |
| 44 | 15,130,165 | Fresh automatic purchase |
| 45 | 15,130,168 | Fresh automatic purchase |

All four original transactions retain their signed fields and hashes, with new
canonical receipt locations. The retired stale nonce-39 purchase remains absent.
Purchases 41 and 42 initially fail for insufficient available stake while the
prior ticket is live; normal selection returns usable rights. Both manual
purchases propagate normally. No direct-recipient delivery is needed, and saved
43 receives no manual submission.

The live acceptance point is **15,130,168**. Donation has six purchases and five
produced blocks; entrant has fifteen purchases and fifteen produced blocks.
Mining and automatic buying are enabled at every pre-shutdown status sample.
The helpers also check both flags during manual recovery. No further start
command is issued. These sampled observations do not prove uninterrupted worker
execution between samples; they do establish that no operator restart is needed.

## Cold verification

The test stops both workers, waits for a common head to remain unchanged for
35 seconds and closes both services. The final block is **15,130,170**:

```text
hash:    0x664f3e3bf69f3d7a6ac70839b56f9fee35b2d1464d8f69dc308953437236520f
state:   0x6aa04903f402e3c61ca3e4257382978260120f4e5662976b030943392dbf316c
tickets: 0xf072925ded01c83680ecc54ee0b0eb5777d6164662ed370c5d1a8c38681675bd
```

The full 22-block continuation contains donation purchases 40–45 and entrant
purchases 63–78, with six donation-produced blocks and sixteen entrant-produced
blocks. No new retreat occurs. The only ordinary transaction added after the
heavier starting head is the original self-transfer; the earlier 33 ordinary
transactions retain their heights. Its fee is 0.000042 FSN. The cold audit's
inherited `AdditionalFunding` field contains those 34 allowed transactions and
does not mean a new positive funding transfer occurred.

The race-enabled live test passes in **308.47 seconds**; the independent cold
audit passes in **52.84 seconds**. Both complete **90-block ledgers** reconcile
account changes, gas, rewards, receipts, tickets and every future time-lock
boundary. Their **360 JSON/RLP artifacts** are identical. The **272 artifacts**
covering the heavier branch's existing 68-block prefix remain unchanged.
There are no race warnings. The backup wallet's inventory is unchanged, and it
signs nothing during this experiment.

| Synthetic owner | Final nonce | Tickets | Liquid FSN | Own saved intent |
| --- | --- | --- | --- | --- |
| Backup | 233430 | 0 | 5.752721845480158626 | Not used |
| Donation | 46 | 0 | 23.851700263999957552 | None |
| Entrant | 79 | 1 | 244.165886000000042448 | Nonce 79, pending |

Stopped service records and cold records agree. Donation's final zero-ticket
checkpoint follows deliberate worker shutdown; its full time-lock rights remain
in the inventory. Actual production and fresh purchases were required before
shutdown, so a ticket count alone is not the acceptance test.

The [413-file evidence bundle and verifier](evidence/restart-live-abandonment-repair-2026-09-27/)
retain source hashes, different starting inventories, live status/pool samples,
automatic reinclusion receipts, manual repair observations, raw transaction bytes,
both complete ledgers and stopped records. The verifier checks original signed
fields independently through RLP decoding, new receipt locations, native ticket
owners, the saved intent, unchanged history, no new funding and staged Git bytes.

All rehearsal processes are stopped. D: has about **134.8 GB** free and WSL
about **63.9 GB**. No W: workload was used. Native logs use UTC+02; structured
observations use UTC.

## Operator consequence and remaining gates

This closes the specific uninterrupted rollback-to-repair timing case. A live
pool can already have recovered and included some displaced transactions. Check
current canonical receipts, nonces and pending transactions before repair;
start with the first genuinely missing nonce. Do not repeat an abandonment or
resubmit every old purchase merely because a rollback occurred.

The saved buyer still does not fill a multi-purchase nonce gap automatically.
This is a monitored, manual recovery with a funded surviving producer and usable
selected-ticket returns. It does not resolve the earlier equal-weight split,
first-retreat funding losses or future validity-window failures, and does not
establish a universal reserve or power-loss durability.

The next work for this path is to consolidate the production monitoring and
response policy for review: alerts must distinguish branch divergence, missing
nonces, stale payloads, funding failures and pending-transaction delivery. Define
who receives and acts on each alert, verify real-address funding and review the
minimal release patch set independently. Wider historical replay, distribution,
public-network checks and final signing/anchor approvals remain separate launch
gates in the [main plan](restart-plan.md). This test introduces no production
code or consensus change.
