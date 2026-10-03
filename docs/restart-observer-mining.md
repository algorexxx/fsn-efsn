# Observer history during ordinary mining

27 September 2026, baseline `c1536fb`. The external observer now has a passing
integration test with an ordinary producer and verifier, including reads that
overlap naturally advancing heads. This change adds tests and evidence only;
the observer executable, node runtime, consensus and P1–P15 are unchanged.

## Result and evidence

The final Linux run passed with race detection in 113.69 seconds. All four child
service runs exited cleanly. Thirteen separate observer invocations reopened the
same history directory and preserved the expected mining/automatic-buy flags;
the verifier never signed. See the [evidence bundle](evidence/restart-observer-mining-2026-09-27/)
and [verified results](evidence/restart-observer-mining-2026-09-27/checks.json).

The test starts with complete compact synthetic history through block 24,
devnet rules, public test keys 1 and 2, and large synthetic reserves. It chooses
the initially nonpreferred ticket owner as the sole ordinary producer so that
fallback retreat is exercised. The other node verifies ordinary peer imports.
The harness does not hold signatures, construct the later blocks or control
the downloader. It runs in a loopback-only network namespace with no backup
input or real funds. These fixture reserves and ticket schedules do not model
the donation wallet's production funding.

| Check | Final run result |
| --- | --- |
| Ordinary blocks | 25–29, identical on both nodes |
| Initial bounded backfill | Stores only 25; reports `batch_limit` |
| HTTP snapshot during advancement | Pins 27; node reaches 28; original snapshot remains consistent |
| HTTP backfill during advancement | Pins 28; node reaches 29; stores only 26–27 under its two-block bound |
| Live IPC/HTTP catch-up | Each node reaches `complete_at_observation` |
| Final and cold checks | Both nodes and retained histories agree at 29 |
| Export preservation | Eight events retained unchanged, followed by two cold rechecks |
| Native inventory audit | 26 starting tickets + 4 purchases − 5 selections − 2 retreats = 23 |

A test HTTP proxy delays one read until the producer naturally mines another
block, then forwards the actual response unchanged. This makes overlap explicit
rather than hoping a short RPC invocation happens to cross a block boundary.
The proxy accepts only the observer's existing read-method allowlist. Its own
separate `eth_blockNumber` reads observe progress; they do not control mining.
The selected delays and 75-second observer deadline are test settings, not
proposed production timings or measured normal collection latency.

After collection, the harness stops automatic buying/mining, allows delayed work
to settle, and verifies the final common head. It audits retained blocks and
receipts against both services, then cold-reopens both nodes and checks coverage
again. The partial-coverage incident remains open for explicit operator review;
catch-up does not silently resolve it. The temporary databases are cleaned up;
exports, raw blocks, account/ticket ledgers and process logs remain available.

## What the native audit establishes

The test-only audit starts from the observer snapshot taken exactly at the
anchor, with inventories for both known owners. It derives successful purchase
IDs and intervals from retained transactions/receipts, removes selected and
ordered retreat tickets from header snapshots, then applies expiry at the parent
timestamp. Each reconstructed inventory equals both nodes' executed state and
the header's remaining ticket count. The existing interval-rights audit also
reconciles rewards, fees and first-retreat losses across these blocks.

This demonstrates that the retained evidence can explain this specific ordinary
purchase/selection/retreat sequence. `native-events.json` is a test artifact,
not a new observer feature. The run has no expiry event, genesis-ticket removal,
native failure, double-mining report, historical fork transition or reorganization.
It does not establish general financial accounting or validate a full production
dataset. The earlier successful run had five retreats and 20 ending tickets;
ordinary scheduling and synthetic starting time affect these counts. Both runs
reconciled their own actual sequence, without fixing an expected winning schedule.

## Requirements before production native accounting

1. **Explicit starting inventory and scope.** Header selection/retreat records
   contain ticket IDs, not ownership, purchase height, interval or value. A
   wallet snapshot taken at a later head cannot identify all tickets removed
   since the anchor. Retain an explicitly anchored inventory for each monitored
   wallet, or derive it from verified earlier evidence. Missing owners or
   unavailable historical inventory must remain unknown. A two-wallet scope
   must never imply complete network ownership coverage.
2. **Native outcomes and all ticket mutations.** Preserve receipt/native-log
   binding and native failure checks, even when the outer receipt succeeds.
   Successful `ReportIllegalFunc` calls can delete tickets before finalization;
   their `DeleteTickets` log is already consumed by inherited reconstruction.
   See [transaction execution](../core/state_transition.go) and
   [report penalties](../consensus/datong/report.go). Historical replay through
   block 786,000 also crosses the existing Vote1 transfer/clear operation in
   [votefork.go](../consensus/datong/votefork.go) and
   [StateDB](../core/state/statedb.go). A later restart anchor excludes that
   historical transition, but any general earlier-history mode must either
   support it or declare the interval unsupported.
3. **Exact removal and return rules.** In
   [finalization](../consensus/datong/consensus.go), selected non-genesis tickets
   can return interval rights. The first retreated ticket does not; subsequent
   non-genesis retreats can. Returns are suppressed when the ticket has expired
   at the current header time. Remaining-ticket expiry uses the parent time.
   Ticket removal is therefore not synonymous with liquid FSN returned, and wall
   time must not substitute for either consensus timestamp.
4. **Safe decoding and explicit gaps.** Validate snapshot framing, checksum,
   record types/order and bounds before attribution. Source review found that
   `snapshot.SetBytes` in [snapshot.go](../consensus/datong/snapshot.go) checks
   only for nonempty input before later slicing four count bytes after checksum
   validation. Short, checksum-matching input needs a focused reproduction and
   call-path review before reusing that parser with untrusted observer data.
   The subsequent [local parser investigation](restart-snapshot-framing.md)
   confirms the panic and adds the three-line P16 candidate guard. No
   hostile-peer crash has been demonstrated or additional patch approved for
   release. The test audit guards minimum framing and operates only on the
   fixture's accepted blocks.
5. **Reorganization-aware derivation.** Rebuild inventory and native outcomes
   from the retained canonical branch, retaining displaced evidence and marking
   unknown intervals. Do not persist a second mutable cursor or inventory cache
   without a measured need. Add expiry, report deletion, failure, missing
   baseline, malformed snapshot and branch replacement cases before exposing
   production accounting status. Block coverage and accounting coverage must
   remain separate claims.

The subsequent [offline wallet ticket timeline](restart-observer-tickets.md)
implements a scoped derivation from this retained anchor inventory and block
evidence, with explicit baseline/unsupported gaps and rewind/replacement tests.
It changes only the external observer. The [historical baseline follow-up](restart-observer-anchor.md)
now handles a monitor first started after the anchor, with actual-service
state comparisons and explicit unavailable/conflicting results. Production
historical-state availability and acquisition cost remain open. Review the
[P16 parser correction and narrowed validation scope](restart-snapshot-framing.md)
separately. Collection during a live competing
reorganization, representative backlog/storage/receipt-index availability,
deployment scheduling and notification delivery remain open. The
[main plan](restart-plan.md) and [monitoring policy](restart-monitoring-response.md)
retain those gates; this test does not declare the restart ready for release.
