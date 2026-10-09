# Allocation stop before the requested 5,400,000 endpoint

10 October 2026 local time. **Requested range incomplete; not a qualification
pass.** The controller requested normal cleanup at its declared sampled 11 GiB
target allocation allowance. The replay log stopped before block 5,331,361 and
the command exited 1. No historical mismatch is reported in that log. The final
job record preserves the failed replay and incomplete-qualification errors.
The success-only verifier was not run on this incomplete job.

All four preparation commands passed. Final backup/baseline metadata, selected
and candidate source checks and all nine additional preservation checks pass,
including the separate 2,400,000 recovery checkpoint. The original STOP, logs,
completion record and sealed input/output manifests remain unchanged.

The monitor's last allocation sample is 11,824,746,496 bytes, slightly above the
11,811,160,064-byte ceiling. This was a sampled stop, not a hard filesystem quota.
Completion was recorded at 23:05:22 UTC on 9 October. No automatic retry occurred.

The subsequent [read-only stopped-checkpoint inspection](../restart-ticket-encoder-stopped-5331360-2026-10-10/RESULTS.md)
passes at exactly 5,331,360 with matching preserved history and unchanged database
hashes. It qualifies that saved checkpoint without making this requested range
pass. Final stopped allocation is 11.016 GiB; D: has about 58.64 GiB free, below
the unchanged 60 GiB starting floor for another replay.

The immutable preparation/status files still describe the earlier running job;
completion.json and this result supersede their pending wording. This file is
sealed separately in RESULTS_SHA256SUMS, leaving the original SHA256SUMS intact.
See the [storage proposal](../../restart-storage-next-step.md) before any new job.
