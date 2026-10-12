# Continuation dispatched after verified recovery

Launched at 06:49:35 UTC on 12 October 2026 from commit
`b256ae6b1f89926f0d9a580bf3533ea0730e9527`, using committed inputs and the
passing 06:47 UTC preflight. The hidden dispatcher and WSL child are recorded.
At 06:51:20 UTC startup was active with no recorded failure, STOP or completion.
The workflow phase is named replay, but replay_pid is still null: actual block
replay has not yet been established by this observation. Startup includes cold
inventories, observer preparation and the backup reference before writing.

Accepted history remains 6,623,296. The next observation should use the prepared
initial-observation.py only after replay_started and a size measurement exist;
do not hash the live database. On completion verify both cold endpoint checks,
closed allocation and all evidence before counting coverage. The original failed
job remains sealed. Range, 39 GiB sampled ceiling, reserves and time limits are
unchanged; the new scanner handles recognized file disappearance only.
