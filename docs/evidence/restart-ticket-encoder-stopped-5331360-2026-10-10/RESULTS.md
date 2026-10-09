# Verified stopped checkpoint at 5,331,360

10 October 2026 local time. **Read-only inspection and evidence verification
pass.** The preceding job requested 5,400,000 and remains incomplete/failed.
It stopped at its declared sampled allocation ceiling, with normal cleanup
before block 5,331,361. No replay retry or limit extension occurred.

All five inspection commands pass, including the retained executable's exact
cold-head check and the separate observer's state/ticket/receipt check. The
backup reference was acquired after the replay stopped. Complete header/RLP,
state and ticket commitments, transaction/receipt commitments, bloom and total
difficulty match. The fresh process reconstructs 3,728 tickets; the endpoint
has four transactions and four receipts. There is no final warm ticket count
from the stopped replay to compare.

- Block hash: `0x494fa4be8ceb267c9237890aa6ba34962408a821a16c0352a6b0fea86b14f296`
- State root: `0xaad715f92ce5537277da4feb82421817bd4b1dd944049f124f6e4d9ff8f35544`
- Ticket commitment: `0xf6050f3ee8d321b51eb860fc41e7a8bb4e1632a4338b261eb7a4eb7ec1d5fb75`
- Total difficulty: `26994846223`

All twelve preservation checks pass. Every one of the 5,591 stopped-target files
has identical before/after hashes. The 1,383-file recovery checkpoint at
2,400,000-v2 matches its sealed inventory. All 1,616 previously manifested
evidence files verify. Backup/baseline metadata, source inventories, executable,
observer, input bytes and the original STOP remain unchanged. Backup preservation
here is a metadata check, not another content hash of the entire backup.

Private mount/network namespaces, loopback down, read-only database mounts,
replay run locks and shared locks on the actual LevelDB LOCK files were required
before hashing. No block import, database copy or public network contact ran.
The observer changes only one height literal; the controller adaptation from
the earlier stopped-checkpoint check is retained in inspection-controller.patch.
No production source or release selection changed.

Inspection ran 23:25:23–23:27:31 UTC on 9 October; evidence verification completed
23:27:58 UTC. Closed allocation is 11,828,121,600 bytes (11.016 GiB). Final free
space is approximately 21.712 GiB Linux / 58.644 GiB D:. The prior 11 GiB limit is
sampled, so shutdown can finish slightly above it; no hard quota was claimed.

Candidate execution now has a cold-verified endpoint at 5,331,360, including
2,651,360 blocks beyond the legacy shortcut boundary at 2,680,000. The last fully
completed requested range remains 4,500,000. Baseline history remains 3,600,000.
F12/G1, later history, final restored-startup/recovery acceptance and independent
review stay open. Preparation README wording is historical; this result and
[verification.json](verification.json) supersede its pending status.

A new writer is blocked by storage: D: is below its unchanged 60 GiB starting
floor and the existing target exceeds the previous job's 11 GiB ceiling. See the
[specific archival proposal](../../restart-storage-next-step.md). Preserve this
working state and the separate recovery checkpoint. A future resume needs a
fresh job, explicit stopped-checkpoint provenance, capacity and exact cold
inventory/identity checks; it must not reclassify the failed job as successful.
