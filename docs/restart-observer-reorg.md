# Observer collection during a live reorganization

3 October 2026, source baseline `ff8984c4`. Tests and evidence only; the observer
executable, node runtime, consensus and P1–P16 candidates are unchanged.

## Test arrangement

The compact fixture has complete synthetic ancestry through anchor block 24,
devnet rules, two public test keys, archive-mode state retention and large
synthetic reserves. The two nodes start disconnected. One ordinary miner starts
earlier; both mine their own post-anchor descendants before an ordinary static
peer connection joins them. No signer is held, later block constructed by the
harness, or downloader forced through the test API. This is an initial peer join,
not a new packet-loss/reconnection test or public-network experiment.

Two separate observer histories first acquire both wallets' anchor inventories
and collect both isolated branches. Separate histories allow a snapshot and a
backfill command to wait concurrently across the same live reorganization without
contending for one history database's exclusive lock.

The existing HTTP test proxy is extended with a gate. It first forwards the
node's actual latest-head response, then delays a subsequent read. The snapshot
pauses at `eth_getTransactionCount`; backfill pauses at the first subsequent
`eth_getBlockByNumber`. The proxy accepts only the observer's existing read-method
allowlist and forwards responses unchanged. While both commands wait, the harness
connects the ordinary miners and waits for the losing node's canonical hash at
each pinned height to change and agree with the other node. Only then are the
held reads forwarded. The artificial delays ensure overlap; they are not normal
RPC latency measurements or proposed production timeouts.

Both buyers remain enabled during collection. A temporary downloader-induced
mining pause is allowed and automatic resumption is required before the harness
stops mining. Reorganization can reduce height, so monotonic head height is not
used as an observer noninterference assertion. The legacy lab signature counter
does not count ordinary keystore signatures; actual isolated descendant blocks
and their producer addresses establish that both miners produced.

## Acceptance checks

The crossing snapshot must report `changed_or_unavailable` and invalidate the
tracked purchase's inclusion, funding, payload and nonce classification. The
crossing backfill must report `unstable`, retain no candidate base/blocks, and
leave its previous stored coverage in place. Its earlier records remain evidence
of an observed branch, not current canonical coverage.

After both miners are stopped and delayed work has settled for the existing
35-second observation period, fresh IPC backfills must reach the common head.
Wallet timelines must agree with the two nodes' executed ticket inventories.
Cold node reopenings and offline timeline rereads must preserve that result.
Every history export must retain the preceding export byte-for-byte as a prefix,
including displaced blocks and the invalidated observation. Canonical replacement
must remain an open incident for operator review; catch-up cannot resolve it.

The ordinary-mining integration test is rerun with race detection because it
shares the extended HTTP delay helper. No production observer behavior is changed
to accommodate the new test.

## Result and evidence

The live reorganization test passed with Linux race detection in 161.11 seconds.
Both delayed reads pinned node-2's block 26. Its canonical hash at that height
changed after joining node-1, and the node advanced to 29 before the reads
continued. The snapshot reported `changed_or_unavailable`; backfill reported
`unstable` without moving its previously retained block-26 coverage. The final
settled head was block 30. Both histories' final and cold wallet timelines
matched executed state, original export prefixes were preserved, and canonical
replacement incidents stayed open. All four child service runs exited cleanly.
The ordinary-mining regression also passed with race detection in 160.03 seconds,
with four more clean child exits and no race reports. The evidence verifier
passed, including 22 stopped-node captures with identical before/after state.
See the [evidence bundle](evidence/restart-observer-reorg-2026-10-03/README.md).

Cold wallet timeline contents are unchanged. The first wallet's initial final
query identifies history sequence 6; the second node's backfill then advances the
shared history to sequence 7. Both cold queries identify sequence 7. The verifier
checks each version against its corresponding history and compares all remaining
timeline fields, rather than incorrectly requiring equal global sequence numbers.

The first attempt stopped on an incorrect test precondition requiring a nonzero
lab signature counter. That counter belongs to manually authorized test signers;
ordinary keystore mining leaves it zero. Both node logs already showed ordinary
production. The corrected test verifies their actual post-anchor blocks and
coinbases, without changing the node or collector. The failed run and its two
affected test source files are retained.

The second attempt passed snapshot invalidation and unstable backfill, then
stopped in the older interval-rights audit helper: its model excludes remaining
genesis tickets, and this valid fixture retained one. Final reconciliation now
reads the settled nodes' complete ticket inventories directly. It does not relax
the financial audit helper or claim financial accounting. That failed run and
its affected test source are also retained.

Evidence review found an observer diagnostic defect in
`internal/observe/block_coverage.go`: the canonical-change incident formats
`common.Hash` with `%s`, which this fork renders as raw bytes. Its explanatory
text contains unreadable hashes. Structured block references and retained exports
still contain the correct hexadecimal identities. Correcting this display text
and adding an exact-string regression is an open observer follow-up; it does not
require a node or consensus patch. This phase preserves the tested source.

## Boundaries

This is one compact, deliberately scheduled heavier-branch replacement. It does
not establish repeated deep fork handling, equal-weight convergence, complete
observation of every transient fork, receipt-index retention, production backlog
or storage performance, or network-wide finality. Archive-mode synthetic state
does not remove the [real backup's sparse historical-state limitation](restart-observer-preserved-inventory.md).
Baseline preservation before production remains required by the launch plan.

The test does not require both owners to replenish after joining or resolve their
saved purchase intent. The existing [monitoring/manual-response policy](restart-monitoring-response.md)
and its funding/recovery limitations remain in force. Notification delivery,
deployed collection scheduling, full financial accounting, real custody and
independent release review remain separate gates in the [main plan](restart-plan.md).
