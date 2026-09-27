# Observer block backfill evidence

Baseline `4edd015`. The [report](../../restart-observer-backfill.md) describes
behavior and limits. Only the external observer and tests change; no node runtime
patch, chain backup, real key, public transaction or notification is involved.

`run-windows.ps1` runs both observer packages and builds the command with offline
Go 1.21.3. `run-linux.sh attempt-N` is invoked through
`wsl -d FusionRehearsal -u root -- unshare --net -- bash <absolute-script> attempt-N`.
It enables only loopback, runs package race tests, builds the service-test and
observer binaries with race detection, and runs the compact actual-service test.
Each script refuses to overwrite its evidence directory/log. Empty build logs
mean successful builds with no compiler output.

Windows and Linux each passed 78 test/subtest results. Linux attempt 1 passed the
service rehearsal in 25.99 seconds with race detection, including clean exits of
both child services. All 18 command state comparisons passed. The 713 input
hashes and deterministic platform exports match; see [checks.json](checks.json).

The retained fixture test uses four actual-service block RLPs and associated
receipts from the prior rehearsal. Its five-event exported sequence is explicitly
synthetic: local branch, replacement partial prefix, resumed completion, manual
review, then a shorter competing branch that reopens the same incident. Platform
exports use fixed times and should match byte for byte. Fault variants do not
claim corresponding real chain execution.

The Linux service extension is enabled by `FUSION_RESTART_OBSERVER_BACKFILL=1`.
It adds history initialization, snapshots, IPC/HTTP bounded backfills, replacement
branch collection, export and endpoint-loss checks to the existing eight-snapshot
rehearsal. It launches actual isolated node services with public test keys 1 and 2,
and compares head/flags/signatures/nonce/controller record/pool before and after
each observer command. The harness controls synchronization and the existing
synthetic queued-transaction submission; the observer remains read-only to nodes.
Every CLI invocation is a separate process reopening the same temporary history.
Database directories are temporary; original/replacement blocks and JSON export
remain in the evidence. Ordinary live mining is not exercised by this test.
The harness names its export `history-export.json`; that particular file contains
JSON Lines (metadata followed by events), matching the command's export format.

`inputs.sha256.json` pins source, module and retained fixture identities. Linux
attempt directories additionally contain full test-harness source/build identities,
network/capacity snapshots, all command outputs, before/after states and process
results. `verify.py` verifies these records and writes `checks.json`; built binaries
remain in ignored `tmp/restart-observer-backfill`.
