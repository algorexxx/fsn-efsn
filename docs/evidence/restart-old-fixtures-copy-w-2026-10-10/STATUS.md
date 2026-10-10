# Four-root copy-only job dispatched

10 October 2026, 09:45:48 UTC. A hidden dispatcher launched the finite Windows
copy-and-verify job. This uses existing W: archival permission and leaves every
local source in place. The outstanding six-folder removal question is unchanged.

Destination: `W:\FusionRestart\old-fixtures-copy-2026-10-10` on the verified
`\\192.168.1.250\mnemosyne1` share. Before dispatch, FusionRehearsal was absent
from the running-distribution list; only docker-desktop was listed. No native
efsn/replay/test/observer process was found. Fresh D: free space was
63,638,929,408 bytes; W: was 3,846,512,762,880 bytes.

Dispatcher PID 30556; copy process PID 47996. At the initial observation the
dispatcher was alive, completion.json was absent, and stdout/stderr contained
no completion or failure. This establishes launch, not successful copying.
The exact invocation is in dispatch.json. Read completion.json, copy.json,
copy-failure.json (if any), per-root manifests and logs before subsequent work.

The controller reuses the established archival checks, has no source-removal
command, and passed PowerShell parsing before launch. Its cooperative deadline
is two hours, with a 7,500-second outer process limit. D:/W: reserves remain
50/100 GiB. Partial copies and failures must be preserved. Do not duplicate this
job, start another bulk workload, hash a live database or launch replay.

On success, verify and seal its evidence before preparing the two Linux
checkpoint copies as a separate finite phase. The copy alone frees no local
space. No additional removal, VHD compaction, real signing or release selection
has been approved.
