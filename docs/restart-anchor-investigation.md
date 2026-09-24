# Restart-anchor entry-point investigation — 24 September 2026

The existing checkpoint feature is not a sufficient restart boundary. Tests on
`82d685e` reproduce an incompatible heavier branch replacing accepted history,
and several ways the legacy checkpoint checks can be bypassed or leave
inconsistent head/index state. Production code is unchanged by this investigation.
The exact production anchor remains undecided. Subsequent implementation is
tracked in [the anchor prototype report](restart-anchor-implementation.md);
the observations below describe the earlier baseline with that rule disabled.

Later status: the [atomic reorganization correction](restart-crash-rehearsal.md)
now propagates the previously ignored per-block checkpoint failure. The current
stored-fork test requires rejection; use the retained baseline revision/evidence
to reproduce its original inconsistent head/index result. Other legacy entry-point
gaps below remain reasons for the separate anchor.

## Reproduced behavior

`TestRestartAnchorEntryPointsCharacterization` builds two valid branches using
the public synthetic key and independent in-memory state. They share the
14-block preparation sequence through synthetic height 15,130,094. The accepted
branch adds four blocks; the returning branch adds five, with different
timestamps and strictly greater accumulated difficulty. The hypothetical anchor
is the accepted branch's first block. This is not a proposed mainnet artifact.

Blocks are serialized and decoded before receiver import to discard cached
ticket-selection fields. Each case runs in its own child process because legacy
checkpoint settings and ticket caches are process-global. No P2P/RPC listeners,
real keys or preserved databases are used.

The completed preserved-history scan found consistent parent links. The
head/index inconsistency described here was created in the synthetic tests.

| Case | Observed behavior |
| --- | --- |
| Ordinary full-block import | The heavier incompatible branch becomes canonical; a displaced accepted-branch transaction loses its canonical lookup. |
| Direct checkpoint mismatch | Control case: importing a batch containing the wrong block at the checkpoint height is rejected. |
| Stored side branch, then checkpoint installation | Importing only later descendants succeeds. The current head follows the incompatible ancestor, while the canonical index at the checkpoint still names the accepted block. |
| Ancestor helper on that inconsistent database | `GetAncestor` returns the accepted canonical index; explicit parent-hash traversal reaches the incompatible ancestor. |
| Header-only continuation | After the incompatible checkpoint-height header is stored, importing later headers rewrites canonical header ancestry despite the checkpoint. The executed full head remains separate. |
| Receipt insertion | Bodies/receipts for incompatible headers stored before checkpoint installation advance the fast head without an anchor check. |
| Fast-sync head commit | `FastSyncCommitHead` accepts an incompatible stored block with available state. It changes the in-memory full head while the persisted full-head marker remains unchanged. |
| Startup on an incompatible database | Constructor returns success after automatically rewinding below the checkpoint. It does not require an explicit migration decision. |
| Checkpoint settings loaded after construction | The incompatible head remains active; installing the checkpoint afterward does not trigger startup revalidation. |
| Adding a later checkpoint | The body validator stops rejecting two purchases from one account below the expanded checkpoint range. This is a validator-level test, not proof that a complete malformed block passes execution. |

The stored-data cases model data that predates an upgraded client. Tests install
the checkpoint in process to isolate individual entry points; they do not claim
that a normal operator can dynamically alter it through RPC. The separate startup
case exercises constructor behavior with the checkpoint already configured.
The late-initialization case exercises the opposite order.

Source inspection shows the ordinary CLI uses that late order: `geth` calls
`makeFullNode`, which reaches `eth.New` and `core.NewBlockChain`, before
`startNode` calls `datong.InitCheckPoints`. The constructor's checkpoint loop
therefore cannot be relied on as the CLI's restart preflight. The new rule must
be available before chain construction, including non-node import/recovery
commands. These tests isolate constructor/configuration ordering; they do not
launch the CLI's networking stack.

## Why the stored-fork case fails

The source interaction is specific:

1. `BlockChain.reorg` collects the incoming branch from the new tip backwards.
2. `CheckPointsInHeaderChain`, called by `CheckPointsInBlockChain`, stops scanning
   at the first height above `LastCheckPoint`. That early exit is suitable for
   ascending import batches, but skips a descending reorg whose tip is above it.
3. Reorg then calls `writeHeadBlock` for each branch block. Its individual
   checkpoint mismatch check logs and returns without an error result.
4. The incompatible checkpoint-height write is skipped, but later descendant
   writes proceed. Canonical height lookup and actual parent ancestry disagree.

`HeaderChain.WriteHeader` has its own ancestor/index rewrite loop and does not
perform that reorg checkpoint check. A check on only the new header cannot
exclude an incompatible ancestor already in the database.

`HeaderChain.GetAncestor` normally accelerates a lookup by jumping directly
between canonical number indexes once its starting hash is canonical. The
reproduced inconsistent database violates that assumption. Reusing that helper
without first establishing index/ancestry consistency could make a new anchor
check falsely accept the wrong branch.

These are demonstrated reasons to enforce one explicit ancestry rule before
head mutation. Fixing only the descending-loop early exit would not cover the
header, receipt, pivot, startup or index-shortcut paths.

## Implementation boundary to carry forward

The anchor should be a separate immutable network rule identifying an exact
height and hash, bound to the intended chain/genesis. Do not add it to
`datong.CheckPoints` or raise `LastCheckPoint`: that also widens historical
ticket-seal and raw-transaction shortcuts. Header signatures and earlier checks
still run in that legacy range; it is inaccurate to say all verification stops.

Before adopting a candidate at or above the anchor, prove its actual linked
ancestry reaches that hash. Missing ancestors or a mismatch must return an
error. Batch-local parents must be considered, and a known block/side-chain
cache entry must not bypass eligibility. Before trusting canonical-index
shortcuts, establish consistency with actual parent hashes. Any proof cache
must be keyed by validated block identity, not just height.

An efficient incremental proof can reuse a previously validated parent's
eligibility. The first check of existing stored ancestry needs explicit
verification. The cache strategy and startup cost still need measurement; this
report does not prescribe a second persistent index or an O(chain length)
walk on every new block.

Enforcement must happen before canonical indexes, head pointers or externally
visible chain events change. A rejection must propagate to the caller, leaving
those markers unchanged. A log message followed by partial mutation is not a
successful rejection. Existing incompatible databases require a read-only
preflight before automatic repair/rewind paths can modify them.

| Surface | Source and requirement |
| --- | --- |
| Full import and stored/pruned side chains | `BlockChain.insertChain`, `WriteBlockWithoutState`, `writeBlockWithState`, `reorg`, `writeHeadBlock`: cover both fresh batches and stored ancestry before adoption. |
| Local mining | Public `WriteBlockWithState` is a separate caller path; it cannot rely only on network import validation. |
| Header import and rewriting | `HeaderChain.ValidateHeaderChain`, `InsertHeaderChain`, `WriteHeader`: both validation and canonical rewrite must preserve the same invariant. |
| Receipt and fast-sync heads | `InsertReceiptChain` and `FastSyncCommitHead`: validate ancestry and keep header/full/fast head relationships coherent. Downloader uses these methods separately. |
| Startup and configuration order | `cmd/efsn` construction, `NewBlockChain`, `loadLastState`, header-chain initialization: load the rule before construction and inspect persisted full/header/fast ancestry before repair, checkpoint rewinds or `ResyncFromHeight` can modify the database. |
| Rewind/reset/recovery | `SetHead`, `Rollback`, `ResetWithGenesisBlock`, header equivalents: define below-anchor recovery explicitly and prevent it being exposed as a launched, settled chain. |
| Light mode, if supported | `LightChain` startup/import/rollback, `SyncCht`, and `light/odr.go` canonical writes must be covered. Shared header checks alone are not the entire light-client surface. |
| Serving/mining readiness | A fresh or rewound node below the anchor may acquire historical data, but must not claim restart readiness or mine the launched chain before validating the required boundary. |

The default sync mode is already full sync. Supporting fast or light modes at
launch remains a decision; unsupported modes should fail explicitly rather
than exposing an untested bypass. Peer filtering/challenges may save bandwidth
but cannot replace local ancestry checks.

This is one fixed restart boundary. Descendants that share the accepted anchor
remain subject to ordinary Fusion fork choice. No new ongoing finality rule,
reorganization-depth cap or periodic checkpoint authority is proposed.

## Validation and remaining work

The nine characterization cases pass in all three Linux/CGO race-detector
repetitions. The complete ordinary Windows/CGO-disabled restart suite also
passes in 92.499 seconds. Final logs, executable/source hashes and
completed historical validation are retained in
[the evidence directory](evidence/restart-validation-2026-09-24).
A passing characterization reproduces the current unsafe behavior; it is not
a test of an implemented restart anchor.

The fixture uses the known single-surviving-ticket setup and synthetic parent
state, not full mainnet state. The heavier chain proves the adoption mechanism,
not the existence or economic viability of a particular unknown operator's
continuation. The same synthetic signer creates both branches; no automatic
illegal-mining report service is running in these tests.

The subsequent [implementation and enforcement tests](restart-anchor-implementation.md)
cover direct mining/state-less writes, stored and known branches, missing ancestry,
damaged startup heads/indexes, rewinds and compatible descendant fork choice.
The original characterization evidence remains available; the current stored-fork
case is now a rejection regression. Later reports cover
[actual service/peer operation](restart-node-rehearsal.md) and selected
[interrupted writes](restart-crash-rehearsal.md). Supported ancient/fast paths,
full-state operation and the remaining crash boundaries are release gates. Do not freeze a production
anchor until the full-state recovery sequence is constructed, reviewed and accepted.
