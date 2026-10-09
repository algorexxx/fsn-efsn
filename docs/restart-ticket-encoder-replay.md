# Candidate historical replay

Updated 9 October 2026. **Completed through 2,400,000 with both cold checks.**
The [43,968-block continuation](evidence/restart-ticket-encoder-replay-2400000-v2-2026-10-09/README.md)
resumed a verified copy of the stopped 2,356,032 checkpoint with the unchanged
executable. All seven commands and evidence verification pass. Full endpoint
header, state/ticket/receipt commitments, bloom and TD match the backup reference
captured before this continuation. The cold ticket count agrees with replay at
6,425; all 1,383 closed-target file hashes remain unchanged during inspection.

The earlier [200,000-block attempt](evidence/restart-ticket-encoder-replay-2400000-2026-10-09/README.md)
remains recorded as incomplete at its 30-minute limit. Its [cold inspection](evidence/restart-ticket-encoder-stopped-2356032-2026-10-09/README.md),
stopped checkpoint and original STOP are preserved. The new result completes the
remaining work without rewriting that outcome or extending its limits.
Legacy checkpoint shortcuts remain active through 2,680,000. F12 is still open.

The original first-range scope below is retained for reference and preserved
verbatim in the [first run's plan at start](evidence/restart-ticket-encoder-replay-100000-2026-10-08/plan-at-start.md).
No replay beyond 2,400,000 has started.

**Storage:** the [verified W: archival](evidence/restart-checkpoint-archive-w-v2-2026-10-09/README.md)
relocated eight older candidate checkpoints, 100,000 through 1,800,000, preserving
all 4,051 files against their sealed hashes. The 2,000,000 and 2,200,000
checkpoints, stopped 2,356,032 target and new 2,400,000 target remain on Linux
ext4. Backup, baselines, binaries, source and sealed evidence retain their
locations. Older reports' paths are historical; the relocation manifest
identifies their W: copies. Active replay remains on local Linux ext4.

Final free capacity is **33.10 GiB Linux / 66.97 GiB D:**, above the unchanged
30/60 GiB starting floors. Recheck before any new copy. No further archival or
capacity extension is automatic.

## Purpose and revised execution strategy — 9 October

The user questioned the cost and value of repeated small runs. The completed
evidence remains valid, but manually prepared 100,000-block stages are no
longer the default next action. No additional replay started during this review.

Three different questions must remain separate:

| Question | Existing evidence | What remains unproven |
| --- | --- | --- |
| Is the saved data internally consistent? | The [complete-data checks](restart-integrity-investigation.md) cover all 15,130,081 stored blocks including genesis, their parent/body/receipt/TD structure, and all reachable current account/storage/code state. | They do not re-execute every transaction or independently validate all historical ticket choices. |
| Can the proposed client reproduce historical transitions? | The encoder candidate executes from genesis through 2,400,000 and passes cold checks; the unchanged baseline separately reaches 3,600,000. | Later candidate history, including ordinary seal validation beyond 2,680,000, remains open. |
| Can the reviewed software safely restart from the accepted snapshot? | Complete-state recovery and operational fixtures exist; the encoder has vector, synthetic and integration evidence. | Final selected-candidate restored startup, identity refusal, recovery/handover and acceptance are still required. Full history replay alone cannot close these. |

The replay has a concrete purpose. The modern compiler's default gzip changed
consensus ticket bytes; the candidate preserves the legacy writer. Re-execution
tests how that implementation behaves on real evolving state, rather than only
the seven available saved ticket vectors. In [the importer](../core/blockchain.go),
each block reads its parent's state, executes its transactions, then calls
[ValidateState](../core/block_validator.go), which compares gas, bloom, receipts
and the resulting state root against the historical header. This is much more
than reading another block number.

Replaying all intermediate blocks is needed for an end-to-end reconstruction
from genesis unless we deliberately trust an intermediate state checkpoint.
A saved complete state allows forward operation without first reconstructing
its entire past. Using it as the acceptance basis is a different trust decision,
not equivalent historical evidence. Sparse old state in this backup also means
we cannot assume arbitrary historical intervals can be jumped into. Keep G1 open:
a snapshot-based alternative needs an explicit documented acceptance decision.
No existing history requirement is silently waived by this review.

Full replay is still this client's validation, not an independent implementation
or proof of globally agreed canonical history. The existing shortcuts through
2,680,000 remain relevant even after reaching the tip. Do not count the baseline's
progress as candidate execution or join their databases by altering identity files.

### Cost and avoidable overhead

There are 12,730,080 blocks between the verified candidate height and backup
head 15,130,080. At 100,000 per stage this would require 128 more stages.
The [latest measurement](evidence/restart-ticket-encoder-replay-2400000-v2-2026-10-09/verification.json)
is 43,968 blocks in 663.394139 seconds by command timestamps. Applying that
rate mechanically gives about 53.35 hours of machine execution for the remaining
blocks. This is an illustration, **not an ETA or a lower/upper bound**:
later transaction load, state size, compaction and storage can differ greatly.
The complete stored history contains 419,409,946 transactions. No extrapolated
full-replay storage requirement is established.

The 30-minute/4 GiB limits are hardcoded in the [initial pilot wrapper](evidence/restart-ticket-encoder-replay-100000-2026-10-08/run.py),
not chain rules. The [replay test](../tests/restart/replay_linux_test.go) uses
128-block internal batches and checks disk reserves before each batch; these
internal batches do not require a separate chat turn, directory or commit.
The previous [baseline range](evidence/restart-replay-3600000-2026-10-04/README.md)
already used a declared 12-hour/20 GiB envelope. That does not automatically
authorize those bounds for the candidate, but demonstrates the old pilot limit
is not a protocol constraint.

Repeated copies, observer builds, manifest checks and progress polling add
operator/assistant overhead. More importantly, retaining a new complete database
for every short interval produces unnecessary storage pressure. Those costs
are distinct from the transaction execution that supplies the actual evidence.

### Next engineering work

1. Prepare a reusable, resumable runner for one finite candidate replay job,
   rather than another one-off 100,000-block bundle. Keep the current source,
   executable and accepted-history identities fixed; record new wrapper inputs
   separately without editing sealed evidence.
2. Make **2,700,000** the next proposed validation milestone: it crosses the
   existing 2,680,000 validation boundary and exercises 20,000 blocks beyond it.
   This is not a declaration that 20,000 later blocks suffice for full acceptance.
   Capture expected references before execution and require cold verification
   at the declared milestone.
3. Declare a realistic finite time/storage envelope after fresh capacity checks.
   The current pilot wrapper will stop after 30 minutes and its Go test after
   55 minutes; all layered timeouts must be reconciled before a longer job.
   Preserve disk reserves, process/identity locks, offline isolation, automatic
   stop on mismatch/low space/monitor failure and stopped-checkpoint inspection.
   A known partial stop must not become an automatic blind retry.
4. Use one working database and a verified recovery checkpoint, with a documented
   checkpoint/retention policy. Preserve the original backup and existing sealed
   failures. Do not delete old copies during this review or hash a live LevelDB
   as though it were a stopped checkpoint. W: can hold verified cold archives;
   active replay should remain on Linux ext4.
5. Let the finite job run without a model turn for each internal batch. Record
   logs, resource samples, exact start/end and failure status automatically;
   review at meaningful checkpoints or actionable changes. No recurring task,
   detached job or larger replay has been created by this document.
6. Prefer one reviewed candidate execution-history pass as the main evidence,
   retaining the baseline as a diagnostic comparator. Do not commission two
   complete passes by default. Any source/toolchain change requires a scoped
   compatibility assessment; do not claim current replay qualifies an altered
   final executable or loosen the existing identity checks to reuse its target.
   Review the evidence/disposition under G1 before closing that gate.
7. Continue the finite restored-startup/identity-refusal and recovery/handover
   acceptance work under F12/G3. These address the intended snapshot launch
   directly and need not wait for every historical block to finish.

No new runtime or runner limit is active yet. The existing pilot's limits remain
unchanged until a new concrete specification and checked runner replace it.
The previous next-step instruction to create a 2,500,000 range is superseded by
this runner/capacity preparation. This review does not approve activation,
resolve F11/F12 or assert that full historical execution is complete.

Retain /home/rehearsal/replay/candidate-ticket-encoding-2400000-v2 at verified
height 2,400,000 (2,894.80 MiB) and its exact replay executable:
b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245.
The older directory ending in 2400000 still has head 2,356,032. The current
separate observer is fixed at 2,400,000; the executable's original details tests
remain fixed at 100,000. Prepare new endpoint observation without rebuilding or
substituting the replay executable.

## Original first-range inputs and boundary

- Frozen D1 **node** selection plus exactly the unselected
  [encoder candidate](evidence/restart-ticket-encoder-candidate-v2-2026-10-08/candidate.patch),
  compiled with the recorded Go 1.27.1 toolchain. Exclude F11, the dependency
  experiment, recovery signer and observer. Check complete source inventories.
- Fresh target `/home/rehearsal/replay/candidate-ticket-encoding-100000`;
  fresh evidence/result directory `restart-ticket-encoder-replay-100000-2026-10-08`
  (use a new dated name if the run happens later). Refuse existing targets.
- Start at the generated historical genesis and stop at **100,000**. Do not
  copy/resume `/home/rehearsal/replay/baseline-mainnet-3600000` or change its
  identity manifest. That baseline and its preserved checkpoint remain intact.
- Preserved source `/home/rehearsal/data/efsn/chaindata`, with its existing
  verification marker and head 15,130,080. Require genesis
  `0xc2422b1d9d16331be2a5b207c0783027d4419498003f729f4b9e9c5c1838623a`
  and head `0xe93ffded087a79097d4309c7831690161db6ed136f4b1a22c4c83a99db80f99f`.
  Capture the source header and commitments at 100,000 before replay.

Use the existing `TestPreservedHistoryReplay`, `prepareReplayDirectory` and
`TestPreservedReplayHeadReadOnly` helpers from the pinned investigation source.
Record the precise test/helper dependency closure, binary hashes, toolchain,
commands and environment. These files are test inputs, not production patches.
Keep the existing executable/source/config identity checks: continuing with a
different binary requires a new qualification target. A changed console label
such as the helper's existing “baseline replay” message is not source identity;
the evidence must explicitly name this as the candidate run.

## Resource and preservation controls

Before launch, confirm no conflicting writer and obtain the target lock.
Require at least 30 GiB free in Linux and 60 GiB on D:. Record current space;
this plan's limits are not a reservation or a measured size estimate.

Run without public peers inside private mount and network namespaces, with
loopback down, a read-only bind mount of the source and read-only LevelDB open.
The root launcher establishes isolation; rehearsal performs the replay.
Record source metadata inventory before and after. Reuse the existing verified
backup rather than creating another bulk copy or hashing 117 GB again.

Use GOMAXPROCS=2 and the existing replay cache limits. Preserve the helper's
per-batch 20 GiB Linux / 50 GiB D: free-space stops. Add a sampled **4 GiB target
allocation stop** and a **30-minute clean-stop request** for this initial range.
The size monitor must retain the corrected bounded retries for disappearing
LevelDB files from the 3,600,000 resume runner. On persistent measurement failure,
request a clean stop; do not silently ignore it. Sampled limits can overshoot
between measurements and are not hard filesystem quotas.

Retain a one-hour outer timeout as a last resort. A timeout, nonzero exit or
short endpoint is incomplete evidence, even if a later cold check succeeds.
Do not automatically extend the range, resume a failed run, delete evidence,
or consume W: capacity. Recheck paths/capacity before any subsequent range.

## Required observations

1. Generated genesis matches the preserved canonical genesis before importing
   block 1. Import sequential canonical batches through exactly 100,000,
   recording progress and every command's exit status.
2. Stop cleanly. In a **fresh process** with the target mounted read-only,
   verify canonical/header/full/fast heads, body transaction root, receipt
   count/root/bloom and cumulative difficulty against preserved history.
3. Open the resulting state root with an empty process-local ticket cache;
   decode tickets and recompute their commitment using the candidate. Require
   the preserved header's state root and MixDigest, and no database error.
   Record ticket count as an observation rather than an invented expected count.
4. Prove the source inventory is unchanged and the cold inspection did not
   modify target files. Retain logs, identities, binary/source hashes, storage
   measurements, failures and SHA256SUMS in a new evidence bundle.

The whole first range lies within legacy checkpoint shortcuts through
2,680,000. Transaction execution and state/receipt-root comparison still run;
ticket-seal and raw-transaction checks retain the documented shortcuts. Report
this limitation explicitly. Passing 100,000 is an early candidate compatibility
result, not all-history validation, independent consensus review, or closure of
the 17 missing sampled blobs. Stop at any mismatch and investigate its cause.
