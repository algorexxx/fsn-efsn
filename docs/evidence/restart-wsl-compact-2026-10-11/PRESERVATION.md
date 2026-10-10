# Prepared preservation checks; not executed

Prepared on C: while the cold archive is running. No WSL startup or database
read occurred during preparation. `preservation-check.py` reuses the previous
220 GiB expansion check and its sealed inventory/metadata helpers. The exact
adaptation is in `preservation-check.patch`; `preservation-preparation.json`
records syntax compilation, helper identity, expected inventory sizes and
verification of all 53 files in the completed replay bundle. This is preparation
evidence, not a passing Linux preservation run.

The changes update the reference to the completed 6,300,000 job, require its
13,794 working hashes and 1,383 recovery hashes in both phases, preserve the
220 GiB geometry in both phases, and add full backup/baseline content inventories.
The backup has 56,107 files; the baselines remain 3,300,000 and 3,600,000.
Each actual run has a two-hour alarm, Linux/D:/C: reserves of 20/50/5 GiB,
private network/mount namespaces, loopback down, actual database/run locks and
read-only bind views. No node executable is launched and no database is opened.
Fresh phase directories refuse accidental repeats and retain failed output.

Before any WSL startup, the Windows-side operator must verify archive completion,
dispatcher exit zero, no archive failure, all three whole-image digests equal,
the final W: archive present at the expected size and mapping, the matching
archive receipt, and the original disk still cold. Check the dispatcher and
worker have exited. Preserve and commit the closed archive evidence first.
These checks are essential because invoking WSL itself attaches the disk before
the Python worker can inspect its prerequisite records.

Only then invoke the prepared script as root inside FusionRehearsal with argument
`before`. Keep an outer read-only job timeout with cleanup grace; do not use
Python optimization, which disables assertions. Its internal alarm is 7,200
seconds. Preserve stdout, stderr and exit status separately from the generated
`before/SHA256SUMS`. Verify and commit the passing before record and manifests
before any trim or native compaction. A failure is not authorization to continue.

Full backup and baseline hashes are taken before the first storage mutation and
checked again with argument `after`. The before metadata must also match the
sealed replay. This establishes logical-file preservation across compaction;
the earlier whole-image equality establishes that W: holds the cold rollback
image. The script does not mount or read the W: image, and does not by itself
constitute an independent restoration rehearsal or filesystem repair check.

Native command qualification, any required unused-block trim, cold detach,
compaction, post-compaction storage health/geometry and the final capacity gate
remain separate steps under `spec.md`. This script cannot compact or delete.
Do not weaken replay reserves or change release selection. Keep the rollback
archive until the complete storage qualification passes.
