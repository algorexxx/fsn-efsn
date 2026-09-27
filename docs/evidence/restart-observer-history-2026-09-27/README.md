# Observer history evidence

Baseline: `b13c92c`. See the [history report](../../restart-observer-history.md)
for behavior, commands and remaining release gates. This change extends only the
external observer command and its internal package; node runtime and P1–P15 are
unchanged.

`run-windows.ps1` runs the collector/CLI suites and builds the command using the
local offline Go 1.21.3 runtime. `run-linux.sh` was invoked through
`wsl -d FusionRehearsal -u root -- unshare --net -- bash <absolute-script-path>`.
It enables only loopback and runs both packages with race detection, then builds
the command as the `rehearsal` user. Both scripts refuse existing test evidence.
Empty build logs indicate successful builds with no compiler output.

The passing suites include history replay, review, scope/budget/locking guards,
corrupt-record rejection, abrupt process exit after a synchronous write and CLI
operations. This is not a power-loss or interrupted-write durability test.

`inputs.sha256.json` pins 590 source/module/retained input files. The transition
test consumes actual IPC observer reports from the previous service rehearsal,
retimes them explicitly, and constructs controlled recurrence/unknown-coverage
variants. This run does not start new node services or claim a live chain
followed that sequence. It uses only retained synthetic public-test-key data.
No chain database, large backup, D:/W: restore, real key or notification is used.

Each platform exports the same nine-event history: seven snapshot reports and
two operator reviews. The sequence demonstrates repeated fork deduplication,
acknowledgement surviving reopen, convergence displacing a purchase receipt,
explicit receipt-incident resolution, unknown coverage, recurrence reopening the
same incident, and removal of tracking leaving it open with unknown observation.
The original signed bytes/reports remain in the JSON Lines export. Final status
is reconstructed; the exported status JSON is test evidence, not a database
cache. These deterministic exports are byte-identical across platforms.

`verify.py` checks input identities, passing logs, matching exports and the
retained review/recurrence sequence, then writes `checks.json`. It also records
binary hashes when the ignored `tmp/restart-observer-history` artifacts exist;
the Linux binary hash is independently retained in `linux-binary.sha256`.
Source hashes apply to this revision, not later observer changes. Run the script
with Python from any directory. Reproducing tests requires fresh evidence output
locations and the documented offline runtimes/dependency caches.

Complete block backfill, history-enabled live mining/reorganization tests,
representative storage/load validation and deployed notification/heartbeat
delivery remain separate work.
