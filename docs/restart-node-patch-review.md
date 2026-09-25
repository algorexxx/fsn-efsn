# Proposed permanent node patches

25 September 2026. Review baseline: original local `master` at
`c5f0174d88ab2b9c3086c6a9cc9ccf38a072992f`; candidate implementation at
`04a676c42015dfe7f86aed47e598fb2920ed1e69`. This is the review inventory, not
an approved release. Later test/document changes do not approve these patches.

The intended release has a fixed recovery ancestry and otherwise retains Fusion's
ticket economics and ordinary fork choice. Each row below is a separate review
decision. Some rows share files or implementation commits; cherry-picking a whole
investigation commit is not a substitute for selecting its intended changes.

## Permanent node candidates

| ID | Exact change | Why include it / necessity | Lasting effect and evidence |
| --- | --- | --- | --- |
| P1 | Fixed restart ancestry; checks on startup, block/header/receipt imports, reorganization, pivot and mining/transaction readiness; refuse unsupported light mode. | Required for the agreed protection against an old isolated chain replacing the accepted recovery prefix. | Restricts eligible history permanently once configured. Compatible descendants retain ordinary fork choice and can reorganize. **Mainnet height/hash is still unset.** Review [anchor implementation](restart-anchor-implementation.md), [reset/pivot coverage](restart-reset-pivot-rehearsal.md) and missing end-to-end sync coverage. |
| P2 | Reconstruct expired tickets using the parent timestamp already used by execution; return an error for a missing reconstruction ancestor. | Required for demonstrated recovery/expiry-boundary reconstruction to agree with directly executed state. | Validation-sensitive bug correction. Existing ticket-commitment verification remains mandatory. No ticket price, lifetime or reward change. Review [original failures and corrections](restart-corrections.md), including synthetic boundaries and 128 real historical cases; full historical replay is incomplete. |
| P3 | Copy receipt logs, topics and data before handing them to another mining task. | Required to remove the reproduced miner data race exercised by normal ticket buying. | Memory ownership correction during mining. Review [race reproduction and passing checks](restart-corrections.md); this does not establish that every miner race is fixed. |
| P4 | Replace automatic ticket-buy orchestration with startup/periodic retry, canonical confirmation and retention of exact signed purchases; use actual pool contents for purchase conflicts. | Required for the chosen unattended producer to recover from the demonstrated purchase failures. Manual buying is an operational alternative, not the selected launch workflow. | Remains active when auto-buy and mining are enabled; manual purchase conflict handling also changes. Local saved transactions are not consensus state. Review [purchase controller](restart-purchase-controller.md) and [full-state handover](restart-full-state-handover.md). Systematic purchase-journal power-loss and live peer-reorg coverage remain incomplete. |
| P5 | Commit a reorganization's canonical indexes, transaction lookups and head markers in one database batch; propagate existing checkpoint errors before publishing. | Required to remove the reproduced partial fork-switch and ignored-checkpoint-error failures. A first block could be mined without this, but the known persistence defect would remain. | Affects ordinary permitted reorganizations. Does not change difficulty weighting or add checkpoint heights. Review [interrupted reorganization evidence](restart-crash-rehearsal.md), including ten original failing cuts. |
| P6 | Commit explicit rewind deletions and final heads together; guard state repair against missing ancestors or unavailable genesis state. | Required to make the supported rewind/repair path survive the demonstrated interruption and nil-pointer failures. | Affects local rewind/startup repair. No new balance or fork-weight policy. Review [rewind evidence](restart-rewind-rehearsal.md), including 30 original failing cuts, and [reset follow-up](restart-reset-pivot-rehearsal.md). |
| P7 | Skip ancient-store truncation only when the database explicitly lacks a freezer; repair header/fast head advancement when reimporting a known block after rollback. | Required for the demonstrated rollback/reimport path on Fusion's existing LevelDB-without-freezer layout. | Persistence and availability correction. Genuine storage errors remain errors. Review [rollback defects](restart-anchor-implementation.md) and [interruption controls](restart-crash-rehearsal.md). |
| P8 | Do not call the database repair routine after a corrupt database fails a read-only open. | Required for the investigation/recovery tools' promise to leave the source unchanged. It is not required to alter ordinary writable node operation. | A read-only corrupt open fails instead of attempting repair. Review `ethdb/leveldb/readonly_test.go` and [offline signing evidence](restart-offline-signing.md). This is also a candidate standalone upstream bug fix. |

## Source boundaries

Paths identify review locations; where shared, select the stated functions/hunks.
All non-test Go changes versus the pinned master are accounted for below or in
the recovery-only section. Tests and evidence must accompany any extracted patch.

| ID | Source files / boundaries |
| --- | --- |
| P1 | `core/restart_anchor.go`, `params/restart_anchor.go`, `params/config.go`, `core/genesis.go`; anchor hooks in `core/blockchain.go`, `core/headerchain.go`, `eth/api_backend.go`, `eth/backend.go`, `eth/handler.go`, `eth/sync.go`, `light/lightchain.go`, `miner/worker.go`. |
| P2 | `consensus/datong/consensus.go`: `getAllTickets` parent lookup and expiry cleanup only. |
| P3 | `miner/worker.go`: `copyReceipts` only. |
| P4 | `cmd/efsn/main.go`, `common/autobuy.go`, `common/fsntypes.go`, `internal/ethapi/autobuy.go`, `internal/ethapi/api_fsn.go`, `eth/api.go`; automatic-purchase notifications in `core/blockchain.go`. |
| P5 | `core/blockchain.go`: reorganization batch and head-write/publication helpers. |
| P6 | `core/blockchain.go`: `SetHead`, `repair`; `core/headerchain.go`: `SetHead` / private `setHead` callback and batch. |
| P7 | `core/blockchain.go`: `truncateAncient` and known-block head advancement in `writeHeadBlock`; `core/rawdb/database.go`, `core/rawdb/freezer_table.go`: exported unsupported-operation sentinel. |
| P8 | `ethdb/leveldb/leveldb.go`: read-only corruption handling. |
| O1 | `cmd/utils/flags.go`: trim/filter explicit bootstrap lists. Inherited gateway usability fix; optional for the restart protocol. Does not create DNS discovery. Review independently if retained. |

P1, P5, P6 and P7 overlap in chain-head code. Extract and test them in a defined
order rather than treating the rows as already independent patch files. P4 uses
P3's miner correction in the exercised runtime. The recovery tool uses P2 and P8.

## Recovery-only tooling and excluded deployment material

- `cmd/fsn-recovery/*.go` and `internal/recovery/*.go` implement construction,
  review, approval, limited signing and export. The normal node does not import
  `internal/recovery`. Its one-backup/two-donation signing limits are local to the
  tool; they do not restrict either wallet's later ordinary mining.
- `consensus/datong/consensus.go`: the added `SigningPayload` accessor exposes the
  existing encoding for that tool. It neither changes `Seal` nor adds a consensus
  exception. Review separately from P2; it can accompany a separate tool build.
- `tests/restart`, other `*_test.go` files, `docs/evidence` and investigation
  scripts are review/reproduction material, not node runtime behavior.
- `Dockerfile.gateway-isolated`, `QuickNodeSetup` changes and related README
  material include the inherited explorer gateway setup. Do not silently use
  this configuration for production validators. Review the launch deployment
  configuration separately. `.gitattributes` / `.gitignore` changes are repository
  bookkeeping, not protocol patches.

DNS discovery defaults, final anchor selection, supported public download/sync
paths and release packaging remain separate unfinished work. This inventory does
not claim those are implemented or that the candidate node is ready to launch.

## Independent review handoff

Reviewers should identify the baseline and candidate commit, reference the row ID,
and report the concrete trigger, affected behavior, severity and reproduction for
each finding. Check the actual source and retained failure logs as well as these
summaries. Record unresolved findings and explicit dispositions before freezing
the release patch list; no row is independently approved by this document.

The highest-priority review surfaces are P1/P2 validation behavior, P5/P6/P7
persisted-head consistency, P4 purchase recovery, and the separate signing tool's
approval/journal/key boundaries. Existing passing tests are evidence for their
specific scenarios, not a completed independent security audit. The
[restart plan](restart-plan.md) retains the wider data, timing, custody, networking
and release gates.
