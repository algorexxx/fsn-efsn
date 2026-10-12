# W-backed ext4 image: small feasibility test passes

12 October 2026. A new 256 MiB raw image at
`W:/FusionRestart/restart-w-image-probe-2026-10-12/disposable.ext4` was attached
to a dedicated loop device and formatted ext4 after asserting its exact backing
file. This was not the rehearsal VHD or any existing archive.

Both the local ext4 control and the W-backed ext4 image passed with the identical
executable from the direct-path attempt. The database subprocess ran as
`rehearsal` with no network interfaces except loopback down. Windows supplied
the existing SMB storage connection through a private DrvFs mount.

| Observation | Local ext4 | Ext4 image on W: |
| --- | ---: | ---: |
| Second writable open refused with EWOULDBLOCK/EAGAIN | Pass | Pass |
| 8,192 values / 32 MiB logical synchronized batch writes | 0.703 s | 13.678 s |
| Explicit compaction | 0.042 s | 0.355 s |
| Reopen and verify all deterministic values | Pass | Pass |
| Synchronized marker retained after child process exit without Close | Pass | Pass |

The image was cleanly unmounted. Read-only `e2fsck -f -n` completed with exit 0
and all five passes; the loop device was detached with exit 0. Post-run checks
found no probe/replay process, no loop attachment for the image, and `/mnt/w`
resolving to the original root filesystem again. The image remains exactly
268,435,456 bytes logically. Small failed direct-path files are retained.

The database values are compressible; these timings are not a 32 MiB physical
transfer benchmark or an estimate of full replay time. Reads can use caches.
This tests ordinary application operations, including WAL recovery after a
process exit, not machine/NAS power loss, storage disconnects or multi-host
locking. Only one Windows/WSL host may attach a future working image.

The result supports a separate image on W: as the next bounded storage trial.
It does not qualify the full migration or any chain block. Preserve the verified
7,170,976 local checkpoint until a new W-backed copy is hashed, cold-opened and
compared; then measure a short replay before extending its range. Keep the
original backup, recovery and cold archives untouched.

No D: expansion, chain replay, node/library modification, real-key access or
public network activity occurred. Source and executable hashes are recorded in
the direct-path bundle; each image operation has separate command/output logs.

Reference context: Microsoft's [WSL issue 7803](https://github.com/microsoft/WSL/issues/7803)
reports limitations of directly attaching a VHD from a network share. The
measured approach here uses a separate Linux loop-backed raw image and does
not depend on moving the registered WSL distribution onto W:.
