# Observer capacity recovery

This adds an offline `fsn-observe --history-copy` operation. It copies every
event into a new history with a larger, explicitly selected logical byte budget.
The original budget, events, incident identities and reviews remain unchanged.
The new history can continue at the next sequence after independent inspection.
Normal node, consensus, mining and ticket-purchase behavior are unchanged.

This is a bounded capacity extension, not rolling retention. It neither removes
events nor reduces replay work. The existing 1 GiB maximum still applies. It
does not select a production cadence, budget, retention duration or alert route.

## Operator procedure

1. Stop the observer collector and any service that could restart it. Stop
   history review/backfill/inventory writers too. This does not require stopping
   the Fusion nodes. Record the collection gap and retain the last successful
   collection, backfill and incident status.
2. Preserve a closed source copy using the tested
   [whole-history procedure](restart-observer-backlog.md). Retain its paths,
   hashes, scope and sequence in the operator evidence manifest. Reopening a
   LevelDB history can change database housekeeping files; event preservation
   does not promise identical physical database bytes.
3. Choose a new absolute destination outside the source history. Its parent
   must exist and the destination must not exist. Confirm space for both
   histories, the closed backup, database overhead, exports and growth. The
   logical budget is **not a physical disk quota**. Use a larger reviewed budget
   no greater than 1073741824 bytes. Merely moving to another disk does not
   remove the logical or replay limits.
4. Obtain `--history-status` and `--history-export` from the source. Capture
   ticket timelines for both named wallets over the reviewed retained range.
   Use that exact positive `Sequence` in the copy command. An empty history has
   no positive sequence and cannot use this command.

```text
fsn-observe --history SOURCE --history-status
fsn-observe --history SOURCE --history-export
fsn-observe --history SOURCE --history-copy NEW_DESTINATION --history-budget REVIEWED_BYTES --at-sequence REVIEWED_SEQUENCE
fsn-observe --history NEW_DESTINATION --history-status
fsn-observe --history NEW_DESTINATION --history-export
```

`SOURCE` and `NEW_DESTINATION` are absolute observer-history paths, never node
datadirs. Replace every placeholder deliberately. Copy needs no configuration
file, endpoint credentials, signing key or live RPC. Save stdout and exit status
for each command using the operator's normal evidence capture.

5. Independently reopen the destination. Compare scope, sequence, incident and
   review state, block coverage and both wallet timelines to the source. Every
   exported event line must match exactly. The first export line is metadata:
   only its budget changes. `LogicalBytes` also reflects the metadata size
   difference if the budget has a different number of decimal digits.
6. Only after these checks, change the collector's explicit history path and
   resume it. Verify the next durable sequence and catch up block/receipt
   coverage for the recorded outage; snapshots missed during the pause cannot
   be reconstructed as original observations. Retain the source as evidence.
   Do not alternate writes between both copies: their independent later events
   are not merged by this command.

## Failure handling

The copy first creates a `COPYING` marker. It publishes `FORMAT` only after all
raw event keys/values have been copied, replay validation succeeds and the
destination database closes. Opening an incomplete copy fails. Cancellation
leaves a partial destination for inspection; the command never overwrites or
resumes it. A retry requires another new destination and the current source
sequence. Do not manually rename the marker to make a failed copy open.

An error writing the command's output can occur after publication. Inspect the
destination status before deciding whether the copy failed. Keep the source
until the independent reopening and continuity checks succeed. Filesystem or
power-loss durability of publication has not been demonstrated. The tests
exercise cancellation during copying, not a machine crash at every write.

## Acceptance and remaining work

The retained [acceptance bundle](evidence/restart-observer-capacity-2026-10-04/README.md)
declares its expectations before execution. It checks exhaustion followed by
copy/reopen/continuation, unchanged source events and budget, unresolved
acknowledgement identity, and both wallet timelines against the previously
executed block-29 ledger. It also checks stale/missing sequence, invalid budget,
occupied/nested paths, interruption, and offline CLI argument separation.

Windows observer/CLI suites and build pass, and Linux passes the race suites
and build in a loopback-only namespace. The existing 4,096-block/64-block
replacement regression also passes with its previous export hash. Windows path
resolution required running tests outside the restricted sandbox; those two
failed runs remain in the bundle. The symlink-alias case passes on Linux and
is skipped on Windows because symlink creation privilege is unavailable.

Production cadence and headroom still need selection using a defined workload
and response window. Collection must be monitored outside the history writer:
a rejected append cannot durably report its own failure in that history. Alert
delivery and collector-loss detection remain open. Beyond the 1 GiB ceiling or
acceptable replay cost, this command provides no further capacity solution;
do not silently start an empty history and discard unresolved evidence.
