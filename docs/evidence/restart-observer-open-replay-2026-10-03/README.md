# Observer opening replay evidence

Baseline `3a760271`, 3 October 2026. The candidate changes only the observer's
`history.go` runtime source and adds `history_open_test.go`. See the
[report](../../restart-observer-open-replay.md) for the rationale and limitations.

## Contents and outcomes

- `baseline/` and `candidate/`: paired non-race history-cost samples, complete
  operation measurements, resource logs, archived implementation/benchmark
  source, source/binary hashes and runner copies. Both runs passed.
- `attempt-1/windows/`: observer and CLI suites, including opening-state
  regressions. Passed on Go 1.21.3, without race instrumentation.
- `attempt-1/linux/`: the same suites with race detection, followed by the
  two-node ordinary-mining mixed command and 512 KiB budget test using race
  binaries. Both passed; both child node exits passed.
- `attempt-2/comparison/`: baseline/candidate retained-fixture comparison.
  Three tests passed on both implementations; all six exported files are
  byte-identical. `baseline/overlay.json` substitutes the archived `history.go`
  and excludes the newly added regression file, without editing working source.
- `baseline/equivalence/`: retained failed initial comparison launch (exit 127,
  missing temporary executable). No test ran in that attempt. The corrected
  runner builds each executable immediately before using it.
- `verify.py` and `checks.json`: source identities, paired data sizes, medians,
  output equivalence, suite results, budget errors, export preservation and
  offline inventory agreement. Verification passed.

The paired reopen/status median at 1,000 prior snapshots is 1,550.73 ms baseline
and 739.60 ms candidate. Both retain 28,520,777 logical bytes after the extra
snapshot. Warm-cache timing and cumulative allocation reductions are not
whole-command latency, retained-memory or production capacity guarantees.

The race workload retained 38 events / 522,018 logical bytes within its 524,288
byte budget and finished at block 31. Snapshot/backfill budget rejections and
their retries preserve evidence and leave both offline inventories readable.
Its inherited `result.json` field `RuntimeChanges: false` describes the reused
scenario, not this candidate's observer diff. It must not be cited as evidence
that the observer implementation was unchanged; source manifests record the
change. Node and consensus sources were unchanged in this work.

## Reproduction

Run the verifier from the repository using an installed Python 3:

```powershell
python docs/evidence/restart-observer-open-replay-2026-10-03/verify.py
```

The verifier expects the candidate source version recorded in this bundle. A
future implementation change correctly fails that identity check; use the
candidate commit when reproducing these results. Do not overwrite old captures.
For fresh suite/workload and equivalence runs, use unused attempt names:

```powershell
pwsh -File docs/evidence/restart-observer-open-replay-2026-10-03/run-windows.ps1 -Attempt attempt-3
wsl -d FusionRehearsal -u root -- unshare --net -- bash /mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-observer-open-replay-2026-10-03/run-linux.sh attempt-3
wsl -d FusionRehearsal -u root -- unshare --net -- bash /mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-observer-open-replay-2026-10-03/compare-linux.sh attempt-3
```

These runners use the existing Windows/WSL Go 1.21.3 toolchains and offline module
caches. Linux builds use the `rehearsal` account. The enclosing network namespace
has only loopback; the mixed workload uses disposable databases and public test
keys 1 and 2. No real backup or production key is required.

`measure-linux.sh baseline` was run before the runtime edit and
`measure-linux.sh candidate` after it. The script refuses existing result
directories. To repeat the pair, use a fresh evidence destination and the exact
respective source manifests (baseline checkout or equivalent compiler overlay).
Merely running the current source with the label `baseline` does not recreate the
old implementation. The archived runner copies, source files and compiler
overlay document how each retained result was produced. The verifier remains
bound to the original retained paths, not a newly named attempt.
