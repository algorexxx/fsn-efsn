# Actual efsn telemetry evidence

Accepted run: **attempt-3**, 3 October 2026. Dashboard commit
`b94e16cbf9527c42a4797e9590c407d7c521ec13`, parent
`57d77791acc3af21160697efb45aa854f0e66066`. The preserved patch adds only three
test files and their operating note. The companion efsn change is the opt-in
`tests/restart/dashboard_telemetry_linux_test.go`; production code is unchanged.

Read [the investigation report](../../restart-dashboard-telemetry.md) for scope,
confirmed legacy flags and the payload calculation. `verification.json` checks
700 dashboard non-Markdown source files against the commit, 1,007 Go/module
source files against the tested worktree, the original dashboard checkout,
runtime/binary hashes, all three database shutdowns and process cleanup.

## Files

- `attempt-3/comparison.json`: actual collector wire capture (hello credential
  removed), PostgreSQL snapshot, HTTP API bodies/headers, direct RPC block and
  node-state responses, explicit test limits and one memory observation.
- `attempt-3/capture.json`: the same raw-message observations separately.
  Messages are decoded JSON, not a packet capture. Byte counts were taken on
  actual uncompressed application payloads before decode or redaction.
- `attempt-3/persistence.txt`, `efsn.txt`, database logs: passing test and clean
  service shutdown. No private signing key was loaded; scalar 1 is public test
  material. All chain state was in memory and discarded.
- Each attempt preserves its runner, source hashes, commands, exit statuses and
  disposable cluster location. Database files remain only in ignored scratch
  directories; password files were removed and postmasters stopped.
- `commit.json`, `dashboard-telemetry.patch`, `node-shasums.txt`: exact patch and
  portable-runtime identity. The official Node archive was verified against the
  checksum published at the recorded HTTPS URL. This is not a signature check.
- Cleanup JSON records no remaining matching Linux or Windows fixture process.

## Failed attempts and interpretation

Windows reporter compilation first found missing cached modules and then the
light-client import's C-only `secp256k1.RecoverPubkey` dependency. Missing modules
were copied from the existing offline rehearsal cache; no module files or
production source were edited. The Linux build uses the existing Go/C toolchain.

Attempts 1 and 2 reached the real API comparisons but failed the history-capture
assertion. The fixture hooked a WebSocket server `connection` event, whereas
the installed Primus uses `handleUpgrade` with a callback. Attempt 2 preserves
the empty capture. Attempt 3 hooks that callback and also waits for chart values
21..60, rather than treating an array's padded length as filled history. It
captures and compares all fifty history blocks. These were fixture defects,
not production changes or evidence that the collector dropped those reports.

## Reproduction

The established local environment is Windows Node 22.11.0, PostgreSQL 18.6,
Python, and WSL distribution `FusionRehearsal`, user `rehearsal`, Linux Go 1.21.3
with its existing offline module cache. The checksum-verified Linux Node 22.11.0
is under `tmp/dashboard-linux-runtime/node-v22.11.0-linux-x64`. The test harness
uses only synthetic telemetry credentials and public test key 1.

From the efsn workspace, compile with:

```
wsl -d FusionRehearsal -u rehearsal -- bash /mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-dashboard-telemetry-2026-10-03/build-linux.sh
```

Run `run.py attempt-N` with the configured Python and a new attempt number. It
creates a fresh loopback PostgreSQL cluster, starts the opt-in test, then stops
the cluster and removes its password. The node and collector bind Linux
loopback; the Windows writer/API use WSL localhost forwarding. The fixture
does not use the isolated network namespace of earlier peer tests, since that
would prevent this localhost forwarding. Instead P2P dialing, listening and
discovery are disabled explicitly. No existing database or backup is opened.

For the frozen accepted evidence, run `verify.py`. It expects the recorded
binary, runtime and source bytes still available. `check-linux-processes.py`
and `check-windows-processes.ps1` capture cleanup. The latter checks the exact
three recorded disposable clusters in addition to the fixture process names.

The compiled browser, TLS, mining during a collector outage, production-sized
messages, concurrent reporters and race detection are outside this run. The
previous 151 contracts/12 socket tests were not rerun: none of their production
inputs changed, and this step's new integration test is separately opt-in.
