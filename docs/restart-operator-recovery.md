# Operator purchase recovery procedure

Draft for release review, 27 September 2026. This collects the demonstrated
manual recovery path. It does not enable an automatic repair mechanism or mean
that every failure below has a supported repair. Production adoption, response
times, named operator coverage and a real funding source remain release decisions.

The normal launch remains one backup-wallet block including the donation wallet's
first funded purchase, followed by donation production. The backup wallet's
automatic purchasing stays disabled. The [handover funding audit](restart-handover-runway.md)
supports that transition. Do not retain the borrowed key as an unagreed emergency
signer; clean shutdown and verified custody handover remain required.

## Observe a consistent state

Record the release/configuration identity, accepted anchor, wall-clock UTC time,
head height/hash/timestamp/state root and ticket commitment. Check that peers
agree on a compatible canonical branch and synchronization has completed before
classifying a purchase problem. The previous tests' ten-second observation and
60/120-second waits are experiment bounds, not approved production thresholds.

Use the existing local administrative/RPC access. Pin account/ticket reads to
one hexadecimal block number, then reread that number's hash; discard the sample
if it changed. Repeat on a separate verifying node where available. A verifier
does not need a ticket or an unlocked key.

| Data | Existing interface | What to retain |
| --- | --- | --- |
| Canonical block | `eth_getBlockByNumber` | Height, hash, timestamp, roots and base fee |
| Canonical wallet nonce | `eth_getTransactionCount(address, blockNumber)` | Use canonical state, separately inspect pending state |
| Liquid FSN | `fsn_getBalance(assetID, address, blockNumber)` | System asset is `0x` followed by 64 `f` characters; amounts are wei |
| Time locks for arithmetic | `fsn_getRawTimeLockBalance(assetID, address, blockNumber)` | Normalized start, end and value segments |
| Free interval coverage | `fsn_getTimeLockValueByInterval(assetID, address, startTime, endTime, blockNumber)` | Amount in wei across the requested interval; start is clamped to the block time, end zero means forever |
| Tickets | `fsn_allTickets(blockNumber)` / `fsn_allTicketsByAddress(address, blockNumber)` | Owners, IDs, heights and interval endpoints |
| Pending/queued transactions | `txpool_content` | Owner, nonce, hash and any conflicting replacement |
| Mining/buyer state | `eth_mining`, `fsn_isAutoBuyTicket`, service logs | Flags, sync state and actual repeated purchase results |
| Purchase result | `eth_getTransactionReceipt` plus canonical block | Receipt status and native result log; verify the ticket was created |

`fsn_getTimeLockBalance` is a display view: its intervals may overlap and are
sorted for presentation. Do not pass that result directly to `TimeLock.Add`,
`Cmp` or `GetSpendableValue`, which require normalized segments. Use raw intervals
for calculations, including any hypothetical ticket returns. The
[uninterrupted-delivery investigation](restart-uninterrupted-delivery.md)
reproduced and corrected this mistake in the rehearsal harness; it understated
backing by 5,000 FSN per wallet in the retained snapshots. Returned backing is
conditional on normal selection and is not a guarantee against retreat losses.

An advancing common chain and enabled flags do not prove this wallet is buying
or mining. Monitor its nonce, successful purchases, usable tickets, free interval
coverage and errors as well as peer count and head movement. Preserve old head
and block hashes so displaced transactions can later be located.
Continue retaining them while connections and synchronization recover: the
[complete-state partition](restart-retry-partition.md) mined three more displaced
purchases after packet flow resumed, beyond the harness's initial capture.
Their bodies remained in the node and existing block-hash RPC recovered them.

## Classify before changing anything

| Observation | Response supported by current evidence |
| --- | --- |
| Normal synchronization pause | Allow sync to finish and check automatic resumption; investigate a persistent pause |
| Retained purchase nonce exceeds canonical nonce, no conflicting pool entries | Retrieve and validate every missing original transaction before sequential repair |
| Temporary lack of free stake, with a live ticket and another producer | Wait for observed ordinary selection/return, then recheck the exact interval and nonce |
| Zero tickets, insufficient liquid and insufficient covering locks | Waiting for the absent ticket's selection cannot help; inspect future expiry rights and actual funding options |
| Conflicting nonce, missing/corrupt record, missing bytes, expired interval or inadequate fee | Stop this procedure and review the specific case; no generic replacement or record deletion is established |
| No available eligible producer | Normal transfer/resubmission cannot itself create the block needed to execute it; this runbook does not establish a repair |
| Compatible-anchor producers advancing different hashes at equal cumulative difficulty | Preserve both branches, agree on a continuation, and assess the rehearsed coordinated-pause option below; local purchase success does not prove convergence |
| Incompatible branch/anchor or unexplained accounting | Preserve evidence and resolve branch/configuration identity before submitting anything |

Interval expiry counts alone are not a complete consensus eligibility check.
Confirm the surviving producer can actually advance the accepted branch. Where
another owner keeps mining, repeated first retreats can reduce the affected
wallet's current rights by another 5,000 FSN each. The
[controlled reserve cases](restart-controlled-reserves.md) demonstrate both
conditional recovery and exhaustion after another retreat.

## Preserve signed transactions and the saved intent

1. Query each displaced block with `eth_getBlockByHash`. Identify the wallet's
   transaction index and call `eth_getRawTransactionByBlockHashAndIndex` using
   that exact block hash and hexadecimal index. The old body must still exist.
   Transaction-hash lookup may return nothing after its canonical index is removed.
2. Decode and retain the raw signed bytes, transaction hash, recovered sender,
   chain ID, nonce, destination, value, gas parameters and native payload. Check
   against the accepted release/network identity and expected purchase. Cover
   every missing nonce; the latest saved intent is not a purchase-history archive.
3. Inspect the automatic intent through the demonstrated offline command if its
   exact bytes are needed. Cleanly stop the owning process and preserve its actual
   data/configuration first. Plan the production interruption if it is the sole
   producer; a backup signer must not overlap with it. `miner_stop` alone is not
   a shutdown barrier because previously signed work can publish afterward.

   ```text
   efsn --datadir <stopped-datadir> --syncmode full db get 0x66736e2d6175746f2d7469636b65742d76312d<40-address-hex-digits>
   ```

   Use matching network/path options and the reviewed executable. The key is
   ASCII `fsn-auto-ticket-v1-` plus the raw 20-byte address. Preserve and decode
   the returned value. Do not delete or edit it to clear a warning. A missing
   record and a locked database are different errors.
4. Restart the inspected service with its intended identity and configuration.
   Resample the branch, nonce, pool, funding and saved-intent assumptions. The
   source node may have fallen behind while stopped. The test-only
   `lab_purchaseState` endpoint is not a production API.

The [retrieval report](restart-small-reserve-and-retrieval.md) contains passing
RPC-before/after-restart and offline-command checks. No pruning recovery or live
saved-record reader is established.

## Check funding and repair one nonce at a time

1. Require an unchanged accepted branch, the expected canonical nonce, the
   retained later intent and no conflicting pending/queued transaction. Reject
   a candidate with the wrong sender, chain ID, native destination/function,
   nonce, value, interval or gas parameters. Check interval validity against the
   head and current time; builder, pool and execution use different timestamp
   contexts. Old signatures can become unsuitable while waiting. Under the
   applicable fork rules, pool parameter validation requires the encoded ticket
   end to be at least 29 days beyond the latest block timestamp. Record the
   earliest `end - 29 days` among all predecessors, not just the saved intent,
   and recheck it before each submission. The [paused-wallet diagnosis](restart-paused-purchases.md)
   verifies acceptance at that boundary and rejection one second beyond it.
   This is a head-timestamp limit, not an interchangeable wall-clock deadline.
   If a predecessor no longer passes validation, stop ordinary resubmission;
   adding funds does not repair its payload. Assess explicit abandonment below
   as a separate owner decision; it does not recover the missing ticket.
2. For the requested interval, require either time locks covering the full
   5,000-FSN amount at every boundary or a full 5,000 FSN liquid payment. The
   purchase path does not combine partial locks with a partial liquid remainder.
   Keep liquid available for the full transaction gas budget as well. Live-ticket
   value and an expected refund are not free funds before that block finalizes.
3. If funding is deficient, identify whether a live ticket can return the needed
   rights through ordinary selection. Recheck state after that return. If an
   ordinary transfer is chosen, document its authorized sender and amount, then
   require canonical success before resuming. The synthetic 5,000/10,000-FSN
   transfers are observations, not universal repair amounts or available funds.
   When a surviving producer supplies funds, sequence its transfer after its
   reviewed saved/pending purchase rather than occupying that purchase's nonce.
   The [stale-intent rehearsal](restart-stale-intent.md) reproduces a stall when
   the sole eligible producer's transfer blocks automatic buying and its last
   ticket cannot seal a block leaving no tickets. On a fresh copy, waiting for
   the next automatic purchase and placing the transfer at the following nonce
   permits both to execute. Recheck the donor's actual nonce, pool and funding;
   this sequencing requirement does not establish a generally safe transfer amount.
4. Submit the reviewed original bytes using `eth_sendRawTransaction`. Submission
   acceptance is not purchase success. Wait for a receipt, verify its block hash
   is canonical, inspect the native BuyTicket result for an `Error` field, and
   match the created ticket's ID/owner/interval/value to the signed payload.
   If the transaction stays pending only at its origin, compare the producer's
   canonical head and pool using its local IPC connection. Once the producer
   has the accepted branch and the purchase is admissible, the same reviewed
   bytes can be submitted directly to that producer through the existing RPC.
   Record the identical returned hash and verify canonical native success on
   both nodes. Do not clear the later saved intent or sign a replacement merely
   because local resubmission says `already known`. A controlled peer test also
   verifies pending replay after a ready-peer reconnect, but that admission
   result alone does not prove sustained purchasing. See the
   [manual-predecessor delivery evidence](restart-manual-purchase-delivery.md).
5. Recheck canonical nonce, pool, original later intent, tickets, free locks,
   liquid and surviving producer. Advance to the next missing nonce only after
   successful canonical inclusion. A changed branch, conflict, new loss or
   insufficient funds returns to diagnosis; do not bulk-submit or sign guessed
   replacements to force progress.
6. Once all predecessors succeed, observe execution of the byte-identical saved
   intent and fresh automatic successor purchases without a new manual start
   command. The passing live rehearsals require at least two fresh successors;
   that is an acceptance check, not proof of indefinite unattended operation.

## Explicitly abandon an unusable predecessor

The [nonce-abandonment rehearsal](restart-expired-nonce-neutralization.md)
demonstrates consuming missing nonces through existing ordinary transaction
RPCs. It deliberately abandons the corresponding purchases. It is not an
automatic replacement policy or a way to restore stake funding.

1. Preserve the original bytes and locations, inspect the saved intent, and
   verify the accepted branch and a functioning surviving producer as above.
   Obtain the owner's decision to abandon each specified purchase, recording
   that its ticket will not be created by this action. Check the saved intent's
   validity separately; this rehearsal leaves its nonce unconsumed.
2. With the affected buyer paused and no conflicting pool transaction, prepare
   an ordinary transaction from the owner to the same owner: explicit current
   nonce, zero value and empty data. For the plain accounts tested here, gas is
   21,000. Review the actual account, network identity and gas price instead of
   copying fixture values. Use the existing signing flow, such as local
   `eth_signTransaction`, and retain the decoded fields, raw bytes and hash.
3. Submit those reviewed bytes through `eth_sendRawTransaction`. Require a
   successful receipt in the accepted canonical block, matching transaction
   identity, gas and nonce movement. This transaction has no BuyTicket result;
   record it as abandonment rather than purchase success. Recheck branch, pool,
   balance and saved intent before the next nonce. The controlled 31-transaction
   batch is evidence of execution, not a reason to bypass these checks.
4. Stop before consuming the saved intent's nonce. Once canonical nonce matches
   it, check its original validity and funding, then follow normal buyer recovery
   and acceptance criteria. In the rehearsal it remains byte-identical but
   unfunded, with zero tickets; that wallet is still not a producer.

An expired probe is rejected by real pool RPC in this experiment, but the 31
historical predecessors had not yet crossed their validity boundaries. No
conflicting pool-price replacement, loss of
the surviving producer, or protection against a later reorganization is proved.
Do not delete the durable intent or relax purchase validation to force progress.

## Explicitly abandon an unsuitable saved intent

The [saved-intent follow-up](restart-stale-intent.md) now demonstrates this
separate case on complete synthetic state. It seeds a stale record before
startup; **that fixture database write is not an operator step**. Existing RPC
rejects the exact transaction before and after funding. The recovery itself
uses one ordinary self-transfer and lets the controller manage its record.

After confirming there is no earlier nonce gap, assess the saved purchase's
exact payload, current admission failure, funding and any conflicting pool
transaction. If the owner explicitly chooses to abandon it, preserve its bytes
and sign a reviewed zero-value self-transfer at that same canonical nonce using
the checks above. Require canonical success before treating the nonce as
consumed. A pending replacement alone is insufficient.

The existing buyer then retires the saved intent with a warning that its nonce
was consumed **without a confirmed purchase**. Do not count that message or the
self-transfer receipt as ticket creation. Require fresh ordinary purchases with
canonical native success and actual block production. The passing test verifies
the first fresh purchase, two automatic successors, three donation-produced
blocks and both cold 60-block ledgers. It adds no automatic replacement behavior
and makes no manual record edits during recovery.

Keep this an owner-authorized transaction decision. The test's 3,000-FSN funding
comes from existing synthetic balances, and the prior no-funding barrier and
funding-order failure remain relevant. The [normal-restart continuation](restart-recovered-buyer-restart.md)
now restores the exact saved successor from an empty pool, executes it and two
fresh successors, and resumes actual production without new funding or manual
submission. Both cold 72-block ledgers pass. Funding, nonce resolution and
payload validity remain distinct gates.

The [compatible-abandonment rollback](restart-abandonment-reorg.md) now verifies
that the self-transfer and later purchases can lose canonical inclusion while
the newest saved intent survives. In the complete-state rehearsal, canonical
nonce 43 becomes 39 and saved 43 stays unchanged. The live pool retains the
original self-transfer 39 and purchase 40; after a restart with no pool journal,
the buyer reports the nonce gap with an empty pool. Both cold 68-block ledgers
agree, and the four displaced transactions remain retrievable by old block hash.

After a branch change, recheck receipts, account nonce and the pool before
authorizing another transaction. Retain and inspect the original self-transfer
as well as the displaced purchases. Do not issue a second abandonment, clear
the saved record or assume an enabled buyer fills the gap. Sequential replay of
the original self-transfer and purchases, followed by saved-intent execution
and resumed production, is the next separate rehearsal. The pause result uses
a held signer and explicit downloader request; it does not prove automatic
repair, unattended convergence or continued mining.

## Acceptance and retained record

Record original and final heads/roots, canonical nonces, transaction bytes and
hashes, native receipts, ticket changes, interval accounting, all funding/fees,
saved intent identity and fresh successor evidence. When a verification restart
is planned, perform a clean restart with the expected configuration and confirm
persisted heads, receipts and continued purchasing. Coordinate downtime with
the available producer; do not cycle every service merely to satisfy a checklist.

The passing restart used the usual miner/buyer start actions with existing
funding and a surviving eligible peer. It did not require a database edit,
re-signing the saved purchase or manually submitting its bytes. Require
canonical native success and fresh automatic successors before declaring buyer
recovery; an enabled mining flag or a restored pending transaction is not enough.
If the accepted branch changes, return to nonce/receipt/funding diagnosis rather
than assuming this clean-restart result covers the new history.

Release review still needs a chosen monitored/manual policy, alert delivery and
response responsibility, validated real-address interval schedules and funding
availability. The [single-producer complete-state outage](restart-full-state-outage.md)
now passes a 90-second network loss, process kill with a pending intent, exact
cold record recovery, automatic successors, ordinary peer catch-up and matching
cold ledgers. It requires the normal miner-start action after process restart
and does not create a nonce rollback. A complete-state competing-producer/manual
repair exercise remains open. The [first complete-state partition attempt](restart-full-state-partition.md)
did not converge within its observation window, so no repair was submitted.
Both cold branch ledgers passed. A separate diagnostic confirmed connected,
equal-weight stopped peers and a downloader failure on missing historical
ancestry in the compact fixture. A peer count alone does not establish a shared
canonical branch; repair remains gated on that evidence. The later
[complete-state P4 partition](restart-retry-partition.md) does converge and
reproduces canonical nonce 7 with saved nonce 14. Both cold canonical ledgers and
competing branches reconcile, and all seven originals are retrievable. However,
two first retreats leave zero entrant tickets, 2,021.664457552 liquid FSN and
only future-starting locks; the actual first repair submission is rejected for
funding on a separate diagnostic copy. The
[funded continuation](restart-funded-gap.md) now passes on restarted copies:
3,000 FSN of specified ordinary synthetic transfers fund sequential originals
7–13, exact saved nonce 14 and two fresh automatic successors. Six funding waits
depend on actual ticket selection/return, and both 58-block cold ledgers pass.
The contribution is not an authorized real funding source or a universal
reserve. A fresh uninterrupted partition-to-repair run and production response
policy remain open. This procedure stops at unsupported conditions instead of
treating a short rehearsal as an automatic recovery guarantee.

The [genuine-history follow-up](restart-partition-history.md) now removes the
exact compact-history ancestor failure. A separate stopped heavier-peer case
converges normally and passes both cold ledgers. It also demonstrates a different
stall: the donation owner's saved and canonical nonces are both 7, but it has
zero tickets, 2,021.665544264 liquid FSN and no free lock coverage for the saved
interval. The real pool rejects its 5,000.000042448-FSN liquid requirement.
Do not apply missing-nonce repair to this state. Recheck authorized usable funds
and intervals; waiting for an absent ticket or clearing a record cannot supply
them. Future rights outside the purchase interval are not available coverage.

The [existing-funds experiment](restart-existing-funds.md) demonstrates why
funding and startup readiness are separate checks. Its 3,000-FSN hypothetical
contribution admits and executes the unchanged saved purchase. The first live
continuation nevertheless stalls: the replacement is sent before the sole
producer starts mining, and finalization refuses to consume the last ticket
without another ticket. Source inspection identifies the acceptance gate as a
plausible cause; the receiver's live rejection was not sampled. Starting both
miners before buyers restores production but still leaves the donation's
correct-nonce purchase pending locally while only the entrant replenishes. Check
that the actual block producer has the replacement transaction; another node's
pending-pool response alone is insufficient. This is a separate recovery
scenario, not an instruction to enable extra signers during the controlled
historical launch. No real backup contribution is assumed.
The final cold checks accept the donation's unchanged nonce-8 purchase on both
nodes and reconcile all 31 blocks. Treat this as a delivery/inclusion diagnosis
with its exact live cause still unobserved, rather than assuming another funding
transfer or missing-nonce repair is required.

The [exact delivery follow-up](restart-purchase-delivery.md) now executes that
unchanged saved purchase through direct submission to the surviving producer,
then passes automatic replenishment for both accounts and the forty-block cold
audit without extra funding. Historical remote pool checks reproduce rejection
before the preceding block is imported: the purchase start is more than three
hours ahead of the recipient's head. After that import the same bytes pass.
For a correct-nonce pending purchase, check the producer's canonical head and
pool before considering direct submission of the reviewed original bytes to an
authorized endpoint. Verify canonical native success and continued purchasing;
do not clear the saved intent, guess a replacement nonce or treat local pending
status as successful delivery. This is a rehearsed manual delivery option,
not yet an automatic retry policy or proof of the original wire failure.

The [peer retry investigation](restart-peer-purchase-retry.md) confirms a second
option: after verifying compatible heads and transaction readiness, a deliberate
reconnect can replay the sender's unchanged pending purchase. Reconnecting too
early can lose that replay as well. The actual two-node test recovers the original
purchase but fails continued replenishment when its automatic successor is
missing from the producer's pool. Treat reconnect or direct delivery as recovery
of a specific transaction, then continue monitoring fresh purchases. Repeated
local submission returning `already known` is not delivery evidence.
The [bounded P4 resend candidate](restart-autobuy-rebroadcast.md) now recovers the
retained correct-nonce failure automatically, followed by two fresh purchases
for each owner and a passing 52-block cold audit. It resends only the unchanged
current-nonce pending intent while mining/buying remain enabled; remote validation
still applies. Queue admission alone is not proof of receipt or inclusion.
Keep monitoring funding and nonce gaps, which this candidate does not repair.
Do not cycle peers or enable extra historical launch signers as an unattended
workaround.

The [uninterrupted funded partition](restart-live-funded-partition.md) now
demonstrates another boundary: six sequential manual predecessors succeed, but
the seventh remains locally pending while the saved automatic intent is still
one nonce ahead. Both cold ledgers pass and the exact predecessor is admissible
in the receiving pool after its stake returns. P4 does not retry this manual
predecessor while the later automatic intent is paused. The
[manual-predecessor follow-up](restart-manual-purchase-delivery.md) now reproduces
rejection/known-peer suppression and exact-byte retry with the real handler.
Direct delivery on restarted full-state copies recovers the original, saved
intents and fresh successors without new funding. A shorter-window case stops
after one fresh donation purchase while waiting for its live ticket's selection;
empty free funding at that point is different from a locally pending transaction.
The original live connection's precise message ordering remains unrecorded.
Do not interpret local admission or `already known` as end-to-end delivery proof.

The [uninterrupted follow-up](restart-uninterrupted-delivery.md) now passes
funding, six sequential originals, unchanged saved intent and two fresh
automatic purchases while both services remain running. Both 59-block cold
ledgers and the isolated branches reconcile. All manual originals propagate
normally in that run; it does not exercise direct recipient submission during
the uninterrupted sequence. Conditional synthetic funding, an observed normal
ticket return and a bounded pass do not establish a real reserve or unattended
recovery policy.

The [injected-rejection follow-up](restart-injected-manual-delivery.md) now also
passes the uninterrupted sequence with actual direct delivery. A temporary
test-only receiver price setting causes a native rejection of the first
original. After normal price restoration and a measured local-only pending
interval, exact-byte direct submission recovers it. Seven originals, the
unchanged saved intent, two fresh automatic purchases and both 54-block cold
ledgers pass; two originals need direct delivery. The price manipulation is an
isolated test stimulus, not an operator recovery step. Use the existing
readiness, funding, original-byte and canonical native-success checks above.
Real funding availability, response responsibility and equal-weight convergence
remain open.

The [equal-weight follow-up](restart-equal-weight.md) now reproduces connected
producers advancing separate branches at identical weight with genuine history
present. Both ledgers and local ticket purchasing remain valid. This is a third
distinct condition to monitor: compare **head hashes and cumulative difficulty**
across producers, not only height, peer count, mining flags or local purchase
success. A correct saved nonce does not rule out a network split. The passing
case with previously fetched fork data does not remove the fresh first-contact
failure. The [coordinated-pause follow-up](restart-equal-weight-pause.md) now
passes on fresh copies of that failure. Pausing only one miner and buyer through
existing RPC, with both services connected, permits ordinary synchronization
and continued production. This option requires agreement on the continuation
and a funded eligible surviving producer; it is not automatic branch selection.
Preserve both histories and signed purchases before acting. Observe actual head
movement after stop calls, which can leave delayed seals.

The paused wallet ends at canonical/saved nonces 8/39 with zero tickets and
about 2,021.98 liquid FSN. Its adopted history already contains two first-retreat
losses. Both final canonical ledgers and both pre-pause ledgers reconcile, but
convergence does not clear the nonce gap or supply usable funds. Keep that
wallet paused while reviewing the exact originals, intervals, fees and funding.
The [paused-wallet follow-up](restart-paused-purchases.md) now recovers all 31
originals exactly through existing RPC before and after restart. Independent
local pool checks reject every original and the saved intent for funding on
both nodes; the entrant's funded purchase is admitted. All canonical ledger
artifacts and saved intents remain unchanged. This diagnostic keeps mining and
buying disabled, so it is not a post-resume or sequential-repair pass. The
first original's native parameter window closes well before the newest saved
intent's window. Assess every original's validity as well as funding before
starting repair. The [explicit-abandonment follow-up](restart-expired-nonce-neutralization.md)
now consumes the 31 missing nonces with owner-signed zero-value self-transfers
for 0.001302 FSN gas, preserving the saved nonce-39 intent and all donation
interval rights. Both 50-block cold ledgers pass. This removes a nonce gap but
leaves the buyer unfunded. The [saved-intent follow-up](restart-stale-intent.md)
now separately passes explicit abandonment of a seeded stale intent, correctly
ordered synthetic funding and fresh automatic purchases/mining, with both cold
60-block ledgers reconciled. Its failed funding-order attempt is also retained.
Do not clear its saved intent, override heads, or count the paused
wallet as a functioning producer merely because its node has synchronized.
The entrant's continued buying does not prove recovery of the paused account.
