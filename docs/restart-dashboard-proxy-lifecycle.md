# Dashboard proxy lifecycle — 2026-10-04

The isolated dashboard branch now has tested nginx supervision, file-log rotation
and certificate replacement candidates. Eight local lifecycle checkpoints and
the existing proxy and native node-to-browser regressions pass. This changes
deployment configuration, tests and operating documentation only; dashboard
application, dependency, frontend and efsn code are unchanged. G6 remains open.

## Candidate and measured behavior

The proxy runs under a dedicated stable account, with separate managed runtime
and log directories, a read-only filesystem elsewhere and only the capability
needed to bind privileged ports. The systemd unit validates configuration before
startup/reload, restarts after five seconds, limits starts to five per minute,
and allows fifteen seconds for deliberate shutdown. The template still binds
to loopback; no public listener was deployed.

A separate timer checks file logs every five minutes. Logrotate requests daily
rotation or earlier rotation above 8 MiB, seven archives, seven-day age cleanup
and delayed compression. It renames logs and signals the managed nginx master
to reopen them. These are retention settings, not hard disk quotas: files can
grow beyond the threshold between checks, frequent rotations can evict recent
history, and age cleanup happens on rotation.

| Local checkpoint | Observed result |
| --- | --- |
| Supervised HTTPS/WSS startup | Verified TLS and fresh authenticated telemetry through the real collector and API |
| Timer-driven rotation | Access/error logs received new inodes; master and worker descriptors reopened them |
| Eight further rotations | Seven archives per log, expected compressed contents, oldest marker evicted, owner/mode preserved; telemetry socket stayed connected |
| Valid certificate replacement | New verified TLS connection served the new certificate; master stayed running; old workers retired after about 10.72 seconds and reporter reconnected |
| Mismatched certificate/key | Reload refused; existing certificate and workers stayed active; valid on-disk selection restored |
| Worker crash | Existing master replaced the worker and telemetry recovered |
| Master crash | Systemd replaced the master, old workers disappeared and telemetry recovered |
| Deliberate stop | Service stayed stopped beyond its restart delay; rotation also succeeded while stopped |

The ten-second worker shutdown setting bounds old workers after reload. Long-lived
WebSocket sessions can close and reconnect; certificate replacement does not
promise uninterrupted telemetry. After a rejected certificate candidate, restore
the valid on-disk selection immediately so a later crash/reboot can start.

The rehearsal used systemd 255.4, nginx Ubuntu package `1.24.0-2ubuntu7.18`,
logrotate 3.21.0 and Node 24.21.0 in the existing isolated WSL environment.
Lifecycle telemetry used in-memory storage and generated private-CA certificates
with normal chain/hostname checks. The real timer ran with a test-only one-second
schedule; generated log padding exercised its size threshold. This does not
measure seven elapsed days or public traffic capacity.

## Regression and evidence

The full proxy regression passes route isolation, authentication, payload limits,
timeouts, TLS checks and byte equality for the compiled index and all three
initial JavaScript assets. Two earlier attempts failed because that test still
expected the removed Create React App `asset-manifest.json`; the second repeated
the failure after a guarded edit had not applied. Both outputs remain failed.
The corrected test reads script paths from the actual compiled HTML and checks
their served bytes without changing the build.

A separate native efsn/WSS/PostgreSQL/compiled-browser regression passes all four
browser checkpoints using the existing synthetic chain fixture. It exercises the
current proxy template, not the systemd lifecycle drill. No backup, real account
key or historical replay is used. Temporary services, certificates, log/state
directories and the disposable database were removed; no fixture process remains.

The [evidence bundle](evidence/restart-dashboard-proxy-lifecycle-2026-10-04/) contains
the run outputs, rendered units/configuration, source/runtime hashes, portable
dashboard patch, commit metadata and verifier. Preservation checks confirm all
1007 efsn source/module files, 546 compiled frontend files and the original
dashboard checkout are unchanged. No packages were installed and no services
were enabled at boot. Nothing was pushed or publicly deployed.

## Remaining acceptance

Select the actual host, public address/domain and certificate issuer/renewal
workflow. Rehearse full-chain/expiry checks, failed renewal alerts, activation
and recovery on that host, then boot startup and persistent logs across reboot.
Review resource budgets, production retry/log volume and delivered health/disk
notifications. nginx error logs may include query strings even though the access
format omits them; credentials must stay out of URLs.

The earlier [application journal probe limitation](restart-dashboard-supervision.md)
is still open; file-log rotation does not resolve it. The common deployment
manifest and exact-package acceptance are also still required. The
[consolidated plan](restart-plan.md) tracks those gates. The dashboard patch adds
`docs/proxy-lifecycle.md` as the detailed installation and recovery runbook.
