# Dashboard browser evidence — 3 October 2026

This bundle records the browser freshness correction following dashboard commit
`a2e9f1b`. `commit.json` identifies the exact candidate, parent and portable patch.
The [report](../../restart-dashboard-browser.md) states scope and remaining work.

- `result.json`: exact tested source hashes, tool versions, settings, commands
  and exit codes. Final results: **110 contracts and six React DOM tests pass;
  production build fails** with `ERR_OSSL_EVP_UNSUPPORTED`.
- `contracts.*`, `react-tests.*`, `build.*`: final unmodified stdout/stderr.
- `run.py`: the final harness; tests/build invoke the Node executable directly.
  Its npm version query refers to the bundled CLI, not the `npm.cmd` wrapper used
  for installation. `install-command.json` records that distinction.
- `install.txt`: unchanged-lock dependency installation output, scripts disabled.
- `build-before.txt`: inherited production build failure before source edits.
- `contracts-1.txt`, `react-tests-1.txt`: exploratory runs (109 contracts and five
  DOM tests), before the synchronous-adapter test and rendering-warning fixes.
- `before-zero-display-review/`: prior 110-contract/five-DOM run with hashes and
  the three source files changed by final review. Final output adds a sixth DOM
  case for height zero and unknown receive time, and keeps timing metadata out
  of presentation state. Earlier warnings/failures are not discarded.
- `verify.py`, `checks.json`: commit/source/patch agreement, observed outcomes,
  unchanged dependency locks, original checkout and node telemetry source checks.

The JSDOM tests render the actual React component with controlled Axios responses
and clock. Root API contracts use real loopback HTTP. No PostgreSQL, actual efsn,
validator key, public server, browser process or TLS proxy ran in this bundle.
No dependency upgrade or legacy crypto option was used. The final build failure
is a release blocker, not a passing result.

Read `run.py` and the dashboard's `docs/browser-freshness.md` before reproduction.
Install the locked dependencies with scripts disabled. Preserve this bundle:
use a new evidence directory for another run instead of overwriting historical
output. Run `verify.py` against the committed local candidate to audit this result.
