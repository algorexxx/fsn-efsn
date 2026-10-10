# Requested 6,300,000 replay stopped at the host-space reserve

The replay exited 1 at **17:45:02 UTC on 10 October 2026**. Its per-batch
space check observed 53,563,531,264 bytes free on D:, below the unchanged
53,687,091,200-byte (50 GiB) reserve. The completion record at 17:45:21 UTC
retains `verified_pass: false` and `automatic_continuation: false`.

The last logged progress height is **5,976,608**, not an independently verified
saved endpoint. Unlike the preceding allocation-limit stop, this native reserve
failure does not print the next block or create a new STOP file. Do not infer
the final persisted head from the progress sample or manufacture a STOP.
Normal test cleanup is registered, but its persisted result still needs cold
inspection. No consensus mismatch is reported in this attempt.

Four startup commands passed; replay failed after a recorded monotonic
8,158.687 seconds. Command wall timestamps remain separate observations.
All ten additional preservation checks passed, as did the original-backup,
baseline, selected-source, candidate-source and input comparisons. The
working database was intentionally advanced; its previous byte inventory is
historical. The separate 2,400,000-v2 recovery checkpoint remains unchanged.

The last sampled working allocation was 22,800,744,448 bytes (21.235 GiB), below
the declared 26 GiB ceiling. This is a pre-shutdown sample, not a cold inventory.
Final recorded free space was 37,115,981,824 bytes in Linux and 53,060,214,784
bytes on D:. The host dispatcher also exited 1. A later read-only capacity check
found FusionRehearsal stopped and about 49.385 GiB free on D:.

The original input, preparation, launch, output and bundle manifests verify.
The separate failure-evidence verification checks these records and the stop
classification; it is **not** a successful job verification or a cold database
check. There is no job `verification.json`. Original completion, status, logs
and manifests remain unchanged. This result supersedes historical running
wording in README/STATUS without editing those launch records.

**Cold-verified candidate coverage remains 5,600,032.** F12/G1 remain open.
Do not start another writer or run the existing cold-inspection wrapper below
its starting reserve. The [capacity review](../../restart-storage-capacity-review.md)
records a concrete 14-folder archival/reclaim proposal. Nothing from that
proposal has been copied or deleted. No reserve, runtime, release selection,
executable or production identity changed.
