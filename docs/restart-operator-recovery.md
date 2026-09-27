# Operator purchase recovery procedure

Draft for release review, 27 September 2026. This collects the demonstrated
manual recovery path. It does not enable an automatic repair mechanism or mean
that every failure below has a supported repair. Production adoption, response
times, named operator coverage and a real funding source remain release decisions.
The [monitoring and response guide](restart-monitoring-response.md) is the
incident entry point: it defines observations, diagnosis order, ownership and
implementation gaps. This document supplies the transaction recovery steps.

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
| Retained purchase nonce exceeds canonical nonce, no conflicting pool entries | Check current receipts and pool reinjection first; retrieve and validate only the originals still missing before sequential repair |
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
the saved record or assume an enabled buyer fills the gap. The pause result uses
a held signer and explicit downloader request; it does not prove automatic
repair, unattended convergence or continued mining.

The [subsequent recovery](restart-abandonment-repair.md) now passes with fresh
services and real miners: replay the unchanged self-transfer at nonce 39,
require its new canonical no-ticket receipt, then recover original purchases
40–42 sequentially. Purchases 41 and 42 wait for ordinary ticket selection to
return usable rights. The unchanged saved 43 executes automatically, followed
by two fresh successors and actual production by both owners. Both 86-block
cold ledgers pass, with no new funding, re-signing, record edits or direct
delivery. All four manual transactions are sent to the originating pool.

This is a conditional recovery after restart. Check actual ticket ownership,
return eligibility, remaining interval coverage and pool admission before
waiting on selection; earlier first-retreat losses can prevent the same route.
The [uninterrupted integration](restart-live-abandonment-repair.md) now passes
ordinary heavier-peer synchronization and recovery with both services running.
Reinjected self-transfer 39 and purchase 40 execute automatically in the same
block, so receipt-aware recovery begins at 41 and manually submits only 41–42.
The unchanged saved 43 and two fresh successors execute automatically; both
owners produce and both 90-block cold ledgers agree. No new funding, direct
delivery or operator pause is needed. This closes that specific timing case.
Do not blindly replay every displaced transaction: inspect its current canonical
receipt and the pool first. A later saved intent with an empty pool and lower
canonical nonce still needs monitored/manual gap repair.

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

Release review still needs adoption of the proposed monitored/manual policy,
verified alert delivery and response coverage, and real-address funding/interval
checks. The [monitoring guide](restart-monitoring-response.md) records these open
gates without treating completed synthetic tests as deployed monitoring.

## Evidence and boundaries

These reports retain the experiments, including failed attempts. They support
specific recovery steps; they do not establish a universal reserve, unattended
repair or permission to choose another operator's branch or spend their funds.

| Case | Evidence and operational consequence |
| --- | --- |
| Single producer, process restart | [Complete-state outage](restart-full-state-outage.md) passes packet loss, SIGKILL, exact saved-intent recovery, fresh purchases and cold ledgers. Normal miner start after service restart is required. It does not create a nonce rollback. |
| Competing producers and missing history | [Initial partition](restart-full-state-partition.md) retains non-convergence and missing fixture ancestry. [Genuine-history follow-up](restart-partition-history.md) resolves the missing-history request and passes heavier-peer sync, but leaves the wallet unfunded. A correct saved nonce does not imply usable stake. |
| Rollback plus exhausted backing | [P4 partition](restart-retry-partition.md) converges but leaves seven missing purchases and insufficient current funding after two first retreats. [Controlled reserves](restart-controlled-reserves.md) show conditional recovery and renewed exhaustion after another loss. Waiting cannot refund an absent ticket. |
| Explicit funded continuation | [Funded gap](restart-funded-gap.md) passes seven originals, saved intent, fresh successors and both cold ledgers with specified synthetic funding. [Full interval audit](restart-handover-runway.md) checks both launch handovers before refunds. Neither establishes available real funds. |
| Producer readiness and transaction delivery | [Existing-funds investigation](restart-existing-funds.md) separates funded admission from startup/inclusion. [Exact delivery](restart-purchase-delivery.md) recovers the unchanged purchase. [Peer retry](restart-peer-purchase-retry.md) recovers one transaction but fails replenishment; [bounded P4 resend](restart-autobuy-rebroadcast.md) passes later automatic purchases. Current pending intent and missing predecessors need different responses. |
| Manual predecessor delivery | [Live funded partition](restart-live-funded-partition.md) retains a local-only pending predecessor. [Manual delivery](restart-manual-purchase-delivery.md) verifies rejection/known-peer suppression and exact-byte recovery. [Uninterrupted repair](restart-uninterrupted-delivery.md) passes with ordinary propagation; [injected rejection](restart-injected-manual-delivery.md) separately exercises direct delivery. Temporary receiver price manipulation is a test stimulus, not an operator step. |
| Equal-weight live split | [Fresh first-contact comparison](restart-equal-weight.md) fails convergence while both nodes purchase and produce. [Coordinated pause](restart-equal-weight-pause.md) passes ordinary synchronization after operator-selected pausing. Preserve both branches, obtain agreement, verify a funded continuing producer and observe delayed seals after stop calls. The paused wallet still needs its own funding/nonce diagnosis. |
| Retrieving and diagnosing original bytes | [Small-reserve/retrieval](restart-small-reserve-and-retrieval.md) verifies existing RPC and offline record extraction. [Paused-wallet diagnosis](restart-paused-purchases.md) retrieves all 31 originals but rejects them for funding; it also establishes each payload's admission window. These diagnostic passes are not resumed production. |
| Deliberate abandonment | [Missing nonces](restart-expired-nonce-neutralization.md) can be consumed by owner-signed self-transfers while preserving the later saved intent, but the wallet remains unfunded. [Stale saved intent](restart-stale-intent.md) additionally tests explicit retirement, correct funding order and fresh production. Funding alone does not fix an invalid payload. |
| Ordinary restart after recovery | [Restart continuation](restart-recovered-buyer-restart.md) restores the exact saved intent, executes fresh successors and produces with no new funding or manual submission. Empty-pool restart does not make a separate nonce gap disappear. |
| Abandonment rolled back again | [Compatible rollback](restart-abandonment-reorg.md) preserves the newer saved intent and displaced bytes. [Restarted repair](restart-abandonment-repair.md) passes exact resubmission. [Live integration](restart-live-abandonment-repair.md) automatically reincludes 39–40, manually repairs only 41–42 and passes saved 43, successors, production and both 90-block cold ledgers. Recheck current receipts before acting. |

Across these cases, keep branch convergence, transaction delivery, payload
validity, nonce continuity and actual funding separate. Resume a paused owner
only after its own conditions have been checked; another owner's continued
buying is not evidence that it recovered. No controller record deletion, head
override, extra historical signer or consensus relaxation is part of this
procedure. Any unsupported condition remains an explicit investigation or release
decision in the [main plan](restart-plan.md).
