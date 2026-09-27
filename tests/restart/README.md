# Synthetic restart investigation

These tests cover the restart investigation and the first narrow corrections,
not a complete mainnet restart implementation. The unchanged characterization
baseline is `d82a229`; current expectations require successful ticket
reconstruction and an error instead of a missing-ancestor panic. See
[the correction report](../../docs/restart-corrections.md). Run from the repository root:

```powershell
$env:CGO_ENABLED = '0'
go test ./tests/restart -v -count=1 -timeout=8m
```

The recorded run used portable Go 1.21.3 on Windows amd64. Its archive SHA-256
was checked against the [official Go releases](https://go.dev/dl/):
`27c8daf157493f288d42a6f38debc6a2cb391f6543139eba9152fceca0be2a10`.
This reproduces the recovery-era compiler version; it is not a recommendation for
a production release toolchain. The local runtime and caches live under ignored
`tmp/restart-runtime`, with no machine-wide installation or PATH change.

## Fixture limits

The fixture reads the saved public RPC observations in
`docs/evidence/restart-2026-09-23/responses.json`. It uses the actual recorded
ticket lifetimes/counts and the investigated owner's liquid/time-lock balances.
It substitutes a public synthetic key for that owner's address and inserts a
synthetic parent state at the observed height. Other owners' full account states
are not present. RPC's ticket map is sorted to obtain deterministic fixture
storage; its ordering is not asserted to reproduce the original ticket blob.

The seed parent and genesis are test scaffolding, not replayed mainnet history.
The source chain rules and activation heights are retained. No real staking key,
live database, network connection, or RPC submission is used by these tests.

The bridge test uses two independent in-memory databases, in one process. Signed
blocks are RLP round-tripped to clear cached selection fields, then passed to
`InsertChain` for header, body, and state validation. Both imports execute their
own transactions and reproduce the block's commitments. This is not yet a
multi-process, cross-platform block-exchange, or network-sync rehearsal. The ticket cache is
process-global, so the tests are deliberately not parallel.

Missing-state tests evict the global ticket cache and wrap the state database so
opening specified roots fails. Ten cases cover bridge steps 1–4 with one through
four consecutive unavailable states, falling back as far as the seed state.
Three expiry-boundary cases deliberately replace the other owners' ticket
lifetimes with synthetic lifetimes ending one second before, exactly at, or one
second after the first historical successor. These altered lifetimes are not
observations about mainnet. A separate missing-header wrapper exercises a
reconstruction error path without deleting data.

The focused purchase tests call the real RPC argument builder through a minimal in-memory
backend, sign with the public test key, and call the real transaction pool.
They do not exercise a JSON-RPC transport, wallet unlock, gas estimation, or the
auto-buy goroutine. The successful purchase is also executed and imported, and
its ticket existence is checked. Pool tests use `TimeLockForever` as the explicit
long-ticket end so they do not age out at the experiment's October 2026 date;
this is a test input, not a recommended production expiry. The production pool
reads its actual wall clock; these cases require a clock after November 2025.
The operating-system clock and production clock code are not changed.

`TestAutoBuyRuntime` adds a child-process experiment with the real miner, auto-buy
loop, gas estimator, temporary test-key keystore, and transaction pool. It runs
for roughly 25 seconds. Its setup uses a jump one hour before the actual clock
and perpetual setup tickets; mined timestamps and transaction hashes vary per
run. It now requires an initial attempt and an automatic retry of the identical
signed transaction after a submission failure, followed by receipt confirmation
and a successful head-triggered purchase. Each mined block is imported by another
in-memory chain. See [the controller report](../../docs/restart-purchase-controller.md)
for behavior, adapter limitations and remaining failure cases. The older
[runtime report](../../docs/restart-autobuy-experiment.md) records the reproduced
baseline stalls. No HTTP or P2P listener starts.

`TestSubmittedTicketReplacementAllowsExplicitRetry` requires the manual purchase
RPC to use the next pool nonce after a transfer replaces the pending purchase.
`TestAutomaticPurchaseRecovery` tests disabled states, wallet/estimator/funding
recovery, clean LevelDB/journal reopen with a locked wallet, conflicting purchases,
nonce gaps, controlled same-height canonical replacement and corrupt saved data.
It uses separate child processes, real temporary on-disk databases, and a mining
state adapter. Other owners receive synthetic perpetual tickets in these cases
so a transfer-only block can be constructed. A full race run with three
repetitions needs a longer timeout, for example `-race -count=3 -timeout=15m`.

`TestRestartAnchorEntryPointsCharacterization` runs nine child-process cases
against the existing client. It reproduces heavier-fork replacement and legacy
checkpoint gaps across stored forks, headers, receipts, fast-sync head commit,
startup/configuration ordering and expanded raw-body validation shortcuts. Its passing assertions
describe unsafe existing behavior, not an implemented anchor. See
[the entry-point report](../../docs/restart-anchor-investigation.md). These cases
use synthetic branches and checkpoint identities, never production anchor values.

## Results and expectations

- Present-day production from the expired seed tickets is rejected by import.
- A historical refund funds a long-lived purchase; eight bridge/replenishment
  blocks import successfully with matching commitments.
- Missing-state reconstruction of the time-jump block and the subsequent
  cleanup block succeeds, preserving direct-state header and ticket selection.
- The three synthetic expiry-boundary cases also require successful
  reconstruction. The old mismatch is retained in the baseline evidence.
- A missing ancestor header during reconstruction returns
  `consensus.ErrUnknownAncestor`; a panic fails the test.
- Before the first refund, the pool accepts a long purchase that the RPC builder
  and execution reject for insufficient historical time-lock coverage. After
  the refund, construction, admission, execution, and import succeed.
- Default historical purchase arguments produce an already expired interval
  and fail local pool admission. Moving the start to the present day fails the
  existing old-parent-plus-three-hours constraint in both builder and pool.
- With only one ticket left, finalizing a block without a replacement purchase
  fails with `Next block doesn't have ticket, wait buy ticket`.

The expected 5,000 FSN coverage after the first selection refund comes from the
independent interval calculation saved in `historical-refund-coverage.json`.
The expiration and minimum-ticket error expectations come from the respective
explicit source guards. Other checks use imported block commitments as the
comparison between separately executed states; they are not independent golden
vectors for the entire state transition.

The model uses the same account to pay fees and receive the block fees/reward.
Its net liquid increment is therefore not a general prediction for other miners.
Replacement ticket expiry is at least 30 days after its purchase start; reusing
one fixed expiry indefinitely would eventually violate the existing rules.

See [the experiment report](../../docs/restart-bridge-experiment.md) for the
temporary parent-time reconstruction experiment and outstanding work.

The following overlay commands are historical reproduction instructions for a
separate checkout of `d82a229`, before the corrections. They are not applicable
to current source. With the same Go environment configured:

```powershell
./tests/restart/run-parent-time-experiment.ps1 -Go go
```

Pass an absolute path to `go.exe` when using the portable compiler. The script
writes two compiler-overlay copies under ignored `tmp`, substitutes parent-time
cleanup, and changes only the reconstruction success expectation. It does not
edit production source. The missing-ancestor panic remains expected in this
experiment; the proposed cleanup change does not repair that separate defect.

Linux/CGO results and race-detector findings are recorded in
[the Linux investigation](../../docs/restart-linux-investigation.md). With the
Linux compiler and CGO prerequisites configured, the portable overlay runners are:

```bash
python3 tests/restart/run-parent-time-experiment.py --go go
CGO_ENABLED=1 python3 tests/restart/run-receipt-copy-experiment.py --go go
```

On that baseline, the receipt-copy experiment runs the auto-buy scenario three times under the
race detector with a temporary receipt-log ownership correction. Unchanged
production code fails that scenario. The verifier now imports both blocks after
the producer is closed, avoiding concurrent two-chain global-header access in
the fixture while retaining independent execution checks.

`TestPreservedBackupReadOnly` is skipped in ordinary runs. It requires
`FUSION_RESTART_CHAINDATA` to name a checksum-verified disposable copy of the
observed LevelDB-only backup. Compile the tests first, then run only this probe
in a network namespace with the copy mounted read-only. It checks the recorded
head/account/ticket observations and selected block/receipt commitments. It
does not run a node, sign blocks, traverse every state node, or replay history.

## Complete integrity and replay probes

The separate restart-anchor implementation is covered by
`TestRestartAnchorEnforcement` (36 isolated cases),
`TestRestartAnchorConfiguration`, and `TestRestartRollbackDatabaseModes`.
They use synthetic anchors; mainnet remains unconfigured. The original
`TestRestartAnchorEntryPointsCharacterization` intentionally retains the legacy
behavior with the new rule disabled, except that its stored-checkpoint-fork case
now requires the atomic reorganization correction to reject the branch. Original
failure evidence is retained. Run the focused set with:

```sh
go test ./tests/restart -run '^TestRestart(Anchor|Rollback)' -v -count=1
```

On Linux, add `-race` and run the compiled binary inside a network namespace.
The [implementation report](../../docs/restart-anchor-implementation.md) describes
coverage, the explicit light-mode restriction, the two rollback fixes and the
remaining process/crash/full-state gates. The tests never use the operator's key.

`TestRestartNodeRehearsal` is Linux-only and explicitly opt-in. It starts separate
instances of the actual node and Ethereum service with disposable LevelDB stores,
IPC endpoints and public synthetic signing keys. It refuses any network namespace
containing an interface other than an enabled loopback. Build first, then run:

```sh
go test -race -c -o /tmp/restart-node-tests ./tests/restart
cd tests/restart
sudo unshare --net -- bash -c 'ip link set lo up; exec runuser -u rehearsal -- env FUSION_RESTART_NODE_REHEARSAL=1 /tmp/restart-node-tests -test.run=^TestRestartNodeRehearsal$ -test.v -test.timeout=6m'
```

Replace `rehearsal` with a local unprivileged test account. No backup path is
needed. The tests use loopback devp2p and IPC, with no HTTP/WS, discovery, NAT,
bootnodes or production anchor. A test-only IPC API triggers the real downloader
and probes the worker guard; it is not included in the production node binary.
See [the service rehearsal report](../../docs/restart-node-rehearsal.md) for the
four scenarios, retained logs and explicit limits on the sparse history/crash case.

`TestRestartCrashBoundaries` is available on Windows and Linux, explicitly enabled
by `FUSION_RESTART_CRASH_REHEARSAL=1`. It uses actual LevelDB with a test-only write
wrapper, exits child processes before and after every observed write, then cold
reopens and resumes in fresh processes. There are 46 cuts per run across
linear import, compatible heavier reorganization, rollback and six explicit
rewind cases, reset and four pivot cases. Rewinds include below-anchor/split heads
and injected missing state or bodies. Pivots include receipt import followed by
full-head commit. It requires no
backup or operator key. For Linux, compile first and run inside a network namespace:

```sh
go test -race -c -o /tmp/restart-crash-tests ./tests/restart
cd tests/restart
sudo unshare --net -- runuser -u rehearsal -- env FUSION_RESTART_CRASH_REHEARSAL=1 /tmp/restart-crash-tests -test.run=^TestRestartCrashBoundaries$ -test.v -test.timeout=6m
```

Use a local unprivileged account in place of `rehearsal`. On Windows:

```powershell
$env:FUSION_RESTART_CRASH_REHEARSAL = '1'
go test ./tests/restart -run '^TestRestartCrashBoundaries$' -v -count=1
```

See the
[crash report](../../docs/restart-crash-rehearsal.md) for the reproduced defect,
atomic branch-publication correction, and the
[rewind report](../../docs/restart-rewind-rehearsal.md) for the atomic rewind and
repair correction. The [reset/pivot report](../../docs/restart-reset-pivot-rehearsal.md)
adds interruption and missing-target checks without further production edits.
These reports describe fixture limits and remaining durability, state-download,
genesis-sync and pruning/freezer gates.

`TestPreservedStateIntegrity`, `TestPreservedHistoryIntegrity` and
`TestPreservedTicketReconstruction` additionally require
`FUSION_RESTART_FULL_AUDIT=1`. Compile first and run the resulting test binary
with no network and the verified source mounted read-only. The first two traverse
reachable state and canonical history respectively; the third validates actual
recent headers with direct state and forced missing-state reconstruction.
The ordinary suite tests the scanners against deliberate database corruption.

On Linux, `TestPreservedHistoryReplay` requires an absolute, nonexistent
`FUSION_RESTART_REPLAY_DIR`, a height in `FUSION_RESTART_REPLAY_END`, and the
Windows drive mount in `FUSION_RESTART_HOST_STORAGE` (for example `/mnt/d`).
The output parent must already exist. It executes canonical blocks into a new
database with the original checkpoint behavior and stops on an import error,
unexpected head, or insufficient disk reserve. Source and output must be separate.
Use a bounded pilot before choosing a full replay layout. Existing targets are
rejected by default. `FUSION_RESTART_REPLAY_RESUME=1` requires a matching identity
manifest from the same retained executable, then verifies the target head and
available state read-only before reopening it writable. Older pilots without
that manifest cannot be automatically resumed. Never run two writers.
`FUSION_RESTART_REPLAY_STOP_FILE` names an optional file whose existence triggers
a controlled failure and normal cleanup at the next batch boundary. A timeout
or forced process/WSL termination does not guarantee that cleanup.

`TestPreservedReplayHeadReadOnly` checks a closed replay without reopening it
writable. Set `FUSION_RESTART_INSPECT_REPLAY_DIR` to a read-only mount of the
replay and `FUSION_RESTART_INSPECT_REPLAY_HEIGHT` to the exact expected height;
the preserved source and `FUSION_RESTART_FULL_AUDIT=1` are also required. It uses
the existing resume checks, including source difficulty, receipts and tickets,
then requires the exact requested height. It does not change the retained
executable identity needed for a later writable resume.

`TestStateExportIntegrity`, `TestStateExportDirectory` and `TestStateExportCrash`
exercise the state-only extractor with disposable fixtures. On Linux,
`TestPreservedStateExport` additionally requires the full-audit/source settings,
a read-only source mount, an absolute new `FUSION_RESTART_STATE_EXPORT_DIR`, and
`FUSION_RESTART_HOST_STORAGE` naming the output's actual host drive. An optional
`FUSION_RESTART_STATE_EXPORT_STOP_FILE` requests cleanup at a batch boundary.
The extractor enforces the existing 20 GiB output-filesystem and 50 GiB host
reserves. Existing targets are rejected and incomplete copies are not resumable.

Run `TestVerifyStateExport` in a separate process with
`FUSION_RESTART_VERIFY_EXPORT_DIR` naming the closed artifact and
`FUSION_RESTART_CHAINDATA` unset. It independently traverses all state and checks
the saved head inventory/tickets before creating `verified.json`. Run only that
test in the process so ticket caches are cold. By default the verifier must be
the retained writer binary. To verify from a different build/platform, explicitly
set `FUSION_RESTART_STATE_EXPORT_WRITER` to an absolute path to the trusted
retained writer binary; its bytes must match the recorded writer SHA-256. Both
writer and verifier hashes are logged. The verifier is portable; the protected
real-backup extraction and replay inspection remain Linux-only.
These probes export no canonical
chain metadata, sign no blocks, and do not create a bootable node database. See
the [extraction report](../../docs/restart-state-export.md) for measured results,
filesystem choice and remaining full-state execution work.

See [the integrity/replay report](../../docs/restart-integrity-investigation.md)
for measured results, limits and evidence. Successful structural checks and
checkpoint-assisted execution are not full independent consensus verification.

The [full-state rehearsal](../../docs/restart-full-state-rehearsal.md) uses new,
checksummed copies of the exported state. `TestExportFullStateContext` is a
Linux-only, read-only-source probe with `FUSION_RESTART_CONTEXT_OUTPUT` naming an
absolute new RLP file; the full-audit/source variables and read-only mount are
required. The retained context also drives ordinary integrity tests.

`TestFullStateRehearsal` takes `FUSION_RESTART_FULL_STATE_DIR` (absolute disposable
copy with the verified-copy proof) and `FUSION_RESTART_FULL_STATE_MODE`:
`prepare`, `produce`, `import`, or `cold`. Run each phase in a separate process.
The latter phases use the absolute `FUSION_RESTART_FULL_STATE_BLOCKS` artifact
directory; only `produce` creates it. Source-backup environment must be unset.
Preparation changes FSN funding and ticket ownership to public key 1, writes a
complete difference ledger and installs a synthetic trusted parent. These are
not mainnet node data directories. Existing fixtures and output artifacts are
not silently reused. Use the retained Windows runner for exact copy checks,
capacity guards, phase ordering and logs.

`TestFullStateKeyAudit` reads only the state artifact when
`FUSION_RESTART_FULL_STATE_AUDIT` is set. Optional
`FUSION_RESTART_AUDIT_ADDRESS` selects one strictly validated public wallet
address; without it the original and public-test-key accounts are reported.
It records the source head and a current 30-day time-lock coverage window.
`TestFullStateLedgerAudit` separately
decodes/checks fixture and block ledgers with `FUSION_RESTART_FULL_STATE_LEDGER`,
`FUSION_RESTART_FULL_STATE_BLOCKS`, and a new absolute
`FUSION_RESTART_FULL_STATE_ACCOUNTING` output. It opens no state database.
`TestFullStateDifferenceAccounting` and `TestFullStateContextIntegrity` run
without opt-in data or real keys. The full-state report records which actual
execution, cold traversal and Linux race checks have passed and their limits.

`TestLastTicketHandover` tests a sparse two-key final-ticket transition using
public keys 1 and 2. Synthetic successor funding is explicit: 10,001 FSN,
the observed donation balance of 12,020.102 FSN, or an insufficient 5,001 FSN.
It checks the old owner's selection/refund, independent imports, replacement
purchases and an unchanged retired account. See the
[handover report](../../docs/restart-wallet-handover.md) for the distinction
between this core test and the remaining full-state/runtime/key-custody gates.

`TestSingleBackupBlockHandover` tests the subsequently selected shorter startup:
one original-signer historical block includes the successor's first long-lived
purchase; the successor then jumps forward and produces five blocks with
replacements. Independent imports agree, the original signer makes no purchase,
its selected ticket is refunded, and its other historical ticket disappears
without another account credit. `TestSingleBackupBlockRejectsShortSuccessorTicket`
rejects using a historical 30-day ticket to seal the present-day jump. Both use
public test keys and explicit synthetic successor funding of 12,020.102 FSN;
neither uses real keys or proves actual miner/network/auto-buy operation.

`TestFullStateHandover` opts into complete preserved-state copies through
`FUSION_RESTART_HANDOVER_DIR`, `FUSION_RESTART_HANDOVER_MODE` and an absolute
`FUSION_RESTART_HANDOVER_BLOCKS` directory. Modes are `prepare`, `produce`,
`runtime`, `import` and `cold`. Preparation reuses the existing three-account
backup-signer substitution, then separately debits the donation balance and
credits public test key 2 with exactly two more account changes. Produce creates
one backup-key block and five successor blocks; each runtime invocation produces
two worker/automatic-buyer blocks, with the second invocation testing process
restart. Separate import and cold modes compare complete ledgers for all ten
blocks; cold also reconstructs unavailable suffix states and traverses the full
state. Use the report's scripts only with new disposable targets.

`TestFullStateHandoverAccounting` opens no database. Set
`FUSION_RESTART_HANDOVER_AUDIT` to the prepared fixture ledger directory and
`FUSION_RESTART_HANDOVER_BLOCKS` to the recorded blocks. It checks conservation
of each owner's future FSN rights over all liquid/time-lock/ticket boundaries,
ordinary fees/rewards/retreat penalties and preservation of unrelated fields.
`TestHandoverFundingGuard` rejects unauthorized funding/field changes;
`TestHandoverTemporalAccounting` checks the boundary arithmetic.

`TestHandoverMissingRecoveryPurchase` characterizes two different outcomes:
omitting the jump replacement produces an accepted but stranded chain with only
expired tickets; omitting the cleanup replacement is rejected and can be retried
with a purchase. The [full-state handover report](../../docs/restart-full-state-handover.md)
records evidence and remaining node-service/network/construction gates.

`TestRecoveryOperatorCLI` requires an absolute `FUSION_RECOVERY_OPERATOR` pointing
to a separately built command. It runs review/prepare/init/sign/export using
public encrypted keys 1 and 2. Each working/verifier import and cold check runs
in its own child process so consensus caches are not inherited from the builder.

`TestFullStateRecoveryOperator` additionally takes
`FUSION_RESTART_OPERATOR_FULL_STATE_ROOT`, containing fresh, checksummed
`reference`, `working` and `verifier` compact-state copies. The original-backup
environment must be unset. It reuses the explicit public-key substitutions,
complete account-difference accounting and command refusal checks. This is an
opt-in complete-state command rehearsal, not a real-key launch or a public node
distribution. Existing targets are refused by the preparation script. Exact
scripts, binary pins and results are in
[the evidence directory](../../docs/evidence/restart-full-state-operator-2026-09-25).

`TestAutomaticPurchaseCrashBoundaries` is enabled with
`FUSION_PURCHASE_CRASH_REHEARSAL=1`. Sixteen cases use separate prepare, abrupt
exit, recover and cold-check processes. Test-only wrappers stop before/after
the real automatic-purchase record save, pool submission, retirement or adoption.
Reopening checks exact record and pool contents; recovery starts with a locked
public-key wallet and rejects extra submission over a retry interval. The
lost-pool cases preserve the original journal and select a fresh journal path.
No production fault hooks or preserved database are used. See the
[report](../../docs/restart-purchase-crash-rehearsal.md) for the matrix and
the distinction between a process exit and machine power loss.

`TestAutomaticPurchaseStorageErrors` runs eight isolated cases returning errors
from automatic-record `Has`, `Get`, `Put` and `Delete`, including writes/deletes
that take effect before reporting an error. It reuses the real pool, keystore and
controller fixture, checks retained bytes and observes a full retry interval.
These are database-interface faults, not physical disk failure emulation.

The opt-in Linux `TestRestartNodeRehearsal/purchase_peer_*` cases add two real
devp2p/downloader reorganizations above a common synthetic anchor. The actual
worker is enabled but its test block signer refuses signatures, allowing the
automatic buyer to run while the peer supplies a controlled heavier branch.
They check receipt relocation/replacement, nonce reconciliation, logs, persisted
heads and exact record recovery into an empty pool after process restart. Use a
short Linux `TMPDIR` for IPC socket paths. See the
[storage/peer report](../../docs/restart-purchase-storage-and-peers.md) for results
and limits; neither case tests simultaneous live block producers.

`TestRestartNodeRehearsal/purchase_peer_nonce_rollback` uses an explicit two-owner
synthetic fixture and a valid heavier three-block peer branch to roll back two
ticket purchases. It requires the saved successor to survive conflicting pool
reinjection and a cold nonce-gap pause, then verifies ordinary raw resubmission
and real mining of the missing purchases followed by byte-identical recovery.

`TestRestartNodeRehearsal/competing_purchase_miners` runs two distinct normal
miners/buyers on disconnected branches, bounds each initial purchase count,
reconnects them, and checks continued purchases and matching canonical/persisted
state. Only its final stable inspection holds block signing. Both tests use
synthetic million-FSN funding to isolate concurrency from launch funding. See
the [nonce rollback report](../../docs/restart-purchase-nonce-rollback.md) for the
demonstrated manual-repair boundary and sparse-history limitations.

`TestFinalizeParentIsolatedFromConcurrentImport` pauses processing of a batch's
second block and verifies/finalizes an independent branch. It deterministically
reproduces the inherited shared-parent ownership defect. The companion
`TestHeaderBatchUsesUnstoredParents` validates three linked headers that are
absent from the receiving database, guarding the explicit batch-parent path.
See the [parent isolation report](../../docs/restart-parent-isolation.md) for
baseline failures, repeated Windows/Linux checks and the separate P9 correction.

`TestColdHeaderValidationBoundaries` runs eight cases in separate processes and
small LevelDBs, checking absent future ticket caches and account states. It
characterizes headers-only rejection, body/receipt requirements, reconstruction
with complete stored data, incremental-header and invalid-header rejection, and
full import followed by another cold reopen. These cases also run with a pre-P9
source overlay. See the [cold-header report](../../docs/restart-cold-header-validation.md);
passing rejection cases do not establish fast/light sync support.

`TestRestartNodeRehearsal/dense_miner_fixture` verifies a complete synthetic
devnet genesis-to-24 history in two independent databases and cold services.
The new `continuous_partition_miners` case requires both node-rehearsal and
network-partition opt-ins, root, and a disposable loopback-only namespace.
It leaves both normal miners and buyers enabled during real packet loss and
healing. Its strict unattended-replenishment requirement currently **fails**:
the nodes can agree on an advancing chain while a buyer's retained future nonce
has missing predecessors. The [continuous partition report](../../docs/restart-continuous-partitions.md)
records the failed runs, the passing complete fixture and compatibility check,
and the difference between re-inclusion and renewed automatic buying. This is
an opt-in limitation reproducer, not evidence of unattended recovery. Its
synthetic genesis and twelve-minute child limit do not affect production code.

`TestRestartNodeRehearsal/continuous_partition_nonce_repair` uses the same opt-ins
and namespace restrictions. After a 90-second outage and a stable future-nonce
pause, it resubmits preserved original purchases individually through the normal
RPC while both miners and buyers remain enabled. It requires the exact saved
intent and at least two fresh automatic successors to execute, samples remaining
tickets, then checks both cold databases and receipts. This tests explicit repair
with generous synthetic funding and available original bytes; it does not change
the failed unattended-replenishment requirement. See the
[live repair report](../../docs/restart-live-nonce-repair.md).

`purchase_peer_nonce_rollback` additionally verifies exact signed-byte retrieval
from a discarded block through ordinary RPC before and after cold restart, then
repairs using the retrieved transaction. `small_reserve_nonce_repair` exercises
the live repair requirement with 12,020.102 synthetic FSN per wallet and only one
or two setup tickets per owner. A zero-ticket owner is logged while another
eligible owner remains; insufficient repair funding fails the requirement.
During initial downloader synchronization, the repair observer permits the
normal temporary worker pause and requires automatic resumption within 30 seconds.

`TestRestartPurchaseRecordCommand` uses the same isolated-network opt-in and an
absolute `FUSION_RESTART_EFSN_COMMAND` path to a built executable. It checks the
existing `db get` command against a stopped synthetic database, exact saved bytes,
unchanged database file hashes, a missing record and an open database lock.
See the [retrieval and small-reserve report](../../docs/restart-small-reserve-and-retrieval.md)
for retained passes, failures and production-accounting limits.

`TestRestartNodeRehearsal/funded_small_reserve_repair` adds a separate public-key
sponsor with 6,000 synthetic FSN at genesis to the same small miner reserves.
It requires a pre-transfer insufficient-balance rejection, one ordinary
5,000-FSN transfer, then sequential original purchases with bounded waits for
ordinary ticket returns. Nonce, saved intent and pool preconditions stay fixed
while waiting. Acceptance includes the exact saved purchase, two automatic
successors, both cold databases and the sponsor's exact transfer/fee accounting.
An independent ledger checks future liquid/time-lock/ticket rights on each
isolated branch, before funding and after repair against ordinary rewards,
fees, transfers and first-retreat losses. See the
[funded repair report](../../docs/restart-funded-repair.md) for the retained
attempts and limits; this does not add an automatic repair or funding mechanism.

`TestRestartNodeRehearsal/controlled_zero_ticket_reserves` replays the same fully
executed synthetic prefix into fresh databases for four funding comparisons.
All ordinary setup tickets have finite 30-day intervals. After two first-retreat
losses leave one owner with zero tickets and insufficient funds, it compares no
transfer, 5,000 FSN, 10,000 FSN and 5,000 FSN followed by another missed ticket.
The same seven manually signed purchases are used across branches. Cooperative
branches advance with the first-ranked producer between insufficient-balance
probes and reject any additional retreat. Both cold services, exact sponsor
spending and per-block interval accounting are checked in every branch.
This constructs/imports valid blocks and uses actual pool admission; it does not
exercise live worker scheduling, a partition, recovered orphan bytes or a saved
automatic intent. It needs the node-rehearsal opt-in and isolated loopback
namespace, but not the packet-loss opt-in. See the
[controlled reserve report](../../docs/restart-controlled-reserves.md) for the
observed waits, repeat-loss boundary and preserved-wallet accounting limits.

`TestPreservedHandoverFundingCoverage` reads both committed ten-block complete-state
handover evidence sets and reuses the independent conservation/receipt audit.
It verifies exact account-RLP continuity, the selected bridge ticket, subsequent
30-day intervals, no successor retreats, and funding before selection refunds.
Independent interval-boundary minima are compared with native spendable-lock
calculations. Six frozen-state future samples per platform separate free funds
from tickets whose intervals remain live. No backup, chain database, node service
or network access is used. See the [funding coverage report](../../docs/restart-handover-runway.md)
for the initial incorrect no-retreat assertion, the final pass and limits.

`TestFullStateSingleProducerOutage` requires fresh verified complete-state copies
under `FUSION_RESTART_FULL_STATE_OUTAGE`, the node/partition opt-ins and the
existing private loopback-only namespace. Both copies execute the retained
three-block recovery. One donation producer and a non-producing verifier then
experience 90 seconds of packet loss, followed by a producer SIGKILL with an
observed persisted pending purchase. Reopen must retain the exact bytes/nonce
into an empty pool. After normal miner start and network healing, acceptance
requires automatic execution plus two fresh successors, ordinary peer catch-up,
matching cold account ledgers and independent interval conservation. It does
not create competing branches or exercise manual nonce repair. See the
[complete-state outage report](../../docs/restart-full-state-outage.md).

`TestFullStateParticipantEntry` requires fresh complete-state copies under
`FUSION_RESTART_PARTICIPANT` and the same isolated-node/namespace opt-ins. It
executes the reviewed recovery prefix, then funds public test key 3 using the
backup fixture's existing mature rights and an ordinary transfer. The donation
key signs every additional constructed block; the backup only signs two funding
transactions and buys no ticket. Both donation and entrant services must then
buy and sign canonical blocks, followed by matching cold databases and complete
interval accounting. The shared node harness permits only public test keys
1, 2 and 3. This hypothetical funding is not a launch requirement or permission
to use the real backup owner's funds. No partition or manual repair is exercised.
See the [participant entry report](../../docs/restart-full-state-participant.md)
for the two preserved setup failures and corrected passing run.

`TestFullStatePartitionRepair` uses fresh complete-state copies under
`FUSION_RESTART_FULL_STATE_PARTITION`, plus the node and network-partition opt-ins.
After the same funding prefix it isolates both active miners for 90 seconds,
then requires ordinary convergence and a stable nonce gap before retrieving and
resubmitting original purchases. Successful repair requires the exact saved
intent, two new automatic purchases and cold interval accounting. The initial
run failed before convergence; later repair assertions remain unexercised here.

`TestFullStatePartitionColdDiagnosis` takes those stopped disposable copies via
`FUSION_RESTART_PARTITION_DIAGNOSIS`. It preserves and audits each cold branch
before reconnecting fresh services with mining/buying disabled. It records
heads, advertised peer difficulty and a separate explicit downloader diagnostic
if ordinary sync fails. `FUSION_RESTART_NODE_DEBUG=1` enables debug output only
in test child services. The diagnostic must not be run against a live database
or an original backup. See the [partition report](../../docs/restart-full-state-partition.md)
for the equal-weight observation, missing-history failure and required follow-up.

The partition test now additionally requires `FUSION_RESTART_HISTORY_INPUT`:
the genuine historical segment exported by `TestExportFullStateHistory`. The
extractor requires the existing read-only backup opt-in/mount, an absolute
`FUSION_RESTART_HISTORY_OUTPUT`, host storage reserve and mode `measure` or
`export`. It measures before copying, preserves linked original headers and
bodies, checks transaction commitments and stored difficulty, and authenticates
the end against the retained preserved context. It deliberately treats Fusion's
`UncleHash` as the existing PoS field and requires an empty actual uncle list.
`TestFullStateHistoryBodyValidation` covers that distinction and damaged bodies
or ancestry. Installation validates the whole file before writing only genuine
blocks below the audited synthetic parent, and requires unchanged active heads.
The recovery observer logs both local and advertised peer heads/difficulty every
ten seconds. See the [genuine ancestry follow-up](../../docs/restart-partition-history.md).

`TestFullStatePostSyncAccounting`, with `FUSION_RESTART_POST_SYNC` pointing at
stopped disposable copies, compares the complete cold canonical suffix after
successful synchronization. It verifies unchanged saved bytes, nonce, tickets,
liquid and head/current-time interval coverage, and checks actual local pool
admission without starting a miner or network service.

`TestFullStateOriginalForkHistory` takes `FUSION_RESTART_HISTORY_RECHECK` plus
the history input and isolated-node opt-ins. It augments the prior stopped fork,
requires its original equal-weight heads, and repeats the previously failed
explicit downloader request with signing/buying disabled. Storing the remote
branch is its acceptance condition; it does not require equal-weight heads to
converge or alter fork choice.

`TestFullStateFundingRecovery` requires `FUSION_RESTART_FUNDING_RECOVERY` to name
verified disposable copies of the retained stopped funding-failure state. It
tests the same saved purchases before and after 1,200/1,800-FSN contributions
from the existing backup/entrant test accounts. The entrant's saved nonce 11
executes before its contribution at nonce 12. No funds or tickets are injected.
Both cold databases and every account interval must reconcile; additional
transfers are constrained by exact signed hash and height. Original failed
databases are copied and rehashed, never opened by this experiment.

`TestFullStateFundingLiveContinuation` opens that controlled result through
`FUSION_RESTART_FUNDING_LIVE`. Its original entrant-first startup failed before
producing a block. `TestFullStateFundingStartOrder` explicitly resumes that
stopped failure with its observed saved-record state, enables both miners before
either buyer, and requires the same automatic nonce-13 bytes. Acceptance still
requires two fresh purchases per owner, canonical native receipts, matching cold
account ledgers and saved intents. All three tests require the existing private
network namespace and node opt-ins; none exercises a partition or nonce gap.
See the [existing-funds report](../../docs/restart-existing-funds.md).

The original and reordered live funding tests both fail full replenishment:
the reordered run advances thirteen blocks but leaves the donation purchase
pending. `TestFullStateFundingColdDiagnosis` uses
`FUSION_RESTART_FUNDING_DIAGNOSIS` on those stopped copies to compare saved
nonces, real pool admission and both complete canonical ledgers. Its first
accounting pass exposed a legitimate additional mature-lock conversion log.
`TestFullStateFundingLedger` rechecks the retained artifacts without opening a
database and passes after validating that conversion independently. The old
one-log assertion failure is retained. The evidence does not establish the exact
remote delivery/admission failure; that needs live recipient-pool observations.

`TestFullStateDeliveryHistoricalAdmission` and `TestFullStatePurchaseDirectDelivery`
use `FUSION_RESTART_PURCHASE_DELIVERY` for a fresh verified copy of the stopped
31-block result, plus the existing isolated-node and network-namespace opt-ins.
The first test uses the real remote pool against retained historical states:
the exact nonce-8 purchase is rejected at height 15,130,098 by the three-hour
start-time rule, then accepted at 15,130,099 and 15,130,111. It does not rewind
the database. The live test records both pools, submits the unchanged saved
bytes directly to the entrant, enables both workers before the buyers, and
requires native canonical receipts for the original purchases and automatic
successors at nonces 9/27 or later. Both tests pass with race detection. Both
cold ledgers and saved records reconcile through forty suffix blocks, with the
prior thirty-one unchanged. Failed expectation/output-path attempts are retained.
This proves explicit delivery recovery without new funds, not the original
wire rejection or automatic retry. See the
[purchase-delivery report](../../docs/restart-purchase-delivery.md).

`eth/TestRestartPeerPurchaseRetry` requires `FUSION_RESTART_PEER_RETRY` to name the
fresh prepared protocol copy. It uses the actual handler, real pools and block
importer over controlled message pipes. Three race-detected cases pass: explicit
same-peer retry, ready pending replay, and discarded replay before readiness
followed by a successful ready replay. The unchanged legacy `eth` package tests
do not compile; the evidence runner builds the platform production file list plus
this focused test and retains the package failure separately.

`TestFullStatePurchasePeerReconnect` shares the delivery harness but submits the
saved purchase only to its originating node. It reconnects the real services
after mining readiness, then requires the same canonical native purchases and
cold accounting as direct delivery. The retained attempt recovers the original
purchase but fails on the next donation purchase, which remains absent from the
recipient pool. The existing cold diagnostic passes all forty-four suffix blocks
and both saved-purchase admissions. `TestFullStateReconnectHistoricalAdmission`
then passes real remote pool checks on the new nonce-9 bytes: insufficient balance
before the donation's selection/refund block, accepted afterward. Both tests use
`FUSION_RESTART_PURCHASE_DELIVERY` on their corresponding disposable state. See
the [peer retry report](../../docs/restart-peer-purchase-retry.md); a successful
one-time replay is not described as sustained recovery.

`TestFullStateRetainedPartitionFundedRepair` uses fresh verified copies of the
retained participant checkpoint through `FUSION_RESTART_RETRY_PARTITION`, the
genuine history input and the existing isolated-network opt-ins. It keeps both
miners and automatic buyers enabled through packet loss, reconnection and a
manual nonce repair. Observed branch hashes/bodies are retained through healing;
all missing signed purchases must be retrieved before funding or resubmission.
The specified 1,200/1,800-FSN transfers use only existing balances and public
synthetic keys. The active donor's transfer follows its exact pending purchase;
a changed nonce/intent stops the attempt instead of replacing a transaction.
The cold audit, `TestFullStateUninterruptedPartitionColdAudit`, runs separately
even after a live failure and accounts for any planned transfers actually mined.
These experiments do not authorize use of the real backup wallet's funds.
See the [uninterrupted funding report](../../docs/restart-live-funded-partition.md).
Its retained run fails at the seventh manual original after six successful
repairs. `TestFullStateManualGapHistoricalAdmission` uses a fresh copy through
`FUSION_RESTART_PURCHASE_DELIVERY` and the existing historical-pool harness to
check those same bytes before and after stake return and at the final head.
Rejection before return and acceptance afterward pass; the original live wire
sequence remains unrecorded.

`eth/TestRestartManualPurchasePeerRetry` uses `FUSION_RESTART_MANUAL_RETRY` with
the exact prepared diagnostic copy and a loopback-only namespace. With the
original nonce-16 purchase and selection block 15,130,121, it records real remote
balance rejection, known-peer broadcast suppression after block import, then
successful explicit resend or ready-peer pending replay. Both cases and the
four earlier nonce-8 cases pass under race detection.

`TestFullStateManualPredecessorDelivery` uses `FUSION_RESTART_PURCHASE_DELIVERY`
on fresh copies of the failed live run at 15,130,125. It submits the original
nonce-16 bytes directly to the entrant through production RPC, checks both saved
intents remain unchanged, and requires native success plus two fresh automatic
purchases from each owner. The 150-second attempt fails waiting for ordinary
ticket selection after one fresh donation purchase; the fresh 300-second-window
attempt passes. Both cold ledgers are checked separately by the existing
`TestFullStateUninterruptedPartitionColdAudit`. These are restarted continuations,
not a passing uninterrupted partition rehearsal. See the
[manual delivery report](../../docs/restart-manual-purchase-delivery.md).

`TestFullStateRetainedPartitionDeliveredRepair` adds recipient delivery to the
uninterrupted funded partition through the existing `FUSION_RESTART_RETRY_PARTITION`
guard. It retains pool observations, allows ordinary propagation first, and may
submit the same reviewed manual predecessor to the other producer only after
checking matching heads, an unchanged saved intent and absence from that pool.
The saved automatic purchase must execute without direct intervention. The
reserve formula is unchanged; this case waits up to 120 seconds for ordinary
production to satisfy it before injecting packet loss. Funding arithmetic uses
`fsn_getRawTimeLockBalance` and validates normalized intervals. The display-form
RPC can contain overlapping intervals and must not be fed directly into
`TimeLock.Add`, `Cmp` or `GetSpendableValue`; doing so caused the retained false
reserve failures. Original purchase and
automatic-successor receipt windows are 300 seconds. The shared node harness
now allows 60 seconds for IPC readiness after a recorded 15-second startup
timeout on a disposable full-state database. These are test limits, not new
production settings. See the [uninterrupted delivery investigation](../../docs/restart-uninterrupted-delivery.md)
for the individually retained attempts and their acceptance results.

`TestFullStateRetainedPartitionRejectedRepair` runs the same uninterrupted
sequence and deliberately rejects its first manual original at the receiving
pool with a temporary minimum-price setting through existing RPC. It requires
the receiver's JSON trace to identify the exact rejected transaction, restores
the original price, observes local-only pending status for 15 seconds, and then
requires successful direct delivery of that specific original by the existing
repair helper. The saved automatic intent receives no direct intervention.
The stimulus is test-only and is not an operator procedure. The ordinary case
retains its original behavior. See the
[injected-rejection report](../../docs/restart-injected-manual-delivery.md).

`TestFullStateEqualWeightRejoin` resumes the original equal-weight full-state
branches after validating their genuine ancestry. It records a connected idle
control, then starts both ordinary miners/buyers and requires convergence plus
three additional common descendants without explicit downloader calls or new
funding. `TestFullStateFreshEqualWeightRejoin` first reconstructs the same signed
branches from the preserved state, restoring their original synthetic saved
intents and requiring that neither copy knows the opposite tip. Both runners
use a separate cold ledger audit even if live convergence fails. See the
[equal-weight investigation](../../docs/restart-equal-weight.md) for the retained
state's earlier downloader history and the distinction from purchase recovery.

`TestFullStateEqualWeightCoordinatedPause` uses fresh copies of the retained
first-contact failure, with expected initial heads derived from its stopped
result and checked against its cold audit. It reproduces at least two further
equal-weight divergent blocks before disabling only the donation miner and
buyer through existing RPC. Both services stay connected; the entrant keeps
mining and buying. The test requires ordinary adoption of the entrant branch
and three additional common descendants within 150 seconds, followed by a
35-second stable shared head after stopping. It retains both pre-pause branches,
all observed branch bodies, per-second head/peer/purchase records and exact
stopped intents. The separate cold audit checks both canonical ledgers and both
pre-pause ledgers even if live convergence fails. This tests assisted branch
convergence, not unattended convergence or recovery of the paused buyer. See
the [coordinated-pause investigation](../../docs/restart-equal-weight-pause.md).

`TestFullStatePausedPurchaseDiagnosis` uses fresh copies of that paused result
and scans retained noncanonical bodies for all missing donation purchases at
nonces 8–38. It compares them with the saved pre-pause branch, retrieves their
exact bytes through existing block-hash RPC before and after restart, and
submits each original plus the saved nonce-39 intent to both local pools.
All 64 submissions must fail for funding; the entrant's unchanged funded intent
must be admitted on both nodes as a positive control. Mining and automatic
buying stay disabled, and the services are not peered. The native purchase
parameter check is also exercised at each `end - 29 days` boundary and one
second beyond it. The separate cold audit must preserve both canonical ledgers
and both saved intents exactly. This is a diagnosis at a fixed head and
recorded wall time, not a sequential repair, future-block execution or automatic
resumption test. See the [paused-purchase report](../../docs/restart-paused-purchases.md).

`TestFullStateExplicitNonceNeutralization` starts fresh copies of the paused
result, signs a separately labelled already-unsuitable BuyTicket probe through
existing RPC and requires native pool rejection. It then signs 31 zero-value
self-transfers for missing nonces 8–38 through `eth_signTransaction`, submits
the exact bytes to the entrant, and requires matching canonical receipts on
both nodes. The entrant mines and buys normally. The donation buyer runs for
12 seconds with the test-only held signing worker; it must preserve saved
nonce 39 and remain unfunded. This is deliberate purchase abandonment, not
historical-original expiry, donation block production or automatic replacement.
`TestFullStateNonceNeutralizationColdAudit` checks both full ledgers, with only
the explicitly listed transaction hashes allowed as zero-value self-transfers.
The evidence verifier independently checks all 31 inclusions, gas accounting,
saved bytes and unchanged donation time locks. See the
[nonce-abandonment report](../../docs/restart-expired-nonce-neutralization.md).

`TestFullStateStaleIntentRecovery` starts fresh copies of the nonce-abandonment
result and explicitly seeds a separately signed, already-unsuitable nonce-39
record before service startup. It retains the original bytes and changes no
canonical state. Real miner/buyer operation must preserve that stale record
and reject it through pool RPC before and after 3,000 FSN of ordinary synthetic
funding. Entrant funding follows its saved/pending nonce-44 purchase at nonce 45;
the retained initial attempt at nonce 44 stalls buying and finalization without
advancing either chain. An explicit RPC-signed nonce-39 self-transfer must then
retire the stale record without a purchase receipt, followed by three fresh
automatic donation purchases and actual donation block production. Recovery
makes no direct database edits and uses no held signing worker. The separate
`TestFullStateStaleIntentColdAudit` includes the previous 31 self-transfers,
the two funding transfers and the new self-transfer in its exact allowlist.
The joint evidence verifier checks both the retained failure and passing case.
See the [saved-intent report](../../docs/restart-stale-intent.md).

`TestFullStateRecoveredBuyerRestart` opens fresh copies of that stopped result
with initially empty pools. The donation buyer must restore the exact saved
nonce-43 bytes, keep them stable across a retry interval at the unchanged head,
and execute them after the eligible entrant starts. Ordinary peer propagation
and automatic buying must then produce two fresh donation successors, entrant
purchases and actual block production by both owners. There is no new funding,
manual transaction submission, record injection or held-signature worker. The
retired stale purchase must still have no canonical receipt. The separate
`TestFullStateRecoveredBuyerRestartColdAudit` reconciles both histories and
requires all 34 ordinary transfers to remain in the original prefix. Evidence
verification checks exact saved-byte inclusion, sequential native purchases,
matching cold intents and the unchanged 60-block prefix. See the
[normal-restart report](../../docs/restart-recovered-buyer-restart.md).

`TestFullStateAbandonmentReorg` starts the recovered donation copy at 15,130,140
with confirmed purchases 40–42 and saved 43. A second, older copy imports the
exact funding prefix through 15,130,132 and constructs an ordinary heavier
entrant-only suffix. No head, account state or purchase record is edited.
An explicit downloader request over real peers must remove the abandonment
and three purchases, restore canonical nonce 39 and preserve saved 43. The
test-only held signer prevents production during observation. The live pool
must retain the original self-transfer and purchase 40; after a restart with
the harness's disabled pool journal, the buyer must retain its nonce gap with
an empty pool. Exact old-block RPC retrieval and absent canonical receipts
are checked for all four displaced transactions before and after restart.
The old and competing histories receive complete ledger audits, followed by
`TestFullStateAbandonmentReorgColdAudit` on both stopped databases. The evidence
verifier compares all histories, native receipts, restored funds, saved bytes
and source hashes. This characterizes safe pausing and data retention; manual
recovery and actual production after this rollback are tested separately. See the
[abandonment rollback report](../../docs/restart-abandonment-reorg.md).

`TestFullStateAbandonmentRepair` opens fresh copies of that rollback result at
15,130,148. It verifies both cold inventories and retrieves the original
self-transfer 39 and purchases 40–42 through existing block-hash RPC before
starting normal miners and buyers. The same self-transfer must execute on both
nodes without a native ticket log, leaving saved 43 unchanged at current nonce
40. Existing manual-repair helpers then validate and replay purchases 40–42
sequentially, allow ordinary ticket-return waits and record any necessary
direct predecessor delivery. Saved 43 receives no manual submission. Acceptance
requires its native success, two fresh automatic successors, sequential
purchases and actual production by both owners. No new funding, re-signing,
head/state/record edit, forced sync or held signer is used. A separate
`TestFullStateAbandonmentRepairColdAudit` reconciles both complete ledgers.
Evidence verification also checks the unchanged 68-block prefix, the four
original transaction identities at new canonical locations, native purchase
receipts and stopped records. See the [rollback repair report](../../docs/restart-abandonment-repair.md).
