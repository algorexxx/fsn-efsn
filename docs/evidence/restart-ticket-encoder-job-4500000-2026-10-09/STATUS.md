# First 4,500,000 job — refused before execution

Dispatch started 2026-10-09 16:11:29 UTC. The job finished unsuccessfully at
16:12:17 UTC because details_test.go had CRLF line endings rather than the
verified prior input's LF bytes. The exact-byte safeguard refused this before
any test command, observer build or replay ran. Starting working-file hashes
matched the verified 3,600,000 inventory. Completed checkpoint remains 3,600,000.

The original sealed input/output manifests and qualification logs remain intact.
This status file and launch-record.json were added after the controller sealed
its result and are follow-up documentation, not entries in that sealed manifest.

The fresh corrected job is ../restart-ticket-encoder-job-4500000-v2-2026-10-09/.
It retains all limits and changes no release/runtime selection.
