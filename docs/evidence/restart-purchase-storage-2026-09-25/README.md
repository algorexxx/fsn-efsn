# Purchase storage errors and compatible peer forks

25 September 2026, baseline `c62d8cd`. No production source changes. See the
[report](../../restart-purchase-storage-and-peers.md) for exact scope and limits.

Final results:

- `windows-storage.txt`: eight storage cases, PASS, 80.12 seconds.
- `linux-storage-race.txt`: the same eight cases, PASS, 97.61 seconds.
- `linux-peer-final-race.txt`: two actual peer/downloader cases, PASS,
  44.81 seconds, with explicit log counts and an initially empty cold pool.

`initial-windows-storage.txt` contains six passes and two fixture failures:
the read-failure cases observed an undrained warning from their intentionally
failed setup submission. The final helper consumes that expected warning.
`linux-peer-race.txt` is the initial IPC-path-length failure, before either
node could open its IPC server. Neither failure required a production edit.

The initial Linux binary remains pinned for the storage results. The final
peer binary additionally contains the log-count and empty-pool assertions.
`identities.json` distinguishes the source files relevant to each group and
pins all three binaries. Shared test helper changes only extract the existing
record reader and dispatch new storage cases. No previous evidence is replaced.

Reproduce from the repository root with the existing offline Go 1.21.3 caches:

```powershell
& ./docs/evidence/restart-purchase-storage-2026-09-25/check-windows.ps1
wsl.exe -d FusionRehearsal -u root -- bash /mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-purchase-storage-2026-09-25/check-linux.sh
wsl.exe -d FusionRehearsal -u root -- bash /mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-purchase-storage-2026-09-25/check-peer-linux.sh
```

Use a fresh results directory when reproducing. Linux runs as `rehearsal` in
private network namespaces, with only loopback enabled for peer tests. The
peer fixture databases use short paths in Linux `/tmp`; storage fixtures use
the repository's existing temporary area. These are small synthetic databases;
no backup, D:/W: dataset, real key or public network is used. Missing historical
bodies and withheld block signatures produce expected fixture warnings.

This proves handling of the specified errors and compatible fork arrangements.
It does not prove power-loss durability, full-disk recovery, deep live-peer nonce
rollback or competing-miner operation. The permanent node patch list is unchanged.
