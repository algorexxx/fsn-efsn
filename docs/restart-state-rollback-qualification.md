# F11 candidate qualification specification

7 October 2026. Implements the remaining review steps in the
[disposition proposal](restart-state-rollback-disposition.md). The
[isolated candidate](evidence/restart-state-rollback-candidate-2026-10-07/README.md)
is unselected and has no production activation height. This specification
does not authorize deployment, real signing or tests against public peers.

## Inputs and execution limits

Use the recorded P1–P17+B1+D1 node/recovery trees and the matching candidate
application patches. Record hashes of every additional test/overlay and actual
compiler environment. Do not build the investigation branch as the release.
The text dependency experiment remains a separate, unselected change.

Use synthetic accounts and disposable memory/small local databases. Use the
existing toolchain/cache, two workers, a two-minute inner test timeout and a
seven-minute outer command limit. Keep the existing 30 GiB Linux / 60 GiB D:
free-space floors. This qualification requires no backup restore or historical
replay workload. Estimate any larger work separately under G1 before starting.

Use a fresh output directory per attempt, preserve failures, and stop the
phase on an unexpected result. Do not weaken an expectation to match the
candidate. If a legacy fixture cannot compile, record the exact omission and
port only the needed fixture against its actual API contract. Keep the original
failing regressions intact and give candidate versions separate provenance.

For local execution, use a verified private network namespace with cached
dependencies. Record the nonempty parent/child namespace IDs and link state;
offline Go flags alone do not establish isolation. Do not expose RPC or load
real wallet keys. The existing successful launcher demonstrates the mechanism.

## Phase 1 — configuration rules and command builds (complete)

The candidate parameter suite passes with race detection. It covers a missing
schedule or block number, the inclusive activation boundary, legacy-field
resolution, conflicting and invalid schedules, network identity, input-copy
isolation, compatibility errors including a zero rewind target, and serialized
configuration. Both candidate executables build. This establishes neither
startup database behavior nor correct state rollback.

## Phase 2 — startup and offline recovery integration (bounded checks complete)

The [integration evidence](evidence/restart-state-rollback-integration-2026-10-07/README.md)
passes five top-level tests and 33 subtests with race detection. Actual startup,
reader and approval-validation methods are exercised against disposable
databases. Rejections leave key/values unchanged and make no observed mutation
attempts. A LevelDB close/reopen retains the resolved schedule; this is within
one process, not a complete node-process restart. Full service restart remains
part of the final rehearsal.

The fixture registers an explicit synthetic genesis identity and restores the
network globals after each case. The separate real-default-genesis equality
probe fails on both selected baseline and candidate, now tracked as F12. Do not
describe these synthetic fresh-initialization cases as a mainnet genesis pass.
The inactive missing-header rejection is also retained for compatibility review.

The [CLI follow-up](evidence/restart-state-rollback-cli-2026-10-07/README.md)
passes four top-level tests and ten subtests through the actual command
dispatcher, report builder and prepare paths. Reports/approvals bind the
independently expected effective configuration; changed report schedules and
prior-policy checksums are rejected without output or chain key/value changes.
These are in-process CLI tests with a synthetic purchase and unsigned block,
not a production executable/signing rehearsal. Together with the earlier
approval validation, they complete the bounded configuration-binding checks.

**Next:** phase 4 supported calls, pending execution and tracing; the bounded
transaction and block results are recorded below. The startup compatibility
review, F12 disposition and
final service/production-artifact rehearsal remain open as stated above.

Use a synthetic schedule in each fixture, with explicit literal expectations
at its height minus one, height and height plus one. Mainnet defaults modified
by a fixture must be restored afterward; do not run such fixtures in parallel.

| Case | Required observation |
| --- | --- |
| Legacy configuration before activation | Node startup and offline reader resolve the same effective schedule. The offline reader leaves all stored bytes unchanged. A permitted node update persists the schedule and a cold restart retains it. |
| Missing or changed schedule at/after activation | Startup fails before a config write, head change or chain repair. Compare all keys/values and head markers before/after. Check the returned error does not enter the backend's automatic config-rewind branch. |
| Already matching schedule after activation | Node startup and recovery retain the same effective configuration; no artificial incompatibility is introduced. |
| Custom genesis/configuration and wrong identity | Recognized mainnet cannot bypass its release schedule. Another genesis with the same chain ID does not inherit mainnet rules. Valid custom schedules keep their stated semantics. |
| Missing configuration or header metadata | An active schedule with no stored configuration is rejected. Exercise the earlier header-height lookup introduced by the candidate, including inactive configurations; document/refine any unintended compatibility change. |
| Fresh database | Validation precedes genesis/config persistence; invalid mainnet schedule input produces no partial initialization. |
| Activation at height one in a custom fixture | The zero rewind target does not bypass this rule's rejection. This is a test boundary, not a proposed mainnet activation. |
| Recovery approval binding | Independently calculate the JSON checksum for a synthetic effective configuration. Both report construction and approval validation use it; an approval for a different schedule is rejected before the test signer is invoked. No real signing. |

The fixture should exercise the actual startup/reader/approval methods. Passing
the parameter helper alone cannot satisfy these integration assertions. Use
test doubles only at the external signer boundary, with a call counter for
the rejection case.

## Phase 3 — rollback compatibility and correction (bounded checks complete)

The [execution evidence](evidence/restart-state-rollback-execution-2026-10-07/README.md)
passes three top-level tests and 50 subtests on each of the selected baseline
and candidate. Disabled/pre-activation observations match. At/after activation,
the candidate restores the absent-entry case's raw ordinary-balance structure;
time locks, deletion flags, beneficiary transfers, other recorded account fields,
gas and refunds retain their independently specified results. The same checks
cover Berlin and London refund rules. This is an in-memory EVM/direct-state
result, not transaction finalization, physical deletion or persistence.

The original follow-up EVM fixture is also rerun unchanged: baseline and
disabled candidate retain the single absent-entry failure and three passing
controls; the active candidate passes all four. F11-b's empty-entry deletion
flag defect remains explicitly observed in both selections. These results
do not imply that the entire state suite passes or close F11's release hold.

Adapt the retained F11-a fixture and controls to the explicit rule parameter
without editing the original evidence. Compare disabled/pre-activation
behavior with the selected baseline, and active behavior with independently
specified pre-snapshot state. Read each field independently and preserve the
distinction between absent and zero ordinary-balance entries. Inspect raw
structure where that is the claim; public balance maps omit zero entries.

Check that gas/refund accounting, beneficiary transfers, successful deletion
and unrelated assets remain within their stated expectations. Use the existing
bounded cases and extend only for a changed path or a discovered discrepancy.
Keep F11-b classified separately: an F11-a correction is not a claim that the
zero-entry direct-API failure or the entire state suite now passes.

## Phase 4 — transaction and block boundary

**Transaction boundary complete within the stated fixture scope.** The
[persistence evidence](evidence/restart-state-rollback-persistence-v2-2026-10-07/README.md)
passes one top-level test and 16 subtests per selection. Actual transactions,
finalization, trie commit/flush, LevelDB close/reopen and a new state cache
establish that a child already pending from an earlier transaction can retain
the extra ordinary zero entry durably. A clean child's in-memory defect does
not persist in this fixture. Active correction changes only the expected
absent-entry observations and the dirty cases' roots; disabled/pre-activation
results match. Time locks, gas, receipts and transfers meet literal expectations.
The first failed attempt and its single nil-versus-empty-list expectation
correction are preserved. No runtime change was introduced by these tests.

**Block boundary complete within the stated fixture scope.** The
[block comparison](evidence/restart-state-rollback-block-v2-2026-10-07/README.md)
passes 16 cases per selection through Prepare, ApplyTransaction, DaTong.Finalize,
synthetic signing and serialized InsertChain into an independently seeded
database. Import and reopening each use a new process with an initially empty
ticket cache: 64 receiver processes total. Account state, canonical heads,
receipts/gas, fees/reward and ticket commitments match specified expectations.
Fourteen pairs have identical block bytes; only dirty absent-entry cases
at/after activation differ in account structure and state root. The failed
zero-base-fee attempt and exact fixture correction are retained.

The parent checkpoint is installed directly. These are accepted synthetic
descendants, not executed historical prefixes or a continuous activation-crossing
chain. The miner worker/Seal timer and mixed-version import were not exercised.
**Still open:** supported calls/pending/tracing, historical compatibility,
independent consensus review and final release/service rehearsal.

Establish finalization/commit outcomes separately from EVM-call observations.
Then establish the relevant supported block-processing outcomes, comparing
mining/import and cold reopening with independently justified state/receipt/gas
expectations. Document dirty-account handling explicitly. An RLP encoding
property or a successful read is insufficient evidence of persistence.

Check that calls, pending execution and supported historical tracing choose
the rules of the block being executed. Retain exact coverage exclusions under
F1 if an inherited tracer/RPC fixture remains unavailable. Do not label an
in-memory fixture as an accepted-block or historical-chain result.

## Exit criteria

Attach the precise candidate diff, fixture sources, manifests, environments,
commands, logs and failed attempts. Record each phase's result and remaining
uncertainty. Independent consensus review must assess those results, the
F11-b disposition and the eventual numeric schedule before selection.

Candidate historical compatibility remains under G1, with baseline replay
still at 3,600,000. Actual recovery artifacts, activation approval and final
rehearsal remain under G3/G8. Keep F11 open until these applicable boundaries
have evidence or an explicit reviewed disposition; configuration/integration
passes alone close none of them.
