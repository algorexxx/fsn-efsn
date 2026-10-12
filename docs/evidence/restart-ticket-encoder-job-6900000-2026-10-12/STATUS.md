# Initial replay observation

The hidden dispatcher launched at 05:46:03 UTC on 12 October 2026 from commit
`4736c9a8867d58657b59ac990c1ea721410a04f0`. Actual replay began at
2026-10-12T05:53:35.234356+00:00; this observation was recorded at 2026-10-12T05:53:40.414222+00:00.
The separate observer build/build-info, cold start at 6,600,000 and backup
reference check all exited zero before the working database resumed.

Startup verifies 16,672 working-file hashes,
1,383 recovery hashes and 1,941
prior evidence files. Replay identity and retained executable match. Private
network/mount namespaces, loopback DOWN and read-only protected views are
recorded. The first allocation sample is successful; no failure/stop is present.
The observer reads only process and job records, never hashes the live LevelDB.

Target: 6,900,000, up to 300,000 new blocks. Keep the 39 GiB sampled allocation
ceiling, Linux20/D50 GiB reserves and six-hour/6h15/6h30 stop limits. Actual
completion and both cold checks must pass final evidence verification. Coverage
remains separately verified through 6,600,000, with 8,530,080 blocks still not
counted to the backup tip. No release or chain-runtime selection changed.
