# Fusion restart plan

Status: investigation and implementation plan; not a launch authorization or a completed security audit.

Last reviewed: 24 September 2026. Source baseline: local `master` / `develop` at `c5f0174` (5.0.3); recovery branch at `6981b00`; documentation branch at `c1806fc`. Narrow client corrections exist on the investigation branch; the complete restart implementation is still pending.

Latest progress: the D:-backed WSL environment contains a fully checksummed
disposable database copy. The [integrity and replay investigation](restart-integrity-investigation.md)
has verified all reachable current state and structural history through `B`,
completed baseline replay through 2,700,000, and passed 128 real historical
ticket-reconstruction cases. Continuation stopped cleanly at 2,613,376 as D:
approached its reserve; a cold read-only check confirms the saved head. A complete
checksum-verified working copy on C: completed 2,700,000 and passed a cold reopen
check, including execution of 20,000 blocks beyond the legacy checkpoint range.
The D: checkpoint remains preserved. Phase status belongs in the linked report.

The [synthetic bridge experiment](restart-bridge-experiment.md) demonstrates
eight independently imported blocks. [Narrow corrections](restart-corrections.md)
address the reproduced receipt-log race, reconstruction expiry mismatch and
missing-ancestor panic. The [purchase controller](restart-purchase-controller.md)
adds startup attempts, periodic retry, signed-transaction recovery and canonical
receipt monitoring, with explicit pauses for nonce conflicts and missing nonces.
Complete historical execution, full-state recovery, the accepted restart anchor
and independent operator rehearsals remain outstanding.

The [anchor entry-point investigation](restart-anchor-investigation.md) now
reproduces heavier-chain replacement and legacy-checkpoint gaps involving stored
forks, canonical indexes, headers, receipts, pivot commits and startup initialization/rewinds.
The [separate anchor prototype](restart-anchor-implementation.md) now checks these
entry points, rejects incompatible startup data before repair, and gates mining
and transaction readiness below the anchor. It also fixes two reproduced rollback
defects. The production height/hash remains unset. Light mode explicitly refuses
an active anchor. An isolated [multi-process rehearsal](restart-node-rehearsal.md)
now exercises the actual service, IPC, miner and peer downloader. Fast/freezer
release support and full-state network rehearsal remain unproven. Adding a legacy
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

The working launch target, clarified on 24 September 2026, is the smallest viable startup: one initial producer using the recovered owner's existing authorized funding, a published anchor-enforcing release and verified recovery data, and a reachable DNS discovery endpoint. The producer may also supply that initial discovery service; a separate fleet of validators or dedicated seeds is not required for day one. Other holders can download the release, follow the documented data/configuration checks, synchronize and choose to produce blocks using ordinary funded tickets. Joining needs no new operator allowlist. Demonstrate separate-process verification during rehearsal without treating that verifier as a mandatory second permanently hosted node.

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

### 3.9 Purchase admission and automatic retry are separate gates

The real purchase argument builder, pool, and execution have now been exercised
against synthetic observed-balance fixtures. Before the first historical refund,
the pool admits a long purchase that execution rejects: the pool checks funding
from wall-clock time, whereas execution needs coverage from historical parent
time. After the refund, construction, admission, import, and ticket creation pass.

Default purchases on the historical head expire in November 2025 and are rejected
by the pool. A present-day start also fails the parent-plus-three-hours rule.
Candidate A's purchases in steps 2 and 3 therefore need explicitly extended ends
while retaining valid historical starts. No general purchase-rule relaxation has
been shown necessary.

Auto-buy is triggered by a new canonical head; the inspected loop drops purchase
errors and has no timer-based retry. Enabling it does not enqueue an initial
purchase. Combined with the reproduced one-ticket/no-replacement failure, this
creates a possible stall after a failed purchase or a cold restart with an empty
pool. The runtime test now reproduces both conditions over bounded observation
windows; an explicit API retry restores mining and ordinary head-triggered
purchases continue. Require initial submission, bounded retry, actual inclusion
checks, and visible errors before launch. An operator watchdog or purchase tool
may suffice; this is not a reason to redesign consensus. Disk restart, journal
restoration, and failures at other purchase stages remain untested.

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

Both candidates require the accepted restart anchor. Neither is approved for launch. Candidate A has a successful synthetic import sequence but a confirmed reconstruction defect; a temporary parent-time correction passes the focused experiment. Candidate B has not been implemented or tested.

### Candidate A — a short bridge under existing ticket rules

Experiment sequence, not executable launch instructions:

1. Construct a block just after `B`, with a valid historical timestamp and ordinary selection by the known owner. Start with no unrelated transactions. Verify the selected ticket, order, difficulty, retreat effects, and ordinary refund.
2. Using the other old ticket, construct another historical-time block containing a normally funded ticket whose lifetime reaches beyond the planned time jump. Verify the refund actually supplies continuous coverage, and account for fees before execution.
3. Advance to current time using that new long-lived ticket. Include required replenishment so consuming it does not halt subsequent blocks.
4. Continue through the next blocks to demonstrate expired-ticket cleanup and stable present-day operation, including cold reconstruction. The exact number of bridge blocks is not yet known.

Why test it first: source rules allow old timestamps subject to their checks, and ticket lifetimes have no maximum in the inspected validation. The recorded balances plus ordinary refunds make funding plausible. It may leave production ticket validation unchanged.

Reasons to reject or revise it:

- Any block fails independent stock-rule verification or replay.
- Ticket reconstruction differs from direct state at the time jump.
- Required funding, gas, nonces, or replenishment cannot be satisfied.
- Retreat penalties or other historical-time economic effects are unacceptable to participants.
- The necessary tooling or operational complexity exceeds a narrow explicit transition.
- Timestamp presentation or application effects cannot be made clear and acceptable.

The bridge would be newly created recovery history bearing historical timestamps, not evidence those blocks existed in 2025. Publish this fact and the full ledger. Do not simulate a year of catch-up mining or change the operating system clock as a launch procedure.

Construction must explicitly set the purchase lifetime in steps 2 and 3: their
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
- Demonstrate automated or scripted ticket replenishment for one producer using the recorded funding, initial submission on an empty pool, cold restart, bounded retry after a failed purchase without any new head, and failure behavior if a purchase is delayed. Demonstrate that a later separately keyed, ordinarily funded producer can join; multiple hosted producers are not a prerequisite for the minimal startup.
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
- Use one initial producer as the working target; agree its tested funding, backup and recovery requirements before choosing a date. Extra producer machines/keys and independent organizations may join later. Multiple machines or addresses under one operator do not establish organizational independence.
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
- Keep node identities stable across IP moves; document DNS changes and the need for re-resolution/restart under current behavior.
- Provide static-peer fallbacks and an explicit empty-bootstrap option. No dedicated seed can eliminate the need for some initial contact information.
- Decide whether to harden unresolved-DNS handling now. If changed, distinguish malformed configuration from temporary resolution failure and make failure visible; test one/all seeds unavailable and multiple DNS answers.
- Inventory v5 defaults, NAT announcements, TCP/UDP reachability, static/trusted peers, and all Foundation hostnames in scripts/configuration. Do not imply v5 hostname support.
- Verify established peers continue when seeds are unavailable. Document initial-contact failure and recovery through a reachable static peer or restored seed; one endpoint cannot provide fresh-node discovery while it is offline.

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
- Compare reported heads against independent RPC observations. Telemetry is self-reported visibility, not consensus authority.

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
| Candidate A or B | Test A first; retain B as fallback; neither proven | Implementation freeze |
| Exact sequence, signers, transactions, time, rewards/refunds | Unspecified; publish complete ledger | Real-key signing |
| Anchor location/hash | End of accepted recovery sequence proposed | Final release/public use |
| Chain ID, network ID, transaction replay policy | Preserve history; no new ID selected | Wallet/operator integration and release |
| Native decode defect and other audit findings | Separate triage; no automatic inclusion | Go/no-go decision |
| Initial operators, producer keys and ticket runway | Target one initial producer using existing authorized funding; prove sustained replenishment and controlled restore. Publish how others can join. Extra producers/independent organizations are not a fixed launch minimum. | Launch date |
| Key custody and real-data rehearsal procedure | Synthetic keys first; avoid conflicting production signatures | Access to production signer |
| Supported sync modes and bootstrap artifacts | Must be demonstrated; unsupported modes explicitly excluded | Operator release |
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

1. Review the completed 2,700,000 baseline replay and cold reopen, preserving the D: checkpoint at 2,613,376 and the new C: checkpoint. Choose the next bounded range and capacity before resuming. Current-state traversal and complete structural history validation have passed. Historical checkpoint shortcuts remain through 2,680,000 and must be labelled accordingly. See [integrity/replay evidence and paths](restart-integrity-investigation.md).
2. Review the [purchase controller and recovery evidence](restart-purchase-controller.md). Initial submission, periodic retry, receipt monitoring, wallet/estimation/funding failures, conflicting replacements, controlled same-height replacement and clean disk/journal restart are covered. Extend to process-crash boundaries, live peer reorgs and full-state operation before release; ordinary auto-buy remains disabled during historical bridge construction.
3. Review the [implemented narrow corrections](restart-corrections.md) and extend realistic mining/import concurrency coverage. Their 128 historical reconstruction checks and synthetic boundary cases pass. Compare Candidate A with the explicit current-time transition, and select a design based on validated behavior and accounting.
4. Review and extend the [implemented anchor prototype](restart-anchor-implementation.md), [multi-process results](restart-node-rehearsal.md), [interrupted-write correction](restart-crash-rehearsal.md), [explicit-rewind correction](restart-rewind-rehearsal.md) and [reset/pivot evidence](restart-reset-pivot-rehearsal.md). Before/after write cuts now cover linear imports, compatible reorgs, rollback, six rewind cases, reset and four pivot cases. Full state acquisition, genesis resync, pruning/freezer recovery, large-batch memory cost, deep ancestry and concurrent peer mining/reorgs remain open. Freeze the production anchor only after the recovery artifacts are reviewed.
5. Review the [full-state recovery rehearsal](restart-full-state-rehearsal.md): independent eight-block imports, exact synthetic funding/ticket substitution, complete account differences, cold traversal and bounded ticket reconstruction now have evidence. Extend to the actual mining worker and automatic replenishment for the minimal single-producer target, including missed purchases and restore; the demonstrated suffix ends with one live ticket. Then demonstrate a later participant joining with a separate funded key. Keep the verified state artifact and original backup intact, and review real-signer refunds/retreats before selecting the recovery sequence.
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
