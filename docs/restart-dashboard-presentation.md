# Dashboard presentation and busier telemetry

3 October 2026. The compiled dashboard now displays an actual synthetic efsn
node through the real collector, PostgreSQL and HTTP API, including expiry and
recovery when the snapshot writer stops. The misleading **Syncing** and
**Reported Uptime** columns have been removed. G6 remains open.

The production change is one frontend file: remove those two headers and both
pinned/unpinned cells, plus the unused progress-bar import. No new interpretation
of the legacy flags is introduced. Connection status, block/stats/pending
freshness, mining, peers, tickets, latency and the existing explanation of
self-reported data remain visible. Raw telemetry fields remain in storage/API
for compatibility and investigation. Neither a client version string nor its
sync/uptime flag establishes agreement or continuous availability.

## Acceptance

The [evidence bundle](evidence/restart-dashboard-presentation-2026-10-03/README.md)
contains the exact source/build identities, patch, RPC comparisons, browser
observations and screenshots. All **eight existing React DOM tests** and the
**strict production build** pass. The new integration run passes four compiled
Edge checkpoints against the live pipeline:

1. Actual head 60, matching abbreviated hash, two owned tickets, zero pending
   transactions and zero peers appear with recent report labels. The removed
   columns/progress bar are absent.
2. Pinning the same node preserves the values and twelve-column alignment.
3. Stopping the snapshot writer allows the stored snapshot to expire after the
   configured ten seconds. The API returns 503 and the browser removes old rows
   and summary values. Direct node RPC still returns the same head.
4. Restarting collection produces a fresh snapshot and the browser automatically
   restores the pinned row. No page errors or foreign network requests occur.

The fixture executes/imports 60 synthetic devnet blocks in memory, each with
one native ticket purchase and nine zero-value self-transfers, using public
test key 1. All 600 transactions pass normal block import. The latest block and
50 historical blocks are compared to RPC, including all transaction hashes,
roots, producer, gas, difficulty and ancestry. There are 59 successful direct
RPC requests in the complete run. P2P dialing/listening/discovery, auto-buy and
the mining worker are disabled. No real key or backup database is used.

The pipeline uses Linux Go 1.21.3 and Node 22.11.0 for the node and collector,
Windows Node 22.11.0/PostgreSQL 18.6 for storage/API, and Edge 154.0.4258.48.
WSL localhost forwarding connects the loopback services. The ephemeral database
is stopped, its password removed, the browser closed and all matching fixture
processes gone. No public service is deployed.

## Payload result and deployment decision

The actual fifty-block history reply is **66,076 application bytes**, containing
500 transaction hashes. This confirms the earlier 64 KiB limit concern with
executed transactions. It is fifty bytes larger than the earlier fixed-field
estimate because each block's gas-used value gained one decimal digit.

The integration fixture explicitly uses a **128 KiB input limit**, with the
existing 256 KiB pending-output limit and 64 KiB snapshot-message limit. These
are the tested settings for this one-node workload, not deployment defaults.
The head report is 1,364 bytes; the largest captured outgoing application
message is 4,864 bytes; compact stored snapshot JSON is 6,958 bytes. One
instrumented collector memory observation is 147,181,568 RSS bytes, including
10,841,168 heap-used and 83,627,087 external bytes. No peak or capacity claim is
made from this single observation.

The offline byte model holds the observed block-field layout and sizes
transaction lists without sending any modeled payload. Only the ten-transaction
row below was executed in this run; one transaction per block was exercised in
the preceding telemetry run.

| Transactions per block | Fifty-block history bytes | Fits 128 KiB | Fits 4 MiB |
| ---: | ---: | :---: | :---: |
| 1 | 30,926 | Yes | Yes |
| 10 | 66,076 | Yes | Yes |
| 100 | 417,126 | No | Yes |
| 714 | 2,811,776 | No | Yes |

At the fixture's 15,000,000 gas limit, 714 minimum-cost transactions fit; this
model includes the ticket purchase's extra gas. It is not a claim that this
block layout covers all future gas limits, field lengths or report variants.
**4 MiB is a candidate for the next bounded input test, not an approved
production setting.**

Larger input limits must be considered with retention. The chart history keeps
2,000 heights and up to configured identities plus one representative fork at
each height. With an illustrative eight identities and the modeled busy blocks,
the JSON for nine variants at every height alone is about **1.01 GB**, before
wrappers and runtime object overhead. This is a size calculation, not a loaded
cache or measured memory usage. Current report validation also permits extra
fields, so a transport limit alone is insufficient to bound retained content.

Source inspection found that chart calculations only read
`block.transactions.length`; they do not use individual transaction hashes.
The live node snapshot and `/blocks` API still carry those hashes, so removing
them globally would change that interface. The next correction should validate
the complete incoming block shape and give the chart cache a compact projection
of the fields it actually needs. Preserve current-head/API behavior deliberately
and test representative/fork comparisons, atomic history rejection and
freshness before raising deployment budgets. Then measure the selected node,
history and fork envelope and align input/output/snapshot/proxy limits.

## Remaining scope

This proves actual browser rendering and **snapshot-writer** loss at a stationary
synthetic head. It does not prove uninterrupted mining through collector loss,
loaded production, multiple simultaneous reporters, long retention, light-client
sync, TLS or race-detector coverage. Earlier synthetic disconnect/freshness tests
retain their original scope. Production reporter, consensus, collector,
database schema, dependency locks and original dashboard checkout are unchanged.

Next: complete field validation and compact chart retention, then a bounded
larger-report/multiple-node profile. Runtime/dependency review, supervision,
proxy/TLS, enrollment and public deployment remain G6 work.
