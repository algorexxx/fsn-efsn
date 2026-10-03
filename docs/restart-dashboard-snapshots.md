# Dashboard snapshot storage and HTTP acceptance

3 October 2026. Dashboard commit
`a2e9f1b0b486bff2c4f90a6c1a65492183af9fc4` on
`codex/dashboard-telemetry-auth`, following the PostgreSQL correction `3ddd755`.
**The real collector → PostgreSQL → HTTP API path now passes with two distinct
synthetic nodes.** The final run also passes 99 contracts, the existing database
tests and the collector wire check.

## Replacement behavior

The previous writer mixed unrelated node events, reused metadata/block/time
across nodes, accumulated reconnect timers and interpolated reports into SQL.
Those paths are removed. The new writer requests the collector's existing full
node snapshot and waits for a following chart message, then stores one complete
document in a single parameterized database statement.

The protocol stays unchanged. Nodes retain their own information, stats, reported
block, history and geographic data; internal collector session bookkeeping is
excluded from the stored projection. Partial broadcasts and charts received
before the node snapshot are ignored. The two messages are separate observations,
not an atomic canonical-chain view. A chart timeout discards the entire sample.

Sampling interval, response deadline, message bytes, maximum node count and API
age limit are explicit required settings. The writer handles Primus ping/pong,
validates basic snapshot shapes and identity uniqueness, and retains one sample
and one write without a write queue. Each message is size-limited; the combined
node/chart document can approach twice the per-message limit. This does not
replace collector admission, deep field validation or global connection/rate limits.

One timer handles the current connection deadline, sampling deadline or next
attempt. Reconnect waits for both the socket's close event and any pending write.
Late callbacks from an old socket cannot affect a new session. Shutdown stops
sampling, closes the socket, drains the pending write and closes the pool; the
transport finishes its own bounded close handshake.

A failed database call does not replay an uncertain write. The next connection
requests a new complete snapshot. The upsert rejects an observation older than
the stored timestamp, protecting against a delayed older write. This design
assumes one writer/collector and a correctly maintained clock; multi-writer
coordination and automatic clock/history repair are outside scope.

## Storage and read API

`db/schema/001-dashboard.sql` creates `dashboard_v1.snapshot` transactionally.
It does not drop a database or touch existing historical tables. Reapplying the
script fails at the existing schema and rolls back, preserving data. The old
`POSTGRESQL_Setup.sh` remains historical and must not be run for this candidate.

A boolean primary key limits the table to one latest snapshot. The row stores a
finite full UTC observation timestamp and the node/chart JSON document. Schema
constraints reject missing or wrongly shaped top-level payloads. Block/info API
fields are derived on read, avoiding separate duplicate columns and tables. This
is current dashboard storage, not an append-only audit or blockchain history.

The writer role needs schema usage and table SELECT/INSERT/UPDATE; the API role
needs usage and SELECT. Neither requires DELETE, DDL or schema ownership. The
local acceptance test verifies these restrictions using separate SCRAM roles.
Production database/role provisioning is still an operator deployment step.

`/nodes` retains the frontend's row envelope (`id`, `utctime`, `block`, serialized
`stats` and `info`), with each field derived from the same snapshot. `/blocks`
and `/info` derive each node's reported data; `/charts` serves the stored chart
object. `/info` no longer calls a missing database method.

All four routes disable caching with `Cache-Control: no-store`. Successful reads
include `X-Dashboard-Observed-At`. A missing, stale or future observation, or a
database read failure, returns HTTP 503 with a generic `snapshot_unavailable`
response. The API does not return old payloads or database error detail in that
case, and it does not erase the last stored snapshot.

## Evidence

The final Windows run uses Node 22.11.0, PostgreSQL 18.6 and pinned `pg` 8.23.1.
No dependency lock or collector runtime source changed in this patch.

- **99 contracts pass**, including the retained authentication/configuration
  checks, all four API views, sampling deadlines, backpressure, uncertain-write
  recovery, late callbacks, actual close-event ordering, basic payload bounds,
  graceful stop and stale/future/unavailable responses.
- **Four real persistence scenarios pass** (five TAP entries with their parent):
  nondestructive schema and role constraints; two-node storage/API agreement;
  writer/node reconnect and disconnect; stopped ingestion becoming stale without
  deleting its stored snapshot. The stale test advances the API's injected clock.
- **Five existing database scenarios pass** (six TAP entries), along with the
  existing real collector WebSocket test.

The integration compares stored projections with a separate live collector
snapshot. It confirms each node keeps its own version, block height and peer
count, including ordinary apostrophes and Unicode. Actual HTTP `/nodes` and
`/charts` responses are exercised against the restricted database reader.

The first run passed before review identified the need to wait for actual socket
closure. Its source and output are retained. The final run adds that lifecycle
check and repeats the real integration successfully. Test clusters are stopped,
generated admin password files are removed, and retained scratch sizes are
recorded. The original dashboard checkout and efsn node source remain unchanged.

See the [evidence bundle](evidence/restart-dashboard-snapshots-2026-10-03/README.md)
and [portable patch](evidence/restart-dashboard-snapshots-2026-10-03/dashboard-snapshots.patch).
The dashboard's `docs/snapshot-storage.md` documents provisioning, settings,
ownership, retry semantics and supported limits. Nothing was pushed or deployed.

## Next gate work

The old [persistence blockers](restart-dashboard-config.md#next-persistence-correctness-before-integration)
are addressed by this replacement path. **Public dashboard readiness remains open.**
The existing React UI still needs explicit unavailable/stale rendering and must
stop presenting cached old nodes when HTTP requests fail. Its full dependency
build and browser behavior have not been tested in this result.

A fresh collector snapshot does not prove fresh reports from every node: cached
`active`/uptime values are not canonical agreement, ticket funding or purchase
health. Finish per-node stale labeling and compare actual efsn telemetry against
direct RPC. Complete collector input/resource limits, production runtime and
dependency review, service supervision, proxy/TLS and the final browser acceptance.
No consensus, recovery sequence or node P1–P16 changes are part of this work.
