# Cold verification at the stopped height 2,356,032

9 October 2026. **Read-only inspection passed; the requested 2,400,000 replay
range remains incomplete.** The preceding [attempt](../restart-ticket-encoder-replay-2400000-2026-10-09/README.md)
hit its unchanged 30-minute allowance and exited nonzero. This separate run
confirmed that its normal cleanup persisted height 2,356,032. No blocks were
imported or retried during inspection. All five commands exited zero and the
[standalone verifier](verification.json) passed on its first run.

The [specification](spec.md), observer and verifier were prepared before this
inspection. The height came from the stop-before-2,356,033 message; expected
hashes and commitments came independently from the preserved backup. The
reference was captured after replay stopped and before the cold checks, not
before the interrupted replay. The separate inspection ran from 07:14:06 to
07:14:38 UTC, including preservation checks.

## Matched endpoint

| Field | Observed and matched |
| --- | --- |
| Height | 2,356,032 |
| Block hash | 0x2b1fe6dfded927ae8e1247cb26e82fdd5833f5754fa852866da9656e5dd14739 |
| State root | 0xf193ba89d37129d792e4effaee77a0511701b1d2458b6092bbdc3ead31d3a4fc |
| Ticket commitment | 0xe8597d83e1a6184bb8477962576b2ae07d94d6981736b75c662dbaad61915943 |
| Transaction root | 0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421 |
| Receipt root | 0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421 |
| Cumulative difficulty | 10831511446 |
| Transactions / receipts | 0 / 0 |

Full header RLP and bloom also match. The original retained executable's
cold-head helper verified all head markers, canonical identity, body/receipt
commitments, cumulative difficulty and state/ticket availability. A separate
fresh observer process began with an empty ticket cache, decoded **6,459 tickets**
and recomputed the preserved commitment. The count is an observation: the
interrupted replay emitted no final warm count, so no warm/cold count agreement
is claimed.

Together with the completed ranges through 2,200,000 and the partial execution
log, this establishes sequential candidate execution and a verified persisted
endpoint through 2,356,032. It does not pass the declared 2,400,000 attempt.
Legacy shortcuts remain in effect through 2,680,000: execution and state/receipt
comparisons run, while ticket-seal and raw-transaction checks retain their
documented shortcuts.

## Preservation and provenance

The replay executable was reused without rebuilding:
b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245.
The observer is a separate Go 1.27.1 binary; its only source change is the
height literal 2400000 to 2356032, shown in [observer-change.patch](observer-change.patch).
Its SHA256 is
5d3ecc3a67a1c2e01c2296f0d020e2b35a2a100233163135bb6dd4c0014804e6.

- All 1,349 files in prior manifests, including the incomplete attempt, verify.
- All 1,157 original checkpoint files match the preceding recorded inventory.
- All 1,299 stopped-target files have identical before/after hashes.
- The replay identity file remains byte-identical to the original checkpoint.
- Selected/candidate source inventories, replay binary, observer, overlay,
  imported runner, evidence inputs and original stop file are unchanged.
- Backup and both baseline metadata inventories are unchanged; this is not a
  new full-content hash of the 117 GB backup. Neither baseline was opened.
- Private mount/network namespaces, loopback down, offline build inputs and
  enforced read-only mounts were verified. The original stop file is retained.
- Allocation is 2,904,657,920 bytes (2,770.10 MiB). Final free space is
  **35.98 GiB Linux / 66.97 GiB D:**. No W: files or database copies were used.

The raw attempt-final-run.json records the original runtime's final exception
after its qualification snapshot was copied. That expected finalization refusal
does not change the earlier nonzero replay result. Both records are preserved;
neither was edited to claim success.

## Next bounded work

Retain /home/rehearsal/replay/candidate-ticket-encoding-2400000 as the verified
**2,356,032** checkpoint; its directory name is only the original requested end.
Preserve the 2,200,000 checkpoint, both attempt records and original STOP.

The next declared range should cover only 2,356,033 through 2,400,000
(43,968 blocks), using a newly verified copy in a distinct target such as
candidate-ticket-encoding-2400000-v2 and a new result directory. Recheck current
capacity against the unchanged 30/60 GiB starting floors, retain the same
30-minute/4 GiB stops and 20/50 GiB continuation reserves, and use the original
replay executable with unchanged identity validation. A new stop-file path must
start absent; do not delete the preserved attempt's STOP. Recapture the 2,400,000
backup reference before the next replay and perform both cold checks afterward.
No continuation has started. This reduces the range after a measured time stop;
it does not extend the allowance. F12 and independent review remain open.
