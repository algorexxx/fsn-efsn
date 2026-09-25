# Automatic ticket purchase controller

Implemented on `codex/restart-investigation-wip`, following the reproduced
startup, submission-failure and stale-cache problems. The implementation is
local purchase orchestration; it changes no ticket price, selection, expiry,
accounting, signature validation or fork-choice rule. It does not implement the
restart anchor or construct the historical recovery bridge.

## Behavior

- Evaluate on startup, when enabled, on a changed head hash, and every five
  seconds. Failed attempts do not require another block to trigger a retry.
- Require both auto-buy and mining to be enabled. Stop and join the controller
  before the node closes its backend/database. The enable flag is atomic and
  head notifications are nonblocking.
- Serialize purchases per account and use the existing account nonce lock.
  Read canonical account state and both pending and queued pool transactions.
- Persist the exact signed transaction before submitting it. After an uncertain
  submission failure, pool loss or clean database restart, rebroadcast those
  bytes with the same hash and nonce. No private key is stored in this record.
- Treat pool acceptance as pending. Once the canonical nonce advances, inspect
  the transaction's canonical block and receipt. Report a purchase as confirmed
  only with a successful receipt and the native purchase log containing the
  expected owner and ticket ID derived from the actual inclusion parent.
  A consumed nonce without that evidence is reported separately.
- Recheck the head before saving a newly signed purchase or retiring a resolved
  one. A confirmation describes current canonical inclusion, not finality.
- If a different transaction occupies the saved nonce, wait for resolution.
  Also preserve a different pending ticket at any nonce: Fusion's existing pool
  otherwise removes an owner's earlier ticket when admitting another ticket.
  There is no automatic fee bump or automatic replacement of a known conflict.
- Replace the old per-height submitted boolean with an actual pool check in
  both purchase RPCs. An explicit same-nonce replacement remains possible.
  After a purchase is replaced by a transfer, a manual purchase uses the next
  available pool nonce instead of being blocked by stale submission history.

The local record is stored under `fsn-auto-ticket-v1-` plus the 20-byte account
address in the existing chain database. Its value is the encoded signed
transaction. It is not consensus state and does not affect the state root.
On load, decoding, sender and native purchase payload are checked. Invalid
records stop new automatic signing and produce an actionable warning.
This record is necessary because the pool journal cannot recover a transaction
that was signed but never accepted into the pool.

## Validation

The complete Linux node builds with the cached Go 1.21.3 toolchain and CGO.
The complete ordinary restart suite passes three repetitions under the Linux
race detector, and on Windows amd64 with CGO disabled in 91.146 seconds.
Full-backup probes are explicitly skipped in these synthetic runs. Raw evidence is in
[the evidence directory](evidence/restart-purchases-2026-09-23).

The tests use only the public synthetic key and disposable state. The runtime
test exercises the actual miner, wallet, estimator and transaction pool, then
independently executes its two produced blocks after stopping the producer.
It requires the initial failed submission to retry with the identical hash and
checks the controller's native-receipt confirmation of the first purchase.

The recovery cases exercise:

| Case | Required result |
| --- | --- |
| Auto-buy disabled; mining disabled; controller stopped | No submission during observation windows longer than a retry interval |
| Locked wallet, failed gas estimation, insufficient construction funds | Visible error, followed by successful retry without a head change once the condition clears |
| Failed submission followed by LevelDB and pool restart | Same signed transaction recovered and accepted with the wallet locked |
| Accepted purchase followed by journal/database restart | Journal restores the transaction; controller submits no duplicate |
| Same-nonce transfer replaces the purchase | Automatic buying pauses, then uses the next nonce after canonical transfer inclusion |
| Rewind leaves a nonce gap and the pool is lost | Controller pauses; after a same-height alternative consumes the missing nonce, the saved next purchase is recovered unchanged and executes |
| Later-nonce ticket evicts the saved purchase | Automatic retry preserves the later ticket rather than removing it through pool admission |
| Corrupt saved transaction | New automatic signing stops |
| Explicit purchase after transfer replacement | Manual RPC purchase uses the next pool nonce without the old cache rejection |

Recovery tests use a mining-state adapter, real LevelDB, real keystore,
estimation and transaction pool. To allow transfer-only blocks, those tests
give other owners synthetic perpetual ticket lifetimes. These lifetimes are
test scaffolding, not observations about mainnet. The miner runtime test retains
the single-surviving-ticket constraint. Reorg coverage uses a controlled rewind
and alternative block import; it is not a network fork-choice rehearsal.

## Limits and operational policy

Keep auto-buy disabled during historical bridge construction. Its ordinary
defaults still derive the purchase interval from the parent timestamp; an old
head produces an already expired default purchase. The explicit long-lived
bridge purchases and current-time transition remain separate work.

Repeated failures are rate-limited and identical consecutive warnings are
deduplicated. A five-second context bounds context-aware backend operations;
the wallet signing interface has no context parameter. Hardware/external wallet
blocking behavior is not covered by these local keystore tests.

Clean restart and the later [process-interruption rehearsal](restart-purchase-crash-rehearsal.md)
are tested. Sixteen cuts per platform now cover both sides of automatic record
save, pool submission, retirement and adoption, with exact cold-record/pool checks
and initially locked recovery. The production controller needed no change.
Abrupt power loss, torn storage, cross-device recovery, cuts within database
writes and every internal pool-journal boundary remain untested. The record uses
the database's normal `Put`, without an additional synchronous flush guarantee.
Do not describe it as power-loss-safe or exactly-once delivery.

An expired or underpriced retained transaction is retried unchanged and its
admission error is logged. A nonce gap, conflicting transaction or corrupt
record can require operator intervention. Automatic buying deliberately does
not choose a new fee, fill an unknown gap or discard unexplained signed intent.
Use the ordinary explicit transaction workflow to resolve a nonce, then let
canonical inclusion reconcile the saved record. Preserve evidence before
repairing corrupt local metadata; disabling auto-buy stops further attempts.

The per-account lock coordinates the two purchase RPCs and this controller.
It does not exclude transactions submitted through other clients or all raw
transaction paths. Normal pool validation and subsequent reconciliation still
apply. A deeper reorg can invalidate a prior confirmation; no ongoing finality
or maximum reorg depth is introduced.

Full-backup verification, full-state bridge execution, hostile-peer/anchor
tests and independent operator rehearsals remain launch gates. Passing these
tests does not establish that Fusion is ready for public economic use.
