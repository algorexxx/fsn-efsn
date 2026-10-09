# Normal-pruning synthetic startup result

**Pass**, independently checked by `verify.py`. The prepared README is retained
unchanged as an input. Execution completed 9 October 2026 at 16:28:23 UTC.

| Phase | Observed result |
| --- | --- |
| Seed | Complete synthetic ancestry 0–129, with a separately encoded child 130 |
| Restored CLI | Exact head/root/ticket commitment at 129; clean shutdown writes at 129, 128, 2 |
| Local import | Child 130 accepted; exact expected commitments; clean shutdown writes at 130, 129, 3 |
| Fresh CLI restart | Exact head/root/ticket commitment at 130; same three clean shutdown writes |
| Separate cold process | States and encoded-ticket commitments available at 130, 129, 3; all nine database file hashes unchanged |

All six commands exited zero. Mining and automatic ticket purchase stayed false.
The import shutdown persisted four new trie nodes; restart and cold observation
then read the resulting state successfully. There was no missing-ancestor panic,
failed recent-state commit or dangling-trie cleanup report. The existing
read-only startup check ran before writable Ethereum service initialization.

The CLI is byte-identical to the first startup candidate:
`07aa74a3f58132e5ff1465152402d5ea3b01738c0017af5dfd5672a75a2550cd`.
The seeder alone was compiled through the recorded overlay; retained source,
executable and input checks pass. Runtime output peaked at 13,797,130 logical
bytes, including the seeder executable. Final free space was 27,472,203,776 bytes
on Linux and 70,369,292,288 bytes on D:. The historical replay was running
separately, so free-space changes are not attributed solely to this fixture.

The process ran as uid 1000 in a different network namespace from its parent,
with only loopback down. P2P listening remained contained in that namespace;
dialing and discovery were disabled. No historical, backup or recovery database
was opened or hashed by this test. Full logs, arguments, time/resource records,
Go environment, source inventories and closed database hashes are retained.

The [first attempt](../restart-restored-startup-pruning-2026-10-09/STATUS.md)
built and seeded successfully but stopped while decoding its log: Go formatted
the child hash as raw bytes. Its raw log and failed run remain preserved.
The fresh v2 changes only that test log to explicit hexadecimal text. No CLI
phase ran in the failed attempt; no runtime fix was introduced for either run.

This closes the **small complete-ancestry pruning lifecycle case**. It supports
the earlier diagnosis that the sparse fixture lacked the ancestors used during
shutdown. It does not establish arbitrary pruning recovery, sustained pruning
under memory pressure, full-backup startup or post-legacy consensus acceptance.
The synthetic configuration puts EVM forks at genesis; the CLI's low-height
checkpoint shortcuts remain in force. Do not count these blocks as F12 history.

Next: let the current bounded historical replay finish and verify. Then assess
the startup candidate read-only against the complete preserved backup under a
separate bounded, read-only mount/lock procedure before considering writable
restored-startup/recovery acceptance. No further repetition of the already
passing small refusal, archive or pruning cases is needed. The startup patch
remains unselected and requires profile/anchor and independent review.
