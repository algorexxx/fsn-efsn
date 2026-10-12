# Copy verified 7,170,976 checkpoint to a separate W-backed Linux image

12 October 2026. Implements the bounded storage step after the user requested
W: and the direct-path and loop-image feasibility checks were completed.
This job performs no chain replay, production activation, real-key access,
network peer contact, deletion, D: resize or release change.

- Source: `/home/rehearsal/replay/candidate-ticket-encoding-working`.
- Destination: new
  `W:/FusionRestart/replay-work-7170976-2026-10-12/replay.ext4`, 512 GiB virtual
  maximum, containing `/checkpoint`. Keep all local and archived originals.
- Required sealed source: `restart-ticket-encoder-stopped-7170976-2026-10-12`,
  root SHA-256 `d7bad96b8fbe3f0b30f7aee4878e205d314cf1bcdb350440c92e2337c2baefcf`.
- Preserve exact 22,501-file inventory. Hash source bytes as copied, fsync each
  new file, check original metadata unchanged, cleanly unmount/check/detach,
  then reattach read-only and hash every destination file against that sealed
  inventory. Preserve modes and modification times.
- Use existing `snapshot_package.py` digest/filename/JSON helpers at recorded
  hash. Copy logic follows the existing archival stream-with-hash procedure,
  with periodic resource checks and a dedicated image destination.
- Run the already-built, hash-verified cold-head and cold-details observers
  after reattachment. Require exact equality with the sealed endpoint,
  including header/RLP, commitments, TD, receipt/transaction counts and 5,031
  tickets. Check destination metadata and executable hashes afterward.

Before image creation, verify the W: mapping, private mount/network namespaces,
only loopback down, source run/database locks and no matching replay process.
Use a read-only source bind mount. Require an absent destination and verify
loop-device identity before formatting that new image only. One image owner
holds a local migration lock for the whole operation. No reuse or automatic
retry of partial output. Existing backup, separate recovery and baseline data
are not opened by this copy job.

Linux/D:/W: running reserves remain 20/50/100 GiB. Startup requires W: more than
612 GiB to allow even the image's entire virtual ceiling plus reserve; actual
allocation should be sparse but is not assumed for capacity safety. The D:
60 GiB writer-start gate applied to D:-growing replay; this W:-only copy retains
the 50 GiB D: reserve and creates only small local logs. The WSL VHD stays at
230 GiB. Default ext4 data ordering/journal remain; no sync bypass. Format
uses 1,048,576 inodes, no reserved-root fraction, eager metadata/journal init.

Outer lifetime is 18,000 seconds plus 20 seconds kill grace. Each worker phase
has a 12,600-second cooperative deadline and a 12,720-second external limit;
the shared outer lifetime takes precedence. Format/e2fsck each cap at 1,200
seconds. Observer limits are five minutes each (four minutes internal).
Update compact resource/progress records every 30 seconds during file loops.
Retain failures and partial files; never mark a killed job verified.

A passing `migration.json` is provisional until `cleanup.json`, `completion.json`
and the host completion show clean termination. Review and seal all evidence
after completion, before adapting the replay writer. A separate bounded replay
trial is still required for throughput/stop-controller acceptance. No replay
launch is automatic in this job. SMB/server power-loss durability is unproven;
the local verified fallback remains available.
