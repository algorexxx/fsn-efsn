# Finite continuation from 6,623,296 to 6,900,000

Resume only the separately cold-verified stopped checkpoint. Preserve the
original failed job/STOP and all sealed evidence; the stopped-attempt gate ties
this new job to its exact inspected state. The retained replay executable is
b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245.
Only the observer height changes, with canonical patch labels checked early.

Complete at most the remaining 276,704 blocks of the original intended range.
Keep the original job's 39 GiB sampled ceiling, six-hour clean stop, 6h15 Go
timeout, 6h30 outer timeout, 20-second kill grace, Linux20/D50 GiB per-batch
reserves and 30-second allocation samples. The cold allocation is
35,399,045,120 bytes; growth allowance is about 6.032 GiB. Require Linux
>27.032 GiB and D: >60 GiB at a fresh preflight and again at startup.

The qualified live allocation scanner handles disappearing recognized LevelDB
files as observed metadata churn, recording every disappearance. Genuine errors
still stop after three bounded attempts; each worker remains limited to 15s
plus 2s kill grace. Closed allocation remains GNU du. This is sampled accounting,
not a hard quota, and no endpoint completion is guaranteed by the limit.

Require private mount/network namespaces, loopback DOWN, read-only protected
views, exclusive run/actual database locks, exact cold working/recovery hashes,
source/toolchain/executable/replay identity and prior evidence checks. Both
endpoint cold checks and final evidence verification must pass before coverage
is accepted. Preserve original backup, 2,400,000-v2 recovery, baselines, failed
runs and W: image. No additional database copy, public peers/mining, real keys,
production activation, release-selection change or blanket passing-test rerun.
Review capacity and evidence value before any subsequent finite range.
