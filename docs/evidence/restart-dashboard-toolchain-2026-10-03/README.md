# Dashboard toolchain evidence

Started 2026-10-03; completed after midnight on 2026-10-04 Europe/Stockholm.
Start with `verification.json`, `commit.json` and the parent report
`../../restart-dashboard-toolchain.md`. `dashboard-toolchain.patch` applies
after dashboard commit `acd443ebae16251c76add282bd75a3877872a60d`.

Final dependency inputs are in that patch. `lint-gap-audit.stdout.txt` is the
final audit; `lint-gap-install.json` records the final clean installation.
`installed-final.json` checks its manifests. Earlier install/audit records
describe intermediate candidates, including the rejected ESLint 9 candidate.

`frontend-5` is the final test/build run. `frontend-4` produced the byte-identical
assets exercised by `browser-result.json` and `stationary-1`. `gate-checks.json`
records the configuration/lint controls and Oxlint's missed default export,
rejected by the additional ESLint check. `lint-migration.json` maps the original
rules; the committed config and report record scope/option compatibility.

The Python/PowerShell/JavaScript files are captured local investigation steps,
not a single replayable deployment script. They require the existing isolated
dashboard worktree, recorded runtimes and prior local fixtures. Some expect an
unused output directory or their preceding intermediate candidate. Commands
and failures are retained; use the final repository scripts for normal CI.
