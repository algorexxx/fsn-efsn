# Closed checkpoint archival to W:

9 October 2026. **Completed and verified.** Eight older candidate checkpoints
were relocated to W:/FusionRestart/checkpoint-archive-2026-10-09 on the verified
network share `\\192.168.1.250\mnemosyne1`. Their **4,051 files / 9,496,804,367
logical bytes** match the previously sealed cold-check inventories.

The separate revalidation/removal phase passed, reclaiming about **8.85 GiB**
inside Linux. Final recorded free space is **38.74 GiB Linux / 66.97 GiB D:**
and about **3.51 TiB on W:**. Both unchanged 30/60 GiB replay starting floors
are met. No historical replay ran in this operation; the candidate remains
verified through 2,200,000 and unselected for release.

## Retained layout

| Candidate checkpoint | Files | Current location |
| --- | ---: | --- |
| 100,000 | 85 | W: archive |
| 300,000 | 161 | W: archive |
| 600,000 | 297 | W: archive |
| 900,000 | 436 | W: archive |
| 1,200,000 | 586 | W: archive |
| 1,400,000 | 743 | W: archive |
| 1,600,000 | 802 | W: archive |
| 1,800,000 | 941 | W: archive |
| 2,000,000 | 1,004 | Original Linux ext4 directory |
| 2,200,000 | 1,157 | Original Linux ext4 directory |

Each archived directory retains its original candidate-ticket-encoding-HEIGHT
name. External HEIGHT.manifest.json files record the exact hashes, original
file sizes, mtimes, permissions and source evidence. The authoritative aggregate
[archive manifest](archive.json) is also copied to W:. SHA256:

`d7f0ba9a64611fbf29fb92d8826f3485c4a603e4ec6b1b7f9b07801e3aec3f6f`

The original Linux directories for these eight older checkpoints are now
absent. Their sibling run-lock files remain. Earlier sealed replay reports keep
their original historical paths; use this relocation record to locate the data.
The backup, both baseline targets and retained binaries/source trees were not
relocated. The two latest candidate targets pass complete before/after hash
checks, and the final filesystem check confirms their presence alongside the
backup and baselines.

## Validation and provenance

The [declared specification](spec.md) fixes the eight source paths and the new
destination. The [first attempt](../restart-checkpoint-archive-w-2026-10-09/README.md)
refused a missing W: mount before any checkpoint copy or removal. Its evidence
remains intact. This corrected launcher holds a verified drvfs mount inside a
private mount namespace for each operation and runs the copy as rehearsal.
No permanent mount setting was installed.

The copy phase ran from 05:50:22 to 06:18:18 UTC; the separate revalidation and
local-copy removal ran from 06:18:50 to 06:30:13 UTC. Both commands exited zero
with empty stderr. Each phase held all ten checkpoint run locks and actual
LevelDB LOCK flocks. Expected hashes came from the previous sealed inventories.
Copies were flushed, fully reread and checked before their .incomplete names
were removed. The second phase rehashed every archived and source file before
removing individually validated files from the eight exact local directories.

[Evidence verification](verification.json) and the independent
[final Windows/WSL check](final-state-verification.json) pass. Windows confirms
the share mapping, exact eight archive names/counts and matching aggregate
manifest copies; WSL confirms the archived local directories are absent,
the protected paths remain present and both free-space floors pass.
Raw commands, logs, manifests and [final state](final-state.json) are retained.

These checks establish filesystem-observed byte preservation. They do not
prove NAS power-loss durability or that readback bypassed caches. No node was
opened directly on the network share.

## Restoring an archived checkpoint

1. Verify the aggregate manifest against the SHA256 above and select the exact
   checkpoint entry. Verify the corresponding per-checkpoint manifest on W:.
2. Copy only that entry's files to a new Linux ext4 directory; refuse existing
   targets, unexpected names, symlinks, nested directories and changed bytes.
3. Require the exact complete SHA256 inventory and file sizes from the manifest,
   including replay-identity.json. Restore the recorded permissions and mtimes
   with the directory owned by the rehearsal user and mode 0700.
4. Run the existing read-only exact-height cold checks with the retained original
   replay executable and height-specific observer before resuming any work.
   Keep W: archived bytes unchanged and all executable/source/config identity
   checks enabled. The network copy itself is not an active replay database.

No restore was needed or performed here. The 2,200,000 checkpoint remains local
for the next bounded replay through 2,400,000, after fresh path/capacity checks.

## Separate preservation follow-up

The September restore rehearsal's previously documented
W:/FusionRestart/restore-rehearsal-2026-09-24 was not present when W: was inspected
before this copy; the share root was empty. This run does not establish why,
or prove loss of copies elsewhere. Its historical report remains unchanged.
Locate or re-establish that separate preserved package before closing G1's
backup/preservation gate. The original local backup is still present.
