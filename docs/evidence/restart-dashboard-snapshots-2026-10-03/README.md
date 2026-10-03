# Dashboard snapshot acceptance — 3 October 2026

This bundle records the replacement snapshot writer, versioned PostgreSQL schema
and HTTP read API. `commit.json` identifies the exact dashboard commit and parent;
`dashboard-snapshots.patch` is its portable review patch.

`run.py` creates a fresh disposable SCRAM-authenticated PostgreSQL 18.6 cluster,
bound only to an ephemeral loopback port. It runs the contracts, existing driver
tests, new persistence acceptance and existing collector wire check. It stops the
cluster, removes the generated admin password file and retains the local data
directory for inspection. Existing databases and the blockchain backup are unused.

- `attempt-1`: all 98 contracts, six driver TAP entries, five persistence TAP
  entries and one collector wire check pass.
- Review then tightens reconnect ordering to wait for the old socket's actual
  close event. One focused lifecycle test is added. The two previous source files
  are retained under attempt 1 and checked against that attempt's source hashes.
- `attempt-2`: all 99 contracts and the same real integration suites pass.
  This is the committed candidate.

Both attempts retain exact runners, source hashes, commands, output and database
logs. Expected permission, constraint and duplicate-schema failures are part of
the acceptance assertions. The inherited `util.isArray` deprecation appears in
the transport test output; the dependency lock is unchanged.

The persistence test starts the real collector with two synthetic telemetry
identities, uses the real WebSocket persistence transport, writes through a
restricted database role, reads through another role and serves the actual
Express API. It checks distinct metadata/heights, quoted Unicode, reconnect,
disconnect, older/invalid write rejection, preserved historical sentinel data,
one-row storage and stale responses using an advanced API test clock. The child
collector exits cleanly and its captured logs omit the synthetic credentials.

`verify.py` validates committed source identities, patch bytes, all retained
outcomes, unchanged locks/collector/original checkout, removal of generated
password files and stopped cluster status. `checks.json` records its result.

This is not a browser build, real efsn-process report, direct-RPC comparison,
TLS/proxy test, production service deployment or complete resource-limit review.
See [the report](../../restart-dashboard-snapshots.md) for remaining G6 work.
