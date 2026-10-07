# State rollback follow-up for Opus 4.8

7 October 2026. Continue from `a0402a0b` on
`codex/restart-investigation-wip`. The earlier investigation checkpoint is
`e34f5c6e`. Read the global repository instructions before starting.

## Requested outcome

Address the four review gaps below in the existing local regression fixture
and its report. Return a precise account of what was observed, what remains
unverified, and the exact inputs needed to reproduce the recorded results.

The central state-rollback diagnosis is supported by the source and retained
evidence. This follow-up concerns test observations, claim accuracy and evidence
provenance. It does not authorize a production correction or close F11.

Keep this pass small: existing synthetic in-memory tests and documentation.
Do not expand it into public-node testing, block-import demonstrations,
historical replay, a consensus redesign or dashboard work. Follow the reviewing
tool's own access requirements and record any work that cannot be completed.

## Starting material

- [Your findings report](restart-state-rollback-findings.md).
- [Original handoff](restart-state-rollback-handoff.md).
- [Corrected fixture](evidence/restart-state-tests-2026-10-07/corrected/suicide_evm_test.go)
  and [its log](evidence/restart-state-tests-2026-10-07/corrected/suicide_evm.txt).
- [Earlier evidence report](evidence/restart-state-tests-2026-10-07/README.md),
  [input/result index](evidence/restart-state-tests-2026-10-07/review.json) and
  [minimal state tests](../core/state/suicide_test.go).
- [Release findings ledger](restart-release-findings.md), especially F11.

The read-only review verified all 55 entries in the existing evidence checksum
manifest and all seven runtime-source hashes in the earlier result index.
No tests were rerun during that review. The two new `corrected/` files are
committed, but are outside that older checksum manifest and result index.

## 1. Describe the affected condition precisely

The report currently presents the distinction as system versus non-system
assets. The relevant condition is whether an ordinary-balance entry already
exists for the same asset before the operation. An existing entry can contain
zero; absence and a zero-valued entry are different structural states.

Review the ordinary and time-lock journal loops in
[StateDB](../core/state/statedb.go), together with reverse journal processing in
[journal.go](../core/state/journal.go). Narrow the report's claim about every
non-system time-locked asset. Distinguish conclusions demonstrated by the
retained cases from conclusions inferred from source inspection. If an adjacent
control is needed to support that distinction, keep it within the same small
in-memory fixture.

Completion criterion: a reviewer can identify the relevant precondition without
assuming that all non-system assets lack ordinary-balance entries. Do not infer
general mainnet impact from the synthetic initial state.

## 2. Separate observation failure from account contents

`readRestoredChildState` catches a failed read, then sets both returned values
to nil. The caller continues comparing both values with the expectations. This
creates secondary mismatch messages from the helper's replacement values.
In particular, if the ordinary-balance read fails first, the time-lock read
never executes. Its later mismatch is not an observation of lost time locks.

Make the status of each observation explicit. Preserve the primary failure,
and prevent unavailable observations from being reported as actual account
contents. If the report makes a claim about a separately observable field,
obtain that observation independently or mark it unverified. Do not silently
skip assertions or turn an observation failure into a passing case.

Keep both existing controls and the independently justified empty-map
expectation. `CopyBalances` omits zero-valued entries, so this view cannot prove
that the raw account representation is identical to the original. Either
narrow the claim of "exact" or "full" restoration to the fields actually
checked, or rely on an appropriate separate structural assertion. The existing
direct-state fixture already provides relevant structural evidence.

Completion criterion: every diagnostic distinguishes a failed read, an actual
observed mismatch and an unavailable observation. Expected values remain based
on the declared initial state and API contract, not copied from failing output.

## 3. Keep serialization and database persistence separate

The sentence saying RLP "would instead silently commit a spurious zero"
overstates the demonstrated result. The nil-pointer encoding behavior can be
established from [rlp/encode.go](../rlp/encode.go). That alone does not show that
the account reaches database persistence. Journal rollback also changes dirty
tracking, and finalization selects which accounts are processed.

For this pass, qualify the sentence as an encoding observation and keep actual
transaction/commit, accepted-block and historical effects explicitly open.
Do not add a new persistence or block-level experiment simply to close this
wording issue. If persistence work is later proposed, describe its separate
scope before treating it as part of this evidence.

Completion criterion: the report consistently distinguishes source inference,
local execution observations, database persistence and chain-level effects.

## 4. Preserve complete provenance for the next bounded run

The corrected log supports its recorded control outcomes and failure, but the
exact overlay, executed command and contemporaneous environment records were
not retained beside it. Do not reconstruct missing historical metadata and
present it as if it was captured during that run.

For a new run, use a fresh evidence directory and retain:

- Exact fixture bytes and the patch from the preceding fixture.
- Exact overlay mappings and source-selection identities/hashes.
- Compiler identity, relevant build/environment settings and executed command.
- Network-isolation record, start/end timestamps, limits, output and exit code.
- An inventory/checksum manifest covering the new evidence files.
- Separate results for each source selection actually tested, including
  failures, unavailable assertions and skips.

The established Linux source trees are:

| Selection | Existing source directory |
| --- | --- |
| Selected D1 baseline | `/home/rehearsal/results/restart-release-jwt-2026-10-04/node` |
| Unselected text experiment | `/home/rehearsal/results/restart-release-text-2026-10-04/node` |

Verify those inputs before use. Apply test-only overlays; do not edit either
source tree. The investigation checkout contains additional excluded work and
must not be substituted for the selected release source.

Use the same corrected fixture against both selections for the before/after
comparison. If only one can be tested, say so and leave the other pending.
The existing runner records the established offline dependency settings,
two-worker limit, race detection, five-minute test timeout and seven-minute
outer limit. Retain the private network namespace and fresh capacity checks
(30 GiB Linux and 60 GiB D: free). Reuse cached dependencies and in-memory data;
no backup copy or large disk workload is needed.

The old runner's named output directories already exist. Preserve them and all
original logs unchanged. A small new runner or recorded command is sufficient;
do not build a new testing framework. Repeat only the affected bounded checks.

Completion criterion: the recorded outcomes can be attributed to exact inputs,
and the manifest clearly states which run it covers. Source-byte checks and
test results must remain separate claims.

## Documentation and return handoff

Update the findings report and add a concise dated follow-up to the F11 ledger.
Its table still calls the EVM probe incomplete while the later paragraph calls
the review completed; distinguish completion of a bounded observation from
closure of the release finding. Preserve earlier evidence as historical records.

Return one short report linked from this document or the original handoff:

- Which of the four gaps were addressed and the supporting file locations.
- The exact tests performed and their outcomes for each source selection.
- Remaining uncertainties, including unavailable observations and any access
  restriction that prevented completion.
- Whether production files or release inputs changed; they should remain
  unchanged for this pass.

Keep F11 open pending its runtime disposition, historical-compatibility decision
and independent consensus review. A proposed fix is not selected merely because
the local diagnosis is convincing. F1 console/tracer/RPC coverage, F10 dependency
and CI acceptance, and the 3,600,000-block baseline replay checkpoint remain
separate work items.
