# Per-node freshness evidence

Dashboard commit `f0c87459d0c64a2703714dd236d2a83f10247089` follows `3d73e95`
on the existing local `codex/dashboard-telemetry-auth` branch. See the
[acceptance report](../../restart-dashboard-node-freshness.md) for behavior,
limitations and the next launch requirements.

## Runs

| Run | Scope and outcome |
| --- | --- |
| `attempt-1` | First contracts/socket/React/build run passes |
| `attempt-2` | First disposable PostgreSQL pipeline run passes and stops |
| `attempt-3` | Final 132 contracts and nine socket tests, eight DOM tests and strict build pass; includes efsn-style latency handling |
| `attempt-4` | Final real collector/PostgreSQL/API suite: five scenarios plus outer test, six TAP passes; cluster stopped and password file removed |
| `attempt-5` | Eight DOM tests and strict build pass after the layout-only change placing freshness labels under node names |
| `browser-before-layout` | First passing 13-checkpoint compiled-browser run, preserved before the layout improvement |
| Root `browser-*` files | Final passing 13-checkpoint run, screenshots, requests and process/listener cleanup |

All runs pass; the repeated runs correspond to additional protocol coverage or
the layout change. Only the frontend was retested after that layout change.
The final verifier confirms the rest of its source matches the full suite.
The inherited `util.isArray` and `punycode` deprecation warnings remain in logs.

## Reproducible artifacts

- `commit.json`, `dashboard-node-freshness.patch`: exact candidate, parent and
  patch hash. No dependency version changes accompany the work.
- `run-tests.py`: root/sockets/DOM/build runner; supply a new attempt directory,
  optionally `frontend` for DOM/build only. Each run captures source hashes,
  commands, elapsed time and complete output. Successful builds record asset hashes.
- `run-persistence.py`: creates a new small SCRAM-authenticated loopback cluster,
  runs only the necessary database pipeline suite, stops it and deletes its test
  password file. Ignored database files remain in the recorded scratch path.
- `run-browser.py`, `serve.py`, `browser-check.cjs`, `set-browser-scenario.py`:
  isolated headless Edge and local API/static fixture. Synthetic browser data uses
  no database or node signing key. Control changes are recorded in JSONL.
- `browser-stale-reports.png`: fresh snapshot and connected node with expired
  individual reports. Other screenshots retain the populated/map/unavailable views.
- `verify.py`, `verification.json`: verifies 691 non-Markdown source files against
  the exact committed blobs, 547 compiled assets, test counts, database source,
  locks, original checkout and efsn telemetry preservation. Documentation was
  updated after runtime tests and is excluded from their source comparison.

The final browser has no page exceptions, missing assets or foreign-origin
requests. One `net::ERR_ABORTED` is expected for the deliberately hanging request.
`browser-run.json` records zero browser/server exits and listener refusal 10061.
The final PostgreSQL runner records a successful stop and status 3/no server.
Both browser runs were visually inspected; the second avoids the crowded extra
status column seen in the first.

These are local synthetic acceptance results. No actual efsn/RPC comparison,
public proxy/TLS deployment, real signer, restored chain or large disk replay was
used. Clock synchronization, chart/cache/resource corrections and runtime/dependency
review remain part of G6. Scripts contain this host's runtime/workspace paths;
adjust those paths to reproduce on a different review machine.
