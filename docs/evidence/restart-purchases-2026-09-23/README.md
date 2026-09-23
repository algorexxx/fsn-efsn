# Purchase-controller evidence

Directory date is UTC. Work crossed midnight in Europe/Stockholm.
Source base is `b830599` plus the changes identified in `source-sha256.txt`.
Final results: full Linux node build passed; `linux-race-final-3.txt` passed
all three ordinary restart-suite repetitions without a reported race;
`windows-final.txt` passed the ordinary suite in 91.146 seconds.
The full implementation and limits are in
[the controller report](../../restart-purchase-controller.md).

`build-info.txt` records Go 1.21.3, the built Linux node version, and SHA-256
digests of the node and final race-enabled test executable. Build commands in
the separate `/home/rehearsal/fsn-efsn-purchases` export:

```sh
CGO_ENABLED=1 GOMAXPROCS=2 GOTOOLCHAIN=local GOPROXY=off go build -p=2 -mod=readonly -o /home/rehearsal/bin/efsn-purchases ./cmd/efsn
CGO_ENABLED=1 GOMAXPROCS=2 GOTOOLCHAIN=local GOPROXY=off go test -race -p=2 -mod=readonly -c -o /home/rehearsal/purchases-tests-final ./tests/restart
```

The Linux regression command runs as `rehearsal` in a new network namespace,
from that export's `tests/restart` directory:

```sh
/home/rehearsal/purchases-tests-final -test.v -test.count=3 -test.timeout=15m
```

`windows-final.txt` is the Windows amd64/CGO-disabled equivalent, using the
previously verified portable Go 1.21.3 runtime and existing local caches:

```powershell
go test ./tests/restart -v -count=1 -timeout=8m
```

Full-backup scans and replay are explicitly skipped in these synthetic runs.
Their unchanged baseline jobs run separately; these logs do not assert their
completion. The old miner package's baseline test compilation failure is
documented in the integrity investigation, so this is not a whole-repository
test-suite claim.

The `initial-*` logs retain the first seven-case recovery run and the earlier
matrix with an incorrect test hash-format expectation. That matrix failed
`TestAutoBuyRuntime` because its captured structured log used a byte-array hash
and the assertion expected hexadecimal; its recovery cases passed. The final
assertion uses the captured representation of the exact submitted hash, without
changing the controller or weakening the receipt-confirmation requirement.

No real key, preserved chaindata writer, public listener or public submission
was used. On-disk recovery cases use temporary LevelDB and pool journals with
the public synthetic key. The real miner case imports both produced blocks on
independent synthetic state after shutting down the producer.
