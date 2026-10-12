# Finite W-backed history trial

Continue only from the verified migrated checkpoint 7,170,976 to exactly
7,200,000: 29,024 new blocks. The old failed 7,200,000 attempt and its STOP
remain immutable; the separate verified inspection is the accepted parent.
Replay binary SHA256 remains b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245.
Only the observer endpoint literal and test orchestration change.

Purpose: measure real history replay throughput/growth on the W-backed ext4
image before selecting larger ranges. Keep GOMAXPROCS=2, offline private mount
and network namespaces, source/recovery read-only mounts and verified locks.
Use a 46 GiB sampled database allocation ceiling (about 1.97 GiB above the
44.033 GiB migrated allocation), 30-second samples, 3,600-second cooperative
stop, 3,900-second Go timeout and 4,200-second replay outer timeout with 20-second
grace. Whole attachment/preparation/replay/cold-verification job: 18,000 seconds
plus 20-second kill grace. Never extend a running limit or retry automatically.

Local preparation floors: Linux >21 GiB, D: >51 GiB. W: >101 GiB + remaining
declared database growth; image filesystem >21 GiB + that growth. Running
reserves: Linux/image >20 GiB, D: >50 GiB, W: >100 GiB. The unchanged executable
checks image/D: each batch; the controller also samples local Linux/W:.
Mount identity or resource failure requests a clean STOP, independently of
the finite timeouts. Preserve incomplete results and do not hash live LevelDB.

Require exact closed starting inventory, replay identity, source/toolchain and
executable hashes. Preserve local fallback metadata under locks, original backup
and baseline metadata and the independent 2,400,000 recovery hashes. After a
clean endpoint, both cold readers must reproduce full reference commitments;
seal the closed target inventory and verify all evidence. Finally unmount,
read-only filesystem-check and detach. A passing inner completion alone is
provisional until storage-completion and host completion pass. Final storage
records are outside the inner automatically sealed manifest and need a separate
post-completion manifest. No whole live image hashing.

If storage failure, forced kill or network outage prevents cleanup, stop and
inspect attachments/processes before any further work. Retain the original
7,170,976 local fallback and all failed/sealed evidence. No activation, key use,
public peers, D: expansion, deletion or release-selection change.
