# Reclaiming older D: test directories through verified W: archival

9 October 2026. **Completed and verified.** Prepared following the user's request to reclaim storage from
previous tests. The completed 3,600,000 replay is preserved; no replay writer is
running during this operation.

The exact ten older September test roots are the allowlist in `archive.ps1`.
They are stored directly under `D:\FusionRehearsal`, outside the Linux VHDX.
Together they occupy about 11.5 GiB of logical file bytes. Relocation therefore
returns host D: space without Linux disk compaction. These are retained test
fixtures, not the original backup or the active historical replay database.

The destination is a fresh `W:\FusionRestart\old-tests-archive-v2-2026-10-09`
directory on the verified existing share. Copy and removal are separate phases.
The copy phase records all paths, sizes, modification times, attributes and
SHA256 digests; flushes and rereads archive files; and rechecks source hashes.
The removal phase independently verifies the complete source and archive again
before removing only individually validated files from the exact allowlisted
source directories. Existing archive destinations and records are never reused.
Two-hour per-phase limits and 50 GiB D: / 100 GiB W: reserves remain enabled.

FusionRehearsal must be stopped, native node/test processes absent, and database
LOCK files held against write access during verification. Docker is unaffected.
No LevelDB is opened. Sealed repository evidence is verified and retained.
Backup, Linux baselines, executable/source identities, stopped historical replay
attempts and the verified 2,400,000 recovery checkpoint remain in their existing
locations. Every included diagnostic/failure artifact within these ten fixture
roots moves intact with its root; none is discarded.

The archived fixture hash inventory describes the bytes found during this cold
relocation. It does not claim that every database byte had an independently
sealed September checksum. The earlier evidence manifests retain their original
meaning and their historical D: paths; this record supplies the relocation map.

To reuse a fixture, verify `copy.json` against this bundle's final manifest and
its W: copy, then copy its complete inventory to a fresh local test directory.
Require every recorded SHA256/size and restore file metadata before running the
original fixture's cold checks. Do not operate LevelDB directly on W:.

Both phases and final verification are complete. All ten D: fixture roots are
absent; all 9,134 archive file paths/sizes match their fully rechecked hashes.
Other D: root names remain unchanged. Final D: free space is 65.787 GiB, an
observed increase of 11.517 GiB. This is sufficient for the unchanged 60 GiB
replay starting floor; fresh preflight also passes the Linux requirement.

The first attempt failed while validating the newly created empty archive root,
before any fixture copy/removal: a parent DirectoryInfo lacks PowerShell PSIsContainer
adaptation under strict mode. This version uses an explicit .NET directory type
check and a new destination. The first attempt is preserved.

The original v2 copy passed all ten complete directory comparisons, then failed
in its aggregate Bytes calculation before writing copy.json. The failure and
console log are preserved; no local data was removed. recover-copy.ps1 does no
bulk copying: it independently rereads each source and archive, saves per-folder
hash manifests immediately and writes a completed copy.json only after all ten
pass. Its explicit byte sum must equal the separately measured 12,382,043,962.
retire.ps1 uses the same corrected summation and authenticates this recovery
script. verify.ps1 independently totals the manifests again. The extra readback
is necessary to recover the inventory lost from the failed process; the fixture
bytes are neither discarded nor recopied.

## Verified copy inventory

The recovered copy record completed at 2026-10-09T16:00:04.4047459Z and independently
matches the initially measured 9,134 files / 12,382,043,962 bytes (11.532 GiB).
Each root keeps its name under the new W: archive.

| Fixture root | Files | Logical GiB |
| --- | ---: | ---: |
| autobuy-rebroadcast-2026-09-27 | 1035 | 1.605 |
| recovered-buyer-restart-2026-09-27 | 912 | 1.104 |
| abandonment-repair-2026-09-27 | 987 | 1.103 |
| funded-gap-2026-09-27 | 978 | 1.103 |
| equal-weight-pause-2026-09-27 | 959 | 1.103 |
| stale-intent-ordered-2026-09-27 | 862 | 1.103 |
| equal-weight-fresh-2026-09-27 | 867 | 1.103 |
| live-funded-partition-2026-09-27 | 900 | 1.103 |
| expired-nonce-neutralization-2026-09-27 | 810 | 1.102 |
| paused-purchases-2026-09-27 | 824 | 1.102 |

The initial transfer and its reporting failure remain recorded separately.
Checks establish filesystem-observed bytes, not independent NAS power-loss
durability. No fixture was opened as a database on W:.

The first final check refused a changed VHD LastWriteTime despite identical
container length; the observation is preserved and its cause is not established.
A container timestamp is not a database identity check. A bounded offline
follow-up verifies actual working/recovery hashes and backup/baseline metadata
against the sealed 3,600,000 result before replay can resume. Its first invocation
stopped before database checks because /sys/class/net still reflected the
existing sysfs mount's interfaces. The corrected observer uses namespace-aware
ip -j link show and requires only loopback, down. Both inputs/logs are retained.

## Final disposition

[Verification](verification.json) passes after the scoped protected-state check.
All 3,514 working and 1,383 recovery database file hashes match sealed prior
inventories. Backup metadata (56,107 files), both baseline metadata inventories,
retained source inventories and replay executable identity also match. This
does not claim a fresh full-content hash of the 117 GB backup.

The VHD timestamp discrepancy remains recorded with unknown cause. The actual
protected-file checks replace that inadequate container-level proxy; no claim
is made that the VHD file itself stayed byte-identical. The archival scripts
never moved, deleted or compacted it. The unrelated initial archive guard and
summary failures and the refused sysfs observer attempt are preserved.

The fresh 16:09:21 UTC capacity preflight passes at 25.805 GiB Linux / 65.787 GiB
D: free. Replay may resume under its existing bounded, offline policy. This
operation authorizes no further general cleanup and changes no release input.
