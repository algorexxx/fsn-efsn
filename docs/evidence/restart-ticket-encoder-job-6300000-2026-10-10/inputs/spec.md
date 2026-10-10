# Finite replay from verified stopped state: 5,331,360 to 6,300,000

Advance the same working DB in place through up to 968,640 additional historical
blocks. This provides new encoder-candidate history; no unchanged baseline rerun
or extra full DB copy. The failed 5,400,000 attempt remains incomplete, with its
STOP, logs and sealed evidence intact. The separate cold inspection qualifies
the actual 5,331,360 starting state. F12/G1 and release selection remain open.

Require successful cold inspection, its exact endpoint, 12 preservation checks,
complete cold file inventory, replay identity and retained source/toolchain/bin.
The controller explicitly distinguishes stopped-checkpoint evidence from a
successful replay and preserves a copy/hash of the original STOP. Its added
refusal checks are independently tested. Database LOCK read locks guard hashing;
release the working lock only before its replay writer opens the database.

A fresh 15 GiB sampled allocation ceiling allows about 3.984 GiB growth from
11.016 GiB. The previous 11 GiB ceiling is unchanged in its old job. Reclaim only
the six authorized obsolete local copies after verified W: archival, then require
fresh capacity: Linux >21 GiB plus remaining growth; D: >max(60 GiB,51 GiB plus
growth). Batch reserves stay Linux20/D50 GiB. Growth is not guaranteed linear.
The 968,640-block endpoint is a finite useful range, not a claim that all history
will fit. Sampling 30s; clean stop6h; Go timeout6h15; outer6h30 plus20s kill grace.

Private mount/network namespaces, loopback DOWN, read-only backup/recovery views,
exclusive run locks and retained executable identity remain required. Preserve
2,400,000-v2 recovery, earlier stopped attempt, baselines, original backup and all
sealed evidence. After replay, require two cold checks, all preservation checks
and independent evidence verification. No public contact, real keys, mining,
production activation or release-input changes. Review capacity and value again
before another finite job; do not chain unbounded replay or cleanup.
