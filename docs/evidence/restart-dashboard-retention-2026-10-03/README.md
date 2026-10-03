# Dashboard report validation and compact retention evidence

See [the investigation report](../../restart-dashboard-retention.md) for results
and scope. All runs are local; credentials and node keys are synthetic.

- `attempt-1`: eight targeted regressions against the preceding production code;
  all eight fail as expected.
- `attempt-2`: 159 contracts pass; one wire test exposes changed ticket values
  in the shared test fixture. This is preserved as a failed attempt.
- `attempt-3`: 159 contracts and all 12 wire tests pass after restoring that
  fixture's intended zero tickets.
- `attempt-4`: six real collector/PostgreSQL/API scenarios pass (seven TAP tests
  including the outer test). Fresh SCRAM-authenticated cluster stopped afterward.
- `attempt-5`: actual-node run fails the freshness assertion without receipt
  diagnostics. Its precise cause is not established. Database and fixture stopped.
- `attempt-6`: readiness requires all three report receipts and records initial
  API data; the actual-node/database/API/browser run passes all assertions with
  unchanged freshness limits. The compiled frontend and Go binary are reused
  from the preceding presentation run and checked by hash.
- `measure-cache.cjs` / `cache-measurement.json`: offline bounded cache population
  and eviction; GC heap samples and JSON bytes, not a loaded network or peak RAM.
- `dashboard-retention.patch`, `commit.json`, `verification.json`: exact local
  dashboard commit, source/build/artifact checks and final verification.
- `*-process-cleanup.json`: post-run Windows/WSL checks for remaining test services.

Reproduce the candidate contracts with bundled Python and
`run-contracts.py attempt-N candidate`; choose a fresh attempt directory. For
database scenarios use `run.py attempt-N persistence`, or `actual-efsn` for the
opt-in WSL/Go/browser fixture. Paths/runtime prerequisites are explicit in the
scripts. `node --expose-gc measure-cache.cjs` reproduces the offline measurement;
preserve the original result first. `verify.py` checks the saved review bundle.

The first eight regression sources remain byte-identical between baseline and
candidate. Other fixtures were filled out to match actual efsn report shapes.
Only the actual integration fixture changed after attempt 3 (readiness and
diagnostics); it is checked against attempt 6. Markdown review notes are excluded
from executable-source identity comparisons.
