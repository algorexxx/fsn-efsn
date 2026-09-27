# Bounded automatic purchase rebroadcast

27 September 2026, baseline `ce7f9718318c49b93594243c0b07d885a6fe04ec`.
This is a narrow extension to **P4**, for review on the investigation branch.
It adds no new patch category, consensus rule or transaction-validity exception.

The [previous investigation](restart-peer-purchase-retry.md) established that
seeing a purchase in the local pool did not establish delivery. A receiver could
reject it before importing a funding/refund block, or discard it before enabling
transaction acceptance. Ordinary gossip then skipped that connection because it
already knew the transaction hash. A manual reconnect recovered one purchase,
but the next purchase became stranded again.

## Candidate behavior

The controller still retains one exact signed purchase per owner. It now permits
a pending-purchase rebroadcast on at most one reconciliation attempt per five
seconds, independently of head-change notifications. The deadline uses elapsed
process time; it is not persisted and a fresh controller can retry immediately.
The existing startup, signing, pool-loss and failed-submission paths remain.

Before requesting that resend, the controller checks the canonical nonce,
conflicting transactions, pending versus queued status, cancellation, both
mining and auto-buy flags, and whether its inspected head is still current.
A queued purchase or nonce gap is not rebroadcast. The full-node backend checks
restart readiness and actual pending status again, then places the single
unchanged transaction into each connection's existing nonblocking transaction
queue, including connections already marked as knowing it. A full queue drops
the attempt; the controller can try again later. No socket-writing goroutine,
new RPC endpoint, global known-hash reset, fee bump or replacement signature is
introduced. The light backend explicitly reports this operation unsupported.

The receiving node still runs its ordinary transaction checks. Successful
queueing is neither acknowledgement nor inclusion. Transactions already queued,
sent or signed cannot be recalled by disabling buying; clean process shutdown
remains the custody-handover boundary. A concurrent head change after the local
checks is also possible; normal remote validation and later reconciliation apply.

The production changes are confined to:

- `internal/ethapi/autobuy.go`: retry scheduling and pending-purchase guards;
  an internal clock/tick seam permits deterministic scheduling checks.
- `internal/ethapi/backend.go`, `eth/api_backend.go`, `les/api_backend.go`:
  the backend operation and its full/light implementations.
- `eth/handler.go`: queue the explicit resend without the ordinary known-peer
  filter, respecting cancellation and a closed peer set.

## Evidence

All final runs below pass under Linux race detection with Go 1.21.3. The normal
node and light-backend production packages also build successfully.

| Check | Result |
| --- | --- |
| Twelve controller cases | Exact saved bytes preserved; due/not-due, pending/queued, nonce gap, replacement, another ticket, cancellation, disabled buying/mining, changed head and consumed nonce covered. Rapid changed heads at fixed times permit retries only at 0, 5 and 10 seconds. |
| Peer queue and wire cases | Known peers receive unchanged bytes; full queues do not block or prevent another peer being queued; cancellation and closed peer sets enqueue nothing. |
| Four ordered real-pool protocol cases | The original three controls still pass. The new backend method is rejected before the original missing block, then admitted after real header verification/import; normal validation is retained. |
| Existing purchase regressions | Runtime startup/retry, all nine recovery cases, explicit replacement and all eight record-storage failure cases pass. |
| Complete-state two-service continuation | Passes in 160.17 seconds, including cold verification; exact retained purchases execute, followed by at least two new purchases for each owner. |

The first regression launcher used the wrong working directory and failed to
find its fixtures. That failed log is retained; the same binary passes from
`tests/restart`. The inherited full `eth` test package still has unrelated stale
test APIs, documented in the previous investigation. Focused peer tests compile
all ten actual production files plus the named current tests; this is not a
claim that the inherited full package suite passes.

`focused.txt` records the earlier guard run before the deterministic clock seam
was added; `focused-final.txt` covers the final controller and all twelve cases.

## Live continuation and accounting

Two fresh copies of the retained 44-block failure were made on D:, with
**614 files / 1,147,983,085 bytes** verified against their source. The separate
ordered-protocol copy uses another 573,895,030 bytes. Only public synthetic keys
and a private loopback-only network namespace were used.

The live nodes begin at **15,130,124**, hash
`0xd94c46f9d7993ebbd0ac7e6d984e36b280724b30028edd04166e0b7d59f5a8f8`,
with canonical/saved donation nonce 9 and entrant nonce 38. The donation's exact
saved purchase is submitted only to its originating node while the connected
receiver is not accepting transactions. The test verifies its absence remotely.
Mining and then automatic buying are enabled; no reconnect or receiving-node
transaction RPC follows. Both exact saved purchases execute at **15,130,125**.

The progress gate requires fresh donation nonce **11** and entrant nonce **40**,
with successful canonical receipts and native purchase logs on both nodes.
Production then stops normally, including the already scheduled seals. Eight
new blocks finish at **15,130,132**, hash
`0x3822ad8774ae56fbda93d439a4d1920bd827bb7f6d4846e9ba87f7ffc7620afe`,
state root `0xfd2b99066f2ff7879dc106d379ef5e685f98d9e86e0e17e768c74c5f7c026612`.
Donation nonces 9–11 and entrant nonces 38–42 have executed. Donation signs two
of the new blocks; the entrant signs six. The backup signs none.

Both stopped databases agree byte-for-byte on the 52-block suffix, receipts,
changed account records and ticket state. The independent interval ledger
accounts for rewards, fees, selected-ticket refunds and the two previously
authorized synthetic funding transactions. **No funding transaction or new
retreat occurs in this continuation.** The original 44 JSON/RLP block records
are unchanged, and all 614 source files still match after the run.

Final donation state has nonce 12, one ticket and **22.915501816 FSN** liquid.
The entrant has nonce 43, zero tickets and **233.227084448 FSN** liquid; its
next signed nonce-43 intent remains saved and pending at shutdown. Both cold
intent checks pass. These are synthetic fixture accounts, not a statement of
the user's present wallet balances. Existing time-lock rights are preserved
in the saved account inventory and independently reconciled by the ledger.

## Remaining scope

This closes the reproduced correct-nonce delivery stall for the tested
continuation. It does not repair nonce gaps after deeper reorganizations,
fund an insolvent owner, guarantee delivery through permanent isolation,
replace expired/underpriced signed intent, or establish power-loss durability.
The protocol samples do not retrospectively expose the earlier live receiver's
exact admission errors.

Next use this candidate in a complete-state live partition/rollback rehearsal,
with explicit funding and monitored nonce-gap repair. Keep peer delivery,
funding, native execution and post-reorganization nonce resolution as distinct
gates. The one-backup-block launch sequence and fifteen-item review inventory
remain unchanged. Independent review and the other launch gates remain open.

Evidence: [scripts, logs and retained results](evidence/restart-autobuy-rebroadcast-2026-09-27/).
The stopped live databases are at
`D:\FusionRehearsal\autobuy-rebroadcast-2026-09-27\{producer,verifier}`.
Preserve them and the earlier failures; use fresh copies for another live run.
