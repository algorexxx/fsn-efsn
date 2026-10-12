# Approved expansion from 220 to 230 GiB

Peter explicitly selected "Expand to 230 GiB and continue" on 12 October 2026.
Only FusionRehearsal at D:/FusionRehearsal/Ubuntu/ext4.vhdx is in scope.
Retain the verified W: image, backup, working state and separate recovery.
No compaction, deletion, pruning, production use or release change is authorized.

Reuse the prior native WSL procedure. Before and after, require private network
and mount namespaces, loopback DOWN, readonly database views, actual DB and run
locks, exact 16,672 working and 1,383 recovery hashes, protected backup/baseline
metadata and unchanged source/executable/toolchain. These checks use the sealed
6,600,000 run plus its explicit successful evidence follow-up; the original
automatic-verifier failure is preserved. Check actual 220/230 GiB geometry and
unchanged Linux20/D50 GiB reserves. Bound each check to 20 minutes plus 20-second
kill grace; no hashing while a writer is active.

The supported resize first stops this distro only. If its VHD stays attached,
the already-qualified fallback may briefly stop only an idle Docker/WSL backend
after proving no unrelated workload is active, and then restore the service.
Preserve failures; never blindly retry a storage rewrite. Independently review
actual post-expansion geometry, filesystem health and capacity before replay.

The next 300,000-block range is still gated on explicit separate-verification
provenance support and fresh capacity. No previous completion is rewritten.
