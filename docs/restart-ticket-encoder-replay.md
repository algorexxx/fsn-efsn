# Candidate historical replay

Updated 9 October 2026. **Completed through 2,200,000 with both cold checks.**
The [latest evidence](evidence/restart-ticket-encoder-replay-2200000-2026-10-09/README.md)
records exact historical agreement and preservation checks. This follows the
[affected regressions](evidence/restart-ticket-encoder-regressions-2026-10-08/spec.md).
It does not select the encoder for release or change the accepted history.
The original first-range scope below is retained for reference and preserved
verbatim in the [first run's plan at start](evidence/restart-ticket-encoder-replay-100000-2026-10-08/plan-at-start.md).
No continuation beyond 2,200,000 has started.

**Next step: resolve storage before another range.** Final free capacity was
29.89 GiB Linux / 66.82 GiB D:. Linux is 0.11 GiB below the unchanged 30 GiB
starting requirement, while the completed run remained above its 20 GiB
continuation reserve. Preserve checkpoints and evidence; assess additional
Linux capacity or verified archival to the already-authorized W: storage.
Verify paths, available capacity and the transfer/preservation procedure before
any migration. No migration has occurred; do not lower the reserve or delete
preserved evidence to permit another run.

Once capacity is resolved, the next bounded range is 2,200,001 through 2,400,000.
The latest command's UTC timestamps span about 27 minutes; its Go test
separately reports 24 minutes 48 seconds. Both measurements are retained in the
evidence; their difference has not been attributed to a specific cause.
Keep the 200,000-block range and unchanged 30-minute monotonic allowance;
runtime still depends on the historical workload. Preserve the verified
2,200,000 checkpoint and use a verified copy in a new target named
candidate-ticket-encoding-2400000.

The current checkpoint occupies 2,475.89 MiB; measure actual space before
copying. Continue with the exact retained replay executable and identity checks,
with a fresh result directory, the same space/time stops and exact-height cold
verification. Its replay/cold-head helpers take the endpoint from the environment;
its built-in details tests remain fixed at 100,000, and the latest separate
observer is fixed at 2,200,000. Neither is a detailed check of the next endpoint.
Build the next observer separately, capture the source reference before replay
and use it for the final comparison. Do not rebuild the replay executable or
weaken identity checks to accommodate an observer change.

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
