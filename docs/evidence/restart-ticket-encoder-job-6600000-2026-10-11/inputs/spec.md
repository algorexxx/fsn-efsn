# Finite continuation from 6,300,000 to 6,600,000

Resume the verified working database for up to 300,000 additional historical
blocks with the retained replay executable and unchanged controller. The prior
6,300,000-v3 job completed successfully; use its completion and verifier records,
not the stopped-attempt path. Earlier failed jobs remain failed and preserved.

Peter reported a reboot and freed host space on 11 October. The initial host
check found about 72.3 GiB free on D:, with FusionRehearsal stopped/detached and
the W: recovery image present. The completed archive/compaction evidence remains
sealed. Require a fresh Linux and host capacity check before launch and exact
cold working/recovery inventories, source, executable, toolchain and identity
agreement before replay. The retained working allocation is 29,064,523,776 bytes.

Declare the previously proposed 34 GiB sampled ceiling (36,507,222,016 bytes),
allowing 6.932 GiB remaining growth. Starting floors are Linux >27.932 GiB and
D: >60 GiB. Keep the per-batch Linux20/D50 GiB reserves, 30-second samples,
six-hour clean stop, 6h15 Go timeout, 6h30 outer timeout and 20-second kill grace.
Sampled limits can overshoot. No in-flight limit changes or endpoint guarantee.

Use the retained replay binary, SHA256
b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245.
The separate observer changes only its endpoint literal. Private mount/network
namespaces, loopback DOWN, read-only backup/recovery views, exclusive run locks
and actual database locks remain mandatory. Both endpoint cold checks and the
automatic evidence verifier must pass before counting the new coverage.

Preserve the original backup, separate 2,400,000-v2 recovery, baselines, failed
states, W: image and sealed evidence. Advancing the working database intentionally
changes its bytes. No extra database copy, baseline rerun, W: bulk workload,
real-key signing, peers, mining, production or release-selection changes.
Review capacity and evidence value again before any subsequent finite range.
