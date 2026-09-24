# Offline signing evidence, 24 September 2026

Baseline: `0ad0136`. Scope and limitations are in
[restart-offline-signing.md](../../restart-offline-signing.md).

- `windows-unit-final.txt`: final journal/export checks and unsigned CLI build;
  symbolic-link creation is explicitly skipped for missing Windows privilege.
- `windows-integration-final.txt`: all three controlled blocks at each of three
  completed-operation process cuts; two uncertain cuts; path/lock/input/head
  refusal tests; existing guard, funding and journal-handover regressions.
- `linux-unit-final-race.txt` and `linux-integration-race.txt`: corresponding checks
  with race detection. Linux symbolic-link alias checks pass. Integration runs
  in a private network namespace. `linux-build.txt` is an empty successful build
  log, not a missing test result.
  `linux-unit-race.txt` retains the passing run before the Windows-only
  error-1314 handling adjustment; the final unit run checks the final sources.
- `check-windows.ps1`, `check-linux.sh`: reproduction using the existing offline
  Go 1.21.3 toolchains/caches, bounded concurrency and C: temporary databases.
  Windows path resolution needs access outside the restricted command sandbox.
  The scripts never open the preserved backup, compact full-state fixture or W:.
- `windows-unit-initial.txt`, `windows-path-diagnostic.txt` and
  `windows-workspace-temp.txt`: sandbox path-resolution failures in both the
  default and workspace temporary directories. The checks were retained and
  passed outside the sandbox in `windows-unit.txt`.
- `windows-integration-initial.txt`: the first passing process rehearsal, before
  the explicit disagreeing-head check was added.
- `windows-symlink-privilege.txt`: the test initially treated Windows error 1314
  as a generic permission error. It now recognizes precisely that missing
  capability as a skip; other errors still fail the test.
- `wsl-runuser-path.txt`: a direct WSL unit-check invocation could not locate
  `runuser`. Using `/usr/sbin/runuser` starts the final passing unit run. The
  reproduction script already resolves it through its normal Linux shell.

Only the two public synthetic private scalars are used. The working and verifier
databases contain small synthetic state, with a four-MiB initial logical-record
cap per copy. Tests close or kill only their own children. Completed operation
recovery uses no new signature; uncertain attempts remain refused.

`identities.json` records the baseline, source and binary hashes. The restart
binaries also contain the earlier, uncommitted snapshot-test sources recorded
there; those opt-in tests were not run by these commands. This is investigation
evidence, not a reproducible release-build attestation. `SHA256SUMS` covers every
other evidence file, and `.gitattributes` preserves their exact bytes.
