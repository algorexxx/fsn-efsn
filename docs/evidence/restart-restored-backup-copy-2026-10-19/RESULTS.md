# Complete preserved-backup fixture copy

**Pass**, reviewed 20 October 2026. The finite copy and independent readback
finished at 01:03:29 UTC, exited zero and detached cleanly. The 01:53 UTC
actual-state check finds no test process, loop device or matching mount; the
host dispatcher is gone. All input/start seals still verify.

All **56,107 files / 117,170,022,674 bytes** match the original September 23
backup manifest, hashed during copy and again after unmount/reattach read-only.
Source and destination metadata remained exact. The original backup is retained.
The separate disposable W: startup.ext4 is 256 GiB, UUID
`0b18a87d-e8ee-413f-b37f-01eec39b0c48`, with the database under `/checkpoint`.
The protected final replay image was never attached by this job.

Both actual cold tests ran and passed (no skipped invocation). Full header,
state/ticket, transactions/receipts, bloom and total difficulty match the final
historical replay at **15,130,080**, with 491 tickets and one transaction/receipt.
Replay and observer executable hashes and the trusted responses stay pinned.
This is a fixture-copy result, not writable startup or release acceptance.

All 463 resource samples pass. Minimum free space was about 21.48 GiB Linux,
52.70 GiB D:, 2,867.05 GiB W: and 145.42 GiB inside the image. Both phases stayed
within their 3.5-hour cooperative limits and 12,720-second external limits;
the whole job stayed under eight hours. Monotonic migration time is
13,924.078 seconds, while wall duration is about 14,873 seconds; the unexplained
clock difference is preserved. No time or content acceptance was waived.

`review.py` independently checks retained results, exact endpoint and executable
identities, actual test PASS markers, phase limits, reserves, input/start seals
and cleanup. `SHA256SUMS` seals this complete bundle; it does not hash any live DB.

Next: qualify the retained unselected guard/encoder CLI on this disposable
complete copy, using normal pruning, the trusted test-only mainnet anchor,
one writable owner, private offline namespaces and finite startup/restart limits.
Keep all protected checkpoints and failed records. Existing small refusals and
synthetic lifecycle tests need no repetition. Production selection, independent
codec/consensus/parent trust and recovery/handover acceptance remain open.
