# Read-only inspection after the 11 GiB replay stop

Declared 10 October 2026 local time, before inspection. The preceding requested
5,400,000 job remains failed/incomplete. The stop-before-5,331,361 log supplies
the height to investigate, not an expected hash or proof of persisted state.

Reuse the earlier stopped-checkpoint inspection, adapting only the attempt,
endpoint and recovery-checkpoint references, provenance assertions and explicit
capacity checks. Its controller diff is included. The observer changes only its
endpoint literal from 5,400,000 to 5,331,360; no node runtime source changes.

Hold replay locks and shared locks on the actual backup/recovery/working LevelDB
LOCK files before hashing. Shared locks exclude normal writers while allowing
read-only observers. Require no node/replay/observer process, private mount and
network namespaces, loopback down and read-only mounts. Retain the independent
2,400,000-v2 recovery checkpoint and original STOP. No import, copy, replay resume,
stop-file deletion, cleanup, network contact, limit change or W: access.

Verify the failed job and all prior sealed manifests, recovery inventory,
source/executable/toolchain identities and exact observer input bytes. Capture
the backup reference before the stopped-target observations; this is post-replay
reference acquisition. Check exact heads, full header/RLP, transaction/receipt
commitments, bloom, TD, state opening and cold ticket reconstruction/commitment.
There is no final warm ticket count for the stopped run. Hash all closed working
files before and after; preserve backup/baseline metadata and recovery hashes.

Start only above 21 GiB Linux / 51 GiB D: free. Before every command retain the
20/50 GiB reserves. Build at most seven minutes; each reader at most three minutes
(two-minute Go timeout); entire invocation at most twenty minutes plus twenty
seconds kill grace. Result logical size must be below 256 MiB. These read-only
inspection bounds do not authorize another historical writer or waive its 60 GiB
D: starting floor. A pass qualifies only the stopped checkpoint; F12/G1 stay open.
