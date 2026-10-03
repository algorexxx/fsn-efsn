# Offline wallet ticket timeline

The external `fsn-observe` command can now derive one configured wallet's ticket
inventory and event timeline from its retained history. This changes only
`cmd/fsn-observe` and `internal/observe`; it adds no node runtime patch, RPC method,
consensus rule, automatic purchase or recovery action. The node patch inventory
remains P1–P16. This is an investigation implementation, not release approval.

## Inputs and command

```text
fsn-observe --history <absolute-observer-history-directory> \
  --ticket-timeline node-2 --ticket-blocks 128
```

Use a single line in PowerShell. `--ticket-from HEIGHT` selects the first event
height; the default is anchor plus one. The range must be after the configured
anchor and contain 1–128 blocks. Inventory derivation still replays earlier
retained blocks from the anchor. It cannot skip that prefix when paging.
Collection flags are rejected with this offline operation. It contacts no node
and appends no history event. Opening LevelDB may still maintain its physical
files; the immutability assertion concerns original logical events and exports.

The baseline must be either a stable matching snapshot taken at the anchor or
an explicit [historical anchor inventory](restart-observer-anchor.md) for this
named wallet. Ticket IDs, owners, purchase
heights, intervals and values receive consistency checks. Repeated eligible
snapshots must agree. A later-head snapshot is never substituted.

Normal snapshot collection reads the latest head. When monitoring starts later,
use `--anchor-inventory NODE` with the matching config, history and timeout to
read the historical anchor through the existing RPC. The
[acquisition report](restart-observer-anchor.md) covers the checks, successful
empty-wallet semantics, history-event compatibility and limits. Historical state
must still be available. Do not rewind a production node to satisfy this report;
until suitable evidence exists, `missing_baseline` is the correct result.

## What the report means

`Sequence` identifies the immutable history view; `BaselineSequence` and
`BaselineTimeUTC` identify its initial wallet snapshot. `Through` is the last
completely derived block, and `Inventory` is the scoped inventory there.
`Events` covers only the requested range. `Blocks` separately preserves the
backfill coverage and last check time: successful accounting does not make a
stale branch current.

| Status | Meaning |
| --- | --- |
| `complete_for_retained_prefix` | Every retained block through the available tip was derived; no claim about uncollected later blocks |
| `range_limit` | The requested page ends before the retained tip |
| `range_not_retained` | The requested event range starts beyond the retained tip, including an anchor-only history |
| `missing_baseline` | No eligible anchor inventory |
| `invalid_baseline` / `conflicting_baseline` | Baseline consistency checks failed; no inventory is claimed |
| `incomplete` | Unsupported or inconsistent evidence stopped derivation before that entire block |
| `data_limit` | The compact JSON report would exceed 8 MiB; see `Through` for any retained complete prefix |

Block and receipt commitments are checked by the existing backfill validator.
The timeline follows the final retained canonical path, replaying it from the
baseline after a rewind or replacement. Displaced raw evidence remains stored.
No second inventory table or canonical cursor is introduced. Historical acquisition
adds an immutable event kind; older observer readers reject that new kind.

Supported mutations are successful native purchases, selected tickets, retreats,
remaining-ticket expiry and report deletions. Native failure is distinct from
outer receipt failure: a successful outer receipt can still contain a native
error. Purchase attribution binds the native log to the signed payload, owner
and parent-derived ticket ID. Report deletions affect the wallet regardless of
who submitted the report. Known `TimeLockFunc` logs, including automatic FSN
maturity conversions on ordinary transactions, do not mutate tickets and are
excluded from ticket outcomes. Missing or ambiguous ticket outcomes stop the block;
events and inventory from a partially derived block are not published.

Return labels describe interval rights, **not liquid FSN refunds**. Genesis
tickets and the first retreat do not return rights. Other eligible removals
return rights only before expiry at the current block time. Remaining-ticket
expiry uses the parent time. Report deletion is labelled a penalty, not a
refund. Full balance, time-lock, fee, reward and report-penalty accounting remains
outside this report.

Snapshot record framing, checksum, order and identity must be supported before
attribution. These are observer support checks, not new consensus restrictions.
The historical Vote1 transition at block 786,000 is explicitly unsupported,
because it performs additional transfers and ticket clearing. A later restart
anchor avoids crossing that transition. Unknown future native functions also
stop derivation. Foreign ticket IDs are outside the scoped inventory; this is
never a complete network-owner reconstruction.

The initial inventory remains an RPC observation. Neither it nor a set of
matching block/receipt hashes proves endpoint honesty, consensus validity,
state execution or finality. The report is conditional on that evidence.

## Validation and limits

Evidence and repeatable runners are in
[restart-observer-tickets-2026-09-27](evidence/restart-observer-tickets-2026-09-27/README.md).
The expected inventory and native events come from the earlier ordinary-mining
run's independent state dumps and test audit, not from this implementation.

At its recorded block 29, the first wallet has 11 tickets and two retreat events;
the second has 12 tickets and nine purchase/selection events. Both agree with
the recorded ledger. Tests also cover paging with prefix replay, cold reopen,
unchanged logical exports, missing/invalid/conflicting baselines, native/outer
failure, foreign-reporter deletion, genesis/expiry return rules, parent-time
cleanup, unsupported evidence, atomic block failure, rewind, reextension and
branch replacement. CLI checks ensure offline queries neither issue RPC calls
nor append events.

The replacement test uses an unsigned in-memory structural variant to exercise
observer branch selection. Native failure/report/removal variants are unit
fixtures. They are not newly executed consensus-valid blocks or report evidence,
and are never submitted to a node. The saved ordinary-mining input is unchanged.
That original offline run involved no new node service, public traffic, real
key, restored backup or large disk workload.

Replay currently scans the bounded history for validation, baseline selection
and derivation. An event range bounds output, not prefix replay cost. Large
histories, receipt-index availability, additional retirement/expiry/report
combinations and production workload are not established by this small fixture.
There is no added persisted cache or performance claim.

The [historical inventory follow-up](restart-observer-anchor.md) now acquires
anchor tickets after the head advances and checks them against independently
saved state on actual IPC/HTTP services. The [preserved-backup probe](restart-observer-preserved-inventory.md)
now confirms sparse historical state and measures local method cost: capture and
preserve both wallet baselines before production. Next validate production
transport/workload cost and collection during a live competing reorganization.
Representative storage/backlog performance,
notification delivery, real funding/custody and independent release review
remain gates in the [main plan](restart-plan.md).
