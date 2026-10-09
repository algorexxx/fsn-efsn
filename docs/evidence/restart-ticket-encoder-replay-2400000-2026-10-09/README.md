# Candidate attempt toward 2,400,000: time stop

9 October 2026. **Incomplete range; not a qualification pass.** The unchanged
encoder-candidate executable resumed the verified 2,200,000 checkpoint and
stopped at its predeclared 30-minute monotonic allowance. The log requests normal
cleanup before block 2,356,033, suggesting saved height 2,356,032. That height
requires independent cold verification; a progress log alone is not proof.

The replay command exited 1. Its timestamps span 06:39:53.747505 to
07:10:04.016614 UTC (1,810.269109 seconds); the Go test reports 1,801.81 seconds.
Keep these as distinct measurements; the cause of the difference is unestablished.
No bounds were extended and no replay retry or continuation was started.
The four preparatory commands passed, including exact-height cold preflight at
2,200,000 and the preserved 2,400,000 reference captured before replay.
No historical mismatch is reported in the retained replay log.

The original success-only [verifier](verify.py) remains unchanged and was not
run against this deliberately incomplete result. The [specification](spec.md),
[plan at start](plan-at-start.md), inputs, nonzero command exit, stop file and
raw [qualification record](qualification/run.json) are retained.
A separate [read-only follow-up](../restart-ticket-encoder-stopped-2356032-2026-10-09/README.md)
will check the inferred stopped height against the backup without importing blocks.
A successful follow-up must not reclassify this 2,400,000 attempt as passed.

The run checked all 1,320 previously manifested files and all 1,157 checkpoint
files before copying. Final preservation checks passed for the original
checkpoint, selected and candidate sources, binaries, observer, imported runner,
backup metadata and both baseline metadata inventories. Backup preservation is a
metadata check, not another full-content hash. Private mount/network namespaces,
loopback down and read-only source/checkpoint mounts were recorded.

Final recorded free space is 38,647,123,968 bytes in Linux (35.99 GiB) and
71,844,024,320 bytes on D: (66.91 GiB). No W: files were touched. The original
2,200,000 checkpoint and stopped target are retained. The stopped target's
directory name still ends in 2400000; it does not establish the actual head.

Replay SHA256:
b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245.
Target: /home/rehearsal/replay/candidate-ticket-encoding-2400000.
F12 remains open. These heights retain legacy checkpoint shortcuts through
2,680,000. No release selection, runtime patch, key or activation changed.
