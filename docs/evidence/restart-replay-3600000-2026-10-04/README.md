# Baseline replay from 3,300,000 to 3,600,000

4 October 2026. This is a bounded continuation of the independently verified
3,300,000 checkpoint with the same retained baseline and cold-check executables.
It changes no node code and does not test historical compatibility of the
P1–P17 candidate patches. **Complete after the validated continuation:** replay
and the fresh exact-height cold check both pass. Original provisional captures,
the monitor interruption and refused preflight remain retained below.

## Declared scope and preservation

- Original preserved history: `/home/rehearsal/data/efsn/chaindata`, mounted read-only.
- Retained source checkpoint: `/home/rehearsal/replay/baseline-mainnet-3300000`, mounted read-only.
- New writable copy: `/home/rehearsal/replay/baseline-mainnet-3600000`.
- Live results: `/home/rehearsal/results/restart-replay-3600000-2026-10-04`.
- Clean-stop request: `/home/rehearsal/replay/STOP-baseline-mainnet-3600000`.

The previous checkpoint is about 6.52 GB. Fresh preflight found 58,757,775,360
free bytes inside Linux and 112,664,543,232 on D:. Its previous replay exit is
zero, the verified marker is present, no baseline replay is active and the new
target does not exist. The source checkpoint resolves to the expected directory
and is not a symlink. This range needs no W: storage or large C: copy.

The existing copy helper requires more than 30 GiB Linux / 60 GiB D: free before
starting, then preserves 20 GiB Linux / 50 GiB D: reserves while copying. Every
file is flushed, reread and checked for SHA-256 and length; the complete target
inventory must match before the verified-copy marker is written. The original
backup, prior replay checkpoints and their stop files remain intact.

The runner checks both retained executable hashes, prior success markers,
unused paths, absence of another replay and source/destination runner locks.
Private mount/network namespaces enforce read-only source/checkpoint mounts and
offline operation. A separate process first checks the old checkpoint at exactly
3,300,000. Replay then verifies the copied identity/resume head and executes only
through 3,600,000 with the existing 12-hour ceiling and 128-block batch checks.

Space reserves remain 20 GiB Linux / 50 GiB D: throughout replay. The wrapper
samples allocated target size every 30 seconds and requests a clean stop at
20 GiB total, including the copied checkpoint. A size-monitor error also requests
a stop. This is a sampled allowance, not a filesystem quota. The wrapper never
starts another range automatically.

## Original startup evidence — provisional at capture

The copy verified all 3,026 files / 6,521,468,908 bytes. The independent read-only
check matched the retained 3,300,000 block hash, state root and ticket commitment
and passed in 5.51 seconds. `isolation.txt` records both source mounts read-only,
only a down loopback interface and the expected executable/identity hashes.

Replay started at 17:40:48 UTC (19:40:48 Stockholm) on 4 October. The provisional
capture at 17:44:29 UTC records progress through 3,314,336, with 48.60 GiB free
inside Linux and 95.96 GiB on D:. The size monitor reported no error; its latest
sample was 6,560,456,704 allocated bytes. `startup-capture.json` explicitly records
`completion_claim=false`. The verified baseline remains 3,300,000 until this
range exits successfully and passes its fresh exact-height cold check.

## Monitor stop and validated continuation

The first replay ended at 18:32:38 UTC with exit 1 after its monitor requested
a clean stop before block 3,521,057. `du` had reported three disappearing `.ldb`
files during live measurement. This is consistent with concurrent LevelDB
compaction; it was not a recorded block/state mismatch or a space-limit breach.
The failed run, size errors and stop request are preserved in `stopped/`.

A separate process then opened both source and stopped target through read-only
mounts in a private network namespace. Exact-height inspection passed at
3,521,056 in 6.98 seconds:

- Block: `0xfff6ae4ff23211b76165e8b5201fd1a8719aa65e3b46d926245ca07a353228aa`.
- State root: `0x92b1b7a3f89f0f6605bc742758f327bcde2fa3e75f384d35dacc6299d1b08399`.
- Ticket commitment: `0xa5cdd2d349d602bffea2ff6da359e1297da94dcbb3c5c0f9efc7daeba4e228b2`.
- Closed allocation: 7,289,987,072 bytes; fresh free space 46.25 GiB Linux /
  93.43 GiB D:.

The initial continuation wrapper omitted a read-only bind view for its repeat
cold preflight. The checker correctly refused it before replay started. That
harness failure and script are retained in `resume-preflight-refused/` and
`resume-preflight-refused.sh`. The corrected `resume-replay.sh` supplies the
required mount and uses new result/stop paths; it does not erase the refusal.

Corrected continuation began at 18:44:57 UTC from the inspected 3,521,056 head,
using the same writable disposable copy and baseline executable. No new bulk
copy was made. The size monitor now requires one successful `du` measurement
within three attempts, each capped at 15 seconds with a two-second kill grace.
Every failed measurement is retained. Three failures, malformed output or a
20 GiB sample still request a clean stop. Existing batch-level 20 GiB Linux /
50 GiB D: free-space checks and the 12-hour ceiling remain in force.

Continuation results:
`/home/rehearsal/results/restart-replay-3600000-resume-v2-2026-10-04`.
Continuation stop request:
`/home/rehearsal/replay/STOP-baseline-mainnet-3600000-resume-v2`.
`status.py --resume` reads this run; the default still reads the original stop.
`collect-continuation.py resume-startup` records provisional progress under
`resume/`, with no completion claim. Only `resume-final` after exit zero and
the exact-height 3,600,000 cold check can complete this range. The previous
complete checkpoint at 3,300,000 remains preserved and unchanged.

## Final acceptance — complete through 3,600,000

The resumed replay passed in 1,024.07 seconds and its wrapper recorded exit zero
at 19:03:13 UTC. The separate read-only cold check passed in 10.39 seconds;
`verified.txt` was written at 19:03:25 UTC on 4 October. Both checks agree on:

| Commitment | Value |
| --- | --- |
| Height | 3,600,000 |
| Block hash | `0x1013c88fb0a8be3b78a0a3acdb287f6e9a6f65e81353aadaccac7a580a5a1c74` |
| State root | `0xff355f1211571f85f3f3c6731db375c6d7c581a8e0c70db1f82382752f3ca0e8` |
| Ticket commitment | `0x09785f30d672027af83e75cb7e71882e52d84d40282d1ebc6f74a977b0fb79d1` |
| Replayed active ticket count | 4,549 |

The closed database occupies 7,534,972,928 allocated bytes. Final capture found
45.84 GiB free in Linux / 93.02 GiB on D:. The resumed size monitor reported no
errors. Its retry branches therefore remain a reviewed operational correction,
not newly exercised failure-injection cases. The original single-attempt
failure is retained and is not relabeled as a passing run.

`resume/resume-final-capture.json` records `range_completion_claim=true` only
after checking both successful outcomes. All raw final logs are under `resume/`.
The unchanged baseline now has a completed checkpoint through 3,600,000, with
the already-documented legacy shortcuts through 2,680,000. Later history and
candidate-patch historical compatibility remain open. No next range was started.

## Execution, status and acceptance

```text
wsl.exe -d FusionRehearsal -u root -- unshare --mount --net --propagation private bash /mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-replay-3600000-2026-10-04/run-replay.sh
```

`status.py` reads bounded log tails and free space without opening the database.
`collect-evidence.py startup` records the verified copy, checkpoint preflight and
progress with `completion_claim=false`. Only after successful replay and a fresh
read-only exact-height 3,600,000 check can `collect-evidence.py final` record
`completion_claim=true`. Both collection modes refuse existing stage captures.

Final acceptance compares canonical head, state root, ticket commitment,
transaction/receipt commitments, bloom, cumulative difficulty and available
state against preserved history. The independent cold checker must pass before
the runner writes `verified.txt`. Source/runtime identity and the inherited
legacy shortcuts through 2,680,000 remain unchanged. The rest of history through
15,130,080 and candidate-patch historical compatibility remain separate work.

Replay executable SHA-256:
`004d4eeb16fc27e68564ff34d18b5bb1c48829cb692b98770fe7c52543d26c1e`.
Cold-check executable SHA-256:
`4dd9b2a105c9984d0f0d8ac154582c997e5560818d365c7ce4cef803cd552778`.

No real key, signing, mining or public network connection is involved. This is
data validation using the unchanged baseline, not authorization for a launch.
