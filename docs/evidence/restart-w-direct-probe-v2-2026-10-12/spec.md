# Direct W: feasibility probe

12 October 2026. The user asks to use W: instead of freeing more D: space.
This is a small disposable storage check, not approval of a historical replay
on unqualified storage and not a migration of the protected rehearsal VHD.

Use the existing W: mapping to `\\192.168.1.250\mnemosyne1` in a private mount
namespace. The Go process uses a private network namespace with only loopback
down; Windows supplies the existing SMB storage connection through DrvFs.
No blockchain network access, keys, chain DB opening, deletion or copy.

Create only a fresh `W:/FusionRestart/restart-w-direct-probe-v2-2026-10-12/db`.
Build using the cached efsn-pinned goleveldb version with downloads disabled.
Check refusal of a second writable open, 32 MiB of synchronous batched writes,
compaction, close/reopen and a synchronized marker after process exit without
closing the DB. Verify all 8,192 deterministic values plus the marker.
Retain the small fixture and logs. Build timeout 90 seconds, database timeout
180 seconds, outer timeout 330 seconds; kill grace 5/5/10 seconds.
Require Linux/D:/W: free reserves of 20/50/100 GiB before starting.

A pass means these particular application operations worked on this mount.
It does not prove NAS power-loss durability, cache bypass, disconnect recovery,
multi-host locking or acceptable full-history performance. Inspect any failure
before proposing more work. The verified 7,170,976 checkpoint stays untouched.
