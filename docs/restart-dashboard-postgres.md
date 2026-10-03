# Dashboard PostgreSQL prerequisite correction

3 October 2026. Dashboard commit
`3ddd7559783de303216bdb361a564d6fd6779d9e` on
`codex/dashboard-telemetry-auth`, following configuration commit `31a1352`.
**A real legacy driver failure is reproduced and corrected.** Five database
scenarios, all 86 existing dashboard contracts and the collector wire test pass.

## Why this came before the persistence rewrite

The installed dashboard driver, `pg` 7.12.1, did not connect under the current
Windows Node 22.11.0 test runtime. A new PostgreSQL 18.6 cluster required SCRAM
authentication and listened only on a temporary `127.0.0.1` port. Native `psql`
connected and returned `42`; the old Node driver against that same server returned
`timeout expired` after its 1500 ms probe deadline.

Local source inspection explains the failure: that driver's `Connection.connect`
calls the socket's `connect` method only when `readyState` is `closed`. It instead
emits its connection event when the state is `open`. The retained observation
shows Node 22.11.0 reports `open` for a newly created, unconnected socket. This is
a runtime compatibility problem in the tested combination, independent of the
old writer's SQL and reconnect defects.

The earlier stubbed database checks could not establish this behavior. Running
a real database control exposed it before investing in storage integration.

## Small correction

The dashboard pins `pg` to **8.23.1**, selected from the official npm registry.
The [package metadata](https://www.npmjs.com/package/pg/v/8.23.1), exact integrity
hash and dependency changes are retained in the evidence. Only PostgreSQL-related
lock entries change; frontend/API lockfiles and unrelated root lock entries are
unchanged. Installation used `--ignore-scripts --no-audit --no-fund`.
This is not a complete dependency advisory review or production runtime approval.

Two application files change, adding nine lines:

- `lib/deployment-config.js` requires `DB_TIMEOUT_MS`, an integer from 1 to
  2147483647, and passes it to connection, server statement and client query limits.
- `db/index.js` adds explicit pool closure and a fixed idle-pool error log without
  connection details. Existing query/client interfaces stay in place.

The timeout setting is an operator choice with no default. Tests use 1000 ms;
production needs measured latency and a reviewed choice. A client timeout does
not establish that a write was rolled back, and this change adds no automatic
write retry. The persistence design must account for an uncertain write outcome.

The [portable patch](evidence/restart-dashboard-postgres-2026-10-03/dashboard-postgres.patch)
includes the pin, tests and operator documentation. No efsn, consensus, observer,
P1–P16 code or original dashboard checkout changed. Nothing was published.

## What passed

With Node 22.11.0, PostgreSQL 18.6 and `pg` 8.23.1, the same connection probe succeeds.
The real adapter tests cover:

1. Parameterized insert/upsert/read of JSON containing ordinary apostrophes and
   Unicode, with full UTC timestamps across midnight and a year boundary.
2. A separate reader role that can read but cannot delete or alter the table.
3. A slow SQL query reaching the configured timeout, followed by a successful query.
4. A connection timeout when a disposable local TCP peer never completes authentication.
5. A rejected SQL statement followed by a successful read of unchanged stored data.

These are five scenarios plus an enclosing test (six passing TAP entries). The
86 authentication/configuration/wiring contracts and the real collector wire
test also pass. PostgreSQL logs retain the expected statement cancellations and
permission failures. All test clusters are stopped, and generated admin password
files are removed; the verifier records retained scratch size and paths.

An initial harness attempt could not finish capturing `pg_ctl` output because of
inherited Windows pipes. Its driver probe never ran. That exact cluster was
stopped; redirecting process output to files resolved the harness issue. Both the
setup failure and subsequent expected legacy failure are retained separately.

## Next bounded work

The [persistence/schema blockers](restart-dashboard-config.md#next-persistence-correctness-before-integration)
remain unresolved. This commit tests the generic adapter, not `Populate`, the
current WebSocket writer, historical SQL setup or browser storage pipeline.

The protocol trace provides a simpler candidate for that next correction:
`ready` on the collector's `/primus` stream returns `emit: ["init", {nodes: ...}]`.
This contains complete node objects, including each node's own information,
stats and block. A bounded periodic snapshot can avoid merging unrelated partial
reports. Store one complete snapshot atomically with its observation time and
derive the API's compatibility fields when reading, rather than duplicating
block/info columns. The separately emitted chart response needs an explicit
collection/deadline policy; node and chart messages are not an atomic chain view.

Implement and test that design with a nondestructive versioned schema, serialized
writes, reconnect/timer cleanup, fresh-snapshot recovery after uncertain writes,
and stale-data handling. The collector's cached `active` value and a fresh snapshot
alone do not prove recent reports from each node or canonical chain agreement.
The complete collector → database → API → browser acceptance test and broader
runtime, resource-limit and TLS review remain required by G6.

Evidence: [retained bundle and verifier](evidence/restart-dashboard-postgres-2026-10-03/README.md).
