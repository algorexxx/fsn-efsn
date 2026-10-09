# Candidate historical replay

Updated 9 October 2026. **Cold-verified through 2,356,032; the requested
2,400,000 range is incomplete.** The [attempt](evidence/restart-ticket-encoder-replay-2400000-2026-10-09/README.md)
reached its unchanged 30-minute allowance and stopped before block 2,356,033.
A separate [read-only inspection](evidence/restart-ticket-encoder-stopped-2356032-2026-10-09/README.md)
confirmed the persisted endpoint against preserved history, including state,
ticket and receipt commitments and TD. All 1,299 target files retained their
hashes. This does not turn the incomplete range into a pass or select a release.
The completed ranges through 2,200,000 remain sealed. These heights retain
legacy checkpoint shortcuts through 2,680,000.

The original first-range scope below is retained for reference and preserved
verbatim in the [first run's plan at start](evidence/restart-ticket-encoder-replay-100000-2026-10-08/plan-at-start.md).
No replay continuation after the time stop has started.

**Storage:** the [verified W: archival](evidence/restart-checkpoint-archive-w-v2-2026-10-09/README.md)
relocated eight older candidate checkpoints, 100,000 through 1,800,000, preserving
all 4,051 files against their sealed hashes. The 2,000,000 and 2,200,000
checkpoints remain on Linux ext4, as does the new stopped target. Backup,
baselines, binaries, source and sealed evidence retain their locations.
Earlier reports' old paths are historical; the archive manifest identifies
their W: copies. Active replay remains on local Linux ext4.

Final inspection free capacity is **35.98 GiB Linux / 66.97 GiB D:**, above the
unchanged 30/60 GiB starting floors. Recheck before any new copy. No further
archival or capacity extension is automatic.

**Next bounded range: 2,356,033 through 2,400,000 (43,968 blocks).** The previous
200,000-block request exceeded its time allowance. Reduce the remaining work;
keep the 30-minute monotonic allowance, 4 GiB sampled target stop and 20/50 GiB
continuation reserves. No next run is authorized to silently extend those bounds.

Preserve the verified stopped directory
/home/rehearsal/replay/candidate-ticket-encoding-2400000. Its actual head is
2,356,032, despite its name; closed allocation is 2,770.10 MiB. Use a verified
copy in a distinct target, candidate-ticket-encoding-2400000-v2, with a fresh
specification and result directory. Preserve the original 2,200,000 checkpoint,
incomplete attempt and its STOP; use a new absent stop-file path for continuation.

Reuse the exact retained replay executable and unchanged executable/source/config
identity validation. Its SHA256 remains
b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245.
The replay/cold-head helpers take the height from the environment; built-in
details tests remain fixed at 100,000. The latest separate observer is fixed
at 2,356,032; the preceding attempt's observer is fixed at 2,400,000. Verify any
observer used for the next endpoint and capture a fresh backup reference before
replay, then perform both exact-height cold checks. Do not rebuild the replay
executable or weaken identity checks to accommodate an observer change.

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
