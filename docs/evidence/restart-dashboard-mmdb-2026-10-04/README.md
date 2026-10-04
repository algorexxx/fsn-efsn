# MMDB integration evidence

The dashboard candidate starts from `2e047abb1eaab6e9315373e39af68212a399b451`.
`commit.json` identifies its completed migration commit and the full binary
patch, including the two small licensed synthetic test databases. Apply that
patch to the named parent, then install from the resulting package lock. Do not
use test databases as production location data.

The [integration report](../../restart-dashboard-mmdb.md) records behavior,
results and remaining deployment work. Local helpers use this workstation's
`FusionRehearsal` distro, selected Node runtime and disposable PostgreSQL/nginx
installations; they are investigation scripts, not production service launchers.

- `prepare.py`, `baseline.json`: source capture and integrity-checked test-fixture
  acquisition from the preceding reader experiment. Both upstream binary hashes
  and licensing are also recorded in the dashboard's fixture README.
- `install.py`, `install-1/`: regenerated v1 lock, clean install, full backend
  registry audit and complete installed dependency tree. The prior dependency
  directory is moved to a checked workspace path and retained, including its
  original GeoIP data. No install scripts run.
- `run-contracts.py`, `contracts-1/`: retained invocation failure; the npm child
  shell did not have Node on PATH, so neither suite started.
- `contracts-2/`: all 14 socket tests pass; one of 204 backend cases fails because
  a preexisting numeric-limit loop includes the newly added nonnumeric mode.
- `contracts-3/`: all 204 contracts pass after the fixture's setting selection
  is corrected. The independent mode-validation cases remain enabled.
- `run-frontend.py`, `frontend-1/`: 23 frontend tests and the initial lint/build.
  The staging output path emits a non-cleaning warning. `frontend-2/` records a
  normal build with empty stderr. `build-comparison.json` proves that only four
  source maps differ; all 542 other files are identical.
- `build-activation.json`: the previous build is preserved and the candidate
  build is selected for local acceptance. The later normal build is the final
  546-file manifest used by native acceptance.
- `run-browser.py`, `browser-check.cjs`, `set-browser-scenario.py`, browser JSON,
  logs and PNGs: twelve compiled-browser checkpoints, including country-only
  flags, mixed geography and unavailable locations. The local server and browser
  stop after the run. Browser country-only screenshot was visually inspected.
- `run-wss.py`, `stationary-1/`: the initial native run exposes a readiness-file
  race in the preexisting test. Its stopped-process and secret cleanup evidence
  is retained alongside the failure.
- `stationary-2/`: the complete native efsn/WSS/PostgreSQL/HTTPS/browser run passes
  with `GEOIP_MODE=mmdb` and the named synthetic file/hash/budget. The native
  fixture has four browser checkpoints. Credentials, generated private TLS keys
  and process cleanup are verified. Certificates/SPKI in this bundle are public
  test material. No signing keys from the chain backup are used.
- `verify.py`, `verification.json`: accepted results, exact eleven-removal/
  one-addition dependency delta, other locked entries unchanged, fixture bytes,
  final build and original source/data preservation. Linux fixture processes are
  absent. A separate Windows process inventory also found no matching test Node
  processes after completion.
- `stage-dashboard.py`, `staged-dashboard.json`, `capture-commit.py`,
  `dashboard-mmdb.patch`, `commit.json`: exact staged scope, byte verification
  with Git newline normalization identified, local commit and portable patch.

The old five-file validator and its fixture/tests are intentionally removed
from the dashboard candidate. Their previous evidence remains in the parent
repository and Git history. Existing original-dashboard changes and unrelated
branding/historical-tracing files in the parent workspace are left untouched.

Whitespace checks apply to authored source and Markdown. Raw tool logs and the
portable patch retain their original bytes, including table padding, blank
terminal lines and diff context prefixes; trimming them would alter the evidence.
All staged files are compared byte-for-byte with the worktree, allowing only
Git's identified Markdown newline normalization.
