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

**Next bounded range: 2,400,001 through 2,500,000 (100,000 blocks).** Reduce the
previous 200,000-block range after its measured time stop. The latest 43,968
blocks took about 11 minutes (663.39 seconds by command timestamps; 658.05
seconds reported by Go). Retain both timing measurements without assuming a
cause for their difference. Future workload can differ; keep the 30-minute
monotonic allowance, 4 GiB sampled target stop and 20/50 GiB continuation
reserves. No silent extension is permitted.

Preserve /home/rehearsal/replay/candidate-ticket-encoding-2400000-v2, whose
verified head is 2,400,000 and closed allocation is 2,894.80 MiB. Use a verified
copy in a new candidate-ticket-encoding-2500000 target and fresh result directory,
after declaring the next specification. The older directory ending in 2400000
still has head 2,356,032; do not confuse it with the new checkpoint.

Reuse the exact retained replay executable and unchanged executable/source/config
identity validation. Its SHA256 remains
b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245.
The replay/cold-head helpers take height from the environment; built-in details
tests remain fixed at 100,000, while the latest separate observer is fixed at
2,400,000. Build the next endpoint observer separately and capture its backup
reference before replay, then perform both exact-height cold checks. Do not
rebuild the replay executable or weaken identity checks for an observer change.

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
