# Dashboard chart cache acceptance

3 October 2026. This follow-up corrects the inherited chart admission and
ordering defects and bounds retained forks on the isolated dashboard branch.
Dashboard commit `6893caa09e0db17d8b0f70a5d8349c1fb5bbb2c2` follows `f0c8745`;
the exact candidate is recorded in the
[evidence bundle](evidence/restart-dashboard-history-2026-10-03/README.md).
G6 remains open.

## Small explicit change list

1. Admit advancing heads and out-of-order reports within a moving window of
   2,000 positive heights. Evict older heights when the window advances; select
   the latest 40 cached heights before reversing them for chart display.
2. Keep each node's current fork reference and the existing chart representative.
   Release other forks and remap indices together. Fix receipt handling when a
   node changes forks, while preserving duplicate first-seen propagation times.
3. Request at most 50 missing heights from the current window, starting after
   the first head and stopping when complete. Validate history before mutation,
   complete its callback once and use the existing debounced chart broadcast.
4. Preserve zero ticket counts and null positions for missing counts. Share the
   collection's injectable clock with the cache for deterministic checks.

This changes dashboard memory and diagnostics only. There is no efsn patch,
consensus or recovery change, dependency upgrade, database migration or frontend
change. No chain data, validator key or public service is involved.

## Findings and retention policy

The old admission condition accepted the first head but ignored subsequent
advancing heads until the cache filled. Independently, the pinned Lodash 3.10.1
lazy slice/reverse chain selected heights **51–90** from cached heights 51–100;
the correct latest forty are **61–100**. An explicit reversal through `thru`
preserves the existing dependency and corrects the affected chart helpers.

On a new fork from an already known node, the old cache appended a fork without
moving that node's propagation reference. Repeated changes retained all old
forks. The correction retains at most **N + 1 forks and N propagation records
per height**, where N is the number of distinct identities in the collector's
fixed startup credential map. Reconnects reuse identities. Together with the
2,000-height window, repeated reports cannot grow retained entries indefinitely.
One extra fork may exist transiently during insertion before pruning.

The existing representative-selection policy is preserved: first report unless
an existing trusted source selects another. This is not canonical-chain
selection. The trusted IP list is empty by default; inherited `LITE=true` trusts
all sources. Self-reported incorrect heights can move the diagnostic window,
and abandoned forks are not archived. The node's own current report remains
separate from this aggregate cache. The dashboard's `docs/chart-history.md`
gives the details and is included in the portable patch.

The formerly missing successful history callback also left console timing
entries open when timing logging was enabled. Completing it now closes that
path; chart data still goes through the single existing debounced callback.
History replies do not renew the separate per-node freshness receipts.

## Verification

Thirteen deterministic history tests fail against the previous implementation;
their original output is preserved. The corrected candidate passes **145 root
contracts and 10 real socket tests**, including normal backfill, ascending heads,
duplicate reports, distinct reporting nodes, fork changes, zero/missing counts,
exact window boundaries, a filled cache and incomplete-history rejection.

The PostgreSQL pipeline adds a chart scenario: synthetic reports pass through
the real collector, snapshot writer, PostgreSQL and HTTP API with exactly the
latest forty heights. All **six pipeline scenarios pass** (seven TAP passes
including the outer test), retaining the identity, receipt, permissions,
reconnect and stale-snapshot checks. The disposable cluster is stopped and its
temporary password file removed; no collector fixture remains running.

The previous compiled frontend is unchanged, so browser/build acceptance was
not repeated. Original checkout preservation, unchanged dependency locks and
tested-source matching pass; 693 non-Markdown source files match the committed
candidate. Node 22.11.0 remains the local
test runtime; production runtime support remains undecided.

## Remaining work

The retention bound is not a measured production memory budget. Credential
count and message byte limits still determine potential retained size.
Outgoing queue limits and slow consumers, deployment traffic/connection limits,
and a complete telemetry schema still need review. Legacy arrival-based block
times and hashrate estimates remain diagnostic.

Next address the remaining resource limits, compare actual efsn telemetry with
direct RPC, and finish runtime/dependency, supervision and TLS/deployment work.
No public-launch gate is closed by these dashboard checks alone.
