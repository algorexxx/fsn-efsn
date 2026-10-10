# Verified replay through 6,300,000

Completed 10 October 2026 at 21:24:13 UTC (23:24:13 Europe/Stockholm).
Replay from 5,976,864 added 323,136 blocks. All seven commands, both fresh-process
cold checks and all ten additional preservation checks pass. Full header/RLP,
state and ticket commitments, transaction/receipt roots, bloom and total
difficulty match the independently captured backup reference. Warm/cold ticket
counts agree at 4,621; the endpoint has zero transactions and receipts.

- Block hash: 0xe36633304dfbb12ce025e5b915d090a53df7bc8f5463c61a81ab924bc9f63bae.
- State root: 0x85a1d99697d485a23cc0753da9a020da0d0edefbf2560d4fc91a09961127bfc8.
- Ticket commitment: 0x094b014a1cac0dfdd3e12dc6cbc877fa38492f234f5427431a7c4b6f152899f0.
- Total difficulty: 30,119,290,856.

All 13,794 closed working-file hashes stayed unchanged during inspection. The
separate recovery's 1,383 hashes, backup/baseline metadata, source, input,
executable, toolchain and prior native-reserve failure provenance remain valid.
The 1,826 previously manifested files verify. This completion does not reclassify
the earlier failed jobs or change their limits or records. No STOP was fabricated.

The independent post-completion review rechecked all six manifests: 9 input,
13 preparation, 3 launch, 3 initial-status, 30 output and 53 full-bundle entries.
Original manifests and their files remain unchanged; this report, review script/
record and final host dispatch record are sealed separately by RESULTS_SHA256SUMS.
The automatic evidence verifier exited zero at 21:24:13 UTC and the host
dispatcher exited zero at 21:24:14 UTC. No node/replay/observer process was found
at the read-only process review at 21:55:11 UTC; no subsequent writer started.

Replay command timestamps span 154.956 minutes; the runner's monotonic duration
is 143.667 minutes. Both measurements are preserved. The cause of the clock
difference was not established, so neither is silently substituted for the
other or used to promise an ETA. Four allocation measurements encountered
files disappearing during LevelDB activity; each bounded retry succeeded.
No persistent measurement failure, stop request or test failure occurred.

Closed allocation is 29,064,523,776 bytes (27.068 GiB), up 5.799 GiB over this
interval. Final recorded free space was 28.689 GiB Linux / 54.615 GiB D:.
The later 21:58:08 UTC capacity review found 28.689 GiB Linux / 55.271 GiB D:.
There is now candidate evidence for 3,620,000 blocks beyond the legacy boundary
at 2,680,000; 8,830,080 blocks remain to the preserved tip. Earlier legacy
shortcuts and the separate baseline at 3,600,000 remain unchanged. F12/G1 and
final selected-binary restored startup/recovery/handover acceptance remain open.

## Next step is capacity, not another writer

A proposed 6,300,000 to 6,600,000 continuation with a 34 GiB sampled ceiling
allows 6.932 GiB growth. The unchanged capacity controller requires more than
27.932 GiB free in Linux and 60 GiB on D:. Applying that controller to the fresh
capacity observation refuses D:. This is a proposal only; no new job directory,
writer, limit relaxation or release change was made. Another tiny retry below
the starting floor is not justified.

All obsolete D: fixture roots have already been archived and retired. The only
remaining roots under D:/FusionRehearsal are Ubuntu and swap. The virtual disk
is 211,278,626,816 bytes; swap is only 37,748,736 bytes. Deleting swap would not
resolve the shortfall and it is retained. See the updated
[capacity decision](../../restart-storage-capacity-review.md#next-capacity-decision)
for a verified cold disk archive followed by possible offline compaction, or
additional host space. No compaction or other storage mutation has started.

Prepared and initial running-status files remain immutable historical records;
this result and completion/verification supersede their pending wording.
