# Signing approval and handover quota evidence

25 September 2026. Baseline `cedde9f` plus the seven source files pinned in
`identities.json`. Tests use public private scalars 1 and 2 and temporary small
databases, capped at four MiB of initial logical chain records.

`check-windows.ps1` runs unit checks, compiles the restart test binary and runs
approved plus legacy offline process/refusal tests. Run it from PowerShell on
Windows outside the Codex filesystem sandbox, which blocks path-resolution
checks. `check-linux.sh` uses the existing FusionRehearsal Go 1.21.3 toolchain,
cached modules and C: temporary directories. Unit checks and the integration
binary use race detection; integration processes run in an isolated network
namespace. No W: access or additional complete-state copies are required.

```powershell
& ./docs/evidence/restart-signing-approval-2026-09-25/check-windows.ps1
wsl.exe --distribution FusionRehearsal --user root --exec bash /mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-signing-approval-2026-09-25/check-linux.sh
```

After the first passing runs, the unfinished-donation-advancement unit test was
added. The same `go test` unit commands were rerun; `windows-unit-final.txt` and
`linux-unit-final-race.txt` contain that final set. No production/integration
source changed after the recorded binary builds, and those integration checks
were not needlessly repeated. Initial unit logs remain as history. Repeating
the scripts against this commit includes the final unit test automatically;
use a fresh evidence directory to retain these original results.

The approved path covers completion-before-export, export-before-import and
import-before-acknowledgement for all three blocks, plus unfinished reservation
and signature-before-completion cuts on the first block. Tests require exact
reference RLP, no second signing callback, independent imports, cold ledgers and
chain-file preservation at signing-only cuts. Policy unit/refusal tests exercise
the additional approval and lifetime journal restrictions.

See [the report](../../restart-signing-approval.md) for the trust boundary and
remaining operator/key-adapter work. This evidence does not repeat the earlier
complete-state rehearsal or establish a reproducible release build.
