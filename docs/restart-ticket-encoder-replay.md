# Candidate historical replay

Updated 10 October 2026. **Cold-verified through 5,976,864; fresh continuation prepared.**
The [native-reserve stopped-state inspection](evidence/restart-ticket-encoder-stopped-reserve-2026-10-10/RESULTS.md)
completed at 18:35:25 UTC and independently verifies. Its discovery command
records the specific expected exact-height refusal; the following five commands
pass, including both exact-height cold checks. Header/RLP, state/tickets,
receipts, bloom and TD match the backup, with 2,564 tickets and 70 transactions/
receipts. All twelve preservation checks pass: 10,895 working and 1,383 recovery
hashes stay unchanged, and 1,780 prior evidence files verify. This adds 376,832
blocks and brings post-legacy coverage to 3,296,864. The requested 6,300,000-v2
attempt remains failed/incomplete; no new STOP file is created or required.

The [14-folder archival/retirement](restart-storage-capacity-review.md) passed.
All 9,191 files remain verified on W:; D: gained 12.715 GiB and has 62.100 GiB free
at inspection completion. Four targeted [controller provenance checks](evidence/restart-reserve-stop-controller-2026-10-10/RESULTS.md)
pass for existing STOP-based and new native-reserve records. The [6,300,000-v3 job](evidence/restart-ticket-encoder-job-6300000-v3-2026-10-10/README.md)
is prepared from 5,976,864 for 323,136 additional blocks. Its fresh 28 GiB ceiling
allows about 6.731 GiB growth; timeouts and 20/50 GiB per-batch reserves stay
unchanged. Fresh launch capacity must pass. No writer has resumed yet.

Earlier checkpoints and failed attempts remain preserved:
The [6,300,000 attempt](evidence/restart-ticket-encoder-job-6300000-2026-10-10/RESULTS.md)
was dispatched at 12:50:50 UTC and stopped at 14:32 UTC at its declared sampled
15 GiB allocation ceiling. Its original failure record and STOP remain intact.
The [separate cold inspection](evidence/restart-ticket-encoder-stopped-5600032-2026-10-10/RESULTS.md)
verifies the saved 5,600,032 endpoint: complete header, state/ticket/receipt
commitments, bloom and TD match the backup. It reconstructs 2,370 tickets with
one transaction/receipt. All five commands, twelve preservation checks and the
evidence verifier pass; 7,625 working-file hashes remain unchanged and 1,698 prior
evidence files verify. The additional coverage is 268,672 blocks, giving 2,920,032
post-legacy blocks in total. No final warm ticket count is available. The requested
6,300,000 range remains incomplete; F12/G1 remain open.

Peter approved the [200 to 220 GiB WSL expansion](restart-storage-capacity-review.md).
It completed with all 7,625 working and 1,383 recovery hashes, protected metadata,
source/executable/toolchain/STOP and replay identities unchanged. The fresh
[6,300,000-v2 continuation](evidence/restart-ticket-encoder-job-6300000-v2-2026-10-10/README.md)
is prepared with passing capacity/provenance preflight at 15:10:44 UTC. Linux/D:
free space is about 40.86/63.64 GiB. Its new 26 GiB sampled ceiling allows about
10.972 GiB growth; the old job's 15 GiB limit is immutable. Timeouts and per-batch
20/50 GiB reserves remain unchanged. The hidden dispatcher launched at
15:14:00 UTC from commit `40551639`. Replay began at 15:17:23 UTC after four
passing startup commands, 7,625 working/1,383 recovery hashes, 1,738 prior evidence
files and unchanged identity/source/executable/toolchain. Its [initial observation](evidence/restart-ticket-encoder-job-6300000-v2-2026-10-10/STATUS.md)
was healthy, with progress beyond 5,602,000 and a passing allocation sample.
That historical observation is superseded by the reserve-stop result above.

The preceding stopped checkpoint remains historical evidence:
The [5,400,000 attempt](evidence/restart-ticket-encoder-job-5400000-2026-10-09/RESULTS.md)
stopped at its declared sampled 11 GiB allocation ceiling. Its requested range
remains incomplete. The [separate read-only inspection](evidence/restart-ticket-encoder-stopped-5331360-2026-10-10/RESULTS.md)
passes at 5,331,360, with complete header, state/ticket/receipt commitments, bloom
and TD matching the backup. It reconstructs 3,728 tickets with four transactions/
receipts. All twelve preservation checks and the evidence verifier pass; all
5,591 target hashes stay unchanged and 1,616 prior evidence files verify.
That inspection established 2,651,360 post-legacy blocks. There is no final warm ticket
count from the stopped attempt. F12/G1 remain open.

**Last fully completed requested range: 4,500,000.**
The [latest 900,000-block job](evidence/restart-ticket-encoder-job-4500000-v2-2026-10-09/RESULTS.md)
passes all seven commands, all nine additional preservation checks and automatic
verification. Replay took 181.781 minutes; verified completion was 19:20:56 UTC.
Full header, state/ticket/receipt commitments, bloom and TD match the fresh backup
reference. Warm/cold ticket counts agree at 6,995, with one transaction/receipt.
All 4,182 closed-target files stayed unchanged during inspection, and all 1,519
previously manifested files verify. Input/output/bundle manifests were independently
rechecked. Candidate history includes 1,820,000 blocks beyond the legacy boundary;
F12/G1 remain open. The unchanged baseline remains at 3,600,000.

The working database is /home/rehearsal/replay/candidate-ticket-encoding-working.
Its latest verified closed allocation is 22,837,567,488 bytes (21.269 GiB) at
5,976,864. Inspection finished with 37,095,866,368 bytes free in Linux and
66,679,324,672 bytes on D:. The separate verified 2,400,000 recovery checkpoint
and earlier stopped 2,356,032 attempt/STOP remain unchanged. Prior working
inventories are historical records, not separate retained copies. Another
in-place continuation intentionally changes these current working bytes.

The earlier D: capacity blocker was resolved. At Peter's request, the
[verified old-fixture archive](evidence/restart-old-tests-archive-w-v2-2026-10-09/README.md)
preserves 9,134 files / 11.532 GiB on W: and retires only the ten named September
D: fixture roots. D: free space increased by 11.517 GiB. Actual protected working/
recovery file hashes, backup/baseline metadata and retained executable/source
identities match sealed evidence. The container timestamp discrepancy remains
recorded; it was not used as a substitute for those actual-file checks.
[Fresh capacity preflight](evidence/restart-ticket-encoder-job-4500000-2026-10-09/preflight-ready-after-archive-2026-10-09.json)
passes at 25.805 GiB Linux / 65.787 GiB D:. No compaction or further cleanup is
needed for that range. The first dispatch refused an observer input's CRLF
bytes before running any test command or replay. Its [sealed failure](evidence/restart-ticket-encoder-job-4500000-2026-10-09/STATUS.md)
remains preserved. The [fresh corrected job](evidence/restart-ticket-encoder-job-4500000-v2-2026-10-09/README.md)
uses exact prior LF bytes with one endpoint substitution. Its fresh preflight
passes at 16:14:05 UTC. The [corrected job](evidence/restart-ticket-encoder-job-4500000-v2-2026-10-09/STATUS.md)
was dispatched at 16:15:14 UTC and completed verification at 19:20:56 UTC.
Its immutable preparation/status files retain their original pending wording;
the completion, verification and linked result supersede that status.
No limit, runtime or release selection changed. The subsequent [5,400,000 job](evidence/restart-ticket-encoder-job-5400000-2026-10-09/RESULTS.md)
was dispatched at 19:32:26 UTC following the passing complete-backup preflight.
All startup checks passed; replay began at 19:34:33 UTC with a passing first
allocation sample. It stopped for size at 23:05 UTC. The read-only follow-up
completed evidence verification at 23:27:58 UTC. That attempt remains stopped.
Peter has authorized removing obsolete copies. The [storage operation](restart-storage-next-step.md)
has verified and retired the four Windows fixtures, reclaiming 4.391 GiB and
leaving 63.689 GiB free on D:. The [two older Linux checkpoint archives](evidence/restart-checkpoint-archive-w-2026-10-10/ARCHIVE-RESULTS.md)
completed and passed independent record/provenance verification at 2,161 files /
4,874,392,642 logical bytes. Their [authorized retirement](evidence/restart-checkpoint-archive-w-2026-10-10/RESULTS.md)
completed at 11:52:51 UTC after rechecking both complete copies, reclaiming
4.544 GiB inside Linux. Actual filesystem and independent evidence checks pass.
The prepared 6,300,000 job's [fresh capacity preflight](evidence/restart-ticket-encoder-job-6300000-2026-10-10/preflight-ready-2026-10-10.json)
passed at 12:49:43 UTC: about 26.26 GiB Linux / 63.68 GiB D: free, no active node
or replay process, and the correct verified stopped-state provenance. That is
the starting observation, superseded by the latest stopped-state capacity above.
Do not change either failed job or retry it.

**Storage:** the [earlier W: archive](evidence/restart-checkpoint-archive-w-v2-2026-10-09/README.md)
holds eight old candidate checkpoints, 100,000 through 1,800,000. The new verified
archive additionally holds 2,000,000 and 2,200,000; their local copies are retired.
The 2,400,000-v2 recovery and stopped 2,356,032 attempt remain local. Backup,
baselines and sealed evidence remain preserved. The six-source cleanup is
complete; no additional removal or compaction is part of this continuation.

## Purpose and revised execution strategy — 9 October

The user questioned the cost and value of repeated small runs. The completed
evidence remains valid, but manually prepared 100,000-block stages are no
longer the default next action. No additional replay started during this review.

Three different questions must remain separate:

| Question | Existing evidence | What remains unproven |
| --- | --- | --- |
| Is the saved data internally consistent? | The [complete-data checks](restart-integrity-investigation.md) cover all 15,130,081 stored blocks including genesis, their parent/body/receipt/TD structure, and all reachable current account/storage/code state. | They do not re-execute every transaction or independently validate all historical ticket choices. |
| Can the proposed client reproduce historical transitions? | The encoder candidate executes from genesis through the cold-verified stopped checkpoint at 5,976,864, including 3,296,864 blocks beyond the legacy boundary; the unchanged baseline separately reaches 3,600,000. | Candidate history after 5,976,864 remains open; the requested 5,400,000 and 6,300,000 ranges remain incomplete. |
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

The **3,600,000 to 4,500,000** continuation is complete and verified. Both cold
checks and all nine preservation checks pass. The subsequent
[complete-backup read-only startup check](evidence/restart-restored-backup-preflight-v2-2026-10-09/RESULTS.md)
also passes at 15,130,080 with unchanged backup metadata and candidate source.
No extra backup copy or writable startup was needed.

The attempted **4,500,000 to 5,400,000** continuation used the same retained
executable/controller, separate 2,400,000 recovery checkpoint, six-hour clean
stop, 6h15m Go timeout, 6h30m external timeout plus 20-second grace, and an
11 GiB sampled target ceiling. Fresh capacity passed at 19:31:25 UTC with
24.51 GiB Linux / 63.68 GiB D: free. The size monitor later requested a stop;
normal cleanup persisted exactly **5,331,360**, independently verified by both
cold checks. The failed requested range and original STOP remain intact.

Peter's explicit message now authorizes the [six-source archival/removal](restart-storage-next-step.md).
The four Windows copies completed at 09:52:08 UTC and separate full re-verification/
retirement completed at 10:37:32 UTC, freeing 4.391 GiB. The two Linux checkpoint
copies completed at 10:52:40 UTC with full cold byte verification and unchanged
protected metadata. Their separately authorized retirement completed at 11:52:51 UTC
and independently verifies, with 4.544 GiB reclaimed inside Linux. Keep all other
data and evidence. Do not run a competing bulk workload,
compact the VHD or repeat unchanged passing tests.

After capacity is available, declare a fresh bounded job from the verified
stopped checkpoint, explicitly validating its inspection rather than requiring
or fabricating a success result for the failed job. Check exact endpoint,
inventory, identity, source and toolchain; retain the separate recovery checkpoint.
Select finite endpoint/growth/time limits from fresh capacity and evidence value.
Further candidate history is useful; another unchanged baseline pass is not
justified without a diagnostic question. A [fresh continuation](evidence/restart-ticket-encoder-job-6300000-2026-10-10/README.md)
was prepared for 5,331,360 to 6,300,000 (968,640 new blocks), with a new 15 GiB
sampled ceiling, 30-second samples and unchanged six-hour/6h15/6h30 time limits.
The [controller provenance/refusal checks](evidence/restart-stopped-resume-controller-2026-10-10/RESULTS.md)
pass. Storage completion and fresh capacity pass. The finite continuation was
dispatched at 12:50:50 UTC and began replay at 12:53:26 UTC after exact closed
inventory/identity checks. It subsequently stopped at its size ceiling; the
[independent cold inspection](evidence/restart-ticket-encoder-stopped-5600032-2026-10-10/RESULTS.md)
verifies 5,600,032. The original failed-attempt records and limits remain immutable.

The latest 268,672 blocks added 4.012 GiB of allocation. With only 22.177 GiB
available inside the then-200 GiB virtual disk, another tiny range was not justified.
Peter approved the [expansion to 220 GiB](restart-storage-capacity-review.md), now
complete with passing preservation checks. The fresh 6,300,000-v2 job names the
5,600,032 inspection as its stopped checkpoint and the failed 6,300,000 job as
its attempt. Launch capacity passed for the declared 26 GiB ceiling and unchanged
timeouts/reserves. The job later stopped at the host-space reserve, below its
sampled allocation ceiling. The authorized archival/retirement and native-reserve cold inspection now pass.
The fresh v3 continuation uses that distinct verified failure provenance; it
does not reinterpret the old STOP-based failure. No full-history size forecast or acceptance waiver follows.

Before any writer starts, require successful completion/evidence verification
of its accepted checkpoint, or an explicitly qualified stopped-checkpoint
inspection with the failed attempt preserved. Require exact endpoint, complete cold file inventory and unchanged
identity/source/toolchain. Keep the separate verified recovery checkpoint at
/home/rehearsal/replay/candidate-ticket-encoding-2400000-v2. In-place continuation
intentionally changes the working database; it must not claim to preserve the
previous working checkpoint's bytes after execution.

Capacity is charged for **remaining growth**, because the existing working
database is already allocated. The resume preflight requires Linux
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

The stopped job's retained runtime status is
/home/rehearsal/results/restart-ticket-encoder-job-6300000-v2-2026-10-10/status.json.
Host dispatch logs are under repo tmp/replay-job-6300000-v2-2026-10-10. Inspect its
completion and resource records before any dependent work. It has no passing
job verification; the separate failure-evidence integrity check does not extend
historical coverage. No duplicate writer, live LevelDB hashing or competing
bulk workload. The preceding
6,300,000 job without v2 retains exit 1 and verified_pass false; no passing job
verification.json exists for it. The separate stopped-checkpoint inspection
establishes 5,600,032. The earlier 5,400,000 failure is also preserved.
The hourly continuation id is continue-fusion-restart-testing.
The failed replay dispatcher has exited. Archival/retirement has also completed.
The cold-inspection dispatcher finished successfully; its host records are
retained under repo tmp/reserve-inspection-2026-10-10 and in its sealed bundle.
The next prepared job is restart-ticket-encoder-job-6300000-v3-2026-10-10; check
fresh capacity before launch and its completion/resources before further work. Useful independent work is limited to documented
acceptance gaps that do not repeat passing checks or compete for large disk
workloads. Further candidate history and independent
consensus review remain open; no snapshot-trust acceptance is inferred.

The independent [reader boundary check](evidence/restart-restored-reader-boundaries-2026-10-09/README.md)
passes ten in-memory cases against retained encoder-candidate recovery source.
It establishes which identity/readiness checks cannot be delegated to the
existing reader alone. The [subsequent unselected startup candidate](evidence/restart-restored-startup-positive-2026-10-09/README.md)
passes fifteen actual CLI refusals and four synthetic archive-mode startup/import/
restart phases. The initial positive fixture's pruning-shutdown failure is retained.
The [complete small synthetic ancestry follow-up](evidence/restart-restored-startup-pruning-v2-2026-10-09/RESULTS.md)
now passes three actual CLI phases under normal pruning: restored startup, local
child import and fresh restart, each with clean shutdown. Independent cold reads
confirm the three shutdown state roots and ticket commitments; database files
remain unchanged during inspection. This is lifecycle evidence, not candidate
historical coverage or complete-backup acceptance. No historical database was
opened and no runtime/source selection changed. The additional lock/permission/
corruption slice already [passes four cases](evidence/restart-restored-startup-open-refusal-2026-10-09/README.md).
Do not repeat these unchanged small tests. The [complete-backup read-only check](evidence/restart-restored-backup-preflight-v2-2026-10-09/RESULTS.md)
now passes using a read-only mount and database locks. The preserved first refusal
came from test-profile wiring; mainnet intentionally trusts the global profile.
No runtime fix or production anchor change was made. Full writable restored
startup/recovery and
final profile/anchor/independent review remain open.

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
