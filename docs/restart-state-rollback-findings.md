# State rollback review — findings handoff

7 October 2026. Investigation branch: `codex/restart-investigation-wip`.
Review performed by Claude (Opus 4.8) continuing the handoff in
[restart-state-rollback-handoff.md](restart-state-rollback-handoff.md).
Tracked as F11 in [restart-release-findings.md](restart-release-findings.md).

This document records the completed state-rollback review in one place so Astra
can take over. No runtime/production code was changed. No consensus activation,
release-selection change, or historical claim is made here. The follow-up pass
requested in
[restart-state-rollback-followup-opus.md](restart-state-rollback-followup-opus.md)
is incorporated throughout and summarised in
[Follow-up return report](#follow-up-return-report).

## Scope

Verify that cancelling (reverting) an operation restores the account state that
existed before it: ordinary balances, time-locked balances, and the
account-deletion (`suicided`) flag. This is transaction-execution snapshot
state only — not chain reorg, total difficulty, or the restart anchor.

## How it was run

- Toolchain Go 1.27.1 (linux/amd64), inside the WSL `FusionRehearsal` distro.
- Immutable D1/baseline source tree
  `restart-release-jwt-2026-10-04/node`; runtime files unchanged, test files
  injected via `go test -overlay`.
- `-race -p=2 -count=1`, offline deps (`GOPROXY=off GOSUMDB=off
  GOFLAGS=-mod=readonly GOTOOLCHAIN=local`), `CGO_ENABLED=1`, synthetic
  addresses/amounts, in-memory database.
- No real wallet key, public peer, blockchain backup, or large disk workload.
- The follow-up re-run (below) was executed against **both** established
  selections — the D1 baseline (`restart-release-jwt-2026-10-04/node`) and the
  unselected text experiment (`restart-release-text-2026-10-04/node`), whose
  three relevant runtime files (`statedb.go`, `journal.go`, `state_object.go`)
  are byte-identical between the two trees. Results were identical, so the
  dependency selection introduces no behavioural difference here.
- Network-namespace isolation (`unshare -n`) is **not permitted** for the
  rehearsal user; the run used the distro default namespace. The offline flags
  make network access impossible regardless (cached modules only). This access
  limit is recorded in the run's `environment.txt`.

## Evidence files

Provenanced follow-up re-run (new, self-describing directory):

- Corrected/refined fixture:
  [evidence/restart-state-rollback-followup-2026-10-07/suicide_evm_test.go](evidence/restart-state-rollback-followup-2026-10-07/suicide_evm_test.go)
- Runner, environment and capacity record, patch vs the preceding fixture,
  per-selection overlays/source hashes/logs/exit codes/timestamps, and a
  checksum manifest: `evidence/restart-state-rollback-followup-2026-10-07/`
  (`run.sh`, `environment.txt`, `fixture-from-corrected.patch`,
  `d1/`, `text/`, `SHA256SUMS`).

Earlier phases (unchanged historical records):

- First completed EVM fixture + log:
  [evidence/restart-state-tests-2026-10-07/corrected/suicide_evm_test.go](evidence/restart-state-tests-2026-10-07/corrected/suicide_evm_test.go),
  [suicide_evm.txt](evidence/restart-state-tests-2026-10-07/corrected/suicide_evm.txt).
  Note: the exact overlay/command/environment for that first run were not
  retained beside it; the follow-up directory above carries the complete
  provenance. The first log is kept only as the earlier observation.
- Prior direct-API suite and logs: `evidence/restart-state-tests-2026-10-07/`
  (`qualified/`, `verified/`, `review.json`) — unchanged.
- Minimal direct-state tests: [../core/state/suicide_test.go](../core/state/suicide_test.go)

## Runtime code involved

- `StateDB.Suicide` — [../core/state/statedb.go:571](../core/state/statedb.go:571)
- `suicideChange` struct and `.revert` — [../core/state/journal.go:95](../core/state/journal.go:95),
  [../core/state/journal.go:174](../core/state/journal.go:174)
- `stateObject.CopyBalances` (zero-omission contract) —
  [../core/state/state_object.go:651](../core/state/state_object.go:651)
- `opSelfdestruct` (sole production caller of `Suicide`) —
  [../core/vm/instructions.go:828](../core/vm/instructions.go:828)

## Findings

### F11-a — Non-system time-locked asset corrupts ordinary balances on rollback (confirmed)

**Defect.** In `StateDB.Suicide` the time-lock journal loop
([statedb.go:588-599](../core/state/statedb.go:588)) builds a `suicideChange`
**without `isTimeLock: true`**; only `prevTimeLockBalance` is populated,
`prevbalance` stays nil. On rollback, `suicideChange.revert`
([journal.go:174-184](../core/state/journal.go:174)) therefore takes the
ordinary-balance branch and calls `setBalance(assetID, nil)`, injecting a nil
`*big.Int` ordinary-balance entry for the self-destructed asset.

**The precondition is structural, not system-ness** (corrected from the earlier
framing). The defect triggers only when the self-destructed time-locked asset
has **no ordinary-balance entry at the moment `Suicide` runs**. An absent entry
and a zero-valued entry are different structural states:

- If an ordinary entry for that asset already exists (even value `0`), the
  ordinary-balance loop emits its own `suicideChange` for the asset, which on
  revert runs after the time-lock loop's faulty entry and overwrites the nil
  with the prior value. No corruption survives.
- If no ordinary entry exists, the faulty `setBalance(asset, nil)` appends a new
  `BalancesHash`/`BalancesVal` pair with a nil value that nothing overwrites.
  Reading it later via `CopyBalances` / `Balance(...).Sign()` nil-dereferences
  and **panics**.

The system asset appears clean in the EVM path only *because* it always already
has an ordinary entry by the time `Suicide` runs — `opSelfdestruct` reads
`GetBalance(SystemAssetID, …)` first, which creates the entry. That is a
consequence of the precondition, not a property of the system asset.

**The time-lock value is restored and is not lost.** The same loop also calls
the capital-S `stateObject.SetTimeLockBalance`, which journals a
`timeLockBalanceChange` that restores the lock on revert. The `suicideChange`
time-lock branch (`isTimeLock`) is never set and is effectively dead code; its
only real effect on revert is the stray nil ordinary entry. The re-run observes
the restored time lock independently in every revert case, including the
corrupted one (see below).

*Demonstrated by the retained cases:* the stray nil ordinary entry and its read
panic; independent restoration of the time lock; the clean outcome when an
ordinary entry pre-exists. *Inferred from source inspection (not independently
re-demonstrated here):* that the `isTimeLock` branch is unreachable in all code
paths, and the per-field revert ordering in the general case.

**Reachability.** `opSelfdestruct` ([instructions.go:828](../core/vm/instructions.go:828))
is the only production `Suicide` caller. The trigger is a contract that holds a
time lock in an asset with no ordinary-balance entry and executes `SELFDESTRUCT`
inside a call frame that later reverts. This is a reachability condition on the
synthetic fixture; it is **not** a claim that such a contract exists on, or that
this has occurred on, any real chain.

**Scope of the balance check.** `GetAllBalances` → `CopyBalances`
([state_object.go:651](../core/state/state_object.go:651)) omits entries whose
value `Sign()==0`, so an empty-map result confirms only that no non-zero
ordinary balance is present after revert — it does **not** prove the raw account
representation (`BalancesHash`/`BalancesVal`) is identical to the original. The
raw-structure evidence (the extra entry surviving a revert) is the direct-state
fixture `TestSuicideSnapshotPreservesTimeLockAsset` in
[../core/state/suicide_test.go](../core/state/suicide_test.go); claims of
restoration here are narrowed to the fields actually read.

**Reproduction — provenanced re-run (both selections, identical results):**
evidence in
[evidence/restart-state-rollback-followup-2026-10-07/](evidence/restart-state-rollback-followup-2026-10-07/)
(`d1/` and `text/`).

| Subtest | Outcome |
| --- | --- |
| `successful_child_and_parent` | PASS — child self-destructs, no false rollback |
| `reverted_asset_without_ordinary_entry` | FAIL — restored ordinary-balance read unavailable (panic on nil entry); time lock independently observed as restored |
| `reverted_asset_with_zero_ordinary_entry` | PASS — pre-existing ordinary entry ⇒ clean revert |
| `reverted_system_asset_with_ordinary_entry` | PASS — clean because the asset already has an ordinary entry |

```
suicide_evm_test.go:121: restored ordinary-balance read unavailable: rollback left an invalid (nil) ordinary entry and GetAllBalances panicked: runtime error: invalid memory address or nil pointer dereference
suicide_evm_test.go:134: restored time lock independently observed as unchanged: [{"StartTime":2000000001,"EndTime":2000000100,"Value":"5"}]
--- FAIL: TestSelfdestructParentRollback/reverted_asset_without_ordinary_entry
--- PASS: TestSelfdestructParentRollback/reverted_asset_with_zero_ordinary_entry
--- PASS: TestSelfdestructParentRollback/reverted_system_asset_with_ordinary_entry
```

**Serialization vs persistence (encoding observation only).** `writeBigIntPtr`
([../rlp/encode.go:382](../rlp/encode.go:382)) encodes a nil `*big.Int` as
`0x80` (the empty/zero RLP string). This is an *encoding* property only. It does
**not** show the corrupted account reaches database persistence: journal
rollback also changes dirty tracking, and finalization selects which accounts
are processed. Actual transaction/commit, accepted-block and historical effects
remain explicitly open and were not tested in this pass.

**Candidate correction (NOT applied, not selected).** Adding `isTimeLock: true`
to the `suicideChange` literal in the time-lock loop would make `revert` restore
via `setTimeLockBalance` instead of injecting a nil ordinary balance. Recorded
as a diagnosis only; it must be gated by a historical-compatibility decision and
explicit activation/consensus review before any production change.

### F11-b — Deletion flag retained on a zero-entry account (confirmed, direct-API only)

**Defect.** `Suicide` appends its `suicideChange` entries *inside* the balance
loops. An account with no balance entries produces no `suicideChange` at all,
while `markSuicided()` still sets `suicided = true`. `RevertToSnapshot` then has
no journal record to clear the flag, so the account stays marked for deletion.

**Reachability.** Not reachable through `opSelfdestruct`: that path calls
`GetBalance(SystemAssetID, …)` before `Suicide`, which creates an ordinary
balance entry (via `balanceAssetIndex`), guaranteeing an ordinary-loop
`suicideChange` that reverts the flag. Confirmed by the control subtest
`system_balance_read_before_snapshot` (PASS) in
[../core/state/suicide_test.go](../core/state/suicide_test.go). Direct-API
callers that mark an empty account for deletion are the only exposure.

### Corrections made to the earlier probe

Two observation problems in the earlier fixture were corrected without relaxing
assertions or copying failing output into expectations:

1. **Zero-omission expectation.** The earlier fixture expected
   `{SystemAssetID:"0"}` from `GetAllBalances` after rollback. `CopyBalances`
   omits entries whose value `Sign()==0` by contract, so the correct expectation
   is an **empty map**. Asserting the true pre-snapshot state (empty map) is what
   isolated the real precondition in F11-a.
2. **Observation availability vs account contents.** The earlier helper caught a
   failed read and set *both* the balance and time-lock return values to nil,
   after which the caller compared both against expectations — producing a
   spurious "time lock = []" mismatch even though the time-lock read had never
   executed (the balance read panicked first). The refined fixture observes each
   field independently, each under its own recover, and distinguishes three
   states: a failed/unavailable read (the balance panic), an actual observed
   mismatch, and a genuinely observed value. With this separation the time lock
   is observed as **restored** in every revert case; the earlier "lost time
   lock" line was an artifact of the shared nil replacement, not an observation.

## Boundaries — what is NOT established

- Not an accepted-block reproduction.
- Not evidence the defect occurred on the historical chain.
- Not a demonstration of a running mainnet node crashing.
- No transaction/commit-level consensus impact proven; reproduced at the
  StateDB / EVM-`Call` level with an in-memory DB and synthetic inputs.

## Follow-up return report

Addresses the four gaps in
[restart-state-rollback-followup-opus.md](restart-state-rollback-followup-opus.md).

**Gaps addressed and where.**

1. *Precondition precision* — done. F11-a now states the trigger as the absence
   of an ordinary-balance entry for the self-destructed asset (not system vs
   non-system), distinguishes absent from zero-valued entries, and separates
   demonstrated from source-inferred conclusions. Two adjacent controls added in
   the same in-memory fixture:
   [suicide_evm_test.go](evidence/restart-state-rollback-followup-2026-10-07/suicide_evm_test.go).
2. *Observation vs account contents* — done. Per-field recover-guarded
   observation; failed reads reported as unavailable, never as contents; the
   empty-map expectation is retained but its scope narrowed (zeros omitted, so
   not a raw-structure claim), with the structural claim deferred to the
   direct-state fixture. See the "Corrections made to the earlier probe" and
   "Scope of the balance check" notes above.
3. *Serialization vs persistence* — done. The RLP line is qualified as an
   encoding observation from `rlp/encode.go`; commit/accepted-block/historical
   effects are kept explicitly open. No persistence experiment was added.
4. *Provenance* — done. Fresh directory
   `evidence/restart-state-rollback-followup-2026-10-07/` with `run.sh`,
   `environment.txt`, `fixture-from-corrected.patch`, per-selection `overlay.json`,
   `source-selection.txt` (runtime hashes), `test.txt`, `exit.txt`,
   `started.txt`/`finished.txt`, and a `SHA256SUMS` manifest of the new files.
   The earlier `corrected/` run is left as a historical record and is *not*
   back-filled with reconstructed metadata.

**Exact tests performed and outcomes (per selection).** One test,
`TestSelfdestructParentRollback` (4 subtests), run with
`-race -p=2 -count=1 -timeout=5m` under a 7m outer limit, Go 1.27.1, against
both trees. Both selections produced identical results and package exit code 1:

| Subtest | D1 baseline | Text experiment |
| --- | --- | --- |
| `successful_child_and_parent` | PASS | PASS |
| `reverted_asset_without_ordinary_entry` | FAIL (balance read unavailable; time lock restored) | FAIL (same) |
| `reverted_asset_with_zero_ordinary_entry` | PASS | PASS |
| `reverted_system_asset_with_ordinary_entry` | PASS | PASS |

**Remaining uncertainties / unavailable observations.**

- The restored raw ordinary-balance *array* for the failing case cannot be read
  through the external (`state_test`) package API without panicking; its
  structure is evidenced only indirectly, via the direct-state fixture. The
  external fixture records that field as an unavailable observation, not a value.
- No transaction/commit, accepted-block, historical-chain, or running-node
  effect was tested (out of scope for this pass).
- Access restriction: `unshare -n` is not permitted for the rehearsal user, so a
  private network namespace could not be created; recorded in `environment.txt`.
  Offline flags mean no network was used regardless.

**Did production files or release inputs change?** No. Only test fixtures,
runner scripts, evidence and documentation were added. Both source trees were
used read-only via overlay; the selected release (P1–P17+B1+D1) and the
unselected text update are unchanged.

## Open items for Astra

1. Decide disposition of F11-a: whether to establish transaction/commit and
   accepted-block effects in an authorized testing context. The local diagnosis
   being convincing does not select a fix.
2. If correcting runtime behavior, specify the historical boundary and
   activation height before touching production code, then independent
   consensus review.
3. F11-b: confirm whether any production or RPC path marks a zero-entry account
   for deletion; if not, record as latent/direct-API-only.
4. Unchanged open items from the original handoff: F1 console/tracer/RPC
   coverage, F10 dependency/CI acceptance, the 3,600,000-block replay checkpoint.

**F11 remains open.** This pass completes a bounded observation; it does not
close the release finding, which still awaits runtime disposition, a
historical-compatibility decision and independent consensus review.
