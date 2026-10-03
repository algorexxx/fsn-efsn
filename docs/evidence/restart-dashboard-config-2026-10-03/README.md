# Dashboard configuration evidence — 3 October 2026

Dashboard branch `codex/dashboard-telemetry-auth`, follow-up to the authentication
patch. `commit.json` identifies the exact candidate and parent. The portable
`dashboard-config.patch` applies after the earlier authentication patch.

- `run.py` records exact commands, source hashes, dependency versions and output
  without installing packages or accessing a database. Each attempt retains its
  runner, stdout/stderr and result JSON.
- `attempt-1`: six syntax checks pass; 84/86 contracts pass; the collector wire
  check passes. Express loading exceeded the fixture's one-second VM execution
  limit, and the stub WebSocket lacked its initial state constants. Both are
  test-harness defects. Its exact wiring-test source is retained.
- `attempt-2`: preload Express outside the VM's limit and give the stub the
  actual initial CONNECTING/OPEN states. Runtime source is identical to attempt 1.
  Six syntax checks, all 86 contracts and the real collector wire check pass.
- `inherited-source-review.json`: exact unchanged persistence/schema sources
  inspected for the next integration step. This is source review, not a SQL run.
- `verify.py` checks tested bytes against the retained Git commit, portable patch,
  unchanged locks/original checkout, failure history and final results.
  `checks.json` records its result.

Windows Node 22.11.0 and the previously installed locked dependencies were used.
The normal Windows sandbox prevents Node from resolving this workspace path;
the authorized checks ran outside that restriction. Only disposable loopback
HTTP/WebSocket listeners and synthetic credentials/reports were used.

The collector wire check now uses the production listener configuration to bind
loopback/port 0; the earlier monkeypatch is removed. The real Express API check
uses stubbed storage. Configuration tests validate database Pool arguments and
persistence startup ordering without opening a PostgreSQL connection.
The browser configuration helper is tested directly; no full React build or
browser session is claimed. No node software, private validator keys, TLS proxy,
public service or production database was used or modified.

See [the report](../../restart-dashboard-config.md) for scope and remaining work.
