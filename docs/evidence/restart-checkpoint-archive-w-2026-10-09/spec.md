# Archive closed candidate checkpoints to W:

Declared 9 October 2026, before copying. User explicitly selected W: after
the completed 2,200,000 replay left Linux below the 30 GiB starting floor.
This is a storage relocation only; no replay or node is started.

Archive exactly candidate-ticket-encoding-{100000,300000,600000,900000,
1200000,1400000,1600000,1800000} from /home/rehearsal/replay to
W:/FusionRestart/checkpoint-archive-2026-10-09. W: was verified as
\\192.168.1.250\mnemosyne1 and mounted at /mnt/w using drvfs. It currently has
3,867,974,118,400 bytes available. Existing FusionRestart content is not present
on this share; this run does not confirm continued availability of the older
September restore rehearsal described in historical reports.

The eight closed targets occupy 9,504,686,080 allocated bytes (about 8.85 GiB).
Keep both latest targets, 2,000,000 and 2,200,000, on Linux ext4. Do not touch
the original backup, baseline replays, retained binaries, source trees or
sealed evidence bundles. Keep current replay identity checks and disk reserves.

1. Reuse streaming digest, JSON writing and space-check helpers from
   tests/restart/snapshot_package.py. Its flat-LevelDB package format excludes
   replay-identity.json, so use a bounded directory copy rather than modifying
   that format. Record the helper and archival script hashes.
2. Hold exclusive run locks and actual LevelDB LOCK flocks for all ten targets.
   Refuse unexpected paths, symlinks, nested directories or names outside the
   existing LevelDB allowlist plus replay-identity.json.
3. Obtain expected file hashes from each prior sealed cold-check inventory,
   checking its evidence manifest. Hash both retained targets before/after.
4. Copy each older checkpoint into a new .incomplete directory on W:, flushing
   files. Compare source bytes and reread every destination against the prior
   expected hashes; require exact file sets and sizes. Preserve Linux mode and
   mtime information in external metadata. Rename only a verified copy to its
   final archive directory, retaining a per-checkpoint manifest.
5. Stop and preserve all output on any failure. No overwrite or automatic retry.
   Require at least 100 GiB free on W: plus copy size, and retain 20/50 GiB
   Linux/D: reserves during archival.
6. Run a separate retirement phase only after archive completion is reviewed.
   Reacquire all locks, rehash every archive and source, confirm both manifests
   and exact resolved paths, then remove only the eight verified local copies.
   Each source is flat: unlink individually validated files and remove its
   now-empty directory; no recursive deletion or cross-shell enumeration.
   Record each removal and verify absence. Recheck the two retained targets
   and record final free space. Preserve W: copies and evidence.

These checks establish byte-preserving relocation as observed through the
filesystem. They do not prove NAS power-loss durability or cache bypass.
Do not start the archived database directly on SMB. Restore to a fresh Linux
ext4 directory, copy only the manifest-listed files, verify their complete
hash inventory and replay identity, restore recorded permissions, then perform
the existing read-only cold checks before using a restored checkpoint.

Acceptance: all eight archives match the previously recorded file hashes,
local copies are removed only after separate revalidation, both retained
checkpoints are byte-identical, and Linux/D: again exceed the unchanged
30/60 GiB starting requirements. Record any partial result explicitly.
