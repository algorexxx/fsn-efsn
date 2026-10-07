# State rollback review — findings handoff

7 October 2026. Investigation branch: `codex/restart-investigation-wip`.
Review performed by Claude (Opus 4.8) continuing the handoff in
[restart-state-rollback-handoff.md](restart-state-rollback-handoff.md).
Tracked as F11 in [restart-release-findings.md](restart-release-findings.md).

This document records the completed state-rollback review in one place so Astra
can take over. No runtime/production code was changed. No consensus activation,
release-selection change, or historical claim is made here.

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

## Evidence files

- Completed EVM fixture:
  [evidence/restart-state-tests-2026-10-07/corrected/suicide_evm_test.go](evidence/restart-state-tests-2026-10-07/corrected/suicide_evm_test.go)
- Its run log:
  [evidence/restart-state-tests-2026-10-07/corrected/suicide_evm.txt](evidence/restart-state-tests-2026-10-07/corrected/suicide_evm.txt)
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
`*big.Int` ordinary-balance entry for every **non-system** time-locked asset
the account held.

The time-lock value itself survives only incidentally: the same loop also calls
the capital-S `stateObject.SetTimeLockBalance`, which journals a
`timeLockBalanceChange` that restores it. The `suicideChange` time-lock branch
is effectively dead code; its only real effect on revert is to corrupt ordinary
balances.

**Why system vs non-system differ:**
- System asset: already has an ordinary entry, and the ordinary-loop's own
  `suicideChange` reverts it back to `0` after the nil, so nothing broken
  survives.
- Non-system asset: no ordinary entry and no ordinary-loop `suicideChange`
  exists for it, so the nil persists. Later `CopyBalances` /
  `Balance(...).Sign()` nil-dereferences and **panics**. RLP
  (`writeBigIntPtr` → `0x80`) would instead silently commit a spurious zero.

**Reachability.** `opSelfdestruct` is the only production `Suicide` caller. A
contract that holds a time lock in a non-system asset and executes
`SELFDESTRUCT` inside a call frame that later reverts triggers this on rollback.

**Reproduction (corrected `TestSelfdestructParentRollback`):**

| Subtest | Outcome |
| --- | --- |
| `successful_child_and_parent` | PASS — child self-destructs, no false rollback |
| `reverted_system_time_lock` | PASS — revert fully restores the child |
| `reverted_other_asset_time_lock` | FAIL — nil-pointer panic + corrupt state |

```
suicide_evm_test.go:105: reading restored child state panicked; snapshot rollback left invalid account state: runtime error: invalid memory address or nil pointer dereference
--- FAIL: TestSelfdestructParentRollback/reverted_other_asset_time_lock
```

**Candidate correction (NOT applied):** add `isTimeLock: true` to the
`suicideChange` literal in the time-lock loop so `revert` restores via
`setTimeLockBalance` instead of injecting a nil ordinary balance. Must be gated
by historical-compatibility and explicit activation/consensus review before any
production change.

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

### Correction made to the earlier probe (observation mistake)

The earlier EVM fixture expected `{SystemAssetID:"0"}` from `GetAllBalances`
after rollback. `CopyBalances` omits entries whose value `Sign()==0` by
contract, so the correct expectation is an **empty map**. This was corrected by
asserting the true pre-snapshot state (empty map + restored time lock), not by
copying observed output to force a pass. Correcting it is what revealed that the
system-asset revert is actually clean and isolated the real defect to F11-a.

## Boundaries — what is NOT established

- Not an accepted-block reproduction.
- Not evidence the defect occurred on the historical chain.
- Not a demonstration of a running mainnet node crashing.
- No transaction/commit-level consensus impact proven; reproduced at the
  StateDB / EVM-`Call` level with an in-memory DB and synthetic inputs.

## Open items for Astra

1. Decide disposition of F11-a: whether to establish transaction/commit and
   accepted-block effects in an authorized testing context.
2. If correcting runtime behavior, specify the historical boundary and
   activation height before touching production code, then independent
   consensus review.
3. F11-b: confirm whether any production or RPC path marks a zero-entry account
   for deletion; if not, record as latent/direct-API-only.
4. Unchanged open items from the original handoff: F1 console/tracer/RPC
   coverage, F10 dependency/CI acceptance, the 3,600,000-block replay checkpoint.
