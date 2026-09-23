# First restart corrections

The investigation baseline is `d82a229`. Three small corrections are now
implemented on `codex/restart-investigation-wip`; they are not a release or a
complete restart implementation. Historical replay continues with the unchanged
baseline in a separate Linux source tree.

## Changes and evidence

| Correction | Reproduced problem | Result required by the corrected tests |
| --- | --- | --- |
| Copy miner receipt logs, topics and data before handing them to a sealing task | The result worker writes a log while another worker copies the same state log; race detector fails in all three baseline repetitions | Actual miner/auto-buy runtime completes without that race |
| Reconstruct tickets using the parent timestamp for expiry cleanup | Reconstruction at a time jump or ordinary expiry boundary disagrees with the stored ticket commitment | Ten missing-state cases and all three exact expiry-boundary cases match direct-state preparation |
| Reuse the existing checked parent lookup in reconstruction | Missing ancestor dereferences the nil result while constructing an error | Return `consensus.ErrUnknownAncestor`, with no panic |

The expiry correction follows the timestamp already used by `Finalize` and
`StateDB.UpdateTickets`. It reconstructs the existing commitment and still
requires `AddCachedTickets` to verify that commitment. It does not introduce a
new expiry rule or bypass an incorrect reconstructed ticket hash.

Linux validation with Go 1.21.3 and CGO enabled:

- The complete ordinary restart suite passed three repetitions under `-race`.
  This includes real miner production, transaction construction/submission,
  independent execution after the producer stops, and deliberate corruption
  checks for the integrity scanners. Full-backup probes were explicitly skipped
  in this synthetic run.
- All 128 read-only historical reconstruction cases passed again with the
  corrections, matching the baseline. Their real headers lie outside the
  checkpoint shortcut range; recent retained history does not supply an expiry
  boundary, so synthetic boundary coverage remains necessary.
- The full Linux node executable builds. It was run only with `version`.
- The ordinary suite also passes on Windows amd64 with CGO disabled
  (23.039 seconds). The later purchase-replacement characterization was tested
  separately on Linux and is not included in that Windows result.

Raw logs, binary digests and source hashes are in
[the evidence directory](evidence/restart-integrity-2026-09-23).
The old miner package tests fail to compile on the unchanged baseline; this
known gap is recorded rather than described as a passing whole-repository suite.

## Limits and follow-up

Realistic mining/import concurrency around the process-global parent-header
slice remains to be investigated. Passing the reproduced race scenario is not
proof that all concurrency defects are removed. Historical replay and additional
reconstruction coverage are still required before release.

Auto-buy startup, error retry and inclusion monitoring are not corrected by
these changes. They require their own implementation and failure-case evidence.
The separate restart anchor is also not implemented. No production key or
preserved database has been changed by this work.

The old parent-time and receipt-copy overlay runners reproduce the original
experiments from `d82a229` or earlier. They intentionally require the old source
expressions and are not applicable after these corrections. Run the ordinary
restart suite directly when testing current code.
