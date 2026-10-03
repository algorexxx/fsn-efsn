# Fusion restart investigation record

> Historical investigation record captured from `fafab7b4` on 3 October 2026.
> The [consolidated launch plan](restart-plan.md) supersedes the task lists below.
> This file preserves dated evidence and rationale; later reports may close its open items.

Status: investigation and implementation plan; not a launch authorization or a completed security audit.

Last reviewed: 3 October 2026. Source baseline: local `master` / `develop` at `c5f0174` (5.0.3); recovery branch at `6981b00`; documentation branch at `c1806fc`. Narrow client corrections exist on the investigation branch; the complete restart implementation is still pending.

The [permanent node patch review list](restart-node-patch-review.md) separates
sixteen candidate fixes/rules from the recovery-only tool, optional bootstrap-list
handling and inherited gateway deployment material. Each candidate has a source
boundary, reason, lasting effect and evidence. Independent human/AI review and
resolution of findings precede selection of the final release patch set; the
investigation branch is not itself that selection.

The [monitoring and response guide](restart-monitoring-response.md) now
consolidates the recovery evidence into a proposed read-only observation and
manual-response policy. It identifies missing live saved-intent visibility,
deduplicated buyer warnings and legacy dashboard signal limits. No monitor or
alert routing is deployed. The [operator procedure](restart-operator-recovery.md)
now links a compact evidence matrix, including the passing uninterrupted rollback
and receipt-aware repair. Policy adoption, collector/delivery validation, named
coverage and real funding remain release gates; this monitoring work adds no node patch.

The [external snapshot observer](restart-observer.md) now collects bounded
read-only reports with explicit unknowns and common-height comparisons. Its
retained-data and fault tests cover nonce gaps, backing, receipt classification
and actual recorded equal-weight divergence. The [actual-service follow-up](restart-observer-services.md)
also passes eight external IPC/HTTP observations on compact synthetic nodes,
including controlled synchronization, a displaced receipt and endpoint loss.
It is separate from the node. [Durable snapshot history and incident review](restart-observer-history.md)
now retain observations/reviews across restarts, deduplicate conditions and reopen
reviewed incidents on recurrence. [Bounded block/receipt backfill](restart-observer-backfill.md)
now preserves contiguous ranges and displaced branches, with explicit gaps and
passing retained-fork/actual-service checks. [Ordinary-mining history](restart-observer-mining.md)
now passes, and [offline wallet ticket timelines](restart-observer-tickets.md)
match its retained ledgers with explicit coverage gaps. [Historical anchor acquisition](restart-observer-anchor.md)
now supports monitoring started later. [Read-only backup probes](restart-observer-preserved-inventory.md)
show sparse historical state, requiring baseline capture and preservation before production.
A [live reorganization test](restart-observer-reorg.md) now passes collection invalidation,
canonical catch-up and cold inventories. Wider forks, full financial accounting,
deployed-workload validation and notification delivery remain open. A [local history-cost follow-up](restart-observer-history-cost.md) fixes incident hash display and measures growing replay cost: 1,000 snapshots take about 0.69 seconds to replay and occupy about 27 MiB logically. Cadence and retention need further design before continuous deployment. The [mixed-workload follow-up](restart-observer-mixed-workload.md) now passes actual IPC/HTTP collection during six advancing-block rounds and preserves evidence through a 512 KiB logical-budget exhaustion check, with ordinary and race builds. The [opening-state follow-up](restart-observer-open-replay.md) now reuses the fully validated opening replay once, reducing paired reopen/status at 1,000 prior snapshots from 1.55 seconds to 0.74 seconds with byte-identical outputs and passing race/budget checks. Only external observer history handling changes. Longer history, retention and collection-failure notification remain open.

Latest progress: the D:-backed WSL environment contains a fully checksummed
disposable database copy. The [integrity and replay investigation](restart-integrity-investigation.md)
has verified all reachable current state and structural history through `B`,
completed baseline replay through 3,000,000, and passed 128 real historical
ticket-reconstruction cases. Continuation stopped cleanly at 2,613,376 as D:
approached its reserve; a cold read-only check confirms the saved head. A complete
checksum-verified working copy on C: completed 2,700,000 and passed a cold reopen
check, including execution of 20,000 blocks beyond the legacy checkpoint range.
Both earlier checkpoints remain preserved. On 25 September a separately copied,
checksummed D:-backed ext4 target completed baseline continuation from 2,700,000
to 3,000,000 with the retained executable, read-only sources and storage guards.
The final cold check passed at 13:33:45 UTC; the closed database is about 4.65 GiB.
This verifies the retained baseline, not historical execution of the newer P1–P15
candidate. Phase results belong in the linked report and captured evidence.

The [synthetic bridge experiment](restart-bridge-experiment.md) demonstrates
eight independently imported blocks. [Narrow corrections](restart-corrections.md)
address the reproduced receipt-log race, reconstruction expiry mismatch and
missing-ancestor panic. The [purchase controller](restart-purchase-controller.md)
adds startup attempts, periodic retry, signed-transaction recovery and canonical
receipt monitoring, with explicit pauses for nonce conflicts and missing nonces.
The [automatic-purchase interruption follow-up](restart-purchase-crash-rehearsal.md)
passes sixteen abrupt-exit/recovery cases per platform, including Linux race
detection: exact saved intent, restored/lost pool, confirmation, nonce replacement
and adoption of a pool purchase. This required no production-code change and
does not establish power-loss durability or live peer-reorganization behavior.
Complete historical execution, the accepted restart anchor and production
operator rehearsals remain outstanding. Full-state worker recovery and a
[guarded two-node handover](restart-recovery-construction.md) now pass with
public test keys. The [durable signing-journal follow-up](restart-signing-journal.md)
now passes reservation, conflict, forced-process-termination and exact-artifact
recovery tests. The known saved backup has an empty transaction journal and no
automatic-purchase record for either wallet. Production signing integration,
real-key custody and the live gateway pool remain separate gates.

The [offline signing integration](restart-offline-signing.md) now passes on
Windows and Linux (with Linux race detection), using both small synthetic
databases and complete preserved state with public test-key substitutions.
Eleven complete-state process cuts per platform cover exact artifact recovery,
independent imports and cold account/receipt/ticket agreement without another
signature. Unfinished attempts, active writers and changed review inputs are
refused. Owner-by-owner accounting of the controlled three-block prefix also
passes. Production key access, operator approval and key/journal custody remain
open; no real key was used.

The [reviewed-input and handover-policy follow-up](restart-signing-approval.md)
now adds canonical approval-byte checking and immutable journal limits: one
backup block or two consecutive donation blocks, bound to the initial parent,
purchaser, executable and chain configuration. Small-state Windows and Linux
rehearsals (with Linux race detection) pass the same eleven cuts and quota/input
refusals. The [operator command follow-up](restart-operator-workflow.md) now passes
actual review/prepare/init/sign/export commands and bounded encrypted-key
preflight on both platforms, with Linux race detection. Wrong passwords leave no
reservation; completed and uncertain attempts avoid key access; both database
locks remain held during credential checks. Complete report rebuilding prevents
altered human-readable metadata from differing from the approved block. The
same executables now also pass the [complete-state command rehearsal](restart-full-state-operator.md):
three fresh copies per platform, exact cross-platform blocks and reports,
separate-process imports/cold checks and complete changed-account accounting.
No production source change was needed. Trusted operator review, actual
wallet/timing selection and final custody checks remain before real-key use.

The [complete preserved-data restore rehearsal](restart-snapshot-restore.md)
has packaged the original 117 GB database onto the user-selected W: network
share. Every packaged file hash matches the independently retained original
backup manifest. Source index inspection and Windows/Linux packaging failure
tests pass. Full restoration, identical restored index reports and two separate
restored-node startup/RPC/P2P processes passed overnight on 25 September. The
release download/mirror and final recovery-data procedure remain unproven. New bulk data stays
off the nearly full D: drive.

The [anchor entry-point investigation](restart-anchor-investigation.md) now
reproduces heavier-chain replacement and legacy-checkpoint gaps involving stored
forks, canonical indexes, headers, receipts, pivot commits and startup initialization/rewinds.
The [separate anchor prototype](restart-anchor-implementation.md) now checks these
entry points, rejects incompatible startup data before repair, and gates mining
and transaction readiness below the anchor. It also fixes two reproduced rollback
defects. The production height/hash remains unset. Light mode explicitly refuses
an active anchor. An isolated [multi-process rehearsal](restart-node-rehearsal.md)
now exercises the actual service, IPC, miner and peer downloader. Fast/freezer
release support and general state acquisition remain unproven. The later
[full-state two-node rehearsal](restart-recovery-construction.md) covers controlled
handover, live block propagation and post-crash suffix catch-up, with explicit
historical-data limitations. Adding a legacy
checkpoint is not an adequate implementation.

The [interrupted-write rehearsal](restart-crash-rehearsal.md) then reproduced
partially published reorganizations that passed cold startup. Canonical branch
replacement now commits its indexes and all head markers in one batch. A short
archive-style fixture covers before/after process exits for linear import,
compatible reorganization and rollback. The [explicit-rewind rehearsal](restart-rewind-rehearsal.md)
also reproduced stranded head pointers and a missing-ancestor repair panic.
Rewinds now commit deletions and head pointers together; synthetic interruption
checks include below-anchor, split-head and missing-state/body cases. Complete
pruning/freezer recovery and large reorganization batch cost remain open gates.

The [reset/pivot follow-up](restart-reset-pivot-rehearsal.md) adds eighteen crash
cuts around reset, three direct pivot positions and receipt-import-to-pivot
publication. Missing target state/body are rejected without database changes.
These cases require no further production edits. Complete state acquisition,
genesis resynchronization and freezer recovery remain separate release gates.

## 1. Objective and agreed scope

Restart Fusion from an explicitly accepted historical state, using the smallest justified changes to the existing client. Preserve historical verification and accounting. Before public economic use, establish a mandatory restart boundary so a previously unknown, incompatible continuation cannot replace the restart merely by presenting greater accumulated difficulty.

The backup is a candidate starting point, not a claim that no later valid blocks exist. Additional history can be assessed before the launch decision. Once accepted and used, the restart boundary must not silently move in response to a returning operator.

On 27 September Peter requested an enode from a possible surviving operator.
The [surviving-node investigation note](restart-surviving-node.md) records the
pending response, a single read-only Node Manager command for the operator,
and the checks needed before choosing ordinary synchronization over historical
recovery. Continued mining is unverified; recovery testing continues meanwhile.

The working launch target, selected on 24 September 2026, uses two nodes initially operated by Peter: backup wallet `0x9fc4c40e50f902b9aa641b4a32ebaafa5c9386a1` signs one historical recovery block without buying another ticket, and donation wallet `0xa3ce60d2dbf51afa0ab106df1c44a2e48853817a` takes over production and replenishment. That first recovery block must include the donation wallet's funded, long-lived first ticket purchase; it cannot wait until the donation node starts mining. The donation signer then bridges to the planned present-day timestamp. The backup wallet has two historical tickets: one is selected/refunded, while the other expires and is removed without another refund of its expired interval. The [wallet handover investigation](restart-wallet-handover.md) records passing sparse consensus tests for this exact one-backup-block arrangement, the earlier longer alternative, and the donation wallet's preserved funding. The [full-state follow-up](restart-full-state-handover.md) now passes complete-state accounting, separate-process imports and actual worker/automatic-buyer restart on Windows and Linux. The [guarded construction and two-node rehearsal](restart-recovery-construction.md) now passes unsigned command review, guard-before-sign checks, peer handover, automatic mining immediately after cleanup, forced-process restart and matching cold account ledgers. Production signing/custody, backup purchase drain and published data distribution remain open; the complete backup now passes local packaging, restore and service checks. It also reproduces an accepted but stranded jump if its replacement purchase is omitted: controlled construction must require that purchase and a usable successor ticket before signing or publishing. Stop our use of the backup key after verified handover and return operation to its owner; he may run his own node later. Publish the anchor-enforcing release, verified recovery data and a reachable DNS discovery endpoint, which the continuing producer may also host. A separate validator fleet or dedicated seeds are not required for day one. Other holders can download the release, follow the data/configuration checks, synchronize and choose to produce blocks using ordinary funded tickets. Joining needs no new operator allowlist. Demonstrate separate-process verification during rehearsal without treating that verifier as a mandatory second permanently hosted node.

In scope:

- Preservation and validation of the recovered data.
- A tested way to resume ticket purchases and block production.
- Enforcement of the accepted restart history across import, synchronization, mining, and existing databases.
- A workable initial operator setup, a path to independent participation, peer discovery, release infrastructure, operational monitoring, and a sustainable way for new nodes to sync. A bootstrap operated by one team is an option; organizational independence is not a DaTong validity rule or a fixed prerequisite for the initial restart.
- A GitHub organization and maintained repositories, preserving upstream history and notices.
- Investigation and triage of defects that could prevent a safe restart.

Explicitly outside the agreed implementation scope:

- New ongoing finality, voting, or consensus economics.
- Automatic periodic checkpoints or arbitrary maximum reorganization depth.
- Burning, freezing, transferring, or excluding disputed Foundation/founder holdings.
- A new genesis or wholesale state migration as the default approach.
- Unrelated consensus fixes bundled into the restart without a separate decision.
- Broad code restructuring, module renaming, or replacing Fusion with a current Ethereum client.

A serious security finding can block launch and require a scope decision. Keeping changes small does not mean ignoring a demonstrated blocker. After the restart boundary, ordinary Fusion fork choice continues; later competing descendants of the accepted anchor remain subject to its existing security assumptions.

## 2. Evidence and present state

The detailed observations and ticket IDs are in [restart-investigation.md](restart-investigation.md). The preservation/deployment history is in [historical-gateway-recovery.md](historical-gateway-recovery.md) and [gateway-endpoint.md](gateway-endpoint.md).

A fresh, read-only RPC batch was captured during this review:

- [Requests](evidence/restart-2026-09-23/requests.json).
- [Raw responses](evidence/restart-2026-09-23/responses.json), retained without parsing and reserializing large numeric values.
- [Capture metadata and response SHA-256](evidence/restart-2026-09-23/metadata.json).
- [Derived time-lock coverage calculation](evidence/restart-2026-09-23/historical-refund-coverage.json).

Confirmed observations from that gateway:

| Item | Observation |
| --- | --- |
| Chain ID | 32659 |
| Candidate historical head, called `B` below | 15,130,080, dated 7 October 2025 |
| Header and state identity | Recorded in the linked evidence and investigation |
| Saved tickets | 491 tickets across eight owner addresses |
| Latest saved ticket expiry | 6 November 2025 |
| Operator-controlled address, as reported by the operator | `0x9fc4c40e50f902b9aa641b4a32ebaafa5c9386a1` |
| Tickets for that address | Two; both expired relative to present time |
| Liquid balance for that address at `B` | Approximately 3,225.54 FSN |
| Time-lock coverage for that address over the sampled present-day month | 10,000 FSN |
| Gateway operation | Zero peers and mining disabled |

Eight owner addresses do not establish eight independent operators. Key control has not been challenged or exercised. Ticket value, liquid balance, and future time-lock rights must not be added together as if they were independent liquid principal.

Limitations:

- These RPC results come from one recovered node; they are not independent validation of the chain.
- File checksums in the recovery report establish faithful copying, not the correctness or finality of the source history.
- Complete structural block/receipt coverage and reachable current-state traversal now pass. Full replay and all historical state remain unproven; replay through 2,000,000 passed, retaining the legacy checkpoint shortcuts.
- No production restart blocks have been constructed or signed. Synthetic blocks using a public test key have now been constructed and imported; see the experiment report.
- No operator private key was read and no production transaction was submitted. Synthetic tests sign with the public key-1 test key and submit only to isolated disposable nodes.
- Go 1.21.3 runs the growing synthetic restart suite on Windows and Linux. Original baseline race failures and their passing corrections are retained separately; current counts and exact results belong to the linked evidence reports. Legacy characterization cases deliberately reproduce defects, while enabled-anchor cases require rejection. Production-release readiness remains unproven. The reviewed workflow named `Build-And-Test` currently only builds.

## 3. Corrections and additional findings from the second review

### 3.1 Expired tickets do not make every unchanged-rule recovery impossible

The confirmed statement is that none of the saved tickets can authorize an ordinarily validated successor with a present-day timestamp. It does not yet follow that ticket-validation exceptions are unavoidable.

At a historical timestamp before expiry, selecting one of the operator's non-genesis tickets refunds its time-lock value under existing rules. Independent interval arithmetic over the recorded balances shows:

- Saved time locks alone provide zero continuous coverage over the sampled interval from shortly after `B` through 23 October 2026 because there is a gap.
- Adding the ordinary selection refund of either old ticket provides 5,000 FSN of continuous coverage over that interval.

The calculation is in the linked derived evidence. It only adds interval values and measures their minimum. Subsequent Go tests confirm the refund coverage and an eight-block bridge in a synthetic fixture, not in the full recovered mainnet state.

This makes a short historical-timestamp bridge a concrete experiment to run before selecting a consensus exception. It may need construction tooling but fewer production consensus changes. Its economic effects and timestamp meaning still need an explicit decision.

### 3.2 A successful local mining log is insufficient evidence

`miner/worker.go` writes a sealed block using `WriteBlockWithState`, rather than routing it through the same validation path as a downloaded block. That write path expects already prepared state. Every rehearsal block must therefore be imported and executed by a separate verifier. Compare state root, receipts, ticket commitment, and accounting, not just height or a miner log.

### 3.3 Ticket reconstruction must agree with direct state

`getAllTickets` has cache, state, and receipt/snapshot reconstruction paths. Normal finalization clears tickets using parent time; reconstruction ends with cleanup using the requested header's time and verifies the resulting ticket commitment. A large time jump can expose a difference between these paths. A bridge that only works while its original state is cached is not acceptable.

Test cold caches, pruned/missing historical state, ticket ordering/serialization, receipt-based reconstruction, and the time-jump block and its successors. Existing error paths also need review; source inspection alone does not establish their behavior under a real recovery workload.

Update: ten synthetic cases cover steps 1–4 with up to four consecutive missing
states; three more cover expiry just before, at, and after a historical successor.
The temporary parent-time overlay resolves all reproduced commitment mismatches
without changing selection or the prepared header. Real historical replay and
platform coverage remain outstanding.

A separate test now reproduces a nil-pointer panic when the fallback's ancestor
lookup returns no header. Its error formatter dereferences that missing header.
The parent-time overlay does not fix it. Correct missing-data handling must return
an explicit error while preserving the requested ancestor identity, not invent
state or silently fall back elsewhere.

### 3.4 Maturity conversion and purchase ordering matter

Fusion ECO processing calls `ProcessMatureFSN` after transaction execution using parent time. It can convert qualifying perpetual time-lock value into liquid FSN for touched accounts. Gas prechecks happen earlier. A future time-lock balance therefore is not simply a liquid balance available at every step.

The test ledger must distinguish liquid balances, time locks, outstanding tickets, fees, rewards, refunds, and maturity-conversion logs. Do not globally substitute a new time reference for every native operation or EVM call to fix one purchase.

### 3.5 Legacy checkpoints cannot simply be extended

The current checkpoint range skips normal ticket/difficulty/expiry checks in header verification and raw-transaction checks in body validation. Raising its end height would expand these shortcuts. Startup also rewinds a database when configured checkpoints disagree, which is inappropriate as an unannounced migration policy for a returning operator.

There is an additional source-level concern: the reorganization code supplies a descending chain to a checkpoint helper that stops at the first block above the last checkpoint. Other import checks may prevent an exploit; no end-to-end bypass has been demonstrated. The new restart boundary needs tests for pre-existing side chains as well as incoming blocks.

### 3.6 Branch separation is distinct from transaction replay protection

The peer handshake checks protocol version, network ID, and genesis. Transaction signatures use chain ID; the legacy signer paths also accept some unprotected transactions. A different network ID or different bootnodes does not prevent a signed transaction being manually relayed to another compatible branch.

Preserving the original chain ID favors compatibility, but replay may be possible when nonce, balance, and execution conditions also match. Changing chain ID globally would break historical signature verification. Decide whether to retain the ID with clearly understood replay exposure or separately specify activation-aware transaction-domain separation, including legacy and typed transactions, wallet APIs, stored chain configuration, and contracts. No new ID or replay scheme has been selected.

### 3.7 Rehearsal signatures can have economic consequences

The client has a multiple-mining report mechanism. `CheckAddingReport` checks differently signed headers with the same parent and coinbase, within its report-depth rules; it does not require both branches to have become canonical.

Use synthetic keys for competing-block experiments. Do not repeatedly sign alternative production-parent headers with the real staking key and assume isolation makes the signatures harmless. Define controlled signing, artifact custody, and the relationship between any real-data rehearsal and the final accepted block before using that key.

### 3.8 DNS support is narrower than a general DNS discovery system

Discovery v4 resolves hostnames to an IP when parsing; it chooses the first returned address. It does not implement periodic DNS refresh. An unresolved v4 bootnode currently causes fatal startup. The reviewed v5 parser requires a literal IP. DNS-based v4 bootnodes and signed DNS discovery trees are different features; the latter is not established here.

The [discovery resilience rehearsal](restart-discovery-resilience.md) now verifies
that one unresolved CLI v4 seed aborts startup even alongside a healthy seed or
with `--nodiscover`; explicit empty lists work. Real peers continue exchanging
messages after a seed stops, and stranded new nodes recover through an added
static peer. It also exposed an inherited discovery startup race: P10 moves one
goroutine start until its UDP transport is initialized. Ten characterization
cases pass with race detection after that correction. Full P2P suites retain
three baseline-reproduced test failures; see the report for scope and limits.

The [peer-cache follow-up](restart-discovery-cache.md) demonstrates cold-process
reconnection from genuine saved contacts after the original seed stops, with no
bootstrap/static peers and outbound dialing disabled on the community peer. Short
visits and fresh installations do not supply that fallback. Contacts have age
limits; P11 fixes lost timestamps and erroneous sparse-reply penalties together.
The [bootstrap DNS follow-up](restart-bootstrap-dns.md) now implements P12:
hostname-preserving CLI/TOML parsing and asynchronous bounded resolution/retry.
P13 corrects duplicate restored seed identities and stale cached endpoint
reinsertion. Live tests cover DNS recovery, UDP-only introductions, multiple
answers, loopback IP moves, cancellation and cold cache fallback with NXDOMAIN.
The [address-move follow-up](restart-peer-addresses.md) adds P14: correct subnet
reservation transfer and replacement promotion, and ignore results from probes
of superseded entries. Deterministic failures and a signed UDP move across
simulated public subnets are reproduced before and pass after correction.
Public NAT/firewall/IPv6 deployment and independent operators remain unverified.

The [operator network profile](restart-network-profile.md) now inventories old
infrastructure references and verifies same-IP two-node ports, NAT advertisement
and restart, effective restored peer lists, and IPv6 discovery/RLPx in isolation.
It provides an actual-command-tested template with explicit v4/v5 and peer-list
settings. No additional runtime patch is added. Keep the public introduction on
the long-lived donation node's P2P identity; on one IP, use donation 40408 and
temporary backup 40409 for both TCP and UDP. NAT/dumpconfig/flag limitations and
their explicit configuration workarounds are recorded in that report.

The [partition follow-up](restart-network-partitions.md) uses real packet loss to
check connection timeouts, redial and discovery recovery. It reproduces a local
self-contact occupying the discovery table and suppressing empty-table refresh,
then adds P15's three-line exclusion. Deterministic and signed-UDP before/after
cases establish the defect; earlier timing-sensitive failures are retained.
Keep normal outbound dialing enabled. The separate
[miner partition follow-up](restart-miner-partitions.md) extends the investigation
to ordinary miners, full sync, purchases and cold recovery. It also reproduces
delayed publication of already-signed work after `miner_stop`; clean process
shutdown and inspection of the resulting head are required for signer handover.
The [continuous-miner follow-up](restart-continuous-partitions.md) now leaves
both miners running through longer packet loss and ordinary reconnection. A
complete small synthetic history avoids the sparse fixture's missing ancestry.
The nodes converge and advance, but the losing buyer remains paused on a nonce
gap: both the initial repeated-outage probe and the stricter single-outage run
fail unattended replenishment. The strict second outage and final cold acceptance
are not reached. A separate [live manual-repair case](restart-live-nonce-repair.md)
now passes four missing nonces, the exact saved intent, two fresh automatic
successors and both cold databases while retaining normal mining through repair.
It uses preserved transaction bytes and many synthetic tickets. The [small-reserve and retrieval follow-up](restart-small-reserve-and-retrieval.md)
now verifies discarded-block RPC retrieval and the existing offline saved-record
command, but two small-reserve runs fail repair funding after the losing owner
has no tickets. The [funded-repair ledger](restart-funded-repair.md) reconciles
ordinary interval losses/returns and records two failed repairs after successful
5,000-FSN transfers plus one conditional pass: six original purchases, the exact saved
intent, four automatic successors and both cold nodes. The successful branch
has one first-retreat loss and more remaining usable rights than the two-loss
failures. It does not establish a universal reserve or that a longer wait fixes
the failed cases. The [controlled reserve comparison](restart-controlled-reserves.md)
now replays the same zero-ticket parent after two finite-ticket losses into four
branches. No funding remains insufficient through twelve healthy blocks; 5,000
and 10,000 FSN transfers each permit seven purchases with ordinary selection
returns. Another first retreat after a 5,000-FSN transfer leaves the next
purchase unfunded again. Both cold databases and interval accounting pass in
every branch. These are controlled signed-block comparisons, not live automatic
recovery. The [handover funding audit](restart-handover-runway.md) now checks both
retained complete-state sequences, including replacement funds before refunds
and the transition from long-lived bridge tickets to ordinary 30-day purchases.
The [manual operator procedure](restart-operator-recovery.md) collects the
demonstrated checks for release review. The [live single-producer complete-state
outage](restart-full-state-outage.md) now passes packet loss, SIGKILL with a pending
purchase, byte-identical recovery, automatic successors, ordinary peer catch-up
and both cold complete-account ledgers. This matches the day-one producer/verifier
topology and does not create competing branches. The [funded participant
entry](restart-full-state-participant.md) now demonstrates a hypothetical ordinary
contribution of existing mature rights, entry by public test key 3, shared live
production and both cold complete-account ledgers. That contribution is not
authorized real funding or a launch requirement. The [complete-state partition](restart-full-state-partition.md)
then failed before repair: both branches continued separately. Both cold account
ledgers passed; stopped-node diagnosis found equal difficulty and missing
historical ancestry in the compact fixture. The [genuine-history follow-up](restart-partition-history.md)
now supplies a verified 67-MiB segment and passes the exact failed ancestor request.
A fresh competing-producer attempt stalls earlier on funding. Its stopped
heavier-peer recovery and matching cold ledgers pass; the donation owner has
zero tickets, 2,021.665544264 liquid FSN and correct saved/canonical nonce 7,
but no usable coverage for the purchase. Complete-state rollback/manual
repair, real reserve funding, monitoring and wider fork coverage remain open.
These follow-ups add no runtime patch.

### 3.9 Purchase admission and automatic retry are separate gates

The original backup-only funding experiment exercised the real purchase argument
builder, pool and execution against observed-balance fixtures. Before that
wallet's first historical refund, the pool admits a long purchase that execution
rejects: the pool checks funding from wall-clock time, whereas execution needs
coverage from historical parent time. The selected donation-wallet route has
12,020.102 liquid FSN and funds its first purchase without waiting for the backup
wallet's refund; its separate complete-state accounting now passes.

Default purchases on the historical head expire in November 2025 and are rejected
by the pool. A present-day start also fails the parent-plus-three-hours rule.
The selected Candidate A's purchases in steps 1 and 2 therefore need explicitly extended ends
while retaining valid historical starts. No general purchase-rule relaxation has
been shown necessary.

The upstream auto-buy loop depended on a new canonical head, dropped purchase
errors and had no initial attempt or timer-based retry. Tests reproduced stalls
after a failed purchase and a cold restart with an empty pool. The investigation
branch now has the [purchase controller](restart-purchase-controller.md), with
initial attempts, bounded retry, signed-transaction journaling and canonical
receipt checks. Complete-state worker tests and the [actual two-node service
rehearsal](restart-recovery-construction.md) now pass startup and process restart.
Systematic journal crash boundaries, live peer reorgs and the real backup wallet's
existing signed transactions remain separate checks. Ordinary automatic buying
is still unsuitable for the historical bridge; construct and review those
long-lived purchases explicitly.

## 4. Design invariants

Every proposed implementation and release must satisfy these requirements:

1. Preserve accepted historical block hashes and replay behavior. Do not change genesis or rewrite the preserved database to manufacture stake.
2. Fund new tickets from existing authorized balances/time-lock rights. No free ticket allocation, unconditional expiry extension, or extra principal refunds.
3. Keep one ticket purchase per owner per block and ordinary signature, nonce, gas, and transaction checks unless a narrowly identified restart exception is separately specified.
4. Make every exceptional rule deterministic from published chain data and restart parameters, never a node's wall clock or an optional operator-local preference.
5. Do not weaken validation below the restart boundary or leave temporary privileges active afterward.
6. Bind any transition exception to the agreed network, parent identity, height, and exact specified transition conditions.
7. Apply the restart ancestry restriction before incompatible history becomes canonical through any supported entry point.
8. Reject a missing or conflicting required restart configuration clearly. Do not silently operate unprotected or silently erase an operator's incompatible history.
9. Make a new node able to obtain and verify the accepted history without depending on the original operator's private database or key.
10. Keep explorer preservation, experiments, public RPC, validator signing, and monitoring operationally separated.

## 5. Compare two recovery candidates

Both candidates require the accepted restart anchor. Candidate A is the working route for the selected two-wallet startup; exact production blocks and launch remain unapproved. Its reproduced reconstruction defect has a narrow correction and passing follow-up checks. Candidate B remains a fallback and has not been implemented or tested.

### Candidate A — a short bridge under existing ticket rules

Selected one-backup-block experiment sequence, not executable launch instructions:

1. Construct the sole backup-signer block just after `B`, with a valid historical timestamp and ordinary ticket selection. Include the donation wallet's funded long-lived first ticket purchase; exclude unrelated transactions and backup-wallet purchases. Verify selection, difficulty, retreats and the original selected-ticket refund.
2. The donation signer advances to the planned current-time timestamp using that new ticket. Require its replacement purchase with an explicit interval spanning the jump and verify a surviving usable successor ticket before signing/publication. A jump without that purchase can be accepted while leaving only expired tickets, stranding production. Account for the backup wallet's unused expired ticket without assuming a second selection refund.
3. Continue donation-only production through expired-ticket cleanup and ordinary replenishment. The sparse test leaves one successor ticket after its second block, but real-address ordering and full-state accounting must be checked.
4. Verify actual worker/construction behavior, independent import, cold reconstruction, automatic-purchase startup and restart before accepting exact recovery artifacts.

Source rules allow old timestamps subject to their checks, and ticket lifetimes have no maximum in the inspected validation. The donation wallet's preserved liquid funding allows its first purchase without waiting for the backup wallet's refund. Sparse Windows/Linux tests now demonstrate this transition without new ticket-validity exceptions. The earlier backup-only sequence, which needs a historical refund before its own long purchase, remains recorded in the bridge experiment and the handover report's alternative.

Reasons to reject or revise it:

- Any block fails independent stock-rule verification or replay.
- Ticket reconstruction differs from direct state at the time jump.
- Required funding, gas, nonces, or replenishment cannot be satisfied.
- Retreat penalties or other historical-time economic effects are unacceptable to participants.
- The necessary tooling or operational complexity exceeds a narrow explicit transition.
- Timestamp presentation or application effects cannot be made clear and acceptable.

The bridge would be newly created recovery history bearing historical timestamps, not evidence those blocks existed in 2025. Publish this fact and the full ledger. Do not simulate a year of catch-up mining or change the operating system clock as a launch procedure.

Construction must explicitly set the purchase lifetime in steps 1 and 2: their
parent timestamps are still historical, and default 30-day purchases fail today's
pool checks. The ordinary worker uses wall-clock timestamps, so stock mining
controls alone do not construct these historical bridge blocks. The tests prove
the mechanism, not the availability of finished construction tooling.

### Candidate B — an explicit transition at current time

If Candidate A is unsuitable, specify a tightly bounded transition from `B`:

1. Authorize the defined old ticket/signer for that transition despite expiry, retaining compatible signature, selection, order, and difficulty checks.
2. Use the specified transition timestamp for its authorized ticket purchases so present-day time-lock rights can fund them. Keep ordinary debit and fee accounting.
3. Expire the old ticket set consistently before successor selection and ensure at least one live ticket survives. Specify selected/retreated ticket handling without duplicating principal.
4. Preserve ordinary rewards unless a separately agreed exception explicitly states otherwise.
5. Resume normal ticket rules in successors, proving that the first successor can buy replacement stake before consuming its selected ticket.

Required implementation surfaces include header/seal verification, block construction, transaction execution, ticket cleanup/reconstruction, purchase RPC construction, pool admission, and automated purchases. It may be possible to use dedicated construction tooling instead of widening general RPC behavior; choose the smaller proven design.

### Selection gate

Produce a comparison with exact block sequence, required edits, total state changes, owner-by-owner economic effects, replay results, and operational steps. Choose the smallest complete design, not the fewest lines at the cost of hidden exceptions. Keep the unsuccessful candidate's findings, not its unused production code.

### Full-state rehearsal with limited disk space

The [test-only extractor](restart-state-export.md) now uses the
existing `core/state.NewStateSync` and `trie.Sync` scheduler to extract only data
reachable from the preserved state root. It already follows account/storage
tries and code references, including native data represented by account code
hashes. This avoids another complete 117 GB historical-database copy and a custom
read-through overlay with its own deletion/iterator semantics. The closed state
database is about 504 MiB. Synthetic extraction/corruption/interruption checks
pass on Windows and under the Linux race detector. The first D: extraction
stopped at the reserve and remains unverified. A fresh C: artifact passed complete
cold verification natively on Windows, matching the exact root, state inventory
and all tickets. The retained Linux writer's identity is explicitly checked.
Two additional execution copies fit within the measured C: capacity, subject to
fresh reserve checks before creating them. The exact artifact remains preserved.

1. Prototype the extraction with synthetic account/storage/code/native-data
   fixtures. Exercise missing/corrupt source data, interruption, rejected target
   reuse and cold reopening. Verify each fetched blob's Keccak hash before
   submitting it to the scheduler; its `Process` method expects the caller to
   establish that identity. Use existing raw database helpers for code formats.
2. Run against the verified disposable backup mounted read-only in an isolated
   network/mount namespace. Create a new explicitly named local target and retain
   source head/root/config and executable identities. Apply the existing 20 GiB
   output-filesystem / 50 GiB host reserves before each bounded write batch. An incomplete
   extraction must not be marked ready or installed as a chain head.
3. Close the target, reopen without any source fallback, and run the existing
   complete state traversal. Require the original state root and recorded
   inventory: 801,355 accounts, 2,886,305 storage leaves, 33,437 code/native-data
   references and 262,368,983 referenced bytes. Verify all 491 tickets and their
   commitment separately. Record the closed database size and checksums before
   deciding whether two independent execution copies fit.
4. Preserve that exact-state artifact. Add only explicitly bounded historical
   context needed by a separately labelled synthetic recovery fixture. Any public
   test-key substitution must have an exact state-difference ledger and cannot
   be presented as a valid continuation of the original backup block. Confirm
   required ancestor access from execution, ticket selection and difficulty
   adjustment rather than silently skipping a missing header.
5. Rehearse bridge construction and independent import with full account/storage
   state, cold reopening, reconstruction and accounting. Actual original-history
   continuation still requires the later reviewed real-signer procedure; this
   extraction does not require the operator's private key or create recovery
   blocks on its own.

## 6. Accepted restart anchor

Let `A` be an exact accepted block at the end of the reviewed recovery sequence. With a one-block transition, `A` may be `B+1`. With a bridge, it should normally commit to the entire reviewed sequence through the time jump and required cleanup. The height and hash remain undecided.

Before public use, publish a release/manifest committing to `A` and the accepted prefix. At heights at or above `A`, a candidate chain is eligible only if its ancestor at `A` is the exact agreed block. Common ancestry at `B` alone is insufficient. Partial sync below `A` must follow a defined verification policy and must not be exposed as a launched, settled chain.

The restriction is a separate rule from legacy checkpoint validation shortcuts.
The [24 September investigation](restart-anchor-investigation.md) demonstrates
why this separation and ancestry validation are required. In particular, a
stored incompatible fork can leave the checkpoint's canonical index apparently
correct while the actual head descends from another block. Startup preflight
must check linked ancestry and all head markers before any automatic rewind.
The rule must be loaded before chain construction, unlike the current CLI's
late initialization of legacy checkpoints.

The rule must cover:

- Full block import, including files and network fetches.
- Header validation, header insertion, and canonical header rewrites.
- Receipt/fast synchronization and pivot/head commitment, if supported at launch.
- Light-client paths, if supported; otherwise explicitly exclude them from launch support rather than assuming safety.
- Locally mined block writes and any path that advances a canonical head.
- Reorganizations onto previously stored side chains.
- Startup with an existing compatible, incompatible, below-anchor, or partially synchronized database.
- Operator recovery/rewind tools, defining how they re-establish the required anchor before serving the live chain.

A peer challenge for the anchor can reject incompatible peers early, but cannot replace ancestry validation: a peer could serve the right anchor while advertising descendants of another branch.

Two-stage production process:

1. Use isolated construction/review tooling to produce and verify the proposed recovery sequence and exact block bytes.
2. Freeze `A`, issue the final anchor-enforcing release, and have launch participants import the same artifacts. Do not expose experimental construction mode as a production bypass switch.

If the artifact becomes stale before launch, stop and revise it through the same review process. Do not start public use while its identity or ticket runway remains unsettled. A returning operator can preserve their old database, adopt the accepted release, and sync separately; incompatible balances and rewards are not merged.

## 7. Work phases and completion gates

### Existing-funds recovery follow-up — 27 September 2026

The [existing-funds investigation](restart-existing-funds.md) preserves the prior
funding failure and tests its exact saved purchase after ordinary contributions
of 1,200 FSN from the backup test account and 1,800 FSN from the entrant. The
controlled execution and both cold complete-state ledgers pass. These are
hypothetical contributions, not authorized real funding or a launch requirement.
The first live continuation stalls at the same head: the entrant's replacement
is broadcast before the sole eligible producer starts mining, and finalization
refuses to consume the last ticket without a replacement. Source inspection
identifies the initial peer-transaction acceptance gate as a plausible cause.
Starting both mining services before either buyer restores thirteen blocks of
production, but the stronger test still fails: the donation's correct-nonce
purchase remains pending while only the entrant replenishes. Do not misclassify
a pending-delivery issue as a nonce gap or assume that changing startup order
established complete recovery.
Both cold pools accept the two saved purchases at their correct canonical
nonces, and both complete databases plus the corrected interval audit agree
across 31 blocks. The accounting correction handles a legitimate automatic
mature-lock conversion log; its initial one-log assertion failure is preserved.
No new retreat occurred in the thirteen live blocks.

The [exact delivery follow-up](restart-purchase-delivery.md) now passes remote
pool admission checks against retained historical states: the same bytes are
rejected before the first live block because their start time exceeds the
recipient head by more than three hours, and accepted afterward. Direct submission
of the unchanged saved purchase to the surviving producer then passes actual
two-service replenishment for both owners without more funding or a replacement
signature. Both cold databases and independent interval accounting agree across
forty blocks; the earlier thirty-one are unchanged. This establishes explicit
delivery recovery, not automatic recovery of the original peer connection.
The [peer retry follow-up](restart-peer-purchase-retry.md) now captures that
transaction-before-block sequence through the actual handler, pool and importer.
Rejected transactions remain known to the connection; ordinary rebroadcast is
suppressed after catch-up. Explicit same-byte transmission and ready pending
replay pass; replay before readiness fails again. An actual two-process reconnect
recovers the original purchase but fails both-owner replenishment when the next
donation purchase stays local. Both cold databases and independent accounting
agree across forty-four blocks. A separate check reproduces insufficient funding
for the newer purchase immediately before its ticket refund, followed by acceptance
of the same bytes afterward. The original live admission errors remain unobserved.
The [bounded P4 rebroadcast candidate](restart-autobuy-rebroadcast.md) now passes
that failed continuation on fresh D: copies: unchanged saved purchases execute,
both owners make at least two fresh purchases, and both stopped databases pass
the complete fifty-two-block ledger audit. The original forty-four blocks and
all source files remain unchanged; there is no additional funding or retreat.
The candidate adds guarded periodic resend through existing peer queues, with
passing fixed-time, queue, protocol and purchase-regression checks. It changes
local delivery behavior, without relaxing consensus or transaction validation.
The [complete-state P4 partition follow-up](restart-retry-partition.md) now
demonstrates automatic reconnection and heavier-branch convergence while both
miners remain enabled. An eight-block rollback leaves the entrant at canonical
nonce 7 with exact saved nonce 14. Both cold 23-block canonical ledgers and both
competing branch audits pass. A live harness capture limit misses the last three
displaced block locations; a separate stopped-copy diagnostic retrieves all seven
original purchases through existing RPC. Its first correct-nonce purchase fails
actual pool admission after two first-retreat interval losses: zero tickets,
2,021.664457552 liquid FSN, and remaining locks that begin in the future. No new
funding or production code change is made in this follow-up. Preserve the failed
live attempt and insufficient-funding control. Next retain displaced locations
through healing and test a separately accounted synthetic funded continuation.
The [funded-gap continuation](restart-funded-gap.md) now passes on restarted
copies of that failure. Ordinary transfers of 1,200 synthetic backup FSN and
1,800 synthetic donation FSN execute through the actual miner and importers;
seven original purchases, the unchanged saved nonce 14 and two automatic
successors then succeed. Both cold databases agree across 58 blocks and all
future interval accounting passes, with no new retreat. The original 23 blocks
and source files remain unchanged. The harness now captures observed heads by
hash throughout healing; retrieval of the three previously missed bodies passes
after rollback. No production code changes. Next test a fresh uninterrupted
partition-to-funded-repair run with that observer; real funding, operational
reserves, monitoring and equal-weight convergence remain open. Keep pool
admission, native success and live production separate. The one-backup-block
launch and fifteen-item inventory are unchanged.

The [fresh uninterrupted funded partition](restart-live-funded-partition.md)
now passes branch capture through healing and live funding with the opposite
owner losing the fork. Six original purchases succeed, but the seventh remains
pending locally without a canonical receipt. Saved intent and automatic
successors are not reached. Both cold 45-block histories and both isolated
branches pass accounting. A separate real remote-pool diagnostic accepts that
exact seventh purchase after stake return and at the final head. P4 retries the
saved automatic intent, not a lower-nonce manual predecessor while the intent
is paused. The [manual-predecessor delivery follow-up](restart-manual-purchase-delivery.md)
now reproduces early rejection and persistent peer-known suppression with those
exact bytes; explicit resend and ready-peer replay pass. Fresh restarted nodes
recover through direct existing-RPC submission, execute both saved intents and
make at least two new automatic purchases each. A shorter-window attempt remains
a failure while waiting for ordinary selection. These tests do not establish the
original connection's exact ordering or an uninterrupted partition-to-completion
pass. Next include the demonstrated delivery check in a fresh uninterrupted
manual-repair rehearsal. Production P1–P15 and real funding authorization remain
unchanged.

The [uninterrupted delivered-repair follow-up](restart-uninterrupted-delivery.md)
now passes the full funded manual sequence: six exact originals, unchanged saved
nonce 12, two fresh automatic successors and matching 59-block cold ledgers.
Both services remain running through the partition, convergence, funding and
repair. Ordinary propagation delivers every original in this passing case;
the direct-recipient fallback is present but not exercised. The earlier
controlled/restarted delivery evidence remains separate. Three earlier attempts
are preserved, including a slow test-node startup and two false reserve stops.
The latter expose test-only use of display-form time locks in normalized
arithmetic. Switching the two rehearsal readers to existing raw-interval RPC
fixes it; independent cold-account analysis verifies the missing 5,000-FSN
backing per owner and the corrected passing snapshot. No reserve threshold,
funding amount or production P1–P15 change is made.

The [injected-rejection follow-up](restart-injected-manual-delivery.md) now
exercises the recipient-delivery intervention in a fresh uninterrupted run.
The first original receives a native remote underprice rejection. After the
normal policy is restored, it remains locally pending through the negative
control and the helper's observation window; direct submission of the exact
bytes then succeeds. Seven originals, unchanged saved nonce 18, two fresh
automatic purchases and both 54-block cold ledgers pass. Two originals need
direct delivery. This is a controlled test-only price-policy fault, distinct
from the historical balance-ordering case and not an operator procedure.
Production P1–P15 remain unchanged. Next resolve real funding,
monitoring/response and equal-weight convergence; do not repeat this same
passing case without a new failure or code change.

The [equal-weight investigation](restart-equal-weight.md) now separates known
opposite-branch data from first contact. Resuming the old equal-weight diagnostic
state passes live convergence and both 31-block cold ledgers; one node already
knows the opposite fork. Reexecuting the same original signed branches into
fresh complete-state copies, with genuine history and neither opposite tip
stored, fails convergence after 150.572 seconds. Both connected miners/buyers
advance 13 blocks and finish at equal total difficulty on different heads.
Native logs repeatedly report unknown parents for propagated blocks, while
sampled peer weight never exceeds local weight. Both separate 39-block cold
ledgers pass, with correct-nonce saved purchases and no new funding. This is a
demonstrated branch-delivery/sync concern, not a sparse-history or funding stall.
The [coordinated-pause follow-up](restart-equal-weight-pause.md) now passes on
fresh copies of that failure. After two more divergent blocks, stopping only
the donation miner/buyer permits ordinary heavier-peer synchronization: a first
shared descendant is observed after 21.201 seconds and continued common
production passes after 52.516 seconds. Both 46-block canonical ledgers match;
both 41-block pre-pause ledgers also pass. The donation inherits canonical/saved
nonces 8/39, zero tickets and about 2,021.98 liquid FSN; the winning history
already contains two donation first-retreat losses. The entrant continues
ordinary purchases with nonces 40/40. This is assisted convergence, not a fix
for unattended convergence or a purchase-recovery pass. The
[paused-wallet diagnosis](restart-paused-purchases.md) now retrieves all 31
missing originals exactly before and after restart. All originals and the saved
intent fail native funding admission on both nodes, while the entrant's funded
saved purchase is accepted. Both cold 46-block ledgers and exact intents remain
unchanged. The oldest original also has a bounded validity window: its native
parameter check fails once the latest block timestamp passes 27 September
21:19:32 UTC in this synthetic fixture. Funding alone cannot make an expired
original valid. The [explicit-abandonment follow-up](restart-expired-nonce-neutralization.md)
now consumes the 31 missing nonces with zero-value self-transfers through
existing RPC for 0.001302 FSN gas. Both 50-block cold ledgers pass; saved nonce
39 and donation time-lock rights remain unchanged, and the buyer stays unfunded.
A separately signed expired probe is rejected by the pool; the historical
originals had not yet expired. This deliberately abandons purchases and does
not restore tickets or resume donation mining. The [saved-intent follow-up](restart-stale-intent.md)
now separately seeds a stale nonce-39 record, verifies actual expiry rejection
before and after 3,000 FSN funding, and passes explicit nonce consumption,
correct retirement as unconfirmed, three fresh automatic purchases and actual
donation mining. Both 60-block cold ledgers pass. A prior funding-order attempt
is retained: a transfer occupying entrant's next purchase nonce prevents buying
and leaves finalization unable to preserve a ticket. The passing sequence waits
for entrant's pending purchase before staging its transfer at the next nonce.
Fixture injection is not an operator step; recovery makes no manual record edits.
The [normal-restart continuation](restart-recovered-buyer-restart.md) now
restores exact saved nonce-43 bytes from an empty pool, executes them and two
fresh successors, and resumes actual production without funding or manual
submission. Both 72-block cold ledgers pass and the original 60-block prefix is
unchanged. The [compatible-abandonment rollback](restart-abandonment-reorg.md)
now removes the self-transfer and purchases 40–42, restores canonical nonce 39,
preserves saved 43 and verifies exact old-block retrieval before/after restart.
Both 68-block cold ledgers agree. The buyer explicitly pauses after an empty-pool
restart; the live pool had retained only the self-transfer and purchase 40.
This uses a held signer and explicit downloader request, not continued mining
or unattended discovery. The [exact-transaction recovery](restart-abandonment-repair.md)
now passes on fresh copies: replayed self-transfer 39 and purchases 40–42,
automatic execution of saved 43, two fresh successors and actual production
by both owners. Both 86-block cold ledgers agree with the original 68-block
prefix unchanged. No new funding, re-signing, record edits or direct delivery
is needed; purchases 41 and 42 wait for ordinary ticket returns. The
[uninterrupted integration](restart-live-abandonment-repair.md) now passes ordinary
heavier-peer synchronization, automatic reinclusion of 39 and 40, manual repair
of only 41–42, unchanged saved 43, fresh successors and actual production.
Both 90-block cold ledgers agree. No held signer, explicit downloader request,
operator pause, service restart or new funds are needed during recovery. This
closes the specific live timing gap; production monitoring and response decisions
remain open.
No consensus or production change is introduced.

### Phase 0 — preserve evidence and accepted decisions

Completed: initial source mapping, branch comparison, read-only RPC inventory, raw evidence capture, scope agreement, and this plan.

Remaining:

- Confirm the preservation backup is immutable and independently duplicated on reliable storage.
- Address or isolate the ESXi storage-controller errors mentioned in the recovery report before using that infrastructure as a launch dependency.
- Record archive hashes, provenance, file manifests, client/build identifiers, and chain configuration.
- Separate preservation copy, running explorer gateway, disposable experiments, and eventual live node data.

Gate: losing a VM or a failed experiment cannot destroy the only copy or interrupt the explorer unnecessarily.

### Phase 1 — establish the historical baseline

- Inventory headers, bodies, receipts, transaction indexes, state availability, ticket storage, and any ancient/freezer data through `B`.
- Verify parent links, transaction/receipt commitments, and the available state against recorded roots. Distinguish full execution from sampled integrity checks.
- Perform a fresh replay from genesis where the data permits; record legacy trusted-checkpoint behavior and do not describe skipped checks as independently verified consensus.
- Compare a replayed head/state/ticket commitment against the recovered node. Resolve missing data and mismatches before constructing a restart.
- Invite other operators to provide block identities and independently verifiable data by an announced pre-launch decision date. Validate additional history on isolated copies.
- Confirm control of the proposed signer through a purpose-specific offline challenge before production signing is scheduled; never put a private key in the repository or plan.

Gate: a documented, reproducible baseline and an explicitly chosen historical parent. If history is incomplete, stop and resolve what the launch would trust rather than silently claiming full verification.

### Phase 2 — build and test baseline

- Establish a disposable Linux build/rehearsal environment with adequate disk for separate databases. Do not repurpose the 200 GiB explorer VM for bulk replay without a capacity plan.
- Reproduce the known 5.0.3/recovery build using recorded dependencies; preserve a baseline binary and logs.
- Run existing relevant tests and record pre-existing failures. Inventory missing Fusion-specific coverage; this review found no test files in `consensus/datong`.
- Review the reproduced miner receipt-log race and the temporary deep-copy experiment. Test ordinary mining/import concurrency around global `glb_parents`; the first report involved two in-memory chains in one process and is not yet a single-node reproduction of that second race.
- Establish actual test execution in CI. Pin toolchain/container inputs and examine dependency security findings before choosing the production toolchain.
- Validate compiler/dependency updates against historical replay and ticket serialization commitments; avoid unrelated bulk upgrades in the consensus patch.

Gate: reproducible build, understood baseline failures, and an executable test harness. A successful historical Docker startup is not this gate.

### Phase 3 — prove the recovery mechanism

- Use synthetic keys and state to test both candidates, starting with Candidate A.
- Match synthetic account/ticket/time-lock structure to the relevant observed conditions.
- Maintain an exact ledger after every block, including effects on offline owners.
- Test a second node importing the producer's blocks; test cold restart and missing-state reconstruction.
- Demonstrate automated or scripted ticket replenishment, initial submission on an empty pool, cold restart, bounded retry after a failed purchase without any new head, and failure behavior if a purchase is delayed. Rehearse the selected one-backup-block handover: backup purchases disabled/drained, donation first purchase included in that block, explicit jump-spanning purchase intervals, original selected-ticket refund and unused-ticket expiry accounted for, then donation-only operation. Verify that disabling purchases and restarting cannot unexpectedly resume old-owner purchases; account for signed transactions already in pools, journals or peer circulation. Additional hosted producers are not a prerequisite for the minimal startup.
- Run an isolated rehearsal on a copy of the backup only after the signing/artifact policy is defined. Do not produce multiple conflicting real-key signatures merely to iterate tests.

Gate: a selected sequence, exact rule changes if any, independent state agreement, adequate ticket runway, and no unexplained accounting differences.

### Phase 4 — implement and test the restart boundary

- Implement the narrowly specified anchor and any selected transition exception on an isolated `codex/` branch based on the agreed release baseline.
- Preserve historical behavior below activation and ordinary behavior afterward.
- Specify configuration persistence and startup errors for wrong/missing anchors or incompatible databases.
- Complete the adversarial test matrix in section 8, including a valid heavier old branch and pre-existing database contents.
- Review all canonical-head entry points. Do not rely solely on network ID, bootnode isolation, downloader depth limits, or the current checkpoint helper.

Gate: incompatible history cannot become canonical through any supported path; compatible history continues normally.

### Phase 5 — organization, infrastructure, and operator rehearsal

- Establish the organization and release governance described in sections 9–11.
- Use the selected backup wallet for one historical block and the donation wallet as the continuing producer; verify the exact handover sequence, accounting, custody and restore requirements before choosing a date. The initial two-wallet transition does not require two permanently hosted producers. Extra producers and independent organizations may join later. Multiple machines or addresses under one operator do not establish organizational independence.
- Verify the selected release and imports across separate machines/processes; seek external operator verification when available. Non-producing full nodes and discovery nodes require no tickets. Keep only one active signer per key; additional simultaneous producers need distinct funded keys, and failover must prevent overlapping signers.
- Demonstrate fresh synchronization and restore from a published, checksummed artifact; publish the artifact's trust assumptions.
- Rehearse DNS loss, bootnode loss, validator outage, restart, disk pressure, clock errors, and network partitions using disposable networks.
- Review the explorer's native calls, receipts, maturity events, rewards, and reorganization behavior against the rehearsal.

Gate: production, replenishment, backup/restore and new-node onboarding work under the declared single-producer model. Demonstrate recovery from producer and discovery outages; continuous block production during loss of the only producer is not promised. The bootstrap must explicitly disclose its initial dependence on that operator. Removing that dependence is a later decentralization objective. The fixed restart anchor and ordinary validity/accounting checks remain required before public economic use.

The original mainnet genesis creates five special tickets for one owner (`core/genesis.go`, `DefaultGenesisBlock` and `ToBlock`); their creation does not pass through an ordinary funded purchase. This confirms a single-owner bootstrap design, without proving how many physical nodes or people ran the historical launch. The restart continues to use existing authorized FSN/time-lock rights and ordinary purchases. Funding calculations must include tickets already outstanding, eligible time-lock intervals, purchase-before-refund ordering, liquid transaction fees and delayed/missed replenishment. A 5,000-FSN ticket is not a requirement for every full-node machine. The completed full-state bridge proves short single-owner replenishment with the recorded funding; a sustained real-miner test and a budget for additional producer keys remain open.

### Phase 6 — freeze and launch

- Complete the decision register and publish the specification, accepted history, changes, evidence, limitations, and operator instructions.
- Choose a recovery timestamp and launch window with sufficient ticket lifetime remaining after release review and distribution.
- Produce the final authorized recovery artifact once the signing procedure is ready; independently import and verify it.
- Freeze `A`, release checksummed/signed binaries and source, and verify operator configurations against the same manifest.
- Start participating nodes in a coordinated sequence, verify matching heads/state/tickets, and confirm ordinary block production and replenishment before announcing public economic use.
- Open public RPC and application activity only after the anchor-enforcing release and launch checks pass. Use no surprise change to the historical parent after that point.

Gate: public launch is an explicit operator/community decision supported by recorded results, not an automatic consequence of passing one test.

### Phase 7 — operate and respond to failures

- Monitor head agreement, peer diversity, live ticket ownership/expiry, purchase failures, signing failures, RPC health, disk capacity, and backups.
- Test regular restore and new-node sync; keep independent history/state providers.
- Preserve evidence and coordinate operator action if a divergence occurs. Pausing local services is not a claim that the network can be globally halted.
- Before public use, a failed rehearsal can be discarded. After public use, silently restoring all users to `B` is not a rollback strategy; any history-changing recovery requires a new explicit decision.

## 8. Required verification matrix

| Area | Required cases | Pass condition |
| --- | --- | --- |
| Historical compatibility | Before/at existing forks; known malformed native calls; full replay where available | Accepted historical block/state/receipt/ticket commitments remain unchanged |
| Ordinary present-day continuation | Saved expired tickets with no restart mechanism | Independent verifier rejects the invalid successor |
| Candidate A | Both possible old-ticket refunds, actual selection, long ticket funding, time jump, cleanup | Complete bridge passes unchanged rules and ledger/reconstruction checks, or is rejected as a design |
| Candidate B | Exact transition; wrong parent/height/time/signer/ticket; replay of exception at later heights | Only the specified transition receives its defined exception |
| Funding | Insufficient gas, insufficient interval coverage, nonce conflicts, more than one purchase per owner | Ordinary constraints remain effective; no duplicate debit/refund or created principal |
| Native execution | Purchase success/error logs, receipt status, maturity conversion, pool vs mining vs replay | Actual ticket state and ledger agree; a successful receipt alone is not proof of purchase |
| Sustained staking | First ordinary successor, repeated purchase/select/refund, delayed purchase, operator restart, expiry boundary | Nodes remain live with demonstrated funding; failures stop clearly without invalid blocks |
| Ticket reconstruction | Warm/cold cache, consecutive missing states, expiry equality, missing headers/receipts, snapshot data, compressed ticket commitment | Same ticket set/order/commitment as executed state when reconstructable; clear error rather than panic or fabricated state otherwise |
| Local producer vs verifier | Locally sealed blocks imported by a distinct process | Same hashes and roots; no reliance on the producer's trusted state write |
| Heavier old history | Valid incompatible continuation sharing `B`; greater/equal/lower weight; returned months later | Cannot replace the anchored history |
| Other divergence points | Before `B`, within a multi-block bridge, wrong `A`, compatible descendants of `A` | Invalid prefix rejected; ordinary fork choice retained after the anchor |
| Stored data | Incompatible canonical head, old side branch already stored, restart midway through sync | No silent adoption or destructive automatic migration |
| Sync entry points | Full import, fetcher, header chain, receipts/pivot/head, any supported light mode | All supported modes enforce the same anchor |
| Peer deception | Correct anchor response with incompatible advertised descendants | Ancestry checks still reject the incompatible candidate |
| Replay policy | Protected legacy, unprotected legacy, typed transactions, both branch directions | Behavior matches the published chain-ID/replay decision |
| Signing/reporting | Alternative same-parent signatures using synthetic keys | Rehearsal and launch procedure account for report/slashing behavior |
| Large time jump | EVM timestamp, native parent time, maturity, swaps, deadlines, rewards and base fee | Effects understood and documented; no invented year of rewards |
| Serialization/builds | Chosen toolchain, cold rebuild, different supported machines | Same execution commitments and reproducible declared artifacts |
| Operations | DNS/seed/validator/dashboard outage, clocks, partition, disk/restore | Documented recovery; dashboard never needed for block production |

Tests must include invalid cases and independent expected values. Do not derive every expected result from the same production helper being tested. Use focused unit/integration tests plus a multi-process rehearsal; one does not replace the other. Track failures as blockers with evidence rather than weakening the assertions.

## 9. GitHub organization and release process

The organization name, maintainers, domains, and registry have not been chosen.

- Preserve upstream Git ancestry, tags where appropriate, and existing copyright/license notices.
- Keep the node, dashboard, and operator infrastructure as clearly owned repositories. Do not change all Go imports merely to move repository ownership.
- Replace inherited ownership settings with real maintainers; use protected release branches, review requirements, and multiple organization administrators.
- Keep the historical gateway configuration distinct from validator and public-RPC configurations.
- Review and publish small changes separately: recovery/anchor rules, required operational fixes, packaging, and dashboard work.
- Build from explicit commits with recorded Go/module/container versions. Publish source, binary/container digests, release signatures, and an understandable changelog.
- Require review of consensus-affecting changes by someone other than the author before launch.
- Preserve the baseline binary and reproducible evidence so reviewers can compare old and proposed behavior.

The current extra branches should not be merged wholesale by assumption. The recovery branch's Go production change is the empty-v4-bootnode fix; much of the remainder deliberately isolates the explorer and must not become the validator defaults.

## 10. Discovery, RPC, and data availability

### Peer discovery

- Use ordinary discovery v4 with new operator-controlled DNS enode addresses as the initial design.
- Start with one reachable DNS discovery endpoint, which may be hosted by the initial producer. Protect its P2P identity separately from the validator signing key. Add seeds across other providers/domains as participation grows; those additional deployments are not an initial launch gate.
- Keep node identities stable across IP moves. The P12 candidate refreshes bootstrap DNS automatically with bounded retries; document refresh/backoff delays and distinguish it from unchanged static/trusted/v5 parsing.
- Provide static-peer fallbacks and an explicit empty-bootstrap option. No dedicated seed can eliminate the need for some initial contact information.
- Review [P12 bootstrap DNS and P13 restored-seed corrections](restart-bootstrap-dns.md) separately from consensus. The candidate retains names, retries without blocking startup, rejects malformed configuration and uses cached/literal/other contacts during DNS failure. The earlier fatal-startup and single-answer [characterization](restart-discovery-resilience.md) remains baseline evidence. The final candidate adds real-command TOML/CLI, deadlines, DNS recovery and persisted-peer cold restart with a failed hostname still configured.
- Use the [tested operator network profile and endpoint inventory](restart-network-profile.md): keep the initial public DNS introduction on the long-lived donation node, use unique P2P identities/datadirs, publish both TCP and UDP, and explicitly override v5/bootstrap/static/trusted settings. The saved [TOML base](restart-network-profile.toml) is not a complete mining/recovery launch command. Retain NAT as an explicit CLI input; do not assume `dumpconfig` can be reused or shows peer files loaded at startup. Replace final release endpoints/images/entrypoints after their new ownership is selected. Do not imply v5 hostname support.
- The isolated live rehearsals verify established peer messaging with the seed stopped, fresh-node failure, static-peer recovery, DNS errors/recovery, address changes and cold restart from genuine persisted peers. [P14](restart-peer-addresses.md) corrects demonstrated subnet accounting and stale-probe defects, with deterministic race tests and signed UDP packets across simulated public subnets. The [profile follow-up](restart-network-profile.md) adds IPv6 UDP-only introduction/RLPx and NAT-adapter lifecycle checks. The [packet-loss follow-up](restart-network-partitions.md) adds kernel-level outage/reconnection checks and P15's self-contact correction. The [miner packet-loss follow-up](restart-miner-partitions.md) adds two passing bounded real-miner cases with automatic reconnect/full sync, native purchases and cold intent recovery. The [continuous-miner follow-up](restart-continuous-partitions.md) demonstrates convergence during uninterrupted mining, but fails unattended replenishment after a multi-purchase rollback; its initial repeated-outage probe retains the same stalled buyer. The [manual-repair follow-up](restart-live-nonce-repair.md) passes one live four-nonce repair with fresh automatic successors and cold receipt checks. Existing discarded-block RPC retrieval and offline saved-record extraction now pass. Two [small-reserve cases](restart-small-reserve-and-retrieval.md) fail because the stalled owner cannot fund a repair purchase. The [funded-repair follow-up](restart-funded-repair.md) reconciles interval accounting and passes one conditional 5,000-FSN transfer/repair with both cold nodes, while retaining two failed attempts after greater ticket losses. Public TCP/UDP/NAT and IPv6, complete-state operational reserves and wider fork/outage coverage remain open.
- Plan for Peter's eventual departure once other operators are active: add independently operated discovery contacts under independent domains as participation grows, retain replaceable/manual peer configuration, and publish portable operating instructions. With all Peter-operated infrastructure unavailable, demonstrate existing-node continuity, restart from remembered peers and fresh installation through independent contacts. Preserving a chain after its sole participant leaves is explicitly outside this investigation. This is an independence milestone, not an added multi-operator requirement for the agreed initial launch.

### RPC and data providers

- Keep validator signing/admin interfaces private; serve public reads through dedicated nodes with explicit API allowlists and resource limits.
- Confirm transaction submission policy, gas estimation, receipts, Fusion methods, time-lock display, and explorer behavior at the transition.
- Retain the isolated historical gateway as a stable reference during rollout; do not turn its database into the experiment or first live validator.
- Publish checksummed history/snapshot artifacts with provenance and clear trust requirements; keep independent mirrors and a replay path.
- Rehearse clean shutdown, backup, restore, pruning settings, disk growth, and indexer workload capacity.

## 11. Node dashboard

`C:/Users/Peter/Documents/CODING/fusionfoundation/fsn-stats` is the candidate telemetry dashboard. It has a collector, WebSocket ingestion client, PostgreSQL, API, and React frontend. Its current state is not production-ready merely because the node supports `--ethstats`.

Work before hosting:

- Replace hardcoded Foundation endpoints with deployment settings.
- Remove default database credentials; bind the database privately and use least-privilege application access. Do not follow the README's broadly accessible PostgreSQL example unchanged.
- Review and update the runtime/dependencies in a dedicated dashboard change, with actual tests and a locked deployment.
- Configure TLS and explicit secure WebSocket URLs. The node's telemetry client can otherwise fall back from secure to plaintext transport when no scheme is supplied.
- Define telemetry authentication, secret distribution/rotation, rate limits, retention, input validation, and API access.
- Test reconnects, malformed/spoofed reports, stale nodes, and complete monitoring outage.
- Compare reported heads against direct RPC observations. The node sends constant `active`/`uptime` fields and its telemetry `syncing` boolean is not equivalent to `eth_syncing`; the dashboard may separately calculate connection uptime. None establishes purchase health. Use the [monitoring guide](restart-monitoring-response.md) for operational signals and explicit unknown states. Telemetry is self-reported visibility, not consensus authority.

The dashboard may be prepared alongside node work, but block production must not depend on it. Public availability and its launch timing remain deployment decisions.

## 12. Known issues and decisions deliberately deferred

The native-call decode behavior in [native-call-decode-errors.md](native-call-decode-errors.md) remains in the code. The documentation branch did not fix it. The transaction pool rejects malformed envelopes, while execution retains historical behavior. The related raw-transaction check can also interpret data from a non-native recipient as a ticket purchase.

Preserve historical behavior. Assess severity and record whether this is a launch blocker; any fix needs its own reviewed activation and compatibility tests. It is not automatically part of the ticket restart. A documented deferral must name the residual risk and rationale.

Disputed holdings and governance remain a separate proposal. Existing address-drain code is historical precedent, not authorization or evidence for new address attribution. An FIP/proposal process can document a decision without assuming a balance-weighted vote settles its legitimacy. No balances are to be changed by this plan for that purpose.

Ongoing finality remains outside scope. Do not expand the restart into permanent checkpoint administration, new voting economics, or arbitrary reorganization limits without a new decision.

## 13. Open decision register

| Decision | Current position | Needed before |
| --- | --- | --- |
| Historical parent and evidence deadline | `B` is the candidate; additional valid history remains welcome before acceptance | Final sequence construction |
| Candidate A or B | Existing-rules historical construction and funded jump (A) pass sparse, complete-state and two-node synthetic rehearsals. Final real-address parameters remain unselected; retain B only as fallback. | Implementation freeze |
| Exact sequence, signers, transactions, time, rewards/refunds | Unspecified; publish complete ledger | Real-key signing |
| Anchor location/hash | End of accepted recovery sequence proposed | Final release/public use |
| Chain ID, network ID, transaction replay policy | Preserve history; no new ID selected | Wallet/operator integration and release |
| Native decode defect and other audit findings | Separate triage; no automatic inclusion | Go/no-go decision |
| Initial operators, producer keys and ticket runway | Peter selected two initial nodes: one backup-wallet block including the donation wallet's first long-lived purchase, then donation-only production. Donation balance is 12,020.102 liquid FSN at the preserved head. Complete-state accounting, guarded unsigned construction and two-node handover/auto-buy/SIGKILL restart now pass with public test keys. Real signing custody, purchase drain and a supported restore/distribution package remain open. | Launch date |
| Post-reorg purchase recovery | Monitored manual recovery is the minimal-policy proposal. Complete-state restarted and uninterrupted cases now pass, including receipt-aware automatic reinclusion followed by only the remaining original purchases, unchanged saved intent and fresh production. Equal-weight convergence failure and first-retreat funding failures remain distinct limitations. The [response guide](restart-monitoring-response.md) and [runbook](restart-operator-recovery.md) consolidate evidence. The [snapshot observer](restart-observer.md) implements bounded reads and retained-case classification. Compact actual-service IPC/HTTP checks and durable snapshot history/review transitions pass. Bounded block/receipt backfill and explicit gaps now pass retained-fork and actual-service tests. Ordinary-mining history and offline wallet ticket derivation now pass against retained evidence. Historical anchor acquisition now passes compact IPC/HTTP state comparisons. Twelve read-only backup samples demonstrate sparse historical state; capture and preserve both wallet baselines before production. One ordinary competing-miner reorganization now passes crossing-read invalidation, preserved evidence, canonical catch-up and final/cold inventories. Wider forks, full account accounting, delivery and deployed-workload validation, policy adoption, response coverage and usable real funding remain open; no automatic gap repair is implemented. | Release candidate |
| Key custody and real-data rehearsal procedure | Synthetic keys first; avoid conflicting production signatures | Access to production signer |
| Supported sync modes and bootstrap artifacts | Full block sync from a verified restored state is the launch candidate path. Cold tests confirm headers alone lack purchase history; original fast sync is disabled in the normal scheduler. Explicitly use `--syncmode full`; fast/light acquisition is not supported by the current evidence. Full-history continuation and public bootstrap distribution remain to demonstrate. | Operator release |
| Organization, maintainers, domains, hosts | Not yet selected | Infrastructure deployment |
| Dashboard deployment and credentials | Separate hardening required | Public dashboard |
| Production toolchain/dependency policy | Reproduce baseline, then validate chosen release inputs | Release candidate |

## 14. Launch manifest and acceptance record

Create a versioned manifest after the decisions are made. Required fields:

- Network identity and transaction replay policy.
- Genesis identity; accepted historical parent height/hash/state root/ticket commitment; evidence provenance.
- Exact recovery block sequence, transaction bytes/IDs, signers, timestamps, expected receipts/state roots/ticket commitments, and complete accounting changes.
- Mandatory anchor height/hash and configuration identity; supported sync modes.
- Source commit/tag, build inputs, artifact digests/signatures, and change review records.
- Approved public bootstrap identities/endpoints, static fallbacks, data mirrors, RPC and monitoring configuration guidance. Do not include secrets.
- Participating independent operators, their verified configuration agreement, ticket runway, and recovery responsibilities.
- Test/replay/rehearsal results, unresolved limitations, accepted residual risks, and the launch decision record.
- Procedure for a stale pre-launch artifact, an incompatible returning node, a post-launch divergence, and emergency operator communication.

Release acceptance requires all applicable phase gates and verification cases to pass or have an explicit justified scope decision. No claim that the chain is audited or restart-ready should precede that evidence.

## 15. Immediate next actions

1. Review the completed 3,000,000 baseline replay and passing cold check, then select the next bounded range and capacity. The closed D:-backed ext4 target is about 4.65 GiB; both earlier checkpoints and the original binary identity remain preserved. No continuation beyond 3,000,000 is running. Current-state traversal and complete structural history validation have passed. Historical checkpoint shortcuts remain through 2,680,000 and must be labelled accordingly. See [integrity/replay evidence and paths](restart-integrity-investigation.md).
2. Review and adopt the proposed [monitoring/response policy](restart-monitoring-response.md) with the [operator recovery procedure and evidence matrix](restart-operator-recovery.md#evidence-and-boundaries). The specific uninterrupted compatible rollback-to-repair case now passes with both 90-block cold ledgers. The [external snapshot observer](restart-observer.md) has retained-data/fault classification tests and an enforced read-method allowlist; eight [actual-service IPC/HTTP observations](restart-observer-services.md) also pass with race detection and no runtime correction. [Durable snapshot history and incident review](restart-observer-history.md) now pass cross-platform replay, reopening, storage guards and abrupt-exit checks. [Bounded canonical block/receipt backfill](restart-observer-backfill.md) now passes retained-fork and actual-service IPC/HTTP checks, preserving displaced evidence and reporting gaps. [Ordinary-mining history collection](restart-observer-mining.md) now passes natural head advancement, bounded catch-up, cold rechecks and a test-only native inventory audit without runtime edits. The [P16 local parser correction](restart-snapshot-framing.md) now rejects truncated counts after a bounded in-memory reproduction; network-level impact remains unverified under the narrowed testing scope. Review that guard separately. The [offline wallet ticket timeline](restart-observer-tickets.md) now derives scoped purchases, removals and native failures from a saved anchor inventory, with cross-platform retained-ledger agreement and explicit gaps. [Historical anchor inventory acquisition](restart-observer-anchor.md) now supports monitoring started later using existing RPCs, with compact IPC/HTTP state reconciliation. Its service run found and corrected an observer-only maturity-log interpretation issue; all failed attempts are retained. The [preserved-backup inventory probe](restart-observer-preserved-inventory.md) now passes twelve read-only samples and measures local query cost. Recent state is sparse, including an unavailable head-minus-two sample: acquire both wallet baselines before production, verify them after reopening history and preserve a closed copy. No 128-block availability guarantee is assumed. Next validate production transport and concurrent acquisition cost; full financial accounting remains outside this timeline. The [live reorganization follow-up](restart-observer-reorg.md) now passes deliberately overlapping snapshot/backfill reads during an ordinary peer join, canonical catch-up, preserved displaced evidence and final/cold inventories, without runtime edits. The [observer history-cost follow-up](restart-observer-history-cost.md) now fixes raw-byte hash formatting with an exact-string regression, passing Windows suites and passing Linux suites with race detection. Its bounded non-race run measures linear replay cost and about 28.5 kB per repeated two-node snapshot: the 64 MiB example budget is not a production retention recommendation. The [mixed actual-command follow-up](restart-observer-mixed-workload.md) now passes six advancing IPC/HTTP rounds and a 512 KiB logical-budget exhaustion check with ordinary and race builds. Rejected snapshot/backfill writes return exit 1 without stdout, preserve status and exports, and leave both offline ticket inventories readable. This is not a full-filesystem failure or sustained-load test. The [opening-state follow-up](restart-observer-open-replay.md) now removes one redundant replay: paired reopen/status at 1,000 prior snapshots falls from 1.55 seconds to 0.74 seconds, with all six deterministic outputs byte-identical. Windows suites, Linux race suites and the two-node race budget workload pass. Complete validation still occurs at open; the first operation consumes that state once, later operations replay normally, and no derived state is persisted. Only external observer history handling changes; node/consensus code and P1-P16 are unchanged. Next measure longer ancestry and design retention that preserves baselines, unresolved incidents, review identity and displaced evidence. Replay remains linear and retained bytes are unchanged. Route collection failure and missed-cadence notifications outside an exhausted history. Wider forks and representative workload remain open; local review records do not automatically verify recovery acceptance. Select notification/acknowledgement coverage and timings before deployment, then exercise actual delivery and collector loss. Recheck real funding and interval schedules. Keep equal-weight convergence failure, conditional reserves, power-loss durability and wider fork coverage explicit; the existing tests do not establish unattended recovery. Ordinary auto-buy stays disabled during historical bridge construction.
3. Review the [implemented narrow corrections](restart-corrections.md) and extend realistic mining/import concurrency coverage. Their 128 historical reconstruction checks and synthetic boundary cases pass. The additional [P9 parent-isolation correction](restart-parent-isolation.md) addresses an inherited race reproduced by concurrent import/mining; review its separate failure evidence and header-batch coverage. [P10 discovery initialization](restart-discovery-resilience.md) removes an inherited seed-startup race. [P11 peer retention](restart-discovery-cache.md) restores the existing peer-cache maturity filter together with accepting validated sparse discovery replies. [P12 bootstrap DNS and P13 cache loading](restart-bootstrap-dns.md) add outage/retry handling and correct restored peer identities/endpoints. [P14 address handling](restart-peer-addresses.md) corrects subnet reservation transfer, replacement promotion and stale probe results. [P15 self-contact exclusion](restart-network-partitions.md) prevents the local identity from occupying discovery contacts and suppressing empty-table refresh. P10–P15 do not change consensus. The permanent inventory now contains sixteen candidates, including the separately recorded [P16 minimum snapshot-length guard](restart-snapshot-framing.md). The [bounded miner partition checks](restart-miner-partitions.md) now pass twice with Linux race detection and no runtime change. The continuous-miner follow-up adds complete synthetic ancestry and observed reconnection/convergence, with no race reports, but unattended replenishment fails. One separate manual-repair case now passes while mining continues, without a runtime change. Public deployment readiness still requires public TCP/UDP/NAT and IPv6 checks; complete-state operational reserves and wider fork/outage coverage remain open. Existing retrieval interfaces now pass, while the small-reserve repair requirement fails funding. The repair harness also recognizes the normal temporary downloader-induced worker pause and checks automatic resumption without another start command. Compare Candidate A with the explicit current-time transition, and select a design based on validated behavior and accounting.
4. Review and extend the [implemented anchor prototype](restart-anchor-implementation.md), [multi-process results](restart-node-rehearsal.md), [interrupted-write correction](restart-crash-rehearsal.md), [explicit-rewind correction](restart-rewind-rehearsal.md) and [reset/pivot evidence](restart-reset-pivot-rehearsal.md). Before/after write cuts now cover linear imports, compatible reorgs, rollback, six rewind cases, reset and four pivot cases. The [cold-header matrix](restart-cold-header-validation.md) now confirms the same header-only reconstruction limit before/after P9, validates reconstruction with stored bodies/receipts, and passes full import plus cold reopen. Normal scheduling already disables fast sync; the launch candidate uses explicit full sync from restored state. General state acquisition, genesis resync, pruning/freezer recovery, large-batch memory cost, deep ancestry and wider concurrent peer mining/reorgs remain open. Freeze the production anchor only after the recovery artifacts are reviewed.
5. Review the [guarded recovery command and full-state two-node result](restart-recovery-construction.md), alongside the [wallet handover](restart-wallet-handover.md) and [earlier full-state worker evidence](restart-full-state-handover.md). The command leaves all source database files unchanged; the actual services reject unsafe plans before signing and reproduce the reviewed three-block prefix. Donation auto-buy/mining starts immediately after cleanup, resumes after SIGKILL, and both cold databases agree on complete account ledgers. The [signing journal and saved-backup inventory](restart-signing-journal.md) now pass synthetic reservation/crash/conflict tests and find no saved purchases for either wallet. The complete preserved database now passes local package/restore and actual-service checks. Next demonstrate release hosting/download and final recovery-data distribution; review the passing complete-state offline interruption and [actual operator command results](restart-full-state-operator.md), finish real-key/artifact custody, verify clean signer-process shutdown (the mining-stop RPC can leave delayed signed work), and inventory/drain the live backup-wallet pool/journal before real signing. The compact state fixture lacks historical bodies and log indexes and is not that distribution package. Preserve the original backup; review real-address refunds/retreats and fresh timing parameters before choosing the production sequence.
6. Resolve the decision register, prepare independent operators/infrastructure, and proceed through the release and launch gates.

## 16. Source map for future implementation

| Concern | Starting points |
| --- | --- |
| Ticket selection, expiry, finalization, reconstruction, rewards | [consensus/datong/consensus.go](../consensus/datong/consensus.go) |
| Checkpoint shortcuts and range behavior | [consensus/datong/checkpoints.go](../consensus/datong/checkpoints.go), [core/block_validator.go](../core/block_validator.go) |
| Canonical selection, reorg, startup, writes, fast-sync head | [core/blockchain.go](../core/blockchain.go) |
| Header-chain selection and import | [core/headerchain.go](../core/headerchain.go) |
| Separate restart rule, preflight and readiness | [core/restart_anchor.go](../core/restart_anchor.go), [params/restart_anchor.go](../params/restart_anchor.go) |
| Mining write path and block preparation | [miner/worker.go](../miner/worker.go) |
| Execution, native errors, time references and receipts | [core/state_transition.go](../core/state_transition.go), [core/state_processor.go](../core/state_processor.go), [core/evm.go](../core/evm.go) |
| Ticket storage/cache and maturity | [core/state/statedb.go](../core/state/statedb.go), [core/state/state_object.go](../core/state/state_object.go) |
| Ticket/time-lock rules and arithmetic | [common/ticket.go](../common/ticket.go), [common/timelock.go](../common/timelock.go), [common/fsnparams.go](../common/fsnparams.go) |
| Purchase construction, defaults, auto-buy, admission | [internal/ethapi/api_fsn.go](../internal/ethapi/api_fsn.go), [common/fsnargs.go](../common/fsnargs.go), [core/tx_pool.go](../core/tx_pool.go) |
| Multiple-mining reports | [consensus/datong/report.go](../consensus/datong/report.go) |
| Chain configuration and transaction signing | [params/config.go](../params/config.go), [core/types/transaction_signing.go](../core/types/transaction_signing.go) |
| Peer challenges, handshake, synchronization | [eth/handler.go](../eth/handler.go), [eth/peer.go](../eth/peer.go), [eth/downloader/downloader.go](../eth/downloader/downloader.go) |
| Bootnodes and hostname parsing | [params/bootnodes.go](../params/bootnodes.go), [cmd/utils/flags.go](../cmd/utils/flags.go), [p2p/discover/node.go](../p2p/discover/node.go), [p2p/discv5/node.go](../p2p/discv5/node.go) |
| Telemetry and release baseline | [ethstats/ethstats.go](../ethstats/ethstats.go), [build workflow](../.github/workflows/build-and-test.yml), [go.mod](../go.mod) |

This map identifies review entry points, not an assertion that every relevant code path has been audited. Keep the plan's decisions and evidence current as implementation and rehearsal resolve the open questions.
