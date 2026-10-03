# Chart cache evidence

Local dashboard acceptance on 3 October 2026. Candidate
`6893caa09e0db17d8b0f70a5d8349c1fb5bbb2c2` follows
`f0c87459d0c64a2703714dd236d2a83f10247089` on
`codex/dashboard-telemetry-auth`. See the
[report](../../restart-dashboard-history.md) for scope and remaining work.

- `baseline`: all 13 new in-memory history regressions fail against the previous
  cache. It includes source hashes and the original failure output.
- `attempt-1`: first corrected run, 145 contracts and 10 socket tests pass.
- `attempt-2`: final contract/socket run, including the filled-cache chart check
  and source with original line endings preserved. Same passing counts.
- `attempt-3`: disposable SCRAM-authenticated PostgreSQL pipeline, commands,
  complete output, tested source hashes and cluster shutdown result. Six
  scenarios pass (seven TAP passes including the outer test).
- `run-tests.py`, `run-persistence.py`: reproduction scripts; require unused
  attempt directories and use the explicit local toolchain paths.
- `record-commit.py`, `dashboard-history.patch`, `commit.json`: portable candidate
  commit capture and hash.
- `verify.py`, `verification.json`: test counts and tested/committed source
  matching for 693 source files, patch/ancestry, unchanged frontend and locks,
  and preservation of the original dashboard checkout and efsn telemetry source.
- `process-cleanup.json`: no remaining owned collector test process.

Fixtures use only synthetic telemetry, fake clocks and loopback endpoints.
The full retention test creates 2,001 small in-memory reports, not chain blocks
or a restored database. The database test uses a small new local cluster; it is
stopped afterward and its temporary password file is removed. Existing chain
data, wallets and production services are not accessed.

The earlier compiled frontend is unchanged; browser tests and builds are not
repeated for this backend-only correction. Old dependency deprecation warnings
remain in the retained output. No dependency versions, production deployment,
or consensus code changed. These scripts use this machine's paths; adjust those
paths for another reviewer. Baseline/intermediate manifests are not independent
source archives; the final patch is the portable review candidate.
