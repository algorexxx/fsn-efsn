# Dashboard proxy lifecycle evidence — 2026-10-04

Scope: isolated systemd/nginx/logrotate lifecycle checks with real dashboard
collector/API code and synthetic loopback telemetry, followed by separate proxy
and native efsn/WSS/PostgreSQL/browser regressions. No public deployment, real
account key, backup access or historical chain replay.

`baseline.json` records dashboard parent `83a35269b1a5b1db47563cefb2a6946ed4982608`,
768 tracked dashboard files, 1007 efsn source/module files and 546 compiled frontend
files. The candidate changes configuration, tests and documentation only.

## Results

| Directory | Result and scope |
| --- | --- |
| `run-1` | All eight proxy lifecycle checkpoints pass; runtime units, fixture certificates, logs/state and isolated journals removed |
| `proxy-1` | Failed: old test requests the removed CRA asset manifest; private fixture removed |
| `proxy-2` | Same failure, unchanged test hash: the guarded edit had failed before this repeat; private fixture removed |
| `proxy-3` | Full proxy contract regression passes with script paths read from the current compiled HTML; private fixture removed |
| `stationary-1` | Native synthetic efsn, WSS, PostgreSQL and four compiled Edge checkpoints pass; no browser errors or foreign requests |

`run-linux.py` renders the committed service/logrotate templates into unique
runtime units. It uses the existing `rehearsal` UID/GID 1000 in place of the
production account and a unique journal namespace. Fixture paths and the nginx
executable are substituted; no units are installed permanently or enabled.
The backend uses in-memory storage; the separate native regression uses PostgreSQL.

The timer has a test-only one-second activation instead of the candidate's
five-minute calendar. Padding pushes each log above 8 MiB. The drill checks
descriptor inodes after actual timer/service rotation, then forces eight further
rotations and checks compression, retention, owner/mode and preserved telemetry.
Certificate replacement uses an atomic directory selection and normal CA/hostname
verification. The intentional invalid pair produces an expected reload failure
while the old pair stays active. Worker/master failures are confined to fixture
processes. Final service state, paths and processes are checked after cleanup.

Raw stdout/stderr, rendered configuration, reporter events and small log archives
are retained. Large padded raw logs are omitted. Generated private keys and
credentials are never copied into evidence. `run-1/result.json` verifies absence
of its synthetic secret. `cleanup.json` confirms no remaining fixture processes,
removal of the native run's stopped disposable database and host-tool hashes.

The manifest failure needed only a test repair: validate each script path parsed
from `build/index.html`, read its expected bytes, then compare the HTTP response.
The first edit attempted CRLF matching against an LF file and stopped without
writing; the subsequent identical failed run is kept rather than discarded.
Linux Node syntax checks and the final regressions pass. A Windows sandbox Node
syntax attempt was unable to inspect `C:\Users\Peter` (EPERM); Linux was the
runtime used for acceptance.

## Reproduction and limits

The local harness requires root in `FusionRehearsal`, systemd/logrotate, the
existing reviewed Linux runtimes under `tmp`, the dashboard worktree/dependencies
and the existing `rehearsal` account. Run `run-linux.py run-N` inside that distro
with a new output directory. Existing evidence is never overwritten.
Windows-side `run-proxy.py proxy-N` and `run-wss.py stationary-N` reuse the earlier
accepted runners; the latter also needs the existing native efsn test binary,
PostgreSQL runtime and compiled-browser tooling. All certificates are local
fixtures, and system trust is unchanged. No download or large restore is needed.

`verify.py` checks checkpoint results, cleanup, captured hashes, unchanged build
and efsn files, preservation of the original dashboard checkout, retained failures
and the portable patch. Run it from Windows with Python and Windows Git after
capturing the candidate commit with `capture-commit.py`.

`dashboard-proxy-lifecycle.patch` and `commit.json` preserve the dashboard change
separately from this efsn repository. The verifier also checks that reversing the
patch is valid against the clean candidate worktree. Application/dependency code
and compiled artifacts remain unchanged.

This is local lifecycle acceptance, not public CA issuance/renewal, host reboot,
seven days of retention, production load sizing or alert delivery. The older
application journal probe's missing-tail/rate-limit uncertainty remains open.
See the [report](../../restart-dashboard-proxy-lifecycle.md) and
[consolidated plan](../../restart-plan.md).
