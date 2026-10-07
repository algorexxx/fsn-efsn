# State rollback investigation handoff

7 October 2026. Investigation branch: `codex/restart-investigation-wip`.
Saved investigation checkpoint: `e34f5c6e`.

## Purpose

Check that cancelling an operation restores the account state that existed
before that operation: ordinary balances, time-locked balances and whether the
account is marked for deletion. This concerns transaction execution state,
not chain reorganization, total difficulty or the restart anchor.

This investigation supports the minimal Fusion restart. No production fix,
consensus activation or change to the release selection has been made.

## What is established

The old state tests were adapted to the current Fusion APIs. The resulting
suite compiles. On both the selected D1 source and the experimental dependency
update, 15 top-level tests pass and three fail. The relevant runtime source
matches the upstream baseline.

The minimal state tests show that snapshot restoration can leave an account
deletion flag or an invalid ordinary balance entry. These findings are tracked
under F11 in the [release findings](restart-release-findings.md). Their full
transaction and historical implications remain unresolved.

## Files to read

- [Evidence report](evidence/restart-state-tests-2026-10-07/README.md): scope,
  independent expected values, source provenance, results and limitations.
- [Minimal state tests](../core/state/suicide_test.go): the completed direct
  state-API checks and control case.
- [Archived execution fixture](evidence/restart-state-tests-2026-10-07/verified/suicide_evm_test.go):
  the unfinished follow-up. It is preserved as evidence and is not currently
  included in the active test package.
- [Original baseline output](evidence/restart-state-tests-2026-10-07/verified/baseline.txt)
  and [experimental output](evidence/restart-state-tests-2026-10-07/verified/candidate.txt):
  retain the initial assertion error and subsequent incomplete execution.
- [Saved input and result index](evidence/restart-state-tests-2026-10-07/review.json):
  identifies exact overlays, source hashes and test outcomes.
- [Existing bounded runner](evidence/restart-state-tests-2026-10-07/run.sh):
  records the original environment and limits. Its output directories already
  exist; do not overwrite them or assume it resumes the unfinished fixture.

## Unfinished review

The execution fixture contains an observation mistake: the balance-list API
omits zero balances, whereas its initial expectation included one. The runtime
implementation establishes that API contract; an observed failing output must
not be copied into the expected result merely to make a test pass.

The follow-up also terminates before all assertions complete. Correcting the
observation and completing the local check remain pending. The required
assertion is that cancelling the parent operation restores the original child
account state. A successful-operation control must remain in place.

Do not describe the existing evidence as a completed passing execution test,
an accepted-block reproduction, a historical occurrence, or a deployed-node
impact demonstration. Those claims have not been established.

## Environment and boundaries

The earlier checks used synthetic addresses and amounts, an in-memory database,
the saved Linux source selections, offline cached dependencies, two workers,
race detection and a private network namespace. No real wallet key, public
peer or blockchain backup was used. No new large disk workload is needed for
reviewing this checkpoint.

Keep production behavior unchanged while deciding the finding's disposition.
Any eventual runtime correction needs historical compatibility and an explicit
activation decision, followed by independent consensus review.

## Why this handoff stops here

The user repeatedly reported a product content restriction during attempts to
continue. No further test execution occurred on the latest retry. This document
preserves the status and existing evidence; it adds no new reproduction
procedure. Detailed test continuation remains unfinished. The original logs
and fixtures have not been altered to hide failures or imply acceptance.
