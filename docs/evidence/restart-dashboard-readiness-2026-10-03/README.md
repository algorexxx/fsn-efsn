# Dashboard baseline evidence

See the [report](../../restart-dashboard-readiness.md) and
[launch gate G6](../../restart-plan.md#g6--public-dashboard).

- `capture.json`: exact source identities for the local dashboard and efsn
  telemetry, existing Git-status digest and line-ending comparison with HEAD.
- `baseline/server.js`: exact collector bytes used by the local harness.
- `collector-contract.test.cjs`: seven desired behavior checks with explicit
  dependency/collection/socket/timer doubles; no external modules or services.
- `baseline/` and `attempt-2/`: two environment failures before test execution,
  retained without overwriting. Both report Windows path-resolution `EPERM`.
- `attempt-3/`: actual Node test results: **2 pass, 5 fail**, exit 1, no skipped
  tests. The failing expectations identify deployment blockers.
- `capture.py`: initial source capture and attempted execution. Refuses an
  existing baseline directory; do not rerun it over retained evidence.
- `run-contracts.py`: subsequent execution against the archived source; requires
  an unused attempt name and checks harness/source identities first.
- `verify.py` / `checks.json`: verification of retained evidence and unchanged
  inspected source. A successful verifier does **not** mean dashboard acceptance
  passed; it confirms the recorded failing baseline.

Reproduce locally with Python 3 and Node.js (retained runner: v22.11.0):

```powershell
python docs/evidence/restart-dashboard-readiness-2026-10-03/run-contracts.py attempt-4
python docs/evidence/restart-dashboard-readiness-2026-10-03/verify.py
```

The contract run should exit 1 for the archived baseline. Windows may require
normal filesystem access for Node to resolve the script path; the retained
approved retry still used only mocked sockets/storage. No HTTP/WebSocket traffic
or database process is part of this harness. Full dependency integration, a
production build and a browser run remain unverified. The verifier checks the
original attempt-3 results, not newly named attempts.
