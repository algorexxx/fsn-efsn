# Initial replay observation

Actual replay began at 09:46:35 UTC on 12 October 2026 after four passing
startup commands: observer build/build-info, checkpoint cold head and backup
reference. Startup verified 19,533 working-file hashes, 1,383 separate recovery
hashes and 2,085 prior evidence files. The retained executable and replay
identity match. Private network/mount namespaces, loopback DOWN and protected
read-only views are recorded in initial-observation.json.

The one-time observation at 10:36:52 UTC confirms the bounded replay process
and its expected command. Status and stdout show provisional height 6,996,128,
with no recorded failure, STOP or completion and empty stderr. The latest
allocation sample exited zero on its first attempt: 42,679,504,896 bytes,
below the unchanged 44 GiB ceiling, with no vanished entries in that sample.
The observation reads process and job records only; it does not open or hash
the live database. Its run/status hashes identify those mutable records at
observation time. LAUNCH.md remains a dated earlier startup observation.

Target remains 7,200,000. Keep Linux20/D50 GiB reserves, six-hour clean stop,
6h15 Go / 6h30 outer timeouts, 20s outer kill grace and 30s allocation samples.
Do not launch another writer or rerun unchanged passing tests while healthy.
Both cold endpoint checks and final evidence verification must pass before
adding coverage. Accepted history remains 6,900,000; F12/G1 and final release
acceptance remain open. No release selection or node runtime changed.
