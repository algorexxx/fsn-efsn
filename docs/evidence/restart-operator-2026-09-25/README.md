# Operator command and credential-preflight evidence

25 September 2026, baseline `7c389ab` plus the source files in `identities.json`.
Only public private scalars 1 and 2 are encrypted/decrypted/signed. No real key,
complete-state fixture, W: data or replay checkpoint is opened.

From PowerShell in the repository root:

```powershell
& ./docs/evidence/restart-operator-2026-09-25/check-windows.ps1
wsl.exe --distribution FusionRehearsal --user root --exec bash /mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-operator-2026-09-25/check-linux.sh
```

Scripts use the existing Go 1.21.3 runtime/caches, offline modules and C: temporary
directories. Windows runs outside the Codex filesystem sandbox for the required
path checks. Linux unit tests, command and integration binaries use race detection;
integration processes and their command children run in an isolated network
namespace. Unit tests and sparse fixtures require no bulk database copy.

Initial passing logs are retained as `initial-*`. Review then added exact rebuild
of the complete report before approval, strict pipe-only password input and the
credential-lock/uncertain-attempt test. Final unprefixed logs and binary hashes
describe that final source. The first logs are historical observations, not an
attestation of the final binary.

The Windows symbolic-link unit case remains an explicit privilege-related skip;
Linux runs it. Helper-only tests skip outside their child-process invocations.
All selected top-level scenarios must pass. `write-identities.py` checks final
logs and records source Git blobs, binary hashes and checksums. Use a fresh
evidence directory for reproduction so the original records remain intact.

See [the operator report](../../restart-operator-workflow.md) for exact behavior,
supported input limits, invocation examples and remaining launch gates. These
records are not a reproducible release-build or power-loss durability proof.
