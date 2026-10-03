# Historical anchor inventory acquisition

Investigation begun 27 September 2026; reviewed 3 October 2026.

The external observer now has an explicit historical inventory operation for
monitoring first started after the anchor. It uses existing read RPCs and adds
no node runtime patch, consensus change or RPC method. The P1–P16 node patch
inventory is unchanged.

```text
fsn-observe --config observer.json --history <absolute-history-directory> --timeout 10s --anchor-inventory node-2
fsn-observe --history <absolute-history-directory> --ticket-timeline node-2 --ticket-blocks 128
```

The first command requires an initialized matching observer history and one
configured node name. It acquires a baseline; the second derives the timeline
from that baseline and previously collected blocks. Acquisition can happen
before or after backfill. It never rewinds a node or substitutes a latest-head
inventory. Retired endpoints are not contacted. Collection, backfill and offline
query flags are separate operations.

## Read semantics and provenance

The collector reads chain ID, network ID, genesis and the configured anchor
header, then calls `fsn_allTicketsByAddress(wallet, anchorNumber)` and re-reads
that anchor header. It requires matching configured identities and the same
anchor hash before and after acquisition. Successful ticket entries must have
nonzero IDs, the configured owner, a purchase height no later than the anchor,
a valid interval and the expected ticket value at purchase height. A successful
compact inventory report is limited to 8 MiB, within the existing history budget.

The inherited [Fusion RPC](../internal/ethapi/api_fsn.go) resolves an explicit
height through [StateAndHeaderByNumber](../eth/api_backend.go) and reads tickets
from that header's state root and ticket hash. It does not reconstruct pruned
historical state. `StateDB.AllTickets` may load the complete ticket collection
before the address filter; a wallet query is not a guarantee of cheap server
work. The collector deadline bounds waiting, not all server-side computation.

The RPC returns successful JSON `null` when that owner has no tickets. This
specific successful result is normalized to an explicit empty map. RPC errors,
including unavailable historical state, remain `unavailable`; they never become
an empty successful baseline. Legacy snapshot reports with a missing map remain
subject to their earlier conservative validation; the explicit acquisition is
the supported way to establish an empty baseline.

Results are `ready`, `unavailable`, `identity_mismatch`, `unstable`,
`invalid_inventory`, `retired` or `data_limit`. Only `ready` contains eligible
tickets. Every attempted acquisition that fits the history budget is retained
as its own immutable `AnchorInventory` event. A failed append returns an error;
the budget test verifies that the original logical history remains unchanged.

The event stores observed historical evidence, not a current inventory cache.
It does not refresh current-head block coverage, change live incident status,
pretend that producer flags were observed at the anchor, or resolve an incident.
Baseline sequence/time in the derived timeline identify its source event.
Failed later reads do not erase an earlier eligible baseline. Different
successful baseline inventories produce `conflicting_baseline` in the timeline,
with no claimed inventory; `ready` describes one read, not agreement with all
previous observations.

The new reader accepts the earlier history events and directory format. This
adds an event kind to that format: older observer binaries reject histories
containing `AnchorInventory` through their strict unknown-field decoding. Use
the updated observer for those histories; there is no downgrade migration or
rewriting of existing events.

Hash checks around a block-number RPC are consistency observations, not an atomic
state proof. They cannot establish endpoint honesty or exclude a branch changing
away and back during the intervening read. Use a trusted controlled endpoint for
acquisition, reconcile against independently retained anchor state where possible,
and retain disagreements for review. The two-node rehearsal demonstrates correct
interpretation by this software in that controlled setting; it does not prove a
remote endpoint's answers or make finality claims.

## Validation and remaining work

[Evidence and repeatable runners](evidence/restart-observer-anchor-2026-09-27/README.md)
cover 142 passing tests/subtests on each of Windows and Linux, with Linux race
detection, plus passing isolated IPC/HTTP services. All 27 command-level node
state comparisons are unchanged. The retained fixture starts with no
eligible baseline and already backfilled block 29; historical acquisition must
recover the recorded anchor inventory and reproduce the independent final
ledger. Cold reopen and byte-identical logical exports are checked.

The real-service extension saves anchor truth directly from state before
advancing either node. It then starts services beyond the anchor on different
branches, collects historical inventories through IPC and HTTP, and compares
both against that saved truth. Timelines must match the separately executed
current states, and after synchronization the first node's timeline must follow
the replacement branch. A real empty-wallet RPC returns `null`, and the command
records a ready empty map. Command-level before/after captures check that node
heads, signatures, flags, nonces, saved purchase intent and pools are unchanged.

Missing-state, deadline, changed/unavailable anchor, invalid inventory, conflicting
baseline, replay validation and storage-budget behavior also have controlled
adapter/unit coverage. Missing historical state is simulated as an RPC error;
this is not a demonstrated production pruning/restore recovery procedure.

The first service run also found an observer limitation: automatic matured-FSN
conversion emits a `TimeLockFunc` log even on an ordinary self-transfer. The
ticket timeline formerly treated it as an unexpected native outcome and stopped.
The observer now excludes that known non-ticket log type before classifying ticket
outcomes. This also permits maturity conversions alongside purchase logs. It does
not claim to verify the converted amount or add full balance accounting. The
initial failure, subsequent incorrect fixture choice, and corrected regression
against the exact original receipt are retained. A later raw-null capture failure
was a test/client-decoding assumption; its correction changes only the service
test and is also recorded in the evidence directory.

No production backup, production key, public endpoint or large restore is used.
The compact services use public test keys and an isolated loopback-only network.
Next validate representative historical-state availability and acquisition cost,
and collect through a live competing reorganization. Full financial accounting,
monitor scheduling/delivery, real funding and signing custody, and independent
release review remain open in the [main plan](restart-plan.md).
