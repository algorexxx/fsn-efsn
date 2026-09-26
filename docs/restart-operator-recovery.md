# Operator purchase recovery procedure

Draft for release review, 26 September 2026. This collects the demonstrated
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
| Time locks | `fsn_getTimeLockBalance(assetID, address, blockNumber)` | Every start, end and value, not just a displayed total |
| Tickets | `fsn_allTickets(blockNumber)` / `fsn_allTicketsByAddress(address, blockNumber)` | Owners, IDs, heights and interval endpoints |
| Pending/queued transactions | `txpool_content` | Owner, nonce, hash and any conflicting replacement |
| Mining/buyer state | `eth_mining`, `fsn_isAutoBuyTicket`, service logs | Flags, sync state and actual repeated purchase results |
| Purchase result | `eth_getTransactionReceipt` plus canonical block | Receipt status and native result log; verify the ticket was created |

An advancing common chain and enabled flags do not prove this wallet is buying
or mining. Monitor its nonce, successful purchases, usable tickets, free interval
coverage and errors as well as peer count and head movement. Preserve old head
and block hashes so displaced transactions can later be located.

## Classify before changing anything

| Observation | Response supported by current evidence |
| --- | --- |
| Normal synchronization pause | Allow sync to finish and check automatic resumption; investigate a persistent pause |
| Retained purchase nonce exceeds canonical nonce, no conflicting pool entries | Retrieve and validate every missing original transaction before sequential repair |
| Temporary lack of free stake, with a live ticket and another producer | Wait for observed ordinary selection/return, then recheck the exact interval and nonce |
| Zero tickets, insufficient liquid and insufficient covering locks | Waiting for the absent ticket's selection cannot help; inspect future expiry rights and actual funding options |
| Conflicting nonce, missing/corrupt record, missing bytes, expired interval or inadequate fee | Stop this procedure and review the specific case; no generic replacement or record deletion is established |
| No available eligible producer | Normal transfer/resubmission cannot itself create the block needed to execute it; this runbook does not establish a repair |
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
   contexts. Old signatures can become unsuitable while waiting.
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
4. Submit the reviewed original bytes using `eth_sendRawTransaction`. Submission
   acceptance is not purchase success. Wait for a receipt, verify its block hash
   is canonical, inspect the native BuyTicket result for an `Error` field, and
   match the created ticket's ID/owner/interval/value to the signed payload.
5. Recheck canonical nonce, pool, original later intent, tickets, free locks,
   liquid and surviving producer. Advance to the next missing nonce only after
   successful canonical inclusion. A changed branch, conflict, new loss or
   insufficient funds returns to diagnosis; do not bulk-submit or sign guessed
   replacements to force progress.
6. Once all predecessors succeed, observe execution of the byte-identical saved
   intent and fresh automatic successor purchases without a new manual start
   command. The passing live rehearsals require at least two fresh successors;
   that is an acceptance check, not proof of indefinite unattended operation.

## Acceptance and retained record

Record original and final heads/roots, canonical nonces, transaction bytes and
hashes, native receipts, ticket changes, interval accounting, all funding/fees,
saved intent identity and fresh successor evidence. When a verification restart
is planned, perform a clean restart with the expected configuration and confirm
persisted heads, receipts and continued purchasing. Coordinate downtime with
the available producer; do not cycle every service merely to satisfy a checklist.

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
canonical branch; repair remains gated on that evidence. This procedure stops at unsupported conditions
instead of treating a successful short rehearsal as an automatic recovery guarantee.

The [genuine-history follow-up](restart-partition-history.md) now removes the
exact compact-history ancestor failure. A separate stopped heavier-peer case
converges normally and passes both cold ledgers. It also demonstrates a different
stall: the donation owner's saved and canonical nonces are both 7, but it has
zero tickets, 2,021.665544264 liquid FSN and no free lock coverage for the saved
interval. The real pool rejects its 5,000.000042448-FSN liquid requirement.
Do not apply missing-nonce repair to this state. Recheck authorized usable funds
and intervals; waiting for an absent ticket or clearing a record cannot supply
them. Future rights outside the purchase interval are not available coverage.
