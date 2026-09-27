# Proposed permanent node patches

27 September 2026. Review baseline: original local `master` at
`c5f0174d88ab2b9c3086c6a9cc9ccf38a072992f`; candidate implementation at
`04a676c42015dfe7f86aed47e598fb2920ed1e69` for P1–P8. P9 is an additional
candidate from baseline `bcbd1ce`, pinned by source blobs in its evidence.
P10 is a discovery startup correction from baseline `0df4014`, also pinned by
source blobs and before/after race evidence.
P11 preserves discovery peer age and accepts validated sparse discovery replies,
from baseline `31433ca`, with deterministic failures and cold-process evidence.
P12 adds bootstrap DNS outage/retry handling; P13 corrects restored seed identity
and endpoint handling, both from baseline `d7fa207`.
P14 corrects discovery address reservations, replacement promotion and stale
probe results, from baseline `a5a6bea`.
P15 excludes the node's own identity from discovery admission, from baseline
`27b1186`, with deterministic and signed-UDP before/after evidence.
This is the review inventory, not
an approved release. Later test/document changes do not approve these patches.

The intended release has a fixed recovery ancestry and otherwise retains Fusion's
ticket economics and ordinary fork choice. Each row below is a separate review
decision. Some rows share files or implementation commits; cherry-picking a whole
investigation commit is not a substitute for selecting its intended changes.

27 September P4 extension: the [peer retry investigation](restart-peer-purchase-retry.md)
reproduced recurring suppression of a pending purchase after early rejection.
The [bounded same-byte resend candidate](restart-autobuy-rebroadcast.md), from
baseline `ce7f971`, now passes the retained live failure with two further purchases
per owner and a matching 52-block cold ledger. Review its five production-file
hunks as part of P4. It changes guarded local delivery, with no consensus or
transaction-validity relaxation and no sixteenth patch category.

The [subsequent complete-state partition](restart-retry-partition.md) adds no
production changes. It demonstrates automatic heavier-branch convergence but
leaves a seven-purchase nonce gap and insufficient funds after ordinary ticket
retreats. Existing RPC retrieves every original; canonical and competing-branch
accounting pass. The [funded continuation](restart-funded-gap.md) subsequently
passes sequential repair of all seven originals, the exact saved intent and two
automatic successors on restarted copies, with matching 58-block cold ledgers.
It adds only tests and does not establish unattended nonce repair, a real funding
source or a universal reserve.

## Permanent node candidates

| ID | Exact change | Why include it / necessity | Lasting effect and evidence |
| --- | --- | --- | --- |
| P1 | Fixed restart ancestry; checks on startup, block/header/receipt imports, reorganization, pivot and mining/transaction readiness; refuse unsupported light mode. | Required for the agreed protection against an old isolated chain replacing the accepted recovery prefix. | Restricts eligible history permanently once configured. Compatible descendants retain ordinary fork choice and can reorganize. **Mainnet height/hash is still unset.** Review [anchor implementation](restart-anchor-implementation.md), [reset/pivot coverage](restart-reset-pivot-rehearsal.md) and missing end-to-end sync coverage. |
| P2 | Reconstruct expired tickets using the parent timestamp already used by execution; return an error for a missing reconstruction ancestor. | Required for demonstrated recovery/expiry-boundary reconstruction to agree with directly executed state. | Validation-sensitive bug correction. Existing ticket-commitment verification remains mandatory. No ticket price, lifetime or reward change. Review [original failures and corrections](restart-corrections.md), including synthetic boundaries and 128 real historical cases; full historical replay is incomplete. |
| P3 | Copy receipt logs, topics and data before handing them to another mining task. | Required to remove the reproduced miner data race exercised by normal ticket buying. | Memory ownership correction during mining. Review [race reproduction and passing checks](restart-corrections.md); this does not establish that every miner race is fixed. |
| P4 | Replace automatic ticket-buy orchestration with startup/periodic retry, canonical confirmation and retention of exact signed purchases; use actual pool contents for purchase conflicts; periodically resend the current-nonce pending purchase to known peers through bounded queues. | Required for the chosen unattended producer to recover from the demonstrated purchase failures. Manual buying is an operational alternative, not the selected launch workflow. | Remains active when auto-buy and mining are enabled; manual purchase conflict handling also changes. Local saved transactions are not consensus state. Review [purchase controller](restart-purchase-controller.md), [full-state handover](restart-full-state-handover.md), [sixteen interruption cases](restart-purchase-crash-rehearsal.md), [storage/peer failures](restart-purchase-storage-and-peers.md), [nonce rollback](restart-purchase-nonce-rollback.md) and [bounded resend/52-block cold continuation](restart-autobuy-rebroadcast.md). Sending does not establish inclusion or remote acceptance. Monitored nonce-gap repair is an explicit release decision; power loss and wider fork/stress coverage remain open. |
| P5 | Commit a reorganization's canonical indexes, transaction lookups and head markers in one database batch; propagate existing checkpoint errors before publishing. | Required to remove the reproduced partial fork-switch and ignored-checkpoint-error failures. A first block could be mined without this, but the known persistence defect would remain. | Affects ordinary permitted reorganizations. Does not change difficulty weighting or add checkpoint heights. Review [interrupted reorganization evidence](restart-crash-rehearsal.md), including ten original failing cuts. |
| P6 | Commit explicit rewind deletions and final heads together; guard state repair against missing ancestors or unavailable genesis state. | Required to make the supported rewind/repair path survive the demonstrated interruption and nil-pointer failures. | Affects local rewind/startup repair. No new balance or fork-weight policy. Review [rewind evidence](restart-rewind-rehearsal.md), including 30 original failing cuts, and [reset follow-up](restart-reset-pivot-rehearsal.md). |
| P7 | Skip ancient-store truncation only when the database explicitly lacks a freezer; repair header/fast head advancement when reimporting a known block after rollback. | Required for the demonstrated rollback/reimport path on Fusion's existing LevelDB-without-freezer layout. | Persistence and availability correction. Genuine storage errors remain errors. Review [rollback defects](restart-anchor-implementation.md) and [interruption controls](restart-crash-rehearsal.md). |
| P8 | Do not call the database repair routine after a corrupt database fails a read-only open. | Required for the investigation/recovery tools' promise to leave the source unchanged. It is not required to alter ordinary writable node operation. | A read-only corrupt open fails instead of attempting repair. Review `ethdb/leveldb/readonly_test.go` and [offline signing evidence](restart-offline-signing.md). This is also a candidate standalone upstream bug fix. |
| P9 | Remove the package-global parent-header list; use each chain reader for single-block work and explicit parent prefixes through the existing header-batch API. | Required to fix the reproduced import/miner race and deterministic cross-branch `unknown ancestor` failures. | Validation-context isolation, with no difficulty, ticket-economics or finality change. Review [parent isolation](restart-parent-isolation.md), baseline failures and corrected concurrency/header-batch tests. The [cold-header follow-up](restart-cold-header-validation.md) distinguishes cached parent routing from state availability; the header-only limit predates P9 and full import/cold reopen passes. Independent validation review remains required. |
| P10 | Start the discovery table's background loop only after the UDP transport has received its table. | Required to remove the inherited startup race reproduced by real seed discovery. | One goroutine-start line moved across two files. Affects discovery startup, with no wire-format, DNS policy, consensus or economic change. Review [discovery resilience](restart-discovery-resilience.md) and retained before/after race results. The relevant focused tests pass; three inherited full-package test failures remain documented. |
| P11 | Preserve a peer's original table timestamp; treat a timed-out reply collection containing validated neighbors as a successful discovery reply. | Corrects a bypass of the existing cache maturity filter and erroneous penalties against healthy small-network peers. The timestamp hunk alone failed the live persistence test; review both together. | Six added/one removed production lines in two files. Affects peer residence and persistence; no schema, DNS, wire-format, ticket or consensus change. Review [cache boundaries and cold restart](restart-discovery-cache.md), baseline failures, the timestamp-only regression and combined checks. |
| P12 | Parse bootstrap configuration without DNS, retain hostnames, resolve/retry asynchronously with deadlines and cancellation, and introduce authenticated allowed endpoints through discovery. | Supports the requested DNS-based introductions through outages and IP changes. It is a networking resilience feature, not a consensus prerequisite. | Changes v4 bootstrap startup and refresh behavior, including CLI/TOML and UDP-only seeds. Ordinary static/trusted parsing and v5 remain separate. Review [DNS behavior, bounds and live evidence](restart-bootstrap-dns.md); public networking checks remain open. |
| P13 | Reconstruct routing hashes for decoded seed records; do not replace an existing table entry with an older cached endpoint. | Prevents duplicate identities in different discovery buckets and stale cache interference with a newly resolved address. Review with P12. | Local seed-cache insertion correction, with unchanged record format and age limits. The targeted duplicate-address regression fails before and passes after correction; see [cache interaction](restart-bootstrap-dns.md). |
| P14 | Transfer discovery subnet reservations when endpoints change, reuse replacement reservations on promotion, start promotion maturity, and ignore probe/deletion results for superseded entries. | Corrects reproduced quota bypass/leaks, stale-endpoint overwrite/eviction and premature replacement persistence. Review with P11–P13. | Local discovery behavior after startup and recovery; no consensus, economic, wire-format or limit-policy change. One runtime file, 63 added/23 removed lines. See [address-move evidence](restart-peer-addresses.md), including deterministic before/after cases and a signed UDP move in an isolated namespace. |
| P15 | Reject the local node ID at the common discovery-table admission entry point. | Prevents self-contacts from occupying active/replacement entries and address reservations, and from suppressing empty-table refresh after real contacts disappear. | Three added runtime lines in `Table.add`. No timer, record format, wire protocol, ticket, fork-choice or consensus change. See [partition/self-contact evidence](restart-network-partitions.md), including four deterministic failures and a real signed-UDP admission failure before correction. |

## Source boundaries

Paths identify review locations; where shared, select the stated functions/hunks.
All non-test Go changes versus the pinned master are accounted for below or in
the recovery-only section. Tests and evidence must accompany any extracted patch.

| ID | Source files / boundaries |
| --- | --- |
| P1 | `core/restart_anchor.go`, `params/restart_anchor.go`, `params/config.go`, `core/genesis.go`; anchor hooks in `core/blockchain.go`, `core/headerchain.go`, `eth/api_backend.go`, `eth/backend.go`, `eth/handler.go`, `eth/sync.go`, `light/lightchain.go`, `miner/worker.go`. |
| P2 | `consensus/datong/consensus.go`: `getAllTickets` parent lookup and expiry cleanup only. |
| P3 | `miner/worker.go`: `copyReceipts` only. |
| P4 | `cmd/efsn/main.go`, `common/autobuy.go`, `common/fsntypes.go`, `internal/ethapi/autobuy.go`, `internal/ethapi/api_fsn.go`, `eth/api.go`; automatic-purchase notifications in `core/blockchain.go`; `RebroadcastTx` in `internal/ethapi/backend.go`, `eth/api_backend.go`, `les/api_backend.go`, and `rebroadcastTx` in `eth/handler.go`. |
| P5 | `core/blockchain.go`: reorganization batch and head-write/publication helpers. |
| P6 | `core/blockchain.go`: `SetHead`, `repair`; `core/headerchain.go`: `SetHead` / private `setHead` callback and batch. |
| P7 | `core/blockchain.go`: `truncateAncient` and known-block head advancement in `writeHeadBlock`; `core/rawdb/database.go`, `core/rawdb/freezer_table.go`: exported unsupported-operation sentinel. |
| P8 | `ethdb/leveldb/leveldb.go`: read-only corruption handling. |
| P9 | `consensus/datong/consensus.go`: remove `glb_parents` / `SetHeaders`, update `VerifyHeader` / `Finalize`; `core/blockchain.go`: remove setter calls; `core/headerchain.go`: use `VerifyHeaders` results. |
| P10 | `p2p/discover/table.go`: remove loop startup from `newTable`; `p2p/discover/udp.go`: start it in `newUDP` after transport initialization. The six direct table-test callers start their own loop. |
| P11 | `p2p/discover/table.go`: `bucket.bump` copies `addedAt` to the replacement; `p2p/discover/udp.go`: `findnode` clears only a collection timeout with a nonempty validated result. Both hunks are separate from P10's initialization hunks in the same files. |
| P12 | `p2p/discover/bootstrap.go`: bootstrap parser, TOML slice decoder and resolver workers; `node.go`: private hostname and shared endpoint parsing; `table.go`: hostname/literal separation and worker lifecycle; `udp.go`: supply network restriction; `p2p/server.go`: bootstrap slice type and literal TCP fallback; `cmd/utils/flags.go`: use bootstrap parser. |
| P13 | `p2p/discover/database.go`: `nextNode` reconstructs the private routing hash; `p2p/discover/table.go`: `loadSeedNodes` preserves an existing entry when loading cached contacts. |
| P14 | `p2p/discover/table.go`: `findnode`, `doRevalidate`, `updateIP`, `addReplacement`, `replace`, `bumpOrAdd`, `deleteInBucket`, shared `findNode`; extend `loadSeedNodes` preservation to replacements. |
| P15 | `p2p/discover/table.go`: three-line local-ID check at the start of `Table.add`, before locking or changing address reservations. |
| O1 | `cmd/utils/flags.go`: trim/filter explicit bootstrap lists. Inherited gateway usability fix; optional for the restart protocol. Does not create DNS discovery. Review independently if retained. |

P1, P5, P6, P7 and P9 overlap in chain/header code. Extract and test them in a defined
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

The [operator network-profile follow-up](restart-network-profile.md) adds no
runtime patch. It records tested configuration workarounds for inherited NAT,
diagnostic dump, discovery-flag and restored-peer-list behavior, plus the remaining
release endpoint/image changes. The current inventory is P1–P15.

The [packet-loss follow-up](restart-network-partitions.md) adds P15 after
reproducing self-contact admission and suppressed refresh. It exercises timeout,
retry and discovery recovery with kernel packet drops, and retains the earlier
timing-dependent failures and inbound-only limitations. No new consensus or
finality rule is proposed.

## Independent review handoff

Reviewers should identify the baseline and candidate commit, reference the row ID,
and report the concrete trigger, affected behavior, severity and reproduction for
each finding. Check the actual source and retained failure logs as well as these
summaries. Record unresolved findings and explicit dispositions before freezing
the release patch list; no row is independently approved by this document.

The highest-priority review surfaces are P1/P2/P9 validation behavior, P5/P6/P7
persisted-head consistency, P4 purchase recovery, and the separate signing tool's
approval/journal/key boundaries. Existing passing tests are evidence for their
specific scenarios, not a completed independent security audit. The
[restart plan](restart-plan.md) retains the wider data, timing, custody, networking
and release gates.
