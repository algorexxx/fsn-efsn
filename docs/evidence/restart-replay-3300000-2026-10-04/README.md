# Baseline replay from 3,000,000 to 3,300,000

4 October 2026. This bounded continuation uses the verified three-million
checkpoint and unchanged retained baseline executable. It introduces no node
runtime change. Replay and the separate exact-height cold check both passed.
The earlier startup capture remains provisional; final acceptance is recorded
separately in `final-capture.json`, with `completion_claim=true`.

Startup is verified: 2,351 copied files / 4,988,076,554 bytes, with the separate
three-million-block cold check passing in 4.89 seconds. Replay began at
13:28:37 UTC (15:28:37 Stockholm). The retained 13:29:50 UTC startup capture
records progress through 3,004,608, with `completion_claim=false`.

## Final result

Replay passed in 4,555.02 seconds; `finished.txt` records 14:45:28 UTC. A fresh
read-only process passed in 9.52 seconds and `verified.txt` records 14:45:38 UTC
(16:45:38 Stockholm). Both processes match the preserved source at exactly
3,300,000:

- Block: `0x74a4fb230a6ee77b9f6e8ca536d7b2e0ffb4abd9796de23ef37c7951cc31583b`.
- State: `0x8c54be811459cc46df46350d9b2266652806a07fe9cff87a592e42fdeb0f7045`.
- Ticket commitment: `0xfe0cce5c894d9a202ea3a8cf751c2c1eb70436626793b33443da21300aea5143`;
  4,716 tickets at the replay head.
- Closed logical size: 6,521,468,908 bytes; allocated size: 6,527,746,048 bytes.
- Completion free space: 60,154,019,840 bytes inside Linux and 113,771,839,488 on D:.
- `exit-code.txt` is zero; `size-monitor-errors.txt` is empty.

The runner has ended. No further range is started by collection. This adds
300,000 executed blocks above the already-passed checkpoint, bringing retained
baseline execution beyond the legacy shortcut boundary to 620,000 blocks.

## Execution and preservation

The runner is invoked in WSL `FusionRehearsal` with:

```text
wsl.exe -d FusionRehearsal -u root -- unshare --mount --net --propagation private bash /mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-replay-3300000-2026-10-04/run-replay.sh
```

It requires the earlier successful verification, exact retained executable
hashes, unused target/results/stop paths, no active baseline replay and both
source-checkpoint and destination runner locks. Private mount/network namespaces
keep this execution offline, with the original backup and completed checkpoint
mounted read-only. The new target is a separate D:-backed Linux ext4 copy.

- Preserved checkpoint: `/home/rehearsal/replay/baseline-mainnet-three-million`
- New target: `/home/rehearsal/replay/baseline-mainnet-3300000`
- Live results: `/home/rehearsal/results/restart-replay-3300000-2026-10-04`
- Clean-stop request: `/home/rehearsal/replay/STOP-baseline-mainnet-3300000`

`copy-checkpoint.py` copies all checkpoint files, flushes file data, rereads each
destination to verify SHA-256 and length, and checks the inventory before writing
its verified-copy marker. Earlier D: and C: checkpoints and their stop files are
preserved. No data copy is placed on C: or W:.

A separate read-only process must match the source checkpoint at exactly
3,000,000. The baseline executable then verifies its copied identity and persisted
resume head before writable open. The requested end is exactly 3,300,000.

Copy preparation requires more than 30 GiB free inside Linux and 60 GiB on D:.
Copying and replay retain the existing 20 GiB Linux / 50 GiB D: reserves; replay
checks them before each 128-block batch. The wrapper samples allocated target
size every 30 seconds and requests a clean stop at 20 GiB, including the copy.
This is a sampled allowance, not a filesystem quota; growth can overshoot between
samples. A size-monitor error also requests a stop. No unattended continuation
to another range is configured.

Only after the replay exits successfully does a fresh process open the target
read-only and require the exact 3,300,000 head, canonical identity, transaction
and receipt commitments, bloom, cumulative difficulty, available state and ticket
commitment against the preserved source. Only that passing check writes
`verified.txt`. The wrapper refuses reuse of its paths; rerunning it is not a
resume procedure.

## Identity, evidence and limits

Replay executable SHA-256:
`004d4eeb16fc27e68564ff34d18b5bb1c48829cb692b98770fe7c52543d26c1e`.
Cold-inspection executable SHA-256:
`4dd9b2a105c9984d0f0d8ac154582c997e5560818d365c7ce4cef803cd552778`.

These are the same baseline executables used for the previous range. This run
does not establish historical compatibility of the P1–P17 candidate patches.
The new range is above the legacy checkpoint shortcut boundary of 2,680,000;
earlier shortcuts remain part of the baseline and are not retroactively checked.
The remaining history through the backup head at 15,130,080 is still pending.
No real key, transaction signing or network mining is involved.

`status.py` reads bounded log tails and current free space without opening a
database. Run it with WSL Python. `collect-evidence.py startup` records the copy,
preflight and a provisional progress snapshot, with `completion_claim=false`.
After the runner finishes, `collect-evidence.py final` requires the successful
exit and exact-height cold check before collecting final outputs. Each stage
refuses an existing stage capture and requires shared immutable files to match.
Collection refreshes `SHA256SUMS`; final documentation and review follow result
collection. See the [integrity investigation](../../restart-integrity-investigation.md)
for the historical verification record.
