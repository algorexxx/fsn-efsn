# Automatic ticket purchase interruption rehearsal

25 September 2026, baseline `33e80d1`. This extends the
[purchase-controller investigation](restart-purchase-controller.md).
Only test code, documentation and evidence are added. The production controller,
transaction pool, database adapter and consensus code are unchanged.

## Boundaries under test

The existing controller signs a purchase, stores its exact binary transaction
under the account's local automatic-purchase key, and then submits it to the
transaction pool. Once canonical state consumes the nonce, it checks the native
receipt before retiring that record. It may then construct a purchase at the new
nonce. Pool acceptance alone is not confirmation.

Test-only wrappers exit the process with code 86 immediately before or after the
real record `Put`, real pool submission or real record `Delete`. Normal cleanup
does not run. No production injection points were added. Each case uses separate
prepare, abrupt-exit, recovery and cold-check processes with a real LevelDB,
transaction pool, gas estimator and encrypted public-scalar-1 keystore.

| Scenario | Abrupt boundaries | Cases per platform | Required recovery |
| --- | --- | ---: | --- |
| New automatic purchase, pool journal restored | Before/after save; before/after submission | 4 | Before save, no record or submitted purchase; otherwise exact saved bytes survive. After submission the pool journal restores the purchase. |
| New automatic purchase, pool journal unavailable | Same four positions | 4 | A saved purchase is resubmitted unchanged with the wallet locked. Before save, signing requires unlocking again; the nonce is still unconsumed. |
| Original purchase confirmed in a block | Before/after retirement; before/after saving its successor | 4 | Canonical receipt, ticket and consumed nonce remain correct. Retire the old record and recover or construct only the next-nonce purchase. |
| Original nonce consumed by a replacement transfer | Before/after retirement | 2 | Do not falsely confirm the original purchase or resubmit its consumed nonce; continue at the canonical next nonce. |
| Purchase already in the pool, with no automatic record yet | Before/after adopting it into the local record | 2 | Recover the existing pool transaction with the wallet locked and preserve its exact bytes. |

The lost-pool cases start recovery with a different empty journal path. The
original journal is preserved. This models an unavailable pool journal; it does
not manufacture corrupt journal bytes or change the automatic-purchase record.

## Verification

Cold recovery checks the exact expected presence and contents of the record at
each cut, and checks which pool entries must have survived. It does not accept
eventual recovery as a substitute for those boundary assertions. Canonical head
and nonce remain unchanged during purchase recovery. The confirmed/replaced
fixtures independently inspect canonical transactions, receipts and ticket state.

The wallet initially remains locked in every recovery process. A retained
purchase can recover without signing access. If the cut preceded saving a new
purchase, the controller must first report the locked wallet without submitting;
the fixture then unlocks the public test key and resumes at the unconsumed nonce.
When a new signed intent was observed before the cut, the recovered bytes must
match it exactly.

Every case observes another complete retry interval after recovery and rejects
an additional submission. A further cold process verifies the same signed bytes,
sender, nonce and exactly one pooled transaction, with the wallet locked again.
For retirement cuts, no next purchase had been signed yet; `same bytes=false` in
the test log means that a prior next-purchase comparison is inapplicable, not
that a byte comparison failed.

## Results and limits

All sixteen final cases pass on Windows (104.47 seconds) and Linux with race
detection (175.07 seconds), with no production-code change required.
Final results are recorded in
[`restart-purchase-crashes-2026-09-25`](evidence/restart-purchase-crashes-2026-09-25).
Each complete run covers sixteen abrupt exits and their separate recovery/cold
processes. Initial runs and the strengthened final assertions are identified
separately in the evidence; the final source and binaries are pinned by hash.

These are sparse synthetic fixtures. Other owners' tickets have test-only
perpetual intervals to permit transfer-only blocks, as in the earlier recovery
tests. The production miner is represented by its enabled-state backend in this
experiment; actual miner/peer handover has separate evidence. No real key, original
backup, complete-state copy, W: data or public network is used. Windows and Linux
fixture timestamps follow their run time, so cross-platform block/transaction
hash equality is not claimed.

The operating system remains running during the abrupt exits. The local record
still uses the database's normal non-synchronous `Put`/`Delete`; these checks do
not establish power-loss durability, torn-write handling or exactly-once network
delivery. They also do not inject cuts within a LevelDB write or at every internal
pool-journal instruction. A submitted transaction may have reached peers before
a process exits; resubmitting the identical transaction is expected behavior.

The subsequent [storage/peer rehearsal](restart-purchase-storage-and-peers.md)
covers eight database-interface errors and two compatible live-peer forks.
Deeper rollback of already retired intent, exact concurrent confirmation cuts,
expired/underpriced retained purchases, machine-level storage failure and
one-active-key custody remain separate review concerns. The existing controller
pauses or reports unresolved conflicts rather than automatically changing fees
or filling unexplained nonce gaps. Independent review of patch P4 in the
[node patch inventory](restart-node-patch-review.md) remains required before release.
