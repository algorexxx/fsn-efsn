# Collector input evidence

Local acceptance on 3 October 2026. Dashboard commit
`3d73e9576e4565bbabb3f6124dfad1bdc5e70fe1` follows `a5bee3f` in
`codex/dashboard-telemetry-auth`. See the [report](../../restart-dashboard-input.md)
for changes, scope and remaining launch work.

- `dashboard-input.patch`, `commit.json`: exact portable commit and ancestry/hash.
- `attempt-1` through `attempt-4`: commands, exits, timings, complete stdout/stderr
  and source hashes. First two attempts retain the failures; third passes;
  fourth checks the final source after applying the required brace style.
- `run-tests.py`: runs the root contracts and socket tests with the explicit
  Node executable. An attempt directory must not already exist.
- `capture.py`, `capture.json`: exact installed Primus 6.1.0 / ws 1.1.5 versions,
  inspected dependency/cache hashes and original-checkout preservation.
- `probe-history.cjs`, `history-probe.*.txt`: bounded in-memory reproduction of
  two inherited chart defects. These are open findings, not passing chart tests.
- `verify.py`, `verification.json`: matches the final 696-file test manifest to
  committed bytes, validates patch/ancestry and counts, checks unchanged locks,
  confirms the chart source matches upstream, and rechecks the original checkout
  and efsn telemetry source. Verification does not execute the tests again.
- `process-cleanup.json`: confirms no collector test child process remains.

The final result is **120/120 contracts and 8/8 socket tests**, with no skips or
cancellations. All sockets use loopback and synthetic credentials. The largest
generated fixture is a normal 50-block telemetry history, not chain data. Test
servers exit cleanly on passing paths; teardown also reaps them on failure.
No PostgreSQL, browser, chain replay, restored node, signing key or public service
was started. The old dependency `util.isArray` deprecation is retained in logs.

The input work includes no dependency version changes, chart-cache correction,
full report schema, per-node freshness or deployment approval. In particular,
application-rate limits do not cover protocol/control frames, HTTP traffic or
connection churn; chart/fork retention and slow-consumer buffering remain open.

The scripts contain local workspace/runtime paths to reproduce this machine's
run. Adjust those paths for another review host. Use the commit and patch for
the exact candidate; intermediate failed attempts retain hashes and outputs,
not independent source archives.
