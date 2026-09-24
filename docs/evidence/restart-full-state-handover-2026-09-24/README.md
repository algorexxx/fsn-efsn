# Full-state handover evidence

See [the report](../../restart-full-state-handover.md). Baseline is `dea2d09` plus
the committed test changes identified by the executable/source hashes here.
All funding/signing substitutions use public keys 1 and 2 on disposable copies.

`run-windows.ps1` verifies the preserved-state manifest, creates two new copies
on C:, then runs prepare/produce, two worker processes, independent import and
two cold complete-state traversals. `check-linux.sh` uses separate C:-backed
copies in a private network namespace, executing the same transition/worker
restart/import with the race detector. Both retain the original 256-header
execution context and body from the preceding full-state rehearsal.

`windows-blocks` and `linux-blocks` retain each run's ten RLP blocks and JSON
ledgers. Their first six constructed blocks agree byte-for-byte. Subsequent
worker blocks use runtime timestamps and differ by platform. The corresponding
`*-fixture.json` and `*-handover.json` files record the two-stage synthetic
substitutions; they do not claim valid production parent seals.

The Windows retained execution binary is `tmp/full-state-handover-v2-tests.exe`.
`windows-binary-sha256.txt` and the per-phase logs identify it. The retained
accounting and final focused binaries are `tmp/full-state-handover-audit-tests.exe`
and `tmp/full-state-handover-final-tests.exe`. Build commands use the cached Go
runtime under `tmp/restart-runtime`, `CGO_ENABLED=0`, `GOMAXPROCS=2`,
`GOTOOLCHAIN=local`, `GOPROXY=off`, and:

```text
go test -p=2 -mod=readonly -c -o tmp/full-state-handover-v2-tests.exe ./tests/restart
```

The test selector for execution is `^TestFullStateHandover$`, run from
`tests/restart` with `-test.v -test.timeout=20m`. The audit uses
`FUSION_RESTART_HANDOVER_AUDIT` for the ledger directory and
`FUSION_RESTART_HANDOVER_BLOCKS` for block artifacts. It never opens a database.
`windows-accounting.txt` checks Windows artifacts. `linux-accounting-race.txt`
checks Linux artifacts twice; `linux-final-focused-race.txt` independently
checks Windows artifacts twice and the final missing-purchase cases.
`check-linux-final.sh` records the final focused procedure.

The worker uses a test backend around the real chain, pool, miner, wallet and
automatic controller. No HTTP/IPC/P2P service is claimed for this test. It starts
after the constructed recovery blocks, not directly at the historical head.
Original pool/journal contents are absent from the compact state export and
remain a separate launch concern. No production code changes were made.

Two investigation failures are deliberately retained:

- `failed-prepare.txt`, `failed-prepare-fixture.go.txt` and
  `failed-binary-sha256.txt`: an initial fixture called `GetTimeLockBalance` on
  the donation account. That getter inserts an empty asset entry in memory;
  the later fixture debit made it persist. The strict difference audit rejected
  the extra field before execution. The fixture now inspects
  `GetAllTimeLockBalances`, which does not insert an entry. The failed disposable
  copies remain under `tmp/full-state-handover-{producer,verifier}`; successful
  copies use `tmp/full-state-handover-v2-{producer,verifier}`. Original state
  was not changed. This is a corrected test-fixture issue, not a production fix.
- `initial-cleanup-expectation.txt` and `.go.txt`: the first characterization
  expected both missing jump and missing cleanup purchases to advance to a
  stranded head. Inspection/test showed that `UpdateTickets` rejects empty
  cleanup, whereas the jump accepts its still-stored expired tickets. Final
  tests assert these distinct outcomes. The initial executable is retained as
  `tmp/full-state-handover-cleanup-tests.exe`.

`identities.json` identifies retained binaries and final sources. Raw Windows
CRLF and Git-archive LF hashes can differ for unchanged baseline files; the
Linux identity files record the exact bytes compiled there. `source-preserved.txt`
checks all 230 original export files again after execution. `SHA256SUMS` covers
all archived evidence except itself.
