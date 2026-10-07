# F11 rollback compatibility and correction

7 October 2026. The [candidate](../restart-state-rollback-candidate-2026-10-07/README.md)
passes the bounded phase-3 checks in the
[qualification specification](../../restart-state-rollback-qualification.md).
The runtime diff is unchanged and remains unselected. These are in-memory
state/EVM observations; finalization, persistence and accepted-block effects
remain phase 4. No production activation height is selected.

## Results

| Run | Result |
| --- | --- |
| Selected P1–P17+B1+D1 baseline, new matrix | Three top-level tests / 50 subtests pass the stated legacy observations, including the known defects. This does not mean the baseline defects are fixed. |
| Same source plus F11 candidate, new matrix | Three top-level tests / 50 subtests pass the pre-activation compatibility and active correction expectations. |
| Original follow-up EVM regression, baseline | Three controls pass; absent ordinary-entry case retains its known failure. |
| Original follow-up EVM regression, candidate disabled | Same three controls and same known failure. |
| Original follow-up EVM regression, candidate active | All four cases pass with the original assertions unchanged. |

`verify.py` compares all 50 recorded observations between selections. Forty-five
are identical. The only five differences are the intended absent-entry
correction: the raw direct-state case with the fix enabled, and the EVM case
at/after the fixture boundary under Berlin and London gas rules. Within those
EVM observations, only ordinary-balance availability/contents differ; every
other recorded field is identical.

The raw test inspects `BalancesHash`, `BalancesVal`, time-lock arrays and the
deletion flag. With the rule disabled, the absent-entry case retains an extra
nil ordinary entry. Enabled, its arrays match the independently specified
pre-snapshot contents. Existing zero and nonzero ordinary entries are distinct
controls and remain correct in both selections.

The EVM matrix has 40 cases: disabled/before/at/after × Berlin/London × five
success/revert and asset-entry controls. It separately observes ordinary
balances, the time lock, beneficiary balances/time locks, an unrelated account,
child code/storage/nonce, the deletion flag, call output, gas and refund.
Each fallible field read has its own observation with availability/panic status;
an unavailable read is never presented as observed empty contents. Public
balance maps still omit zero entries; the separate raw fixture supplies the
structural assertion.

Successful calls retain the deletion marker and the expected FSN transfer;
reverting calls restore the marker and transfers. The successful marker is not
a persisted-deletion assertion. The beneficiary's FSN time lock moves only in
the system-asset control; the other account stays unchanged. Successful
deletion still clears the child's other assets as the inherited implementation
does; this candidate does not redesign asset-transfer semantics.

F11-b is explicitly unchanged: four direct-API cases compare disabled/enabled
deletion with and without a prior ordinary entry. The empty-entry account keeps
its deletion flag after rollback in both selections. These are characterizations
of the retained defect, not passing correctness regressions for F11-b. Its
scoped disposition and independent review remain open.

## Independent gas and state expectations

The fixture uses fixed balances, nonces, storage and future time-lock intervals.
Expected restored state is declared from those fixture inputs, not copied from
observed runtime output. The beneficiary starts with 3 base units of FSN and receives
the child's 11 only on success; its matching lock value 7 becomes 12 only when
the child's system-asset lock value 5 transfers. The unrelated account retains
ordinary value 17 and lock value 9.

`gas-vector.json` retains the arithmetic checked independently of Go execution:
seven pre-CALL pushes cost 21; warm CALL costs 100; child PUSH costs 3;
SELFDESTRUCT costs 5,000; three subsequent pushes cost 9; MSTORE costs 3;
one-word memory expansion costs 3; RETURN/REVERT adds zero. Both target accounts
are warmed and the beneficiary already exists, so no cold-access or creation
charge applies. Total is 5,139, leaving 194,861 from 200,000. These costs follow
the selected `params/protocol_params.go`, `core/vm/jump_table.go`,
`core/vm/eips.go` and `core/vm/operations_acl.go`, whose hashes are recorded.
An initial refund of 7 remains 7 after revert; successful Berlin deletion adds
24,000, while London adds none. All observations match these expectations.

## Inputs, adapters and limits

The matrix uses fixture height 15,130,081 solely to test an inclusive boundary
after the existing Fusion forks; it is not an activation proposal. Candidate
configuration adapters set this test height or leave the schedule nil. Baseline
adapters keep its unchanged configuration/API. Both use the same matrix source
and literal assertions. A test-only environment switch enables the candidate
schedule for the original regression; its fixture bytes are unchanged.

The modernized state fixtures from the earlier state-test bundle allow package
compilation. `test-api-adaptation.patch` changes only three direct calls in two
of those test files to pass `false` to the candidate's explicit API. Their
original assertions remain intact; those legacy tests are not included in the
new matrix's passing count. The original EVM regression is separately selected
and executed from the unchanged follow-up bundle. No full state-suite pass is
claimed, and the text dependency experiment is not part of this comparison.

`qualification/` contains all five commands, overlays, environments, input
hashes and logs. Expected exit 1 runs are accepted only after verifying the
specific original failing subtest and its three passing controls; a compilation
failure cannot satisfy that check. There were no unexpected test failures in
this run. Prior evidence remains immutable.

The runner checks previous manifests, selected source hashes and the existing
30 GiB Linux / 60 GiB D: capacity floors. It uses Go 1.27.1, race detection, two
workers, a two-minute test timeout and seven-minute outer limit per command.
A private network namespace is created before dropping to UID 1000; distinct
parent/child IDs and only a down loopback link are recorded. Cached dependencies
and offline flags are additional limits. All state is synthetic and in memory;
no backup database, keys, RPC endpoint, peer or bulk disk job is involved.

`verification.json` records the evidence checks and exact cross-selection
comparison. `SHA256SUMS` covers this bundle. Keep its outputs intact and use
fresh paths for another run. F11 remains open pending phase 4, historical
compatibility, the recorded startup/F11-b dispositions and independent consensus
review. F12 and final launch rehearsal are separate outstanding items.
