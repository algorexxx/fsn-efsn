# Complete-backup read-only startup preflight

Prepared 9 October 2026 after verified replay through 4,500,000.
Call the unselected startup candidate's existing `core.CheckRestoredState`
against the preserved complete backup. Require the recorded genesis and full
head 15,130,080/hash; use that head as a **test-only** anchor. This does not select
the recovery anchor or authorize writable startup, mining or signing.

Compile only a Go test overlay on the retained candidate source. Do not rebuild
or change its runtime files. One worker, offline Go modules, nice 10. Build <=5m,
read-only check <=3m (Go2m), kill grace10s, overall12m. Require >21/51 GiB Linux/D:
before preparation and >20/50 GiB before each command. Output ceiling256 MiB,
sampled between commands. No historical replay or bulk copy runs concurrently.

Use private mount/network namespaces, loopback down, a read-only bind mount and
shared nonblocking flock on the actual LevelDB LOCK (the pinned implementation
uses shared locks for read-only access and exclusive locks for writers). Hold
the replay working-directory run lock as well. The observer checks ST_RDONLY
and opens LevelDB read-only. Record metadata inventories before and after and
compare against the sealed completed replay inventory; do not hash117GB again.

Pass requires expected genesis/head, unchanged candidate code/toolchain, successful
startup validation, unchanged complete backup metadata and preserved input hashes.
Retain inputs, raw logs, namespaces/mounts, locks, identities, resources, metadata
inventories, verification and any failure. This checks readiness at the saved
head; it is not full history re-execution, full-state traversal or actual CLI
writable startup/recovery/handover acceptance.
