# Fixed restart-anchor prototype — 24 September 2026

The investigation branch now contains a separate, inactive restart-anchor rule.
It is exercised with synthetic anchors; **no mainnet height/hash is configured**.
This is an implementation and test checkpoint, not a release or launch approval.

The [preceding investigation](restart-anchor-investigation.md) records the nine
legacy failures and controls. Their historical evidence remains available.
The later atomic reorganization correction changes the stored-checkpoint-fork
case into a rejection regression; the other legacy characterizations still run
with the new rule disabled. The new enforcement tests require rejection with
the rule enabled, including when incompatible blocks were stored before upgrade.

## Configuration and ancestry

`params.RestartAnchor` binds a block number/hash to the genesis hash and chain ID.
`ChainConfig.RestartAnchor` is excluded from JSON. For the mainnet genesis,
constructors resolve the rule from the compiled mainnet configuration, ignoring
a caller-supplied alternative. Other programmatic configurations let the tests
use their synthetic genesis. Constructors validate identity and copy the rule;
changing the caller's configuration later does not change the active rule.

There is no new CLI switch, database configuration override, mutable checkpoint
file, or periodic authority. Selecting the mainnet value remains a later source
change after the complete recovery artifact is reviewed. The legacy checkpoint
map and its verification range are unchanged.

At and above the anchor, eligibility follows actual parent hashes until the
required hash, or a previously proved descendant, is reached. Missing/corrupt
ancestors and a different hash at the anchor return errors. Batch-local parents
are included. The proof does not use `GetAncestor`'s canonical-index shortcut.
A bounded 512-entry memory cache records proved header hashes, not heights or
mutable canonical status. It proves ancestry only, not signatures, execution or
current state availability. Normal validation still runs.

Batch prechecks keep their proofs local until import. A measured regression
used 8,192 stored descendants followed by a 600-header batch: the first version
required 8,796 header reads because the batch evicted the stored-tip proof.
The corrected version required 601. These unsigned synthetic headers isolate
ancestry cost; they are not a consensus-validation or historical replay result.

Below the anchor, initial synchronization is allowed. When the accepted anchor
already has a canonical index, older inputs must match the indexed historical
prefix. This prefix check assumes the historical canonical indexes are sound;
it is not a substitute for the separate complete history scan. Startup explicitly
checks header ancestry and canonical-index agreement from the header head down
through the anchor, not every pre-anchor index back to genesis.

## Covered entry points

- Full-block batches are checked before execution, known-block shortcuts,
  reporting, canonical writes or events. State-less side-chain writes and direct
  writes with state also check ancestry; reorganization checks its proposed tip.
- Header validation, header insertion and direct header writes apply the same
  rule. A head-changing write cannot move an anchored head below the anchor.
- Receipt insertion checks the complete batch before live/ancient writes and
  checks again before advancing the fast head. Head-update errors propagate.
- With an active anchor, fast-sync pivot commit requires an eligible canonical
  block no higher than the current header head, available state, and persists
  the full-head marker before updating memory. This also rejects stale indexes
  remaining above a rolled-back header head.
- Existing-database genesis setup and header-chain construction perform a
  read-only preflight before configuration writes, repairs, checkpoint rewinds
  or resync actions. All three persisted heads must exist, have valid ancestry,
  and be no higher than the header head. Full/fast head bodies must be readable.
  Incompatible or inconsistent data returns an error; it is not silently rewound.
- Explicit rewind/reset remains available. Reset cannot substitute a different
  genesis. Header rewinds and rollbacks discard proof-cache entries. A node below
  the anchor can synchronize historical data but cannot mine or submit/accept
  transactions as a ready node. Mining startup, work creation and the direct
  mining write path check readiness. RPC sync progress retains at least the
  required anchor height and uses executed progress while below it.
- Light-chain construction explicitly fails with an active anchor. Its ODR
  canonical-write paths have not been implemented or approved for restart use.
  Fast-sync live-body/pivot paths have synthetic coverage; this does not establish
  end-to-end fast-sync or freezer support for a release.

The anchor remains fixed after an explicit rewind. Rewinding is not a way to
accept a different anchor on resynchronization. A missing state can still cause
the existing repair routine to move a compatible node below the anchor; readiness
gates then apply until the accepted history is restored.

## Rollback defects found while testing

The existing full-node setup opens LevelDB without a freezer. `Rollback` called
`truncateAncient`, treated that layout's unsupported-operation result as a real
storage failure and exited through `log.Crit`. The original failure is retained
in [the evidence directory](evidence/restart-anchor-implementation-2026-09-24).
The fix exports the existing rawdb error sentinel and skips truncation only for
that exact unsupported-operation result. Injected storage errors remain fatal.

A second problem appeared after rollback: canonical indexes remain stored, so
reimporting a known block could advance the full head without advancing a lower
header head. `writeHeadBlock` now also advances the other head markers when the
header head is behind the adopted block. The regression requires readiness to
recover after reimport, rather than accepting a split between those head heights.

These are narrow persistence/recovery fixes. They do not change ticket rules,
rewards, balances, or fork weight.

## Validation

`TestRestartAnchorEnforcement` has 34 isolated cases covering incompatible fresh,
stored and known blocks; header/direct-header, receipt/ancient-receipt rejection;
mining/state-less writes; missing ancestry; incompatible or damaged startup
heads/indexes/bodies; configuration identity and snapshotting; genesis setup;
rewind and rollback recovery; and compatible full/header/receipt/pivot imports.
Rejected inputs are checked against a digest of every key/value, persisted and
in-memory heads, and the head-event channel. Compatible synchronization is also
checked after clean reopening. The additional large-batch case measures proof-cache
behavior after growing a stored header chain beyond cache capacity.

The compatible-fork case adopts a heavier branch diverging **after** the anchor.
This is intentional: the change prevents incompatible pre-restart ancestry from
winning, while descendants sharing the anchor retain ordinary Fusion fork choice.
It provides no new ongoing finality for transactions after the anchor.

`TestRestartRollbackDatabaseModes` covers memory and on-disk LevelDB without a
freezer, and verifies a genuine injected storage error is not ignored.
`TestRestartAnchorConfiguration` checks that mainnet remains unconfigured, a
caller cannot substitute its mainnet rule, and JSON does not persist the rule.

Final commands, logs, compiler/source/binary identities and exit codes belong in
[the evidence directory](evidence/restart-anchor-implementation-2026-09-24).
The final Windows ordinary restart suite passed in 96.397 seconds. The focused
Linux/CGO race suite passed all three repetitions, and the full Linux node build
succeeded. The 34 enabled-anchor cases therefore passed 102 Linux invocations.
The broader `core/rawdb` test package cannot compile because inherited tests
reference the removed `params.RinkebyGenesisHash`; the same failure was verified
on the unchanged source export. The `params` race tests passed. This is not a
claim that the entire repository test suite passes.
The synthetic fixtures use the public test key and selected backup observations,
not a full mainnet state or the operator's real signing key. They open no public
network listeners. The baseline replay uses its separately retained executable
and database; this work does not replace them.

## Remaining release gates

The later [multi-process rehearsal](restart-node-rehearsal.md) adds actual
service/IPC/miner/downloader evidence and readable hexadecimal hashes in anchor
rejection diagnostics. Its synthetic network passed compatible synchronization,
heavier stored-fork rejection, mining/transaction readiness, committed-head
SIGKILL/reopen and incompatible LevelDB startup refusal. These close specific
gaps in the initial entry-point tests, subject to that report's fixture limits.

The [interrupted-write rehearsal](restart-crash-rehearsal.md) subsequently found
and corrected partially published compatible reorganizations. It covers process
exits around every observed write for linear import, reorg and rollback, without
claiming power-loss durability or covering all head-changing APIs.

1. Review the implementation independently, including interrupted head/index
   writes, deep incompatible stored ancestry and cache behavior under concurrent
   imports. Measure startup cost on long
   post-anchor chains; the initial preflight walks their actual headers and can
   be repeated during service construction. Do not assume the memory cache makes
   initial startup constant-time.
2. Extend the separate-process peer/miner/RPC coverage to concurrent mining,
   live reorganization, rewinds during activity, disconnected operators and
   complete historical/full-state fixtures. The first rehearsal uses actual
   devp2p transport with an explicit downloader trigger and a sparse synthetic
   history; it does not prove operator startup timing or a genesis sync.
3. Extend write-boundary crash coverage to explicit rewind/reset/pivot operations,
   pruning and realistic large reorganization batches, and test supported
   ancient/freezer and fast-state-sync paths. The ancient-receipt negative case
   rejects before touching a freezer; it is not a successful freezer import test.
   The service can open its database before preflight, so this is not a claim that
   arbitrary database backends perform no file maintenance on open.
4. Complete full-state recovery construction, accounting review, signer procedure,
   baseline execution and supported-mode decisions. Bind the release to the exact
   accepted recovery end block only after those artifacts are approved.

No production anchor, public deployment, real-key signing, or balances policy
was selected by this implementation.
