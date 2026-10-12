# Bounded continuation dispatched

Launched at 2026-10-12T09:40:14.769452+00:00 from committed preparation
`c77429d7a23c7b332db987be2f6a61aff0eda66f`. The hidden Windows dispatcher and WSL child
are recorded in launch.json and dispatch.json. The fresh preflight passed;
the startup capacity gate also passed with Linux/D: reserves intact.

The observation at 2026-10-12T09:41:10.234341+00:00 records an active startup
without failure, STOP or completion. replay_pid is still null: actual block
replay is not established by this observation. Startup must finish the cold
inventory, provenance, observer and backup-reference checks before writing.
Use initial-observation.py once replay_started and a size sample exist.

Accepted history remains 6,900,000. Target 7,200,000, 44 GiB sampled ceiling,
Linux20/D50 GiB running reserves and all finite stop limits remain fixed.
Both cold endpoint checks and automatic evidence verification are required
before accepting new coverage. Do not hash a live database or start a duplicate
writer. The previous job's verified evidence and failed ancestors remain intact.
