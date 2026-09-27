# Pending purchases and peer retry

27 September 2026, baseline `cf70290`. Production P1–P15 is unchanged. This
follow-up adds tests and evidence for the delivery gap identified by the
[direct-submission rehearsal](restart-purchase-delivery.md).

The controlled peer cases establish that a rejected purchase can remain known
to the connection, suppressing ordinary rebroadcast even after the recipient
has caught up. Explicit transmission of the same bytes and a ready connection's
pending-transaction replay both work. However, the actual two-node reconnect
test **fails sustained replenishment**: the original purchase succeeds, then the
donation's next purchase becomes stranded. One reconnect is not a complete fix.

## Ordered protocol reproduction

One verified disposable database copy is rewound to block 15,130,098. The
sender's real pool uses the retained state at 15,130,099; the receiver's real pool
uses its canonical state at 15,130,098. The original saved donation purchase
at nonce 8 is sent through the actual `TxMsg` handler. The original signed
15,130,099 block then passes through `NewBlockMsg`, the fetcher, ordinary header
verification and block execution. No new signature, balance or ticket is created.

The transport is `p2p.MsgPipe`, which controls message order. These focused cases
exercise actual peer/pool/import methods, not a complete TCP session or handshake.
The later live case exercises the full node processes and reconnect path.

All three ordered cases pass under Linux race detection in **0.29 seconds**:

| Action | Captured result |
| --- | --- |
| Send the nonce-8 purchase before the block | Remote pool rejects the three-hour start-time violation; handler has already marked it known; handler itself returns success. |
| Submit the same bytes to the sender's pool again | `already known`; no new transaction is introduced. |
| Call ordinary broadcast again | Zero eligible peers; no additional message is queued or written. |
| Explicitly resend before the block | Remote validation rejects it again. Resending does not bypass validation. |
| Import the original block and call ordinary broadcast | The pool is caught up, but the rejected transaction is still absent and ordinary broadcast is still suppressed. |
| Explicitly resend on the same connection after import | Exact bytes are admitted remotely and become pending. |
| Replay pending transactions on a fresh, ready connection | Exact bytes are admitted remotely. |
| Replay on a fresh connection with transaction acceptance disabled | Message is discarded before pool admission; enabling acceptance afterward does not defeat the sender's known-transaction suppression. A further ready reconnect succeeds. |

The recorder captures the real pool's returned error, serialized transaction,
canonical head and the receiver's known-transaction flag **before admission**.
Each successful case ends with canonical nonce 8 and pending nonce 9: admission
has not been confused with execution. The imported block bytes match the retained
original exactly. These are deliberately recreated exchanges, not a recording of
the earlier failed connection.

## Actual two-node reconnect

Two further verified copies begin at the previously retained block 15,130,111.
Both services reopen with the exact saved records, correct canonical nonces and
empty pools. They connect while mining and buying are disabled. The saved
donation nonce-8 bytes are submitted only to the originating donation node.
The test records them pending there and absent from the entrant's pool.

Both mining services are enabled before either buyer. The purchase is still
absent from the recipient. The test removes the one static connection, waits
until both peer counts are zero, and reconnects the same running node identities.
Ordinary pending replay delivers the purchase. The receiver gets no transaction
RPC submission, and neither saved intent is replaced.

Both automatic buyers are then enabled. The two original saved purchases
(donation nonce 8 and entrant nonce 26) execute in block 15,130,112. The donation
signs 15,130,113, consuming its ticket and refunding its rights. Its new automatic
nonce 9 stays pending locally, while the entrant continues through nonce 37.

The stronger both-owner replenishment gate **fails after 155.60 seconds**. Both
heads reach 15,130,124, hash
`0xd94c46f9d7993ebbd0ac7e6d984e36b280724b30028edd04166e0b7d59f5a8f8`.
The final observations show:

| Owner | Canonical nonce | Own pending purchase | Recipient pool |
| --- | --- | --- | --- |
| Donation | 9 | `0xa13b447eb428b69640202b0257a0d61b7a43e53d03c5c5e4c6c5a531ab92db46` | Absent from the entrant's pending and queued pools |
| Entrant | 38 | `0xa34cf490d674e941cdac376a9590f748a7fa9ef47db47feaadc68b216b822867` | Continued buying is confirmed by the canonical suffix |

This failure is preserved; successful delivery of the initial purchase does not
satisfy the required fresh successor purchases for both owners.

## New purchase's funding boundary and cold audit

After clean process termination, both cold pools accept both saved purchases at
their matching canonical nonces. The existing complete-state diagnostic and
independent accounting pass in **16.54 seconds** across all **44 suffix blocks**.
The earlier 31 artifacts are unchanged. The thirteen new blocks contain the
donation's nonce 8 and twelve entrant purchases, with no new retreat. All account
differences, receipts, tickets and future time-lock intervals reconcile. The
reused cold helper's log describes what that helper samples; the separate live
pool trace does retain the missing recipient transaction in this experiment.

A further race-instrumented historical pool check passes in **0.15 seconds**:

| Recipient state | Exact donation nonce-9 purchase |
| --- | --- |
| 15,130,112, before donation ticket selection/refund | Rejected: available liquid is 21.978001816 FSN and covering free locks are absent; the pool requires 5,000.000021224000021224 liquid FSN. |
| 15,130,113, after selection/refund | Accepted remotely, pending. |
| 15,130,124, final stopped state | Accepted remotely, pending. |

No funding is added between these checks. The same signed bytes and nonce pass
after ordinary ticket rights are returned. This is a funding-state boundary
during ordinary production, distinct from the earlier eight-hour timestamp jump.
Logs place the new submission at 08:47:48.033 and the entrant's refund-block import
at 08:47:48.037, in the logs' local timezone. That timing and the captured states
support a transaction-before-refund explanation. The precise live admission call
was not instrumented, so its error is not retroactively claimed captured.

The donation ends with zero tickets, 22.290523040000021224 liquid FSN and free
5,000-FSN rights covering its saved purchase. The entrant has one ticket and
231.352063223999978776 liquid FSN. No new contribution or supply change occurred.

## Build and evidence limits

The full `eth` package tests fail to compile in unchanged legacy tests referencing
removed `ethdb.MemDatabase` APIs and old state signatures. The failure is retained.
The focused protocol executable compiles all current platform production Go files
reported by `go list`, plus the new protocol test, as an explicit file list. No
production overlay, fake pool validation, or claim of a passing full suite is used.
The live and cold tests compile the normal `tests/restart` package.

New disposable copies use 573,895,030 bytes for the protocol case and
1,147,817,023 bytes for the live pair on C:. All 612 files in the shared source
pair are rechecked unchanged. The protocol subset's 304 files are independently
checked too. All services are stopped. Raw successes, the live failure, the legacy
build failure, observations, block artifacts, source/executable identities and
checksums are in [the evidence directory](evidence/restart-peer-purchase-retry-2026-09-27).

## Next decision

A manual ready reconnect or direct submission of reviewed bytes remains a
recovery option for a specific missing purchase. It does not establish unattended
operation, and repeated peer cycling should not be treated as a permanent solution.

The next candidate belongs within P4's automatic-purchase delivery behavior:
bounded retries of the **same signed purchase** while its nonce remains current
and it is still locally pending. Ordinary broadcast and repeated local submission
are insufficient in the reproduced known-peer state. A candidate must bound rate
and work, stop when buying/mining is disabled or the nonce is consumed, preserve
the saved bytes, and leave remote funding/timestamp checks intact. Test the two
rejection boundaries, unready peers, inclusion/nonce changes, shutdown and the
failed complete-state continuation before selecting a patch.

No such production change is made here. Consensus, ticket economics, fixed
ancestry and the one-backup-block launch remain unchanged. Complete-state live
nonce rollback/repair and operational reserves remain separate gates.
