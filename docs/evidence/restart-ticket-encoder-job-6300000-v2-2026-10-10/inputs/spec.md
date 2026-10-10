# Finite replay from verified stopped state: 5,600,032 to 6,300,000

Advance the same working DB in place through up to 699,968 additional historical
blocks. Require verified completion of the approved 220 GiB WSL expansion and
fresh capacity. Keep the failed 6,300,000 attempt, original STOP and sealed logs;
its separate cold inspection qualifies the actual 5,600,032 starting checkpoint.

Use exactly the retained replay executable and unchanged tested controllers.
The observer differs from the prior inspection only by its endpoint literal;
its source matches the previous 6,300,000 observer. Require all twelve inspection
preservation checks, complete cold working/recovery hashes, exact endpoint,
source/toolchain/bin and replay identity. Preserve the separate 2,400,000-v2
recovery checkpoint. No extra full database copy or unchanged baseline rerun.

Declare a new sampled target ceiling of 26 GiB (27,917,287,424 bytes), allowing
about 10.972 GiB growth from the 15.028 GiB working checkpoint. Require Linux free
above 21 GiB plus remaining growth and D: above max(60 GiB, 51 GiB plus growth).
Retain per-batch Linux20/D50 GiB reserves, 30-second samples, six-hour clean stop,
Go timeout6h15 and outer6h30 plus20s grace. Sampled limits may overshoot; growth
is not guaranteed linear. Fresh capacity may refuse launch. This is not a full
history storage forecast or authorization to alter limits during a run.

Private mount/network namespaces, loopback DOWN, read-only backup/recovery views,
exclusive run locks and actual database locks remain required. Do not hash a live
LevelDB or launch a duplicate writer. Preserve the original backup, baselines,
failed states, all sealed evidence and the verified separate recovery. Require
both cold checks and independent evidence verification after replay. No real
keys, public mining/contact, production activation or release selection change.
Review results, capacity and value before another finite continuation.
