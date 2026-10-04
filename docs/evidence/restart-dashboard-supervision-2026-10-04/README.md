# Dashboard supervision evidence — 2026-10-04

Scope: three real dashboard Node entry points under systemd, a disposable
PostgreSQL 16 database, synthetic loopback telemetry and a private journal
namespace. No nginx, browser, native miner, backup or real account key is used.
The existing compiled dashboard and all efsn source files are preservation checks.

`baseline.json` captures dashboard parent commit `02c882a1dcd88ee6e5794846a075d6154b233a99`,
763 tracked dashboard files, 1007 efsn source/module files and the compiled build.
`run-linux.py` renders temporary service paths from the actual committed candidate,
creates only named local fixture resources and removes its runtime units and
plaintext test credentials in `finally`. PostgreSQL is stopped on every run.

The run directories retain raw command output, non-secret environment settings,
rendered units, journals, source hashes and harness versions. `run-4` passes all
eleven application checkpoints but fails its subsequent logging probe. The
separate `journal-1` passes rotation. `verification.json` verifies those results
together and preserves `combined_run_passed=false`; no failed run is relabelled.

## Retained failures and corrections

1. `run-1`: the synthetic reporter inherited a helper's rejected close promise
   on a connection attempt before collector readiness. Attach its rejection
   handler immediately and let the reporter retry. The same run showed that
   `/run/systemd/journald@NAME.conf` was ignored; the correct temporary override
   is `/run/systemd/journald@NAME.conf.d/50-test.conf`. The production candidate
   installs its primary configuration under `/etc/systemd/`.
2. `run-2`: all recovery/shutdown checkpoints reached that point, then the harness
   tried `reset-failed` on a stopped unit that systemd had already unloaded.
   Remove that unnecessary reset. Repair of an actually failed unit still resets
   its state explicitly.
3. `run-3`: systemd refused the sixth start, but the harness waited for the
   `Result=start-limit-hit` string. On systemd 255, `service_enter_dead` preserves
   an existing failure result; this run therefore kept `exit-code`. The corrected
   check requires failed state, five scheduled restart jobs, the explicit start
   refusal journal entry, no process, and unchanged state for another six seconds.
   This expectation follows the [upstream implementation](https://github.com/systemd/systemd/blob/v255/src/core/service.c),
   rather than weakening the restart budget.
4. `run-4`: all eleven application checkpoints pass. Its logging probe does not
   retain the intended volume, so the oldest marker remains and the rotation
   assertion fails. The final saved tail reaches input record 1748 rather than
   the final marker. The isolated `journal-1` removes this fixture ambiguity:
   disable the namespace rate limit, retain the probe unit after exit, and wait
   for the final marker before synchronizing/measuring the journal. It processes
   the bounded input and retains exactly 16 MiB; the old marker is gone and the
   last marker remains. This does not establish the precise cause of the earlier
   missing log tail or validate per-unit rate-limit overrides in namespaces.

No dashboard application code changed to address these fixture failures. Their
original outputs and scripts remain available. `run-1` script copies were
reconstructed immediately from the one-line fixture edits and checked against
the hashes already captured by that run. Later runs copy their scripts at start.

## Reproduction and limits

The helper is a local acceptance harness, not a production installer. It needs
root in the isolated `FusionRehearsal` WSL distro, the existing reviewed Linux
Node/PostgreSQL binaries under `tmp`, the dashboard worktree/dependencies and
the existing `rehearsal` user with UID/GID 1000. Invoke the retained combined
`run-linux.py` with a new `run-N` directory; its final logging probe has the
limitation above. Reproduce accepted isolated rotation with `run-journal.py
journal-N`. Existing output is never overwritten. The private database is
small and created from scratch. No package download or historical chain replay
is needed. The Windows-side `verify.py` checks final evidence and preservation.

Production and rehearsal use the same service settings except the release,
runtime, environment/credential paths and unique journal namespace. No services
are enabled at boot. The journal rehearsal uses volatile storage and disables
compression; it retains the candidate's 16 MiB/2 MiB runtime budgets. Rate limiting
is disabled in the separate synthetic logging namespace so rotation can be exercised
with bounded input. The acceptance ceiling allows active-file/allocation overhead;
it is not a claim that `RuntimeMaxUse` is a hard filesystem quota.

The drill does not validate public certificates, proxy process/log lifecycle,
machine reboot, persistent journal retention across reboot, seven elapsed days,
host resource sizing, hung-process health alerts or production retry/rate limits.
Those remain in G6. Application receipt/freshness checks use one Linux clock.

`dashboard-supervision.patch` and `commit.json` provide the portable dashboard
change after commit. `verification.json` verifies its reverse applicability and
that the original dashboard checkout and prior runtime binaries are unchanged.
Raw logs/patches retain their original whitespace; authored sources are checked
separately. Nothing is pushed or publicly deployed.
