# Dashboard deployment configuration and persistence findings

3 October 2026. Dashboard commit
`31a13524e03b29dc3e7fe22ed9132699c906bc00`, following the
[authentication correction](restart-dashboard-auth.md) on
`codex/dashboard-telemetry-auth`. **86 contracts and one real collector WebSocket
test pass.** Configuration is now explicit; the complete public dashboard is
still blocked by persistence, build and deployment work.

## Scope

Work remains in the isolated dashboard checkout at
`C:/Users/Peter/Documents/CODING/fsn-efsn/tmp/fsn-stats-auth`. The original
`fusionfoundation/fsn-stats` checkout retains its prior bytes and Git status.
No efsn, consensus, observer or P1–P16 source changed. Nothing was pushed or
deployed, and no large disk workload was started.

Seven dashboard runtime files change: collector `server.js`, database `db/index.js`,
API `api-server/server.js`, persistence `wsclient/wsclient.js`, browser `Main.js`,
and two small configuration modules. Documentation and tests accompany them.
Dependency locks remain unchanged. The
[portable patch](evidence/restart-dashboard-config-2026-10-03/dashboard-config.patch)
applies after the authentication patch.

## Configuration contract

The supported candidate topology places collector, API and database on one host
behind a local HTTPS/WSS reverse proxy. Collector and API require explicit numeric
loopback addresses and ports; there is no wildcard or default-port fallback.
Port 0 is accepted for disposable tests; deployed services require fixed ports.
The existing wire test now exercises that real configuration instead of replacing
the HTTP listener method.

Database host, port, database, role and absolute password-file path are required
before constructing the connection pool. Password-file errors omit contents and
paths. An optional trailing line ending is removed while other password whitespace
is preserved. Old `SQLHOST`/`SQLPASS` settings are rejected. The five-connection
pool limit is retained. Transport is explicitly plaintext over numeric loopback;
remote database deployment is outside this candidate. Provisioning separate
least-privilege reader/writer roles remains an operational requirement, not a
property that environment validation can establish.

Persistence requires `COLLECTOR_WS_URL`, ending in `/primus`, using loopback WS
or WSS. It no longer defaults to the foundation's old host. Embedded credentials,
query strings, fragments and alternate paths are rejected.

The browser uses `REACT_APP_STATS_API_PATH`, a validated same-origin path such as
`/stats-api`, instead of the old foundation API host. The reverse proxy must remove
that prefix when forwarding to the private API. The value is compiled into the
browser bundle; validation runs when the module loads. No full frontend build
has been performed yet. Wildcard CORS headers are removed; separate-origin browser
hosting is outside this candidate. CORS does not restrict command-line access to
public data.

The dashboard's `docs/deployment-configuration.md` records all settings, routing,
secret handling and supported limits. Its README and enrollment command now use
those settings rather than the unsafe historical database recipe.

## Validation and limits

The retained Windows run uses Node 22.11.0 with existing locked dependencies.
Six syntax checks, **86 contracts**, and **one real collector wire test** pass.
This includes all 71 previous authentication contracts, eight configuration
tests and seven wiring tests. The wiring suite starts the real Express API on
configured loopback/port 0, requests `/nodes`, verifies the expected synthetic
response and absence of wildcard CORS, then closes the listener. Storage is
stubbed. Database Pool arguments and persistence startup ordering are tested
without a database connection.

The first run passed 84/86 contracts. It exposed two harness defects: loading
Express inside the fixture's one-second VM limit, and a WebSocket stub without
its initial state constants. The second run loads the dependency before entering
the VM and supplies realistic stub state. Runtime code did not change between
attempts. Both attempts and the first harness source are retained.

There is no PostgreSQL, full React build, browser, Linux service, TLS/proxy,
actual efsn-process telemetry, resource-limit or public-deployment acceptance
claim here. Legacy dependency deprecations remain; this is not an advisory audit
or approval of Node 22.11.0 as the production runtime.

## Next: persistence correctness before integration

Inspection of the inherited persistence/schema sources found concrete blockers:

| Source | Finding | Required acceptance |
| --- | --- | --- |
| `wsclient/wsclient.js` | Reconnects create new cleanup and keepalive timers without cancelling old ones; cleanup loses its interval value | One connection/timer lifecycle, bounded retries and clean stop |
| Same file | Shared metadata/block/time across nodes; unchecked `myData.data`; missing initial snapshot request and explicit Primus heartbeat handling | Distinct nodes retain their own reports through connect, update and reconnect |
| `Populate.initDbAndTables()` | Deletes charts, then references undefined `record`; caller does not await/catch initialization | Remove connection-time destructive initialization; explicit, checked schema setup |
| `db_methods/populate.js` | Several SQL statements interpolate report values | Parameterized operations, including ordinary quoted-text round trips |
| `POSTGRESQL_Setup.sh` | Drops database, does not switch connection to it, uses time of day instead of full timestamp, omits `blocks` table | Nondestructive versioned schema and verified database/role setup |
| API `/info` | Calls a missing retrieval method | Define the supported API routes and verify each against stored data |

These findings come from source inspection; no production data or SQL was used.
They are separate from the configuration correction and remain unfixed in this
commit. The next bounded task should correct persistence and schema behavior,
then prove collector → storage → API → browser agreement with multiple synthetic
nodes and disconnect/reconnect/staleness cases. API bounds/error output, runtime
review, input/resource limits and proxy/TLS acceptance remain in G6.

Evidence: [bundle and verifier](evidence/restart-dashboard-config-2026-10-03/README.md).
Launch tracking: [G6 in the consolidated plan](restart-plan.md#g6--public-dashboard).
