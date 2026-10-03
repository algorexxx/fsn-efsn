# Dashboard authentication correction evidence

See the [report](../../restart-dashboard-auth.md). Dashboard branch
`codex/dashboard-telemetry-auth`, commit `497b0831a148d67624974748c0ee609b4e815a08`,
base `e2049634802d4a49adadf998853ce6ee6b1158d0`. No chain source changed.

- `dashboard-auth.patch` / `commit.json`: portable commit patch and identity.
- `install.txt`: original locked collector install output; lifecycle scripts,
  package advisory scanning and deployment were disabled. The dependency lock
  remains unchanged; this is not a maintenance/security approval of those versions.
- `initial-syntax-launch.json`: normalized record of the Windows sandbox
  path-resolution error before the initial checks could run.
- `attempt-1/`: exact syntax/contract/wire commands, source hashes, dependency
  versions, stdout/stderr and runner copy. Both syntax checks pass; 71 contracts
  and one real collector/WebSocket test pass, with no skipped tests.
- `verify.py` / `checks.json`: verify identities, results and the clean committed
  dashboard worktree against the original preserved source/status.

The original dashboard checkout was left untouched. The isolated working
checkout is `C:/Users/Peter/Documents/CODING/fsn-efsn/tmp/fsn-stats-auth`.
If that worktree is removed later, the committed dashboard branch and portable
patch preserve the change. Do not use this directory as a production deployment.

Reproduce on the retained dashboard commit with the existing locked dependencies:

```powershell
npm.cmd ci --ignore-scripts --no-audit --no-fund
npm.cmd test
npm.cmd run test:wire
```

Those commands run from the dashboard checkout. To capture fresh evidence from
the current efsn workspace without overwriting previous results:

```powershell
python docs/evidence/restart-dashboard-auth-2026-10-03/run.py attempt-2
python docs/evidence/restart-dashboard-auth-2026-10-03/verify.py
```

`run.py` requires the retained worktree path and compares the original source
against the readiness baseline. The verifier is tied to `attempt-1`, the exact
dashboard commit and source bytes; later changes intentionally fail identity
checks. The observed runner is Node 22.11.0. The Windows environment required
normal filesystem access for Node to resolve these paths.

Only the transport test opens a listener, forced by its fixture to ephemeral
loopback. It uses synthetic credentials and disposes of its collector child.
No chain database, node signing key, public endpoint, PostgreSQL, read API or
browser is involved. The production dashboard gate remains open.
