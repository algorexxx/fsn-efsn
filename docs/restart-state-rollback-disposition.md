# F11 disposition proposal

7 October 2026. Source review at `12eb2f34` on
`codex/restart-investigation-wip`, following the evidence in `92c3e634` and the
[corrected findings](restart-state-rollback-findings.md). This is a proposal,
not a selected runtime change, activation schedule or release waiver.

**Recommendation:** qualify a narrow, block-height-gated correction for F11-a.
Preserve the inherited execution path before activation. Keep F11-b separately
classified as a direct-state-API defect in the inspected production source.
F11 stays open until the candidate or an explicit alternative disposition has
the evidence and independent review below.

## Decision and evidence limits

The retained tests establish an in-memory rollback defect when a time-locked
asset lacks an ordinary-balance entry. They independently observe the time
lock as restored. The subsequent [transaction-persistence check](evidence/restart-state-rollback-persistence-v2-2026-10-07/README.md)
establishes durable extra-zero-entry state when an earlier transaction leaves
the child pending for commit; active correction changes that fixture's root.
The subsequent [block comparison](evidence/restart-state-rollback-block-v2-2026-10-07/README.md)
establishes the same difference in normally imported synthetic blocks and
fresh-process reopening. Neither establishes historical occurrence or a
running-mainnet-node failure. See the findings and linked qualification bundles for
the exact controls, failed observations and execution limits. The original
proposal was source analysis; subsequent qualification is recorded below.

| Option | Historical execution | Remaining consequence | Recommendation |
| --- | --- | --- | --- |
| Preserve the current implementation | No new F11 execution change | The demonstrated defect remains. A release disposition must explain the supported-path impact and obtain independent acceptance; age of the code or lack of a reported incident is not sufficient. | Keep as the comparison baseline; no waiver selected. |
| Set the missing journal discriminator unconditionally | Changes rollback semantics at every height, including historical replay | Could change execution of old transactions; existing evidence does not show whether historical outputs would differ. | Do not select for this restart. |
| Correct that discriminator only under a new execution rule | Old path below an explicit height; corrected path at and above it | Requires configuration, call-path, compatibility and candidate validation. Treat as a consensus-sensitive execution change even while accepted-block impact remains unproven. | Preferred candidate for qualification, not yet production-approved. |

Changing how blocks are selected, ticket economics, ongoing finality, account
ownership or token supply is outside this proposal. It addresses the inherited
rollback defect discovered during release qualification.

## What the source supports

| Source | Observation and implication |
| --- | --- |
| [StateDB.Suicide](../core/state/statedb.go:571), [suicideChange.revert](../core/state/journal.go:174) | The time-lock loop supplies `prevTimeLockBalance` but omits `isTimeLock`. The proposed semantic change is confined to that discriminator. The existing correct branch restores a time lock. Its sufficiency still needs candidate validation. |
| [StateDB fields](../core/state/statedb.go:58) | StateDB currently holds no execution height or chain rules. Setting a mutable global or remembering the most recently executed height would add avoidable state and could misapply rules during replay. |
| [ChainConfig](../params/config.go:160), [Rules](../params/config.go:448), [NewEVM](../core/vm/evm.go:143) | Persisted fork heights and block-specific EVM rules already exist. `isForked` treats a missing height or block number as inactive and uses an inclusive height boundary. Reuse this mechanism. |
| [Fusion fork helpers](../common/fork.go:35) | These use global network selectors, and `IsHardFork` treats a nil block number as active. Do not append this correction to those arrays or change their existing semantics. |
| [RestartAnchor](../params/restart_anchor.go:9) | This selects a required chain prefix. It is excluded from ChainConfig JSON and is not an execution-fork schedule. An accepted anchor does not activate a journal correction. |
| [Finalise](../core/state/statedb.go:873), [journal revert](../core/state/journal.go:60) | Dirty tracking affects which accounts are finalized. The nil RLP encoding observation alone cannot establish persistence or a resulting state root. |

## Proposed implementation boundary

The names here are illustrative and do not exist in the current release.
The candidate should have one rule, provisionally `SuicideTimeLockFixBlock`,
serialized with the chain configuration and exposed through `params.Rules`.
Use the existing fork comparison and compatibility helpers. Include the rule
in the configuration banner and update the existing positional configuration
literals deliberately. A missing schedule keeps the legacy behavior in
unscheduled configurations; it must not silently disable an approved schedule
on the recovered mainnet.

Pass the block-specific rule explicitly from `opSelfdestruct` to
`StateDB.Suicide`, through the `vm.StateDB` interface. A required boolean
parameter for this one decision is the proposed smallest route. Update the
no-op implementation and direct callers explicitly; do not use an optional
type assertion that could silently select different semantics. This changes
a Go API, so callers and test doubles must be compiled and reviewed.

When the rule is false, preserve the current mutation order and journal
contents. When true, set the time-lock entry's discriminator correctly. Keep
the ordinary-balance loop, the separate time-lock journal entry, deletion
behavior, gas/refunds, beneficiary transfers and account encoding unchanged
in this candidate. Do not combine the correction with a journal refactor,
nil-to-zero repair on reads, or a database migration. Those would obscure the
compatibility comparison. No StateDB copy/reset rule field is needed with an
explicit per-call parameter.

`NewEVM` obtains rules from the block being executed. Its `Reset` changes the
transaction context and StateDB only; the current processor reuses it within
one block. Preserve that scope. Historical calls and traces must use the
requested block's rules, not the latest head, machine clock or launch date.

| Supported path to review | Existing source connection |
| --- | --- |
| Block import and historical execution | [StateProcessor.Process](../core/state_processor.go:58) constructs an EVM from the block header and chain config. |
| Mining | [worker.commitTransaction](../miner/worker.go:679) calls [ApplyTransaction](../core/state_processor.go:142) with the candidate header. |
| Calls and gas estimation | [EthAPIBackend.GetEVM](../eth/api_backend.go:184) constructs the EVM from the selected header and blockchain config. Check pending-header behavior at the boundary as well. |
| Historical tracing | [tracer execution](../eth/tracers/api.go:525) and the other EVM construction sites use block context and chain config; retain each supported tracer path in qualification. |
| Offline recovery construction | [recovery.Build](../internal/recovery/build.go:75) calls ApplyTransaction using its reader's config. That config comes from the database, as discussed below. |

These source connections identify where validation belongs. They are not new
passing runtime results or a claim that all legacy tracer tests compile.

## Activation and recovery configuration

Let `B` be the accepted historical parent height, `A` the final controlled
recovery anchor height, and `H` the proposed execution-fix height. None is
selected by this document. The backup head is still a candidate historical
parent, not an automatically approved activation input.

- Require `H > B`; never retrofit the correction into accepted history.
- Prefer evaluating `H = A + 1`: this places the correction before ordinary
  public use while retaining legacy execution for the controlled bridge. It
  does not establish that bridge as safe or waive its existing review.
- Activating inside the bridge instead would require constructing and
  qualifying that bridge with the new rule. Existing bridge evidence cannot
  establish the changed execution.
- Freeze the actual numeric schedule with the reviewed recovery plan before
  signing real artifacts. Check that public use cannot begin below `H`.
  If the accepted parent or bridge length changes, review the schedule again.

Normal startup resolves a mainnet default configuration through
[SetupGenesisBlock](../core/genesis.go:191). The offline
[recovery reader](../internal/recovery/chain.go:24) instead reads the stored
config directly and intentionally avoids startup repair and writes. An old
backup will not acquire a newly added schedule merely by updating the node's
mainnet defaults.

The candidate must make those two paths use the same reviewed effective
configuration for the recognized genesis. Prefer one narrow configuration
resolution/validation path shared by these actual consumers: accept a missing
legacy field only while no affected execution has been accepted, supply the
approved schedule in memory, and reject conflicting schedules. Keep the
offline reader read-only. Do not identify the network using chain ID alone or
introduce an operator switch that silently bypasses the mainnet rule.

The recovery [configuration checksum](../internal/recovery/approval.go:71)
hashes JSON, and [approval validation](../internal/recovery/approval.go:120)
compares it with the reader's effective configuration. A serialized schedule
therefore changes the approval input even when `H` follows the bridge. Generate
and review fresh artifacts/checksums with that effective configuration; do not
reinterpret old approvals as covering the new rule. The preservation copy of
the backup remains untouched.

## Compatibility checks that the candidate must satisfy

Adding a ChainConfig field is necessary but insufficient:

- Extend `CheckCompatible` to cover the new schedule, including missing vs
  present and changed heights. Same schedule must survive restart unchanged.
  Test activation minus one, activation, and activation plus one.
- Review actual startup, not just that helper. [SetupGenesisBlock](../core/genesis.go:219)
  has special handling for zero-height rewinds, and
  [eth.New](../eth/backend.go:174) currently attempts `SetHead` on a config
  conflict and writes the new config without checking its return value.
  For a conflict in this new rule after affected execution, the candidate
  should fail before a rewind or config write. Do not rely on the anchor
  silently making this sequence safe. This is a requirement for the proposed
  addition, not a newly demonstrated failure of the current selection.
- Check missing configuration, custom-genesis input, future scheduling,
  existing databases above `H`, recovery reader behavior and downgrade
  handling. Refuse an inconsistent supported-mainnet schedule. An old binary
  cannot be made to enforce a new field by this proposal; do not advertise a
  downgrade across activation as safe.
- Peer connection does not prove execution-rule agreement. The current
  [status packet](../eth/protocol.go:112) and
  [handshake checks](../eth/peer.go:369) do not exchange this schedule. Publish
  the exact supported release/configuration for joining operators and verify
  block validation independently. No protocol redesign is proposed here.

## F11-b disposition scope

A tracked production-source search at the reviewed commit found only
`opSelfdestruct` calling `Suicide`, plus the StateDB definition, VM interface
and no-op implementation. That opcode reads the FSN ordinary balance first,
which materializes an entry. No separate production/RPC deletion caller was
found. This supports the **latent/direct-API-only classification for the
inspected source**, not a claim about every external consumer or future code.

Retain the direct-state failing regression and this limitation in F11. Do not
fold a separate zero-entry deletion-flag correction into F11-a just to make
the entire state suite green. Independent review must accept its disposition
or identify a supported reachable path needing separate treatment.

## Evidence needed before selecting a correction

These are acceptance criteria for a later bounded qualification, not a test
run performed by this review or instructions to operate against live peers.

1. Review the exact candidate diff against the selected P1–P17+B1+D1 inputs.
   Prove the inactive path retains legacy behavior and independently review
   the active journal ordering. Preserve the original failing evidence; use
   separate compatibility assertions and corrected-rule assertions.
2. Validate the retained F11-a failing case and adjacent controls under both
   rules, including raw account structure and independent field reads.
   The active path must restore the actual pre-snapshot state. The inactive
   path must match the legacy observation. Do not report a universal state
   suite pass while the separately classified F11-b remains failing.
3. Establish transaction finalization/commit and supported block-processing
   outcomes separately from the existing in-memory observation. Expected
   state, receipts and gas results need independently justified expectations.
   Record absent observations as unverified, not as proof of no impact.
4. Demonstrate consistent rules across the supported execution paths and the
   startup/configuration cases above, with cold reload where relevant.
   Reconcile recovery configuration hashes and approvals without real signing.
5. Supply candidate historical compatibility evidence under G1. Baseline
   replay remains at 3,600,000; neither it nor the local fixture proves that
   the patched executable reproduces the full accepted history.
6. Obtain independent consensus review of the diff, evidence, F11-b
   disposition and actual schedule before selecting a production patch.
   Retain the existing final rehearsal and go/no-go requirements in G8.

**Candidate follow-up:** the [isolated diff and initial evidence](evidence/restart-state-rollback-candidate-2026-10-07/README.md)
and [qualification specification](restart-state-rollback-qualification.md) are
now prepared. Configuration tests and both command builds pass. The
[integration evidence](evidence/restart-state-rollback-integration-2026-10-07/README.md)
also passes startup/reader configuration, database reopen and approval-rejection
checks on a registered synthetic network. The [CLI follow-up](evidence/restart-state-rollback-cli-2026-10-07/README.md)
also passes report/prepare configuration binding. The [rollback comparison](evidence/restart-state-rollback-execution-2026-10-07/README.md)
now demonstrates bounded pre-activation compatibility and the active F11-a
correction; F11-b remains unchanged. The [persistence comparison](evidence/restart-state-rollback-persistence-v2-2026-10-07/README.md)
now passes 16 cases per selection through transaction finalization, durable
commit and LevelDB reopen. Dirty absent-entry cases have different roots under
the active rule, reinforcing the need to preserve historical execution.
The [block comparison](evidence/restart-state-rollback-block-v2-2026-10-07/README.md)
also passes 16 cases per selection through construction, import and fresh-process
reopening from synthetic checkpoints. The [API comparison](evidence/restart-state-rollback-api-2026-10-08/README.md)
passes 84 cases per selection through actual call, injected-pending and
available-state tracing methods. The active rule changes only the expected raw
balance structure; disabled/pre-activation observations match. Its explicit
constructor seams and coverage limits remain in the report. Next: reconcile
remaining supported-path/F1 exclusions and startup/F12 compatibility dispositions;
candidate historical compatibility remains unverified.
The separate [F12 follow-up](evidence/restart-genesis-startup-v2-2026-10-08/README.md)
now identifies compiler-dependent ticket compression as the cause of the genesis
mismatch and reproduces it through both actual executables. That compatibility
blocker takes priority; it is not an F11 correction.
Keep the production selection unchanged until review and qualification are complete.
The source proposal is complete;
F11 release acceptance, F1 coverage, F10 dependency acceptance and G1 historical
replay remain open in the [canonical plan](restart-plan.md).
