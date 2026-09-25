# Baseline replay through three million

25 September 2026. Approved continuation from the verified 2,700,000 checkpoint
to a bounded target of 3,000,000. This directory records operational work only;
it introduces no node-runtime change and does not approve the candidate patches.

Completed successfully on 25 September at 13:33:45 UTC (15:33:45 Stockholm).
Replay: PASS, 4,452.18 test seconds. Separate cold exact-height verification:
PASS, 12.81 seconds. The wrapper's total start-to-verified interval was about
77 minutes 27 seconds. `final-capture.json`, `replay.txt`, `exit-code.txt` and
`final-cold-check.txt` retain acceptance evidence. The original `startup-*`
records remain explicitly provisional snapshots of the earlier running job.

The closed target is 4,988,076,554 logical bytes / 4,992,933,888 allocated bytes
(about 4.65 GiB); logical growth during this phase was about 0.94 GiB. D: retained
about 155.47 GiB free and Linux about 60.87 GiB. No size-monitor error or stop
occurred. Exact final commitments and scope are in the
[investigation report](../../restart-integrity-investigation.md).

## Execution

`run-replay.sh` is launched inside WSL `FusionRehearsal` with:

```text
wsl.exe -d FusionRehearsal -u root -- unshare --mount --net --propagation private bash /mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-replay-three-million-2026-09-25/run-replay.sh
```

It requires a new destination and result directory, checks the retained binary
hashes and earlier successful result, and acquires both copy-source and target
runner locks. The original preserved history and C: checkpoint are mounted
read-only in the private namespace. `copy-checkpoint.py`, derived from the
previous verified-copy script, copies every file to a new Linux ext4 directory,
flushes file data, rereads every destination SHA-256/length and checks its file
inventory before writing the completed-copy marker.

- Checkpoint source: `C:/Users/Peter/Documents/CODING/fsn-efsn/tmp/replay-mainnet-c`
- New D:-backed ext4 target: `/home/rehearsal/replay/baseline-mainnet-three-million`
- Original D: checkpoint retained: `/home/rehearsal/replay/baseline-mainnet`
- Live results: `/home/rehearsal/results/restart-replay-three-million-2026-09-25`
- Clean-stop request: `/home/rehearsal/replay/STOP-baseline-mainnet-three-million`

A fresh read-only process checks the source checkpoint at exactly 2,700,000.
The unchanged replay executable then requires the copied executable/source/config
identity and independently validates the resume head before writable open. The
run uses no networking and checks free-space reserves before every 128-block
batch: 20 GiB within Linux and 50 GiB on D:. The wrapper samples allocated target
size every 30 seconds and requests the existing clean stop at 20 GiB total target
size, including the initial copy. That sampled allowance is not a filesystem
quota and can overshoot between samples; the per-batch reserve checks remain.
A size-monitor error also requests a clean stop.

On successful completion the wrapper opens both source and new target read-only
in a separate checker process and requires exactly block 3,000,000. A
`verified.txt` marker is written only after that check passes. A replay PASS
alone is not this final acceptance marker. Scripts refuse reuse; rerunning this
exact wrapper after preparation is not a supported resume procedure.

## Identity and scope

Replay executable SHA-256:
`004d4eeb16fc27e68564ff34d18b5bb1c48829cb692b98770fe7c52543d26c1e`.
Cold-inspection executable SHA-256:
`4dd9b2a105c9984d0f0d8ac154582c997e5560818d365c7ce4cef803cd552778`.

These are the retained **baseline** binaries used in the preceding phases,
not the current P1–P9 candidate. Earlier historical checkpoint shortcuts remain
part of the baseline through 2,680,000. The new range lies above that boundary.
Success here cannot be represented as historical replay of the proposed patches,
nor as validation of the remaining chain through 15,130,080.

`status.py` reads bounded log tails and both free-space figures without opening
the databases. The checkpoint copy contains 1,836 files / 3,978,652,725 bytes;
the original earlier checkpoints are preserved. Full result acceptance and final
space use are recorded in the collected logs and investigation report after the
run ends. No real key is used and no W: data is accessed.

`collect-evidence.py startup` retains the immutable copy/preflight records and a
clearly labelled progress snapshot. It makes no completion claim. After the
runner finishes, `collect-evidence.py final` requires a zero replay exit and a
passing exact-height cold check, then retains the final outputs and refreshes
`SHA256SUMS`. Both stages refuse overwriting an existing stage capture, and
shared immutable files must match any earlier captured bytes. Run this collector
with WSL Python because it reads the live Linux result paths. Final documentation
and commit review still follow collection; startup evidence is not final evidence.
