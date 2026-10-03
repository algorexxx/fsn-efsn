# Mixed observer commands and history-budget exhaustion

3 October 2026, baseline `db549c03`. This phase adds Linux investigation tests and
evidence only. Observer/node runtime, consensus and P1–P16 candidates are unchanged.

## Arrangement and acceptance

Two actual node services start from the existing compact devnet fixture with
complete synthetic ancestry through block 24, archive-mode state and public test
keys 1 and 2. One node runs ordinary automatic ticket buying and mining; the other
verifies and follows it. Both wallets' anchor inventories are acquired before
production and compared with independently captured state.

Six rounds each wait for both nodes to advance beyond the preceding observed
height, then invoke the actual observer executable for one two-node snapshot and
one block/receipt backfill per node. Rounds alternate IPC and loopback HTTP. Each
backfill has an explicit 128-block ceiling and must reach its observed head.
Snapshot identities and inventories must be stable. No proxy adds delays or
changes responses, no signer is held, and the controlled downloader is not used.

Each invocation records elapsed process time, exit code, stdout, stderr and
before/after node status. Timings cover process startup, local history reopening,
RPC acquisition when applicable, history validation/write and output generation;
they exclude the harness's node-status checks and evidence-file writes. Commands
must leave producer and verifier controls unchanged. The RPC deadline is five
seconds and the harness also enforces a 30-second whole-command deadline.

After production stops, the existing 35-second quiet-head check allows delayed
work to settle. Backfills for both nodes catch up to the settled head. Both
executed node inventories must agree. The same observer history, with a deliberately
small 524,288-byte logical budget, is filled with stopped-node snapshots until one
is rejected, then smaller no-op backfills until one is rejected. Each fill loop
has a 64-command cap. The rejected command must return exit 1, an explicit budget
error and no stdout, leaving the preceding persisted status unchanged.

Both rejected operations are retried in fresh processes. Both nodes then shut
down cleanly. Fresh offline status, ticket-timeline and export commands must still
succeed. The timelines must match the last executed inventory, the export must
match its pre-retry bytes exactly, and all earlier exports must remain prefixes.
This checks a logical history limit, not a full filesystem or disk-write failure.

## Results

The ordinary build passed in 152.59 seconds, with two clean node exits. It settled
at block 31 and retained 39 events using 522,399 logical bytes of the 524,288-byte
budget. Closed history file lengths totalled 235,603 bytes. The first rejected
snapshot was fill attempt 16; two smaller backfills still fit before backfill
attempt 3 failed. Both retries failed explicitly. Stopped-node status, original
exports and both offline inventories remained intact.

The race-instrumented run also passed in 163.71 seconds with two clean node exits
and no race reports. It settled at block 31 and retained 38 events using 521,039
logical bytes; closed file lengths totalled 230,444 bytes. One smaller backfill
fit after snapshot rejection before the second backfill attempt failed. Timing
and block contents differ naturally between the two independent mining runs.
Final evidence verification passed, including 61 identical stopped-node
before/after command captures across both runs and matching offline inventories.

| Live operation, ordinary build | Samples | Median | Range |
| --- | ---: | ---: | ---: |
| IPC two-node snapshot | 3 | 47.10 ms | 39.01–59.12 ms |
| HTTP two-node snapshot | 3 | 63.95 ms | 60.80–157.43 ms |
| IPC one-node block backfill | 6 | 38.07 ms | 34.81–42.86 ms |
| HTTP one-node block backfill | 6 | 60.42 ms | 47.28–94.75 ms |

These are small local samples over a growing history, not a controlled comparison
isolating transport overhead or a production latency guarantee. No explicit
signed-transaction tracking list is configured. The separate race build checks
correctness; its process timings are not performance measurements.

## Operational conclusion and remaining work

The budget guard preserves existing evidence and supports offline inspection,
but it stops retaining new observations. A rejected snapshot produces no report
on stdout. An external runner must treat nonzero exit and missed collection as
actionable failures rather than reading an old successful file as fresh. Delivery
of that notification remains unimplemented. A rejected large event also does not
mean every smaller event is blocked; budget checks apply to each prospective event.

This small-history command run does not supersede the [larger snapshot replay
measurement](restart-observer-history-cost.md), which found growing local replay
cost and short example-budget lifetimes at frequent collection. The next useful
comparison is avoiding duplicate complete replay within one command while keeping
the same source events, validation, scope checks and review semantics. Measure
that before introducing a persistent status cache. Longer advancing ancestry,
ticket-timeline reconstruction cost and actual operational cadence remain open.

Retention must preserve anchor baselines, unresolved incidents, review identity
and displaced evidence. No rotation, pruning, automatic budget increase or new
history is introduced here. Public-network transport, concurrent scheduling,
notification delivery, power-loss durability and independent release review
remain gates in the [main plan](restart-plan.md).

The [evidence bundle](evidence/restart-observer-mixed-workload-2026-10-03/README.md)
contains exact commands, captures, source/binary hashes and a verifier. It uses no
production backup, real signing key, public endpoint or large restore.
