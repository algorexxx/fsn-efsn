# Collector output evidence

Local acceptance on 3 October 2026. Candidate
`57d77791acc3af21160697efb45aa854f0e66066` follows dashboard commit
`6893caa09e0db17d8b0f70a5d8349c1fb5bbb2c2` on
`codex/dashboard-telemetry-auth`. See the [report](../../restart-dashboard-output.md).

- `capture-baseline.py`, `baseline.json`: pre-change collector and inspected
  dependency source hashes.
- `probe-buffer.cjs`, `probe-buffer.*.txt`: two eight-byte writes in an isolated
  corked stream, illustrating unguarded queue growth without network traffic.
- `attempt-1`: 151 contracts and 12 socket tests pass, with complete output,
  source hashes, commands and timings. Socket diagnostics include actual queued
  bytes before refusal and zero queued bytes after destruction.
- `attempt-2`: six real collector/PostgreSQL/HTTP pipeline scenarios pass (seven
  TAP passes), with source hashes, command outcomes and stopped-cluster evidence.
- `run-tests.py`, `run-persistence.py`: reproduction scripts using explicit local
  runtime paths and previously unused attempt directories.
- `record-commit.py`, `commit.json`, `dashboard-output.patch`: exact portable
  candidate commit, ancestry and patch hash.
- `verify.py`, `verification.json`: 697-file tested-source matching, patch/count/scope
  checks, unchanged locks/frontend, original-checkout preservation and cleanup.
- `process-cleanup.json`: no owned collector/browser fixture processes remain.

All fixtures use synthetic credentials, loopback endpoints and bounded data.
The special fixture corks a socket to hold output deterministically; production
contains none of its corking or inspection controls. This is functional limit
acceptance, not a throughput benchmark or a physical slow-reader measurement.
No chain restore, replay, signing, real wallet or public service was used.

The disposable database is stopped and its temporary password file removed.
Old dependency deprecation warnings remain in the logs. Dependencies, database
schema, frontend and consensus code are unchanged. Browser/build checks were
not repeated for this backend-only change. Scripts reference this machine's
paths; adjust them for another reviewer. The final patch is the portable source
candidate; intermediate hashes are not independent source archives.
