# Dashboard per-node freshness acceptance

3 October 2026. Dashboard commit `f0c87459d0c64a2703714dd236d2a83f10247089`
follows `3d73e95`. It now distinguishes a connected node from recent
block, stats and pending reports. A fresh database snapshot no longer makes old
node values look current. **132 contracts, nine real socket tests, eight React
DOM tests, a strict production build, five PostgreSQL pipeline scenarios and
13 compiled Edge checkpoints pass.** G6 remains open.

## Small explicit change list

1. Record collector-owned receipt times separately for the three report groups.
   Repeated unchanged reports refresh their own clock. Pings, latency and history
   do not. Reconnecting resets all three, and incomplete reports cannot refresh
   them. Minimal field validation supports that distinction.
2. Preserve receipt metadata and the collector's connection observation in the
   existing JSONB snapshot. Connection status is independent of self-reported
   `stats.active`; no database migration or additional table is required.
3. Require API setting `NODE_REPORT_MAX_AGE_MS`. `/nodes` derives separate
   remaining lifetimes using the server clock. Missing/future metadata is
   unknown; expired or disconnected reports have no remaining lifetime.
4. Deduct request elapsed time in the browser and expire individual fields even
   during another pending request. Keep connection status and per-group labels
   visible, replace expired values with dashes, and recover on new reports.
   Summaries use the highest recent block report and independently check pending.
5. Correct adjacent report compatibility defects: normalize efsn's string-form
   latency, preserve unknown ticket counts as null, and fix combined updates'
   pending assignment and duplicate callback. Last Latency remains explicitly
   historical because that display has no receipt-age metadata.

The final labels sit under each node name, avoiding an extra wide column. The
browser's block receipt display now uses the report receipt, not the inherited
block-propagation cache's first-seen time. Earlier snapshot expiry, request
cancellation, visibility refresh and outage/recovery behavior still pass.

## Evidence

Deterministic checks cover independent report clocks, unchanged values, missing
and future metadata, invalid reports, reconnect reset, exact expiry, zero counts
and receipt-budget subtraction during requests. Real sockets also verify that
client-supplied receipt fields cannot set collector times and that pings/history
cannot refresh them. The locked dependencies remain unchanged.

The real collector → PostgreSQL 18.6 → HTTP API test preserves each node's
metadata, receives efsn-style latency strings, and demonstrates expired reports
under a still-fresh database snapshot. It has five scenarios plus an outer test,
which TAP reports as six passes. Both small disposable clusters used in the
investigation are stopped; their temporary password files were removed.

The optimized bundle runs in an isolated headless Edge 154 profile using
Playwright 1.62.1 and the real local HTTP API. Thirteen checkpoints cover the
earlier browser cases plus silent-but-connected nodes, independent report
freshness, reconnects awaiting reports, and recovery. There are no page
exceptions, foreign-origin requests or missing assets. One canceled request is
expected from the timeout scenario. Screenshots were inspected; the initial
passing browser run is preserved before the layout improvement.

Node 22.11.0 remains the tested runtime, not a production-support decision.
Inherited dependency deprecation warnings remain. All browser/collector test
processes and listeners are stopped. The original dashboard checkout is
preserved. No efsn, consensus/recovery, chain data or validator key changed.

The [evidence bundle](evidence/restart-dashboard-node-freshness-2026-10-03/README.md)
records the exact candidate and patch, source/build hashes, tests, browser
screenshots and cleanup. Source inspection shows a 15-second full-report ticker
in efsn; deployed report/snapshot lifetimes still need actual-node measurements.
The verifier matches 691 non-Markdown source files and 547 compiled assets,
including the precise database-tested source and final browser layout.

## Remaining launch work

A recent self-report does not prove canonical chain agreement or advancement,
ticket funding, or working automatic purchases. Collector, writer and API clocks
must be synchronized; browser expiry uses elapsed monotonic time. Browser
suspension can delay rendering until execution resumes. The cached `/blocks`,
`/info` and `/charts` views do not gain per-node freshness guarantees; current
consumers use `/nodes` metadata.

Next correct the already reproduced chart-cache ordering/admission defects and
bound retained forks/outbound buffering. Then compare actual efsn telemetry with
direct RPC, complete runtime/dependency/supervision review and test public TLS
deployment. Independent operators still receive telemetry credentials separately
from their ability to join and mine. Nothing was pushed or deployed.
