# Candidate historical replay

Updated 9 October 2026. **Completed through 3,600,000 with both cold checks.**
The [900,000-block in-place job](evidence/restart-ticket-encoder-job-3600000-2026-10-09/verification.json)
passes all seven commands, all nine additional preservation checks and automatic
evidence verification. Replay took 182.972 minutes; verified completion was
14:56:56 UTC. Full header, state/ticket/receipt commitments, bloom and TD match
the fresh pre-replay reference. Warm/cold ticket counts agree at 4,549, with ten
transactions and receipts. All 3,514 closed-target files stay unchanged during
inspection, and all 1,470 previously manifested files verify. Input/output/bundle
manifests were independently rechecked. The retained baseline at the same height
also has identical head hash, state root and ticket commitment. F12/G1 remain open.

The working database is /home/rehearsal/replay/candidate-ticket-encoding-working.
Closed allocation is 7,580,307,456 bytes (7.06 GiB). The separate verified
2,400,000 recovery checkpoint and earlier stopped 2,356,032 attempt/STOP remain
unchanged. Earlier job inventories retain their historical meaning; the working
database has advanced in place and is not a separate retained 2,700,000 copy.

The former D: capacity blocker is resolved. At Peter's request, the
[verified old-fixture archive](evidence/restart-old-tests-archive-w-v2-2026-10-09/README.md)
preserves 9,134 files / 11.532 GiB on W: and retires only the ten named September
D: fixture roots. D: free space increased by 11.517 GiB. Actual protected working/
recovery file hashes, backup/baseline metadata and retained executable/source
identities match sealed evidence. The container timestamp discrepancy remains
recorded; it was not used as a substitute for those actual-file checks.
[Fresh capacity preflight](evidence/restart-ticket-encoder-job-4500000-2026-10-09/preflight-ready-after-archive-2026-10-09.json)
passes at 25.805 GiB Linux / 65.787 GiB D:. No compaction or further cleanup is
needed for the next range. The first dispatch refused an observer input's CRLF
bytes before running any test command or replay. Its [sealed failure](evidence/restart-ticket-encoder-job-4500000-2026-10-09/STATUS.md)
remains preserved. The [fresh corrected job](evidence/restart-ticket-encoder-job-4500000-v2-2026-10-09/README.md)
uses exact prior LF bytes with one endpoint substitution. Its fresh preflight
passes at 16:14:05 UTC. The [corrected job](evidence/restart-ticket-encoder-job-4500000-v2-2026-10-09/STATUS.md)
was dispatched at 16:15:14 UTC; all starting checks passed and replay began
at 16:18:06 UTC (PID 653). The first size sample passes at 7.06 GiB; no stop or
failure is recorded. Completion remains pending.
No limit, runtime or release selection changes. Do not duplicate its writer or
hash the working database while it is live.

**Storage:** the [earlier W: archive](evidence/restart-checkpoint-archive-w-v2-2026-10-09/README.md)
holds eight old candidate checkpoints, 100,000 through 1,800,000. The 2,000,000,
2,200,000 and 2,400,000 checkpoints and stopped 2,356,032 attempt remain local.
Backup, baselines and sealed evidence remain preserved. The newer archive is
limited to the named old D: fixtures; it grants no general cleanup permission.

## Purpose and revised execution strategy — 9 October

The user questioned the cost and value of repeated small runs. The completed
evidence remains valid, but manually prepared 100,000-block stages are no
longer the default next action. No additional replay started during this review.

Three different questions must remain separate:

| Question | Existing evidence | What remains unproven |
| --- | --- | --- |
| Is the saved data internally consistent? | The [complete-data checks](restart-integrity-investigation.md) cover all 15,130,081 stored blocks including genesis, their parent/body/receipt/TD structure, and all reachable current account/storage/code state. | They do not re-execute every transaction or independently validate all historical ticket choices. |
| Can the proposed client reproduce historical transitions? | The encoder candidate executes from genesis through 3,600,000 and passes cold checks, including 920,000 blocks beyond the legacy boundary; the unchanged baseline separately reaches 3,600,000. | Candidate history after 3,600,000 remains open. |
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

At the earlier 2,400,000 review, there were 12,730,080 blocks to backup
head 15,130,080. At 100,000 per stage this would require 128 more stages.
The [measurement used in that review](evidence/restart-ticket-encoder-replay-2400000-v2-2026-10-09/verification.json)
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

The **2,700,000 to 3,600,000** continuation is complete and verified. It used
the identical retained replay executable, validated its starting inventory and
advanced in place without a new database copy. The separate 2,400,000 recovery
checkpoint remains intact. Both cold checks and all nine preservation checks pass.

The next justified interval is **3,600,000 to 4,500,000**. The [corrected inputs](evidence/restart-ticket-encoder-job-4500000-v2-2026-10-09/README.md)
preserve the original executable/controller and differ from the refused job only
in job identity and observer CRLF correction. The endpoint observer now differs
from the verified prior by exactly one literal substitution. Preserve the first
capacity refusal and the later before-execution byte-identity refusal. The
16:14:05 UTC corrected-job preflight passes; dispatch occurred at 16:15:14 UTC
under the existing autonomous-testing authorization. Keep six hours to request a clean stop, 6h15m Go timeout and 6h30m
external timeout plus 20-second kill grace. Plan an 11 GiB sampled target ceiling:
the completed 900,000-block job grew the target from 3.73 to 7.06 GiB, and the new
ceiling leaves about 3.94 GiB growth allowance. This is a finite stop threshold,
not a guarantee that another 900,000 blocks fit. Stop and inspect if growth or
execution reaches a limit. All original sealed jobs keep their original bounds.
Further history is justified because the ticket-encoder candidate still needs
verification beyond the retained baseline; extending that baseline again is
unnecessary without a specific diagnostic question.

Before any writer starts, require the preceding job's successful completion and
evidence verification, exact endpoint, complete cold file inventory and unchanged
identity/source/toolchain. Keep the separate verified recovery checkpoint at
/home/rehearsal/replay/candidate-ticket-encoding-2400000-v2. In-place continuation
intentionally changes the working database; it must not claim to preserve the
previous working checkpoint's bytes after execution.

Capacity is charged for **remaining growth**, because the existing 7.06 GiB
working database is already allocated. The resume preflight requires Linux
free space greater than 20 GiB reserve + remaining growth to the declared target ceiling + 1 GiB
preparation margin. D: must exceed both 60 GiB and its 50 GiB reserve + remaining
growth + 1 GiB margin. Copy mode retains its original 30/60 GiB minimums.
The unchanged Go executable still checks the 20/50 GiB reserves every batch.
A bounded allocation measurement and recorded required floors precede launch;
unmeasurable storage, insufficient capacity or unverified prior completion
refuses the job. Fourteen controller tests cover these gates and existing stops.

After replay, both cold checks and evidence verification run automatically;
complete manifests seal the outputs. A stopped/failed job needs diagnosis and
separate cold inspection before any resume. There is no blind retry.
All node runtime code, replay identity, production selection and sealed evidence
remain unchanged.

The user authorized continued useful tests without more continue prompts on
9 October. An hourly chat follow-up named Continue Fusion restart testing
inspects completion/resources, records verified results and advances the next
justified finite test. Avoid duplicate writers and unchanged passing reruns.
Stop dependent work and ask if a substantive decision, unresolved blocker or
doubt about a test's value needs the user. Production activation, real keys and
public mining remain outside this testing authorization.

The completed job's runtime status is
/home/rehearsal/results/restart-ticket-encoder-job-3600000-2026-10-09/status.json.
Host dispatch logs are under repo tmp/replay-job-3600000-2026-10-09.
The hourly continuation id is continue-fusion-restart-testing.
The hidden Windows dispatcher keeps WSL attached after the launching shell
returns. Keep Windows awake and the app running for scheduled follow-up.
While replay runs, useful independent work is the documented restored-startup/
identity-refusal and recovery/handover acceptance gaps. Do not compete with the
replay for large disk workloads. Further candidate history and independent
consensus review remain open; no snapshot-trust acceptance is inferred.

The independent [reader boundary check](evidence/restart-restored-reader-boundaries-2026-10-09/README.md)
passes ten in-memory cases against retained encoder-candidate recovery source.
It establishes which identity/readiness checks cannot be delegated to the
existing reader alone. The [subsequent unselected startup candidate](evidence/restart-restored-startup-positive-2026-10-09/README.md)
passes fifteen actual CLI refusals and four synthetic archive-mode startup/import/
restart phases. The initial positive fixture's pruning-shutdown failure is retained;
complete-history/pruning acceptance remains open. No historical database was
opened and no runtime/source selection changed. Continue only the listed uncovered
startup cases; the additional lock/permission/corruption slice now [passes four cases](evidence/restart-restored-startup-open-refusal-2026-10-09/README.md).

Retained executable SHA256:
b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245.
The separate endpoint observer is not substituted for that executable.

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
