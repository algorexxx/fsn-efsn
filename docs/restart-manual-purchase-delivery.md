# Manual predecessor delivery after a nonce rollback

27 September 2026, baseline `3213b81`. Production P1–P15 is unchanged. This
investigation uses disposable copies of the retained
[uninterrupted funded partition](restart-live-funded-partition.md), synthetic
keys 1–3 and private loopback-only network namespaces.

## Controlled peer reproduction

The exact stalled donation nonce-16 purchase is
`0xb48486a5a0d79ba11ed9c67107e7e83aa886c3309fbb9785fc7cbe21fd9b0e61`.
The recipient is rewound only in the disposable diagnostic copy to 15,130,120.
The sender's real pool uses the retained state at 15,130,121. Both sends go
through the production transaction message handler and real remote pool.
The original signed selection block 15,130,121 is then imported through the
production block message handler, fetcher, verification and execution.

| Ordered action | Observed result |
| --- | --- |
| Ordinary send before selection | Remote pool rejects insufficient balance; receiver has already marked the hash known. |
| Duplicate local submission and ordinary broadcast | Local `already known`; peer-known filtering produces no additional wire write or queued message. |
| Explicit resend before selection | Same balance rejection; validation is still enforced. |
| Import the original selection block, then ordinary broadcast | Original block bytes match; recipient pool refreshes, but the rejected purchase remains absent and broadcast remains suppressed. |
| Explicit resend on the same connection | Exact signed purchase is admitted and pending. |
| Pending replay on a fresh ready connection | Exact signed purchase is admitted and pending. |

Both cases pass Linux race instrumentation in **0.19 seconds**. The trace retains
actual admission errors, heads, signed bytes, known flags and wire-write counts.
Final canonical nonce is 16; pending nonce is 17. Admission is not execution.
The transport is an ordered `p2p.MsgPipe`, not a TCP handshake.

This proves a mechanism consistent with the original failure. It does **not**
retroactively identify the original live connection's exact message ordering
or remote rejection, which that run did not capture. P4 still retries the saved
automatic intent; it cannot reach that retry while saved nonce 17 is paused
behind manual predecessor 16.

The first protocol attempt failed a test assertion because `insufficient balance`
has additional balance/gas details in the actual error. That stopped copy and
log are retained. The corrected assertion checks the expected error prefix,
while retaining exact hash, bytes, parent height and known-flag checks. A fresh
copy is used for the passing attempt. All four earlier nonce-8 peer cases also
pass again in **0.35 seconds**, including readiness-gated reconnect and P4 retry.
The focused `eth` build uses the package's production Go files plus the selected
test files; it does not claim that the unrelated legacy `eth` tests compile.

## Real-node delivery and ordinary replenishment

Each live attempt begins from a fresh, checksummed two-database copy at
15,130,125, hash
`0x93ccd33c56bcdff1a572b381887f99eb0ca349af63b63ecffa63858b7cffef77`.
Donation has canonical nonce 16 and saved automatic nonce 17. Entrant has
canonical/saved nonce 32. Both cold pools are empty.

The exact original nonce-16 bytes are submitted once to the entrant through
existing `eth_sendRawTransaction`, before connecting the nodes. The test checks
the returned hash, the entrant's pending pool, and that neither saved intent was
altered. Both ordinary mining services are then enabled before the buyers.
The stronger acceptance check requires canonical native success for both saved
intents and at least two new automatic purchases from each owner, then cold
accounting on both stopped databases. There is no new funding, nonce replacement,
saved-record clearing, forced synchronization or further backup block.

The first live attempt **fails its 150-second successor window** after
**154.69 seconds** overall. Manual nonce 16 executes at 15,130,126, unchanged
saved nonce 17 at 15,130,129, and fresh automatic nonce 18 at 15,130,133.
Donation stops at canonical nonce 19 with no saved/pending purchase and one live
ticket. Its 25.103044263999957552 liquid FSN and future free locks cannot fund
another current purchase until ordinary selection returns its committed stake.
There is no new first retreat. Entrant continues buying through nonce 42.

Both first-attempt cold databases pass **58-block** accounting in **29.34 seconds**,
ending at 15,130,138, hash
`0x71b62081d18216a1468db0c9b3f4e4564e835b2d6326fcf3d60876b200f3c0cb`.
This is a selection/funding wait, not another locally pending delivery failure.
The planned successful-stop snapshot is not reached in this attempt.

The second fresh attempt uses a 300-second selection window and **passes in
159.73 seconds overall**, including startup and shutdown:

| Purchase | Canonical inclusion |
| --- | --- |
| Unchanged manual donation nonce 16 | 15,130,126 |
| Unchanged saved donation nonce 17 | 15,130,128 |
| Unchanged saved entrant nonce 32 | 15,130,126 |
| Fresh automatic donation nonces 18 and 19 | 15,130,131 and 15,130,134 |
| Five fresh entrant purchases observed at the progress gate | Nonces 33–37; another nonce 38 is included before final shutdown. |

Both cold ledgers pass in **29.08 seconds**, with identical **56-block** canonical
suffixes. Final height is **15,130,136**, hash
`0x6ed2979ba3eed77b7493ff4b153d3fab9960b5bd5be88e1a7191230d5b716e45`,
state root
`0xfd0ae97613b0897f2c1afc0317f2ad34eaa54f510cbccab95d8f7dadb355f773`.
The eleven added canonical blocks have four donation and seven entrant signers,
with no backup block or new retreat. All purchase receipts, rewards, fees, ticket
returns, account changes and future interval boundaries reconcile. The two
earlier funding transfers remain the only additional funding in the ledger.

Final donation nonce is 20, with zero tickets, 25.728044263999957552 liquid FSN
and free returned time locks. Entrant nonce is 39, with one ticket and
231.664542000000042448 liquid FSN. Cold owner nonces and saved bytes match the
successful stopped-node observations. Donation has no saved intent; entrant
retains its own nonce-39 intent.

This second attempt follows a different selection sequence. Its pass does not
prove that simply extending the first run would necessarily have succeeded within
the same duration, nor does either window establish a production timeout.

## Preservation and verification

The original failed run's 699 copied files remain unchanged. Both attempts retain
the same first 45 canonical blocks byte-for-byte in JSON and RLP. All 304 source
files for the earlier peer-test regression are also unchanged. Failed diagnostic
and live attempts are retained alongside the passing attempts, with their own
logs and source identities. All race-instrumented runs are free of race reports.

The test databases and binaries are on D:, leaving about 154.1 GB free. All
rehearsal processes are stopped. The final passing copy is
`D:\FusionRehearsal\manual-purchase-live-2026-09-27-attempt-02`; preserve it and
use a fresh copy for future experiments. Native logs use local UTC+02 time;
the structured pool traces carry explicit UTC timestamps.

## Operational scope

Direct submission of already reviewed signed bytes to the active producer is an
existing-interface recovery option. Verify the accepted branch, interval funding,
canonical receipt and native BuyTicket result; do not treat an RPC return or
`already known` as execution. Keep the later saved automatic intent intact.
The [operator procedure](restart-operator-recovery.md) now includes that distinction.

The tests' pool/saved-record observation uses test-only `lab` RPC. Delivery uses
existing production RPC. This is a restarted continuation of the failed run,
not an uninterrupted partition-to-completion pass, and it is not evidence of
indefinite operation or a universal recovery reserve. First-retreat losses,
equal-weight branches, monitoring and actual authorized funding remain separate
release concerns. No new runtime patch is proposed by this investigation.

The [fresh uninterrupted follow-up](restart-uninterrupted-delivery.md) now passes
the funded sequence with six originals, the exact saved intent, two automatic
successors and both 59-block cold ledgers. It includes the recipient-delivery
check, but ordinary propagation succeeds for every original in that run, so no
direct submission is needed. An uninterrupted reproduction requiring that
intervention remains separate from this pass and the restarted-copy evidence
above. The follow-up also fixes test-only interval arithmetic by using existing
raw time-lock RPC; the production inventory is unchanged.

Evidence: [scripts, raw logs, pool traces and block ledgers](evidence/restart-manual-purchase-delivery-2026-09-27/).
