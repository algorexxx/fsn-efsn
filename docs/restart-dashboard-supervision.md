# Dashboard service supervision — 2026-10-04

The collector, snapshot writer and API now have tested systemd service candidates
in the isolated dashboard branch. This is deployment configuration and operating
documentation only: no dashboard application, dependency, frontend or efsn code
changes. The public dashboard gate G6 remains open.

## Candidate

Three independent services run the existing Node entry points directly. Each
receives a different unprivileged dynamic identity, a read-only release and only
its own credential file. The collector receives telemetry credentials; the writer
and API receive separate restricted PostgreSQL passwords. Real signing keys are
never part of dashboard deployment.

Unexpected exits restart after five seconds. Five starts within sixty seconds
are allowed before the service stays failed for operator repair. Deliberate
`systemctl stop` stays stopped. Shutdown allows fifteen seconds before remaining
processes are killed. The writer already drains pending writes; the collector
and API use normal SIGTERM exit, so open requests/sockets can be interrupted.
No new shutdown implementation was necessary.

A dashboard-specific journal configuration requests 64 MiB persistent storage,
8 MiB files, a 16 MiB/2 MiB volatile fallback and seven-day maximum retention.
It also configures free-space reserves, a diagnostic rate limit and no forwarding
to other logging sinks. These are reviewable candidates, not selected public-host
defaults or hard filesystem quotas. The dashboard runbook explains startup,
credential provisioning, configuration repair, log inspection and limitations.

## Measured results

Tests use systemd 255.4, Linux Node 24.21.0 and PostgreSQL 16.15 in the existing
WSL rehearsal environment. The actual service entry points use a fresh, small
database and synthetic loopback reports. No historical data or mining is involved.

| Check | Result |
| --- | --- |
| Writer/API before collector startup | Initially unavailable API; writer recovers without restart |
| Collector, writer and API crashes | Each replaces its process and restores reports; other service PIDs stay unchanged |
| PostgreSQL outage | API returns unavailable; all application processes survive and reconnect |
| Stop writer during a blocked database write | Pending transaction commits; writer exits successfully in about 2.16 seconds |
| Stopped writer | Snapshot becomes stale; API refuses it; explicit restart restores fresh reports |
| Deliberate stop | All three services remain stopped beyond the restart delay |
| Invalid configuration | Five failed starts, explicit restart refusal, no live process or subsequent automatic retry |
| Configuration repair | Reset failed state and restart restores a fresh report |
| Credentials in application logs | None of the generated fixture secrets appears |
| Isolated journal rotation | Exactly 16 MiB retained; oldest marker evicted, newest marker retained |

The evidence is deliberately split: `run-4` passes all eleven application
checkpoints, then fails its logging probe; `journal-1` passes the isolated rotation
check. The combined run is **not** marked passed. The old probe did not retain its
intended log volume. The isolated check disables the namespace rate limit, keeps
the probe unit loaded and waits for its final marker before measuring rotation.
The precise earlier missing-tail cause and per-unit rate-limit overrides are
not established. Production log-rate acceptance remains open.

Earlier failed attempts also exposed reporter readiness/rejection handling,
the proper temporary journald configuration directory and a test assumption
about resetting an unloaded unit. The restart-limit test initially expected the
wrong result string: systemd 255 preserves the original exit failure even when
it later refuses further starts. The final check verifies the stopped state,
retry count and explicit refusal. This matches the
[systemd implementation](https://github.com/systemd/systemd/blob/v255/src/core/service.c).
All original failed outputs and harness versions are retained.

## Preservation and remaining work

The [evidence bundle](evidence/restart-dashboard-supervision-2026-10-04/) includes
rendered services, journals, reproducible helpers, the portable dashboard patch,
commit metadata, source hashes and a verifier. It confirms 1007 efsn source/module
files, 546 compiled frontend files, application/dependency files, prior runtime
binaries and the original dashboard checkout are unchanged. All temporary units,
plaintext fixture credentials, four disposable databases and isolated journal
directories were removed after checking stopped processes and exact paths.
No services were enabled at boot, and nothing was pushed or publicly deployed.

This closes bounded local supervision of the three application processes and
isolated journal rotation. Next, handle nginx supervision and its current file
logs, log reopening/retention, public certificate acceptance/renewal and the
coordinated host manifest. Still rehearse actual-host reboot, persistent journal
retention, health/notification delivery, resource allocation and production
retry/log-rate behaviour. A running process alone does not prove readiness;
the existing freshness and report checks remain essential. See the
[consolidated launch plan](restart-plan.md).
