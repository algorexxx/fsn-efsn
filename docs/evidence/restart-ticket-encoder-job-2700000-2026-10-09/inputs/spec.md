# Finite candidate replay: 2,400,000 to 2,700,000

Declared 9 October 2026. This is a candidate qualification job, not a release
selection. It crosses the legacy checkpoint boundary at 2,680,000. Success
requires the retained replay executable to execute every intervening block,
followed by both cold endpoint checks and independent evidence verification.

The authoritative interval, paths and allowances are in [config.json](config.json).
The clean-stop budget is four hours of replay execution; the Go timeout is
4h15m and the external timeout 4h30m, plus a 20-second kill grace.
Preparation, cold inspection and evidence capture add time outside that replay
budget. Each Go preparatory/cold command is separately bounded. The sampled
working-target allocation limit is 8 GiB, with 30-second sampling and the
previous helper's three bounded measurement attempts. This is a stop threshold,
not an exact allocation ceiling. The retained Go test checks Linux 20 GiB / D:
50 GiB reserves before every 128-block batch. Initial floors remain 30/60 GiB.

The first job makes one verified copy of the completed 2,400,000 checkpoint.
The recovery checkpoint, original backup and original sealed stopped attempt
remain untouched. Later jobs may reuse the working database only after this
job passes, its output bundle is sealed, all its cold file hashes match and a
separate recovery checkpoint remains preserved. The current job has no
automatic continuation or retry. A stopped/failed target needs separate cold
inspection and disposition; it cannot be silently reused as a passed checkpoint.
The first job exercises copy mode; in-place resume has not yet been qualified
by a complete production-data run.

Runtime execution uses the unchanged retained executable SHA256
b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245,
unchanged candidate/selected source inventories and the sealed helper.
Only the separate observer's endpoint literal changes. Its build occurs
offline with cached dependencies. The job runs as rehearsal under a root-created
private mount/network namespace with read-only backup, checkpoint and recovery
views. No peer connections, mining, wallet keys or network services are used.

The inputs/SHA256SUMS manifest seals immutable inputs before launch. Do not
change inputs during execution. Do not edit this bundle after launch: the
launcher owns its qualification, verification and completion files and writes
both output-only and complete-bundle manifests at the end. Prior evidence
remains byte-preserved. Runtime status is provisional until completion.json
says verified_pass is true. The verifier checks the interval, identity, full
endpoint/header/receipt/TD observations, tickets, cold file preservation, all
seven command outcomes, source/backup preservation and declared limits.
A nonzero command or STOP cannot count as a pass.

A hidden Windows Python dispatcher holds the WSL invocation open independently
of the initiating shell. Host dispatch logs go outside this immutable input
bundle under repo tmp/replay-job-2700000-2026-10-09. It cannot survive a host
shutdown/reboot and does not disable sleep. There is no scheduler, automatic
notification, recurring job or automatic second range.

To observe, read /home/rehearsal/results/<job>/status.json and the tail of
replay.stdout.txt. To request an early clean stop, exclusively create
/home/rehearsal/results/<job>/STOP with an explanatory text, as rehearsal,
then let the process perform normal cleanup. Do not remove that marker or
resume the stopped directory automatically. Never hash/open the working LevelDB
through another writer while replay is active.
