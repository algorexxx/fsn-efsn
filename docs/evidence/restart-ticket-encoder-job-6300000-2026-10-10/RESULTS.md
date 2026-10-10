# Requested 6,300,000 replay stopped at its allocation ceiling

The finite job ended with exit1 at14:32UTC on10October2026 after requesting a
clean stop at its declared sampled15GiB target limit. The log reports stopping
before block5,600,033 and normal persistence. No consensus mismatch is reported
in this attempt. Four preparatory commands passed; replay exited1. All ten
additional preservation checks and backup/baseline/source/input checks passed.
All prepared/input/launch/output/bundle manifests were independently verified.

The [separate cold inspection](../restart-ticket-encoder-stopped-5600032-2026-10-10/RESULTS.md) verifies the saved5,600,032
endpoint. It does not reclassify this job as completed. The original STOP, logs,
completion and manifests remain immutable. The interval added268,672 blocks;
closed allocation grew from11.016 to15.028GiB. Logged replay monotonic
elapsed time is5438.296s; wall-clock timestamps
are retained independently and are not substituted for that timer.

Further replay is held for a capacity decision. Do not lower reserves, remove
STOP, blindly retry, or claim6,300,000 verified. No runtime/release selection changed.
