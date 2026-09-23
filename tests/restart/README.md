# Synthetic restart investigation

These are characterization tests against unchanged Fusion production code, not a
mainnet restart implementation. Run from the repository root:

```powershell
$env:CGO_ENABLED = '0'
go test ./tests/restart -v -count=1 -timeout=90s
```

The recorded run used portable Go 1.21.3 on Windows amd64. Its archive SHA-256
was checked against the [official Go releases](https://go.dev/dl/):
`27c8daf157493f288d42a6f38debc6a2cb391f6543139eba9152fceca0be2a10`.
This reproduces the recovery-era compiler version; it is not a recommendation for
a production release toolchain. The local runtime and caches live under ignored
`tmp/restart-runtime`, with no machine-wide installation or PATH change.

## Fixture limits

The fixture reads the saved public RPC observations in
`docs/evidence/restart-2026-09-23/responses.json`. It uses the actual recorded
ticket lifetimes/counts and the investigated owner's liquid/time-lock balances.
It substitutes a public synthetic key for that owner's address and inserts a
synthetic parent state at the observed height. Other owners' full account states
are not present. RPC's ticket map is sorted to obtain deterministic fixture
storage; its ordering is not asserted to reproduce the original ticket blob.

The seed parent and genesis are test scaffolding, not replayed mainnet history.
The source chain rules and activation heights are retained. No real staking key,
live database, network connection, or RPC submission is used by these tests.

The bridge test uses two independent in-memory databases, in one process. Signed
blocks are RLP round-tripped to clear cached selection fields, then passed to
`InsertChain` for header, body, and state validation. Both imports execute their
own transactions and reproduce the block's commitments. This is not yet a
multi-process, multi-platform, or network-sync rehearsal. The ticket cache is
process-global, so the tests are deliberately not parallel.

Missing-state tests evict the global ticket cache and wrap the state database so
opening specified roots fails. Ten cases cover bridge steps 1–4 with one through
four consecutive unavailable states, falling back as far as the seed state.
Three expiry-boundary cases deliberately replace the other owners' ticket
lifetimes with synthetic lifetimes ending one second before, exactly at, or one
second after the first historical successor. These altered lifetimes are not
observations about mainnet. A separate missing-header wrapper exercises a
reconstruction error path without deleting data.

The focused purchase tests call the real RPC argument builder through a minimal in-memory
backend, sign with the public test key, and call the real transaction pool.
They do not exercise a JSON-RPC transport, wallet unlock, gas estimation, or the
auto-buy goroutine. The successful purchase is also executed and imported, and
its ticket existence is checked. Pool tests use `TimeLockForever` as the explicit
long-ticket end so they do not age out at the experiment's October 2026 date;
this is a test input, not a recommended production expiry. The production pool
reads its actual wall clock; these cases require a clock after November 2025.
The operating-system clock and production clock code are not changed.

`TestAutoBuyRuntime` adds a child-process experiment with the real miner, auto-buy
loop, gas estimator, temporary test-key keystore, and transaction pool. It runs
for roughly 25 seconds. Its setup uses a jump one hour before the actual clock
and perpetual setup tickets; mined timestamps and transaction hashes vary per
run. It reproduces empty-pool startup and a submission-failure stall, then proves
an explicit retry restores mining and head-triggered auto-buy continues. Each
mined block is imported by another in-memory chain. See
[the runtime report](../../docs/restart-autobuy-experiment.md) for bounded timing,
adapter limitations, and remaining failure cases. No HTTP or P2P listener starts.

## Results and expectations

- Present-day production from the expired seed tickets is rejected by import.
- A historical refund funds a long-lived purchase; eight bridge/replenishment
  blocks import successfully with matching commitments.
- Missing-state reconstruction of the time-jump block returns
  `AddCachedTickets: hash mismatch` under the unchanged code. This test passes
  when it reproduces the defect; it is not a test that restart safety passes.
- Reconstruction after the subsequent cleanup block succeeds.
- The same mismatch occurs at a synthetic historical expiry boundary. A large
  jump is sufficient but not necessary to expose it.
- A missing ancestor header during reconstruction causes a nil-pointer panic.
  The characterization test catches and expects that panic; a passing suite
  does not mean this defect has been fixed.
- Before the first refund, the pool accepts a long purchase that the RPC builder
  and execution reject for insufficient historical time-lock coverage. After
  the refund, construction, admission, execution, and import succeed.
- Default historical purchase arguments produce an already expired interval
  and fail local pool admission. Moving the start to the present day fails the
  existing old-parent-plus-three-hours constraint in both builder and pool.
- With only one ticket left, finalizing a block without a replacement purchase
  fails with `Next block doesn't have ticket, wait buy ticket`.

The expected 5,000 FSN coverage after the first selection refund comes from the
independent interval calculation saved in `historical-refund-coverage.json`.
The expiration and minimum-ticket error expectations come from the respective
explicit source guards. Other checks use imported block commitments as the
comparison between separately executed states; they are not independent golden
vectors for the entire state transition.

The model uses the same account to pay fees and receive the block fees/reward.
Its net liquid increment is therefore not a general prediction for other miners.
Replacement ticket expiry is at least 30 days after its purchase start; reusing
one fixed expiry indefinitely would eventually violate the existing rules.

See [the experiment report](../../docs/restart-bridge-experiment.md) for the
temporary parent-time reconstruction experiment and outstanding work.

To repeat that overlay experiment after the baseline run, with the same Go
environment configured:

```powershell
./tests/restart/run-parent-time-experiment.ps1 -Go go
```

Pass an absolute path to `go.exe` when using the portable compiler. The script
writes two compiler-overlay copies under ignored `tmp`, substitutes parent-time
cleanup, and changes only the reconstruction success expectation. It does not
edit production source. The missing-ancestor panic remains expected in this
experiment; the proposed cleanup change does not repair that separate defect.
