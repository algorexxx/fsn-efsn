# Coordinated pause after an equal-weight split

Status: bounded assisted-convergence pass, 27 September 2026. The preceding
[unattended first-contact failure](restart-equal-weight.md) remains a failure.
This experiment changes only the test harness and documentation. Production
candidates P1–P15, fork choice and the agreed single-producer launch are unchanged.

## Question and preserved inputs

Can stopping one active producer and its automatic buyer, while leaving both
services connected, allow the other branch to become sufficiently heavier for
ordinary synchronization? What purchase and funding state does the paused
wallet inherit after adoption?

The source is the stopped fresh-reconstruction failure at
`D:\FusionRehearsal\equal-weight-fresh-2026-09-27`. Its two valid branches end
at 15,130,119 with total difficulty 63,370,514,750 and distinct hashes. Their
own-wallet canonical/saved nonces are donation 37/37 and entrant 33/33.

The runner copies 593 files, 1,147,827,919 bytes, into the new disposable root
`D:\FusionRehearsal\equal-weight-pause-2026-09-27`. Every copied source hash
is checked before and after the experiment. The earlier failed directories
remain unchanged. No original backup database or real signing key is used.

The shared preflight helper expects `cold-sync-diagnosis.json`. For this
attempt that file is explicitly derived from the source's stopped observations,
cross-checked with its cold audit, and records the source result's SHA256.
It is expected-input metadata: no explicit downloader diagnosis is performed.
Preflight checks both exact heads and weights, the shared recovery anchor,
90,000 genuine historical ancestors, and the original export identity.
Both copies still lack the opposite branch tip.

## Test sequence

1. Start two real node services using only synthetic keys 2 and 3, in a network
   namespace containing only loopback. Connect them with ordinary peers.
2. Enable both miners and buyers. Require at least two further divergent
   equal-height, equal-weight descendants before attempting the pause.
3. Retain each complete pre-pause recovery suffix. Call
   `miner_stopAutoBuyTicket` and `miner_stop` on the donation service only.
   Keep the entrant mining and buying, and both peer connections active.
4. Within 150 seconds require ordinary adoption of the entrant's recorded
   pre-pause branch, then three more common descendants beyond the first
   common descendant observed. Do not force downloader synchronization,
   reconnect, rewind, change anchors, fund wallets or repair nonces.
5. Stop the entrant too, require a shared head unchanged for 35 seconds,
   retain exact purchase records and observed branch bodies, and shut down.
6. In a separate race-enabled cold test, audit both canonical suffixes and
   both retained pre-pause suffixes, including complete account differences,
   native receipts, ticket inventories and future interval rights.

The observer samples approximately once per second. Its status, purchase and
peer RPC calls are sequential, not an atomic snapshot. The source and final
heads are checked independently by cold reopening. Elapsed limits use Go's
monotonic clock; UTC observation timestamps are retained separately.

## Observed result

The live test passes in **233.96 seconds**, including history preflight. Both
miners reach different 15,130,121 blocks with total difficulty
**63,370,514,754**. The pause is applied at **12:19:57.820 UTC**. All 25
both-mining samples have distinct heads. All 53 paused-phase samples retain
one peer per service, with the donation worker disabled and entrant enabled.

The entrant's first new block, 15,130,122, still encounters an unknown-parent
import at the donation node. At 15,130,123 its advertised parent is now
strictly heavier than the paused node. The native logs show ordinary downloader
sync, a reorganization from common block 15,130,089 that drops **32** blocks
and adopts **33**, and synchronization completing in about **295 ms**.
This matches the parent-weight advertisement and strict heavier-peer gate
described in the preceding investigation.

The first common descendant observed is **15,130,122**, after **21.201 seconds**
from the pause call. Continued common production satisfies the acceptance
condition after **52.516 seconds**. The final shared head is **15,130,126**:

| Commitment | Value |
| --- | --- |
| Hash | `0x0e01aeb3c7e60ad34d818e6fe784af1aaf72e09602975815dcac263a4feaea91` |
| State root | `0xb7a4b7b703af20d7f28a952b426c960e415990440a2ebd05120a184ce50f81b0` |
| Ticket commitment | `0x86143dfd2b4bd1df4fa666fbba60096474b7da63588758e62ed1135109f2c2ec` |

No further donation seal is observed after its pause. After the entrant stops,
no head change is observed during the 35-second quiet window. This schedule
does not remove the previously demonstrated risk of delayed seals after a
stop call; a false mining flag alone is still insufficient evidence of signing
quiescence or safe key handover.

The cold test passes in **43.44 seconds**. The two canonical **46-block**
suffixes match byte-for-byte in their JSON ledgers and signed block RLP.
Both **41-block** pre-pause suffixes also reconcile. Exact saved purchase
bytes and own-wallet canonical nonces survive shutdown and cold reopening.
No race warning occurs, no additional funding transfer occurs, and all
593 copied source files remain unchanged.

## Purchase and interval consequences

| Synthetic wallet | Before pause canonical/saved nonce | Final canonical/saved nonce | Final tickets | Final liquid FSN |
| --- | --- | --- | --- | --- |
| Donation | 39 / 39 | 8 / 39 | 0 | 2,021.978065487999978776 |
| Entrant | 35 / 35 | 40 / 40 | 1 | 2,032.289478776000021224 |

The donation retains its exact signed nonce-39 intent, leaving missing canonical
nonces **8–38**, a **31-purchase gap**. Its own purchase pool is empty at the
end; the entrant still has its next nonce-40 purchase pending. The donation
buyer remains deliberately disabled, so this test does not claim to observe
its post-resume behavior or pass automatic purchase recovery.

The adopted entrant history already contains donation first-retreat losses at
15,130,092 and 15,130,093. Each forfeits the remaining rights of a 5,000-FSN
ticket. The losing donation branch instead contains two entrant first-retreat
losses. Both histories reconcile separately; adopting one changes which
losses are canonical. There are **no new retreats after the copied height
15,130,119** in either the retained pre-pause suffix or the final history.

The donation's surviving free time locks start at Unix time **1,793,049,397**,
after the final head's time. Together with zero tickets and less than 5,000 FSN
liquid, this provides no currently spendable 5,000-FSN stake. Do not infer that
nonce resubmission alone can restore production, or describe the losses as
destruction of all future rights in the principal. A subsequent repair needs
the original signed transactions, exact interval/fee checks and an explicitly
accounted funding source; none is supplied or authorized here for real wallets.

## Operational boundary and next work

A coordinated pause is now a rehearsed option for this particular split.
Choosing which producer continues has transaction and balance consequences:
the ordinary reorganization discards the competing suffix. The experiment
does not decide which history operators should agree to continue, provide
ongoing finality, or fix unattended equal-weight convergence.

Before using this approach, establish compatible anchors and operator agreement
on the continuation, preserve both branches and purchase bytes, and verify
that the continuing producer has live tickets and can replenish. Monitor hashes
and cumulative difficulty, then native purchases and funding after convergence.
Keep the paused wallet disabled until its distinct purchase/funding condition
has been assessed. Do not replace these checks with a head override or by
retaining the real backup owner's key beyond the agreed handover.

The subsequent [paused-wallet diagnosis](restart-paused-purchases.md) retrieves
all 31 missing originals exactly before and after restart on fresh copies.
Every original and the saved intent fail actual funding admission on both
nodes; the entrant's funded control passes. Both canonical ledgers and intents
remain unchanged. It also establishes the native parameter check's limited
admission window for each original, making expiry a distinct condition from
funding. The next question is an explicit recovery procedure once an original
becomes inadmissible; no automatic replacement is established. Production
monitoring thresholds, response responsibility and real funding availability
still require release decisions. Repeating this passing pause schedule without
a new question would add little evidence.

Both services are stopped and all rehearsal processes are absent. D: has about
**144.5 GB** free and the WSL filesystem about **64.0 GB**. No W: workload was
needed. Native logs use UTC+02; structured observations use UTC.

The [evidence directory](evidence/restart-equal-weight-pause-2026-09-27/)
retains scripts, source identities, copy proofs, observations, signed branch
bodies and all four ledgers. `verify-evidence.py` checks the run's conditions,
source identities, linked blocks, receipts, saved intents and its 384-file
SHA256 manifest; `--index` also checks staged Git bytes.
