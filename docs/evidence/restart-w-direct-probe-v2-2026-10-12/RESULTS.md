# Direct W: path is not usable for this Linux LevelDB configuration

12 October 2026. The corrected probe reached the database operation. Building
and executable identification passed with Go 1.21.3 and efsn's pinned
`goleveldb v1.0.1-0.20210819022825-2ae1ddf74ef7`.

The first `leveldb.OpenFile` failed with:

```
sync /mnt/w/FusionRestart/restart-w-direct-probe-v2-2026-10-12/db: input/output error
```

The fixture directory and small creation files remain. No 32 MiB batch-write
test, compaction, reopen or lock-contention check was reached in this attempt.
The current mount is W: through WSL DrvFs/9p over the existing Windows SMB
mapping, not a native Linux CIFS mount. This result applies to that stack; it
does not establish that every network filesystem is incompatible.

The pinned library calls `syncDir` and ignores EINVAL, but not this EIO.
Do not bypass sync or modify the node/library to conceal the storage error.
The same executable passed on local ext4 in the separate
[image probe](../restart-w-image-probe-2026-10-12/RESULTS.md), isolating this
failure from a general inability to create a database with the fixture.

Executable SHA-256:
`bc16405e3ddf4738ba80380709d15714a70641fd5054a44e74d08f4174cfb4e6`.
Only disposable synthetic data was opened. The original chain backup,
checkpoint 7,170,976, independent recovery and archives were not opened.
