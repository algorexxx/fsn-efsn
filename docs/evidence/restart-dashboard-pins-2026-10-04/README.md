# Saved-pin recovery evidence

See [the UI maintenance report](../../restart-dashboard-ui-maintenance.md) for
the findings, remaining release decisions and limits of this acceptance.

`baseline.json` identifies the previous dashboard commit and source/build bytes.
`pins-baseline-2` reproduces three failures on that compiled build. The first
`pins-baseline` attempt is retained: its assertion incorrectly required a
page-error event for the object-valued preference. The corrected harness checks
the observable missing rows; both attempts stopped their local fixture server.

`frontend-1` records 22 passing tests, lint and the production build.
`pins-final` records seven passing storage scenarios on that build.
`browser-result.json` records the nine existing compiled-browser checkpoints;
the two aborted API requests match two deliberate hangs in `browser.stdout.txt`.
`stationary-1` records native local telemetry through WSS, PostgreSQL and HTTPS,
including report expiry and recovery. The native mining-outage drill and the
unchanged backend suites were not repeated in this slice.

`ui-package-review.json` captures public npm metadata without installation.
`commit.json` and `dashboard-pins.patch` preserve the dashboard commit.
`verification.json` checks the evidence against local source/build hashes,
the original dashboard, process cleanup and the retained prior build.

The helpers use the existing Windows/WSL fixture layout, cached Node runtimes,
Edge/Playwright, local PostgreSQL/nginx and synthetic efsn test binary; they are
not portable deployment instructions. Output directories are single-use.
`prepare.py` captures the pre-change baseline and must not be rerun over this
record. The accepted frontend run is `run-frontend.py 1`; its build was then
activated with `activate-build.ps1`, retaining the previous build. Browser runs
use `run-pins-browser.py baseline 2`, `run-pins-browser.py final`, `run-browser.py`
and `run-wss.py stationary-1` with the corresponding old/new build active.
`verify.py --commit` rechecks the retained evidence without launching services.
