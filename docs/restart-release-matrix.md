# efsn release acceptance and reviewer handoff

4 October 2026. This freezes the coverage for G2 and the efsn portions of G3–G8
in the [launch plan](restart-plan.md). It is a finite worklist, not release
approval. Investigation source reviewed here: `4a216701`; upstream baseline:
`c5f0174d88ab2b9c3086c6a9cc9ccf38a072992f`. Neither is the selected release.
No production anchor is configured yet.

## Scope and evidence rules

The initial target is Linux amd64, full block synchronization from a verified
restored LevelDB without a freezer. Pin the actual distribution, filesystem,
pruning/cache settings, service limits and build inputs before acceptance.
Windows investigation results are supporting evidence, not a Windows validator
release. Fast/light acquisition, genesis resync and other database layouts are
outside the supported launch path. Reachable anchor bypasses remain blockers.

The ten rows below are acceptance groups, not ten new investigations. Retained
passes establish their stated fixtures only. Rebuild the selected regression
tests against the final source/toolchain; exercise the actual release executable
for CLI, configuration and operator acceptance. A service embedded in a test
binary does not by itself verify release packaging or compiled mainnet constants.

Run the final selected checks once, then repeat only rows affected by a source,
toolchain, artifact or configuration change, a failure, or newly uncovered
supported behavior. Keep original failures and corrected results together. A
skipped opt-in, expected limitation reproducer or uncompiled package is not a
passing regression. No automatic launch of archived scripts is implied: many
pin old sources, fixed result paths and disposable data prerequisites.

## Bounded acceptance matrix

| ID / gates | Scope and retained evidence | Final acceptance still required |
| --- | --- | --- |
| R1 — G2/G5 | Source selection and build. [P1–P17 inventory](restart-node-patch-review.md) and [concrete source extraction](restart-release-extraction.md) separate node, optional O1, recovery, observer and gateway material. Existing Linux builds use rehearsal Go 1.21.3. | Select exact hunks and release toolchain/dependencies; record dispositions below. Pin source, modules, compiler, CGO compiler/libraries and build flags. Build twice from clean inputs, explain any binary difference, and record hashes/CI results. Verify CLI defaults and the final compiled anchor. Go 1.21.3 is not an approved release choice. |
| R2 — G1/G2 | Anchor and validation: [36 entry-point cases](restart-anchor-implementation.md), [ticket reconstruction](restart-corrections.md), [parent isolation](restart-parent-isolation.md), [cold headers](restart-cold-header-validation.md), [snapshot framing](restart-snapshot-framing.md). Covers P1/P2/P9/P16. | Rerun these fixtures with the selected source. Incompatible startup/import/header/receipt/mining paths must reject without publishing a new head; eligible heavier descendants must still win. Missing ancestors must fail. Preserve valid encoding and expiry commitments. G1 historical compatibility remains separate. Update the test that currently expects an unset mainnet anchor to require the approved exact identity when that value is selected. |
| R3 — G2 | Persistence: [rollback](restart-anchor-implementation.md), [reorg](restart-crash-rehearsal.md), [rewind](restart-rewind-rehearsal.md), [reset/pivot](restart-reset-pivot-rehearsal.md), and P8 read-only corruption refusal. The combined small crash fixture has 14 scenarios / 46 cuts. [Larger batch evidence](restart-reorg-cost.md) passes six cases through 4,096 displaced blocks. | Rerun the 46 application-write cuts and six bounded batch cases against selected source. Fresh processes must resolve heads, canonical indexes, transactions and receipts consistently, including shorter heavier forks. Read-only corruption must not invoke repair. Keep the existing workload/budget assertions. This does not certify power loss, torn writes or arbitrary fork depth. |
| R4 — G2 | Automatic buying and miner ownership: [controller](restart-purchase-controller.md), [16 purchase cuts](restart-purchase-crash-rehearsal.md), [eight storage-error cases](restart-purchase-storage-and-peers.md), [nonce rollback](restart-purchase-nonce-rollback.md), [bounded resend](restart-autobuy-rebroadcast.md). Covers P3/P4. | Rerun controller guards, interrupted saved-intent handling, actual miner race case and the corrected delivery continuation. Require the exact saved purchase to execute and at least two subsequent purchases per owner in the retained two-owner scenario. Do not count local queueing as inclusion or silently sign replacements. |
| R5 — G3 | Separate recovery executable: [complete-state command rehearsal](restart-full-state-operator.md), [offline cuts](restart-offline-signing.md), [approval](restart-signing-approval.md). Public test keys; independent processes importing the same client's output. | On fresh verified test copies, reproduce the three-block Candidate A construction, approval/journal refusal cases, exact exported bytes and cold account/ticket ledger checks. Recheck real addresses, fresh timing, authorized funds and key custody separately before real signing. The tool's local signing limits do not restrict subsequent ordinary node mining. |
| R6 — G3/G4/G7 | Live operation: [funded entrant](restart-full-state-participant.md), [single-producer outage](restart-full-state-outage.md), [operator recovery](restart-operator-recovery.md) and [funded gap continuation](restart-funded-gap.md). Existing entry uses public test key 3 and hypothetical funding. | One final isolated rehearsal follows the operator kit: stop the backup signer, continue donation production, join a distinct test-key producer, purchase/mine/replenish, cold-restart and compare ledgers. Rehearse supervised SSH detection/response to stalled production and failed buying using retained failure scenarios. Record who responds and the available repair funds. Actual independent ownership is a later milestone, not simulated by Peter operating another key. |
| R7 — G2/G5 | Discovery P10–P15: [startup/cache](restart-discovery-resilience.md), [maturity](restart-discovery-cache.md), [DNS](restart-bootstrap-dns.md), [address changes](restart-peer-addresses.md), [partitions](restart-network-partitions.md), [configuration](restart-network-profile.md). | Rerun focused unit/race and isolated live DNS/cache/partition fixtures. On selected hosts, test advertised TCP/UDP, NAT/firewall and advertised IP families, DNS endpoint replacement and static fallback. Keep outbound dialing enabled. Public endpoints and DNS ownership remain unselected; fixture success does not supply them. |
| R8 — G2/G5/G7 | Synchronization and returning histories: [actual-service rehearsal](restart-node-rehearsal.md) rejects a strictly heavier stored incompatible fork, using sparse history and an explicit downloader trigger. Later [miner partitions](restart-miner-partitions.md) and [complete synthetic ancestry](restart-continuous-partitions.md) exercise ordinary automatic synchronization of compatible forks. | Close the remaining combination: complete ancestry, ordinary automatic full-sync scheduling and an initially unknown incompatible branch in an isolated public-test-key fixture. The [three-case next test](restart-release-extraction.md#next-bounded-sync-check) specifies the existing helper, fork/deadline bounds and unanchored control. Require correct compatible catch-up, explicit greater competing weight, unchanged accepted canonical transactions on refusal and matching cold heads/state/tickets. Define a bounded fork window and deadline before execution; this is not a request for a year-long fork or public-peer fault injection. |
| R9 — G1/G2/G5 | Data and host operation: [complete package/restore](restart-snapshot-restore.md), [12 startup cases](restart-anchor-startup.md), and the R3 batch measurements. The one-million-descendant startup took about 26 s aligned / 37 s split locally. | Verify the final downloadable package, trusted manifest, fresh destination and executable on a clean machine; restore, start with full sync and complete R6/R8 readiness checks. Measure startup/shutdown, resource use and growth on selected host/storage; set explicit service limits and demonstrate clean backup/restore and host restart. Reuse existing bounded measurements; rerun those fixtures only where selected code/toolchain/storage changes invalidate them. Do not infer maximum-gas or production capacity from compressed synthetic data. |
| R10 — G4/G6 | efsn telemetry P17: [collector-loss mining drill](restart-dashboard-mining-outage.md) continued twelve blocks/purchases, recovered WSS and rejected obsolete queued-head reports. Dashboard implementation is parked in its separate repository. | Check the selected efsn reporter with the selected dashboard release: loss does not stop production, unavailable/stale observation is visible, and recovered reports agree with direct RPC. Reuse the existing bounded drill and actual-host SSH handover checks. No new dashboard feature, observer deployment or external notification provider is required by this row. |

R6, R8, R9 and R10 may share one final rehearsal and evidence set. Record the
separate assertions rather than repeating the entire environment four times.
The current synthetic mainnet-like fixtures must remain explicitly distinct
from the eventual immutable real recovery package. Publishing and real-key
signing occur only after the plan's review/approval boundaries.

## Reproduction index

These are existing entry points, not a claim that they all ran at the source
revision above. The linked reports pin earlier commands, test bytes, executable
hashes, failures, results and opt-ins. Inspect those inputs before adapting a
runner into a fresh results directory. Compile before entering an offline network
namespace; enable only the intended opt-ins, with public test keys and disposable
copies. Backup/replay probes keep original data read-only.

| Rows | Existing tests / runner references |
| --- | --- |
| R2 | In `tests/restart`: `TestRestartAnchorEnforcement`, `TestRestartAnchorConfiguration`, `TestReconstructionAcrossMissingStates`, `TestReconstructionAtHistoricalExpiryBoundary`, `TestReconstructionWithMissingAncestorReturnsError`, `TestPreservedTicketReconstruction`, `TestHeaderBatchUsesUnstoredParents`, `TestFinalizeParentIsolatedFromConcurrentImport`, `TestColdHeaderValidationBoundaries`. In `consensus/datong`: `TestSnapshotRejectsTruncatedCount`, `TestSnapshotPreservesValidEncoding`, `TestSnapshotRejectsInvalidFraming`. [Parent runner](evidence/restart-parent-isolation-2026-09-25/check-linux.sh). |
| R3 | `TestRestartRollbackDatabaseModes`, `TestRestartCrashBoundaries` (`FUSION_RESTART_CRASH_REHEARSAL=1`); [combined crash runner](evidence/restart-reset-pivot-rehearsal-2026-09-24/run-linux.sh). `ethdb/leveldb/TestReadOnlyCorruptionDoesNotRepair`. `TestRestartReorganizationCost` (`FUSION_RESTART_REORG_COST=1`); [corrected six-case runner](evidence/restart-reorg-cost-2026-10-04/attempt-2/run-linux.sh). |
| R4 | `TestAutoBuyRuntime`, `TestAutomaticPurchaseRecovery`, `TestSubmittedTicketReplacementAllowsExplicitRetry`, `TestAutomaticPurchaseStorageErrors`, `TestAutomaticPurchaseCrashBoundaries` (`FUSION_PURCHASE_CRASH_REHEARSAL=1`). `internal/ethapi/TestPendingAutomaticTicketRetry`, `eth/TestAutomaticTicketRebroadcastQueues`, `eth/TestAutomaticTicketRebroadcastWire`. [Focused](evidence/restart-autobuy-rebroadcast-2026-09-27/run-focused.sh), [protocol](evidence/restart-autobuy-rebroadcast-2026-09-27/run-protocol.sh) and [live](evidence/restart-autobuy-rebroadcast-2026-09-27/run-live.sh) runners; the focused eth compilation is explicitly narrower than its broken whole-package suite. |
| R5 | `TestRecoveryOperatorCLI`, `TestFullStateRecoveryOperator`, `TestApprovedOfflineProcessCuts`, `TestApprovedOfflineRefusals`, `TestOfflineRecoveryProcessCuts`, `TestOfflineRecoveryUncertainCuts`, `TestOfflineRecoveryRefusals`, `TestKeystorePreflightLocksAndUncertain`. See [operator setup](restart-full-state-operator.md) and the [test instructions](../tests/restart/README.md) for command and verified-copy inputs. |
| R6 | `TestFullStateParticipantEntry`, `TestFullStateSingleProducerOutage`, `TestFullStateFundedGapRepair`, `TestFullStateFundedGapColdAudit`; retained complete-state inputs and cold ledgers are linked in the R6 reports. These require explicit dataset preparation, not a blanket opt-in over every historical failure reproducer. |
| R7 | `TestRestartDiscoveryRehearsal`, `TestRestartBootstrapDNSRehearsal`, `TestRestartNetworkPartitionRehearsal`, `TestRestartNetworkProfileRehearsal`; focused table/UDP/address/self-contact tests in `p2p/discover`. [DNS final runner](evidence/restart-bootstrap-dns-2026-09-25/check-final.sh), [partition final runner](evidence/restart-network-partitions-2026-09-25/check-final.sh). Preserve their namespace, explicit opt-ins, timers and bounds. |
| R8 | Existing `TestRestartNodeRehearsal/compatible_peer`, `/heavier_stored_fork_peer`, `/incompatible_database_startup`, `/readiness_mining_crash`, `/dense_miner_fixture`, `/partition_purchase_miners`; `FUSION_RESTART_NODE_REHEARSAL=1` in an isolated loopback-only namespace, plus the partition opt-in for packet-loss cases. The combined unknown-incompatible-branch acceptance remains to be added; compatible automatic convergence is already retained. |
| R9 | `TestPreservedSnapshotPackage`, `TestRestoredSnapshotService`, `TestRestartAnchorStartupCost` (`FUSION_RESTART_ANCHOR_STARTUP=1`); [startup runner](evidence/restart-anchor-startup-2026-10-04/run-linux.sh). The package's hashes/paths and final host service checks require their own final manifest. |
| R10 | `TestDashboardTelemetryNode` with the existing opt-in mining fixture and external outage controller described in the [mining-outage report](restart-dashboard-mining-outage.md). Coordinate the final dashboard commit via the [repository handoff](restart-dashboard-handoff.md); do not expand the efsn runtime inventory. |

## Findings requiring a recorded disposition

All entries below remain open until the release review records an owner,
decision and evidence. They are not implicit waivers or extra patch categories.

| Finding | Release disposition to record |
| --- | --- |
| Legacy package compilation | `miner` has obsolete worker/database/state test APIs ([baseline log](evidence/restart-integrity-2026-09-23/baseline-package-tests.txt)); `core/rawdb` refers to removed `params.RinkebyGenesisHash` ([anchor report](restart-anchor-implementation.md)); `core/bench_test.go` uses obsolete APIs ([parent report](restart-parent-isolation.md)); broader `eth` tests also contain stale APIs ([resend report](restart-autobuy-rebroadcast.md)). Repair test compatibility or explicitly document the excluded checks and replacement coverage. A `-run` filter cannot bypass package compilation. |
| Inherited networking failures | `TestParseNode` expected-error differences, `TestForwardCompatibility` Ethereum/Fusion packet-type mismatch, and `TestProtocolHandshake` disconnect-size mismatch (`got 2, want 1`) remain in the [discovery evidence](restart-discovery-resilience.md). Confirm their status on the final toolchain and review runtime implications; do not label the entire p2p suite green. |
| Native-call decoding | [Ignored decode errors](native-call-decode-errors.md) affect historical balances/fees and some transaction validation. Preserve historical behavior while the reviewer decides whether a separately activated change is needed. No activation or additional consensus patch is selected here; pool rejection alone does not dispose of block-validation concerns. |
| Ordinary compatible forks | Equal-weight forks can need operator intervention; heavier compatible forks can replace post-anchor transactions. [Response guide](restart-monitoring-response.md) must state the limit. The fixed recovery anchor adds no ongoing finality. |
| Buying and funding | Nonce gaps, stale saved purchases and retreat losses can require manual repair and additional authorized funds. Retained successful funded repair is not an automatic funding source or universal reserve. Record the supported operator response and actual runway. |
| State, durability and discovery limits | Sparse historical state, inherited header-only reconstruction limits, process-exit versus power-loss durability, and inbound-only discovery recovery limits stay explicit. The selected restored full-sync path and storage acceptance must address their operational consequences. |

## Independent reviewer packet and completion

Prepare one packet with: upstream and selected release commits; the small
production diff mapped hunk-by-hunk to P1–P17/O1; separate recovery-tool diff;
source/build/data/anchor hashes; this matrix with final result links; the findings
ledger above; and the operator launch/stop/restore procedure. Optional observer
code and gateway packaging must not enter the node patch set unnoticed. Shared
files mean investigation commits are not independently cherry-pickable patches.

Prioritize independent human review of P1/P2/P9 validation, P5/P6/P7 persisted
heads, P4 purchase recovery and the recovery tool's approval/journal/key bounds.
Review P10–P15 as the networking group, P16 as parser behavior and P17 as telemetry.
For each finding record the concrete trigger, affected source and matrix row,
reproduction, severity, decision and validation of any correction. Additional AI
review supports this work; it does not replace the agreed human review.

G1 baseline replay now closes at **3,300,000**, including an independent exact-height
cold check ([evidence](evidence/restart-replay-3300000-2026-10-04)). The unchanged
baseline retains legacy shortcuts through 2,680,000. Execution through the accepted
parent and historical compatibility of the selected candidate are still open;
neither this matrix nor synthetic passes replace them.

Next technical order: select the production hunks/build inputs and record the
failure dispositions; continue bounded G1 replay after fresh capacity checks;
close R8 and the clean-machine operator-kit gap; then run the final artifact/host
rehearsal. Public endpoints, custody, real artifact approval and go/no-go remain
the decisions in the main plan. Stop extending the investigation when these
declared cases pass and findings have reviewed dispositions; new work needs a
changed input, demonstrated failure or uncovered supported requirement.
