# Finite replay: 4,500,000 to 5,400,000

Continue the verified working database in place with the exact retained replay
binary and controller. Observer bytes change only the endpoint literal. Preserve
the separate verified 2,400,000 recovery checkpoint, earlier failed/stopped runs,
original backup, baselines and sealed evidence. No additional database copy.

Keep the existing six-hour clean-stop request, 6h15m Go timeout, 6h30m outer timeout
plus 20-second kill grace, 11 GiB sampled allocation ceiling and 30-second sampling.
Starting allocation is 8.295 GiB; the last 900,000 blocks added about 1.24 GiB.
The remaining ceiling allowance is 2.70 GiB, not a guarantee about future growth.
Fresh starting floors account for remaining growth plus margin; each batch still
requires 20/50 GiB Linux/D: reserve. Refuse inadequate capacity or identity checks.

Require prior completion/verification, exact cold starting inventory, original
source/toolchain/executable identity and read-only starting head agreement.
Use the existing private mount/network launcher, loopback down and read-only
backup/recovery mounts. Two endpoint cold checks and all preservation checks
must pass before another continuation. No public contact, real keys, mining or
release selection change. Do not extend the unchanged baseline without a
specific diagnostic need. Candidate history after 4,500,000 remains unverified.
