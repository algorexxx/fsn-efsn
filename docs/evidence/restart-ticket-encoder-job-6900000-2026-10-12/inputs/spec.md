# Finite continuation from 6,600,000 to 6,900,000

Resume the verified working database for at most 300,000 further historical
blocks. The original 6,600,000 job completed replay and cold checks but failed
automatic evidence verification solely on patch filename labels. Preserve that
failure; pin its separately verified follow-up in config.json and enforce the
qualified controller gate. Do not use the stopped-attempt path or rewrite any
old input, failure, manifest or observation.

Peter approved expansion to 230 GiB; its preservation and storage checks pass.
The 39 GiB sampled allocation ceiling (41,875,931,136 bytes) allows 6.415 GiB
growth from the closed 34,987,921,408-byte working database. Starting capacity
must exceed Linux 27.415 GiB and D: 60 GiB. Keep Linux20/D50 GiB reserves,
30-second sampling, six-hour clean stop, 6h15 Go timeout, 6h30 outer timeout and
20-second kill grace. Sampled limits may overshoot; no endpoint guarantee or
in-flight limit change. Review actual resources and value before a later job.

Retained replay executable SHA256:
b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245.
Only the separate observer height changes; canonical a/b patch labels are
checked before replay. Verify source, toolchain, executable, working/recovery
hashes, preserved metadata and replay identity first. Require private mount
and network namespaces, loopback DOWN, read-only backup/recovery mounts,
exclusive run locks and actual database locks. Both cold endpoint checks and
the final evidence verifier must pass to count any new completed coverage.

Preserve original backup, 2,400,000-v2 recovery, baselines, failed runs, W: image
and sealed evidence. No extra database copy, baseline rerun, W: bulk workload,
real-key signing, peers, public mining, production or release-selection change.
