# Synthetic restart investigation

These tests cover the restart investigation and the first narrow corrections,
not a complete mainnet restart implementation. The unchanged characterization
baseline is `d82a229`; current expectations require successful ticket
reconstruction and an error instead of a missing-ancestor panic. See
[the correction report](../../docs/restart-corrections.md). Run from the repository root:

```powershell
$env:CGO_ENABLED = '0'
go test ./tests/restart -v -count=1 -timeout=8m
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
multi-process, cross-platform block-exchange, or network-sync rehearsal. The ticket cache is
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
run. It now requires an initial attempt and an automatic retry of the identical
signed transaction after a submission failure, followed by receipt confirmation
and a successful head-triggered purchase. Each mined block is imported by another
in-memory chain. See [the controller report](../../docs/restart-purchase-controller.md)
for behavior, adapter limitations and remaining failure cases. The older
[runtime report](../../docs/restart-autobuy-experiment.md) records the reproduced
baseline stalls. No HTTP or P2P listener starts.

`TestSubmittedTicketReplacementAllowsExplicitRetry` requires the manual purchase
RPC to use the next pool nonce after a transfer replaces the pending purchase.
`TestAutomaticPurchaseRecovery` tests disabled states, wallet/estimator/funding
recovery, clean LevelDB/journal reopen with a locked wallet, conflicting purchases,
nonce gaps, controlled same-height canonical replacement and corrupt saved data.
It uses separate child processes, real temporary on-disk databases, and a mining
state adapter. Other owners receive synthetic perpetual tickets in these cases
so a transfer-only block can be constructed. A full race run with three
repetitions needs a longer timeout, for example `-race -count=3 -timeout=15m`.

`TestRestartAnchorEntryPointsCharacterization` runs nine child-process cases
against the existing client. It reproduces heavier-fork replacement and legacy
checkpoint gaps across stored forks, headers, receipts, fast-sync head commit,
startup/configuration ordering and expanded raw-body validation shortcuts. Its passing assertions
describe unsafe existing behavior, not an implemented anchor. See
[the entry-point report](../../docs/restart-anchor-investigation.md). These cases
use synthetic branches and checkpoint identities, never production anchor values.

## Results and expectations

- Present-day production from the expired seed tickets is rejected by import.
- A historical refund funds a long-lived purchase; eight bridge/replenishment
  blocks import successfully with matching commitments.
- Missing-state reconstruction of the time-jump block and the subsequent
  cleanup block succeeds, preserving direct-state header and ticket selection.
- The three synthetic expiry-boundary cases also require successful
  reconstruction. The old mismatch is retained in the baseline evidence.
- A missing ancestor header during reconstruction returns
  `consensus.ErrUnknownAncestor`; a panic fails the test.
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

The following overlay commands are historical reproduction instructions for a
separate checkout of `d82a229`, before the corrections. They are not applicable
to current source. With the same Go environment configured:

```powershell
./tests/restart/run-parent-time-experiment.ps1 -Go go
```

Pass an absolute path to `go.exe` when using the portable compiler. The script
writes two compiler-overlay copies under ignored `tmp`, substitutes parent-time
cleanup, and changes only the reconstruction success expectation. It does not
edit production source. The missing-ancestor panic remains expected in this
experiment; the proposed cleanup change does not repair that separate defect.

Linux/CGO results and race-detector findings are recorded in
[the Linux investigation](../../docs/restart-linux-investigation.md). With the
Linux compiler and CGO prerequisites configured, the portable overlay runners are:

```bash
python3 tests/restart/run-parent-time-experiment.py --go go
CGO_ENABLED=1 python3 tests/restart/run-receipt-copy-experiment.py --go go
```

On that baseline, the receipt-copy experiment runs the auto-buy scenario three times under the
race detector with a temporary receipt-log ownership correction. Unchanged
production code fails that scenario. The verifier now imports both blocks after
the producer is closed, avoiding concurrent two-chain global-header access in
the fixture while retaining independent execution checks.

`TestPreservedBackupReadOnly` is skipped in ordinary runs. It requires
`FUSION_RESTART_CHAINDATA` to name a checksum-verified disposable copy of the
observed LevelDB-only backup. Compile the tests first, then run only this probe
in a network namespace with the copy mounted read-only. It checks the recorded
head/account/ticket observations and selected block/receipt commitments. It
does not run a node, sign blocks, traverse every state node, or replay history.

## Complete integrity and replay probes

`TestPreservedStateIntegrity`, `TestPreservedHistoryIntegrity` and
`TestPreservedTicketReconstruction` additionally require
`FUSION_RESTART_FULL_AUDIT=1`. Compile first and run the resulting test binary
with no network and the verified source mounted read-only. The first two traverse
reachable state and canonical history respectively; the third validates actual
recent headers with direct state and forced missing-state reconstruction.
The ordinary suite tests the scanners against deliberate database corruption.

On Linux, `TestPreservedHistoryReplay` requires an absolute, nonexistent
`FUSION_RESTART_REPLAY_DIR`, a height in `FUSION_RESTART_REPLAY_END`, and the
Windows drive mount in `FUSION_RESTART_HOST_STORAGE` (for example `/mnt/d`).
The output parent must already exist. It executes canonical blocks into a new
database with the original checkpoint behavior and stops on an import error,
unexpected head, or insufficient disk reserve. Source and output must be separate.
Use a bounded pilot before choosing a full replay layout. Existing targets are
rejected by default. `FUSION_RESTART_REPLAY_RESUME=1` requires a matching identity
manifest from the same retained executable, then verifies the target head and
available state read-only before reopening it writable. Older pilots without
that manifest cannot be automatically resumed. Never run two writers.
`FUSION_RESTART_REPLAY_STOP_FILE` names an optional file whose existence triggers
a controlled failure and normal cleanup at the next batch boundary. A timeout
or forced process/WSL termination does not guarantee that cleanup.

See [the integrity/replay report](../../docs/restart-integrity-investigation.md)
for measured results, limits and evidence. Successful structural checks and
checkpoint-assisted execution are not full independent consensus verification.
