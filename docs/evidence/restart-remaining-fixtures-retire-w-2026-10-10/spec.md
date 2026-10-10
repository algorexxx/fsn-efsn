# Authorized retirement after verified archival

Peter explicitly authorized archiving necessary folders and removing obsolete
copies. Retire only the 14 D:\FusionRehearsal roots in proposal.json after
restart-remaining-fixtures-copy-w-2026-10-10 has completed, independently verified
and sealed. This is not a deletion of failed-run evidence: every file remains in
the verified W: archive and every existing repository evidence bundle remains.

Reuse the previous retirement worker with the recorded patch. Reverify complete
source and archive bytes under database locks, validate exact absolute paths and
reparse entries, then remove only the inventoried files and empty directories.
Record actual absence, preserved other roots, unchanged VHD metadata and actual
free-space gain. Preserve partial failure rather than retrying automatically.

Bounds: two hours cooperative, 7,500 seconds external; C: >=5 GiB and W: >=100 GiB
for output records. This reclaim-only worker does not require D: to be above its
replay reserve before it can free D: space. No database opens, VHD resize/compact,
network peers or replay guard changes. FusionRehearsal must stay stopped.
