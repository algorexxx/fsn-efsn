# Dashboard PostgreSQL compatibility — 3 October 2026

This bundle records a real prerequisite discovered while preparing the dashboard
persistence correction. It does not claim that the legacy writer or schema works.

- `attempt-1`: harness setup failure. PostgreSQL started, but Windows child
  processes retained the captured stdout pipe. The driver probe never ran.
  The exact test cluster was manually stopped. `harness-recovery.json` records
  the correction; later verification checks that this cluster is stopped too.
- `attempt-2`: corrected file-based process output. A fresh SCRAM-authenticated
  loopback cluster accepts native `psql` (`42`), but `pg` 7.12.1 on Node 22.11.0
  fails the identical connection/query probe with `timeout expired`.
- `attempt-3`: fresh cluster, same probe with pinned `pg` 8.23.1. Native and Node
  probes pass. Five real database scenarios (six TAP entries), 86 existing
  contracts and one real collector WebSocket test pass. The cluster stops cleanly.

`run.py` and `probe.cjs` are retained per attempt. Commands, exit codes, source
hashes, stdout/stderr and PostgreSQL logs are included. Passwords are synthetic;
generated admin passwords are absent from evidence and their files are removed.
Cluster data is retained only in ignored scratch directories. The test harness
does not install PostgreSQL, alter system services or access an existing database.

`dependency-changes.json` inventories the changed lock entries. The unrelated
entries and frontend/API lockfiles are unchanged. `pg-registry-metadata.json`
records the official npm package version, runtime requirement and integrity hash.
`install.json` records the scoped install with lifecycle scripts disabled.
No advisory audit is claimed.

`commit.json` and `dashboard-postgres.patch` preserve the dashboard change on top
of the configuration commit. `verify.py` compares the tested bytes with those
commits, validates the expected failure and passing checks, confirms the original
dashboard checkout is unchanged, and checks all three test clusters are stopped.
`checks.json` records its result.

See [the report](../../restart-dashboard-postgres.md) and
[the launch plan](../../restart-plan.md) for scope and next work.
