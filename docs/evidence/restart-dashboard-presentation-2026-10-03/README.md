# Dashboard presentation and actual browser acceptance

3 October 2026. Dashboard commit
`e69fe7982049dad5621871d6d96f380624e148af`, parent
`b94e16cbf9527c42a4797e9590c407d7c521ec13`. The preserved patch changes one
production frontend file, updates the opt-in telemetry integration fixture and
adds its browser helper. It removes the ambiguous sync and uptime columns from
both row paths. See [the report](../../restart-dashboard-presentation.md).

## Accepted evidence

- **attempt-1:** eight existing React DOM tests and the strict production build
  pass. `source-sha256.json` records inputs; `build-sha256.json` records all 547
  compiled output files. Build environment uses `/stats-api`, 250 ms polling and
  a 1,000 ms request timeout. The DOM tests use their existing faster fake-clock
  settings. These were not new tests mirroring a text edit.
- **attempt-2:** the full actual-node → collector → PostgreSQL → API → compiled
  Edge test passes. It executes/imports 600 synthetic transactions across sixty
  blocks and compares 51 distinct blocks using 59 direct RPC requests overall.
  Four browser checkpoints cover real data, pinning, expiry after stopping the
  snapshot writer and recovery. This is the first integration attempt for this
  follow-up; the attempt numbers distinguish build and integration evidence.
- `attempt-2/comparison.json` includes direct RPC, the actual stored snapshot,
  HTTP results, early wire capture, explicit test limits and browser observations.
  `capture.json` stores the same wire observation separately. Hello credentials
  are removed. Wire byte counts precede decode/redaction and include efsn's
  trailing JSON newline. It is not a packet capture or full-duration memory trace.
- `browser-actual.png` and `browser-expired.png` were inspected: the node row and
  fresh summaries appear initially, and the expired page has no old rows or
  current summary values. No misleading sync/uptime column remains. The browser
  preserves the user's pin and restores the row when collection resumes.
- `size-model.py` / `size-model.json` are offline byte calculations using the
  captured shape. They send no network traffic and do not create valid blocks.
  The larger 100/714-transaction rows and cache-size illustration are **not**
  executed capacity measurements. Gas cost varies with encoded purchase data;
  direct comparisons check each block against its RPC value. The model uses the
  observed maximum ticket overhead of 288 gas; this does not change the measured
  payload digit lengths in its ten-transaction row.
- `commit.json` and `dashboard-presentation.patch` preserve the candidate and
  runtime/binary identities. `verification.json` checks 701 non-Markdown dashboard
  sources against the commit, 1,007 Go/module sources against tested worktree
  bytes, compiled build hashes, raw comparison values, cleanup and preservation
  of the original dashboard checkout and efsn reporter.

No reporter, consensus, collector, persistence schema or dependency lock changes
were made. The previous 151 contract/12 socket tests were not rerun because
their production inputs are unchanged. The changed frontend was built/tested,
and the real collector/storage/API were exercised by the new browser scenario.

## Reproduction

Use the established Windows Node 22.11.0, Python and PostgreSQL 18.6 runtime.
WSL `FusionRehearsal`, user `rehearsal`, contains the existing Linux Go 1.21.3/C
toolchain and offline modules. Linux Node 22.11.0 remains the checksum-verified
portable runtime from the preceding evidence bundle. Playwright uses the
installed Edge `msedge` channel; the accepted browser is 154.0.4258.48.

From the efsn workspace:

```
wsl -d FusionRehearsal -u rehearsal -- bash /mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-dashboard-presentation-2026-10-03/build-linux.sh
```

With the configured Python, run `run-tests.py attempt-N frontend`, then
`run.py attempt-M`, each using an unused attempt directory. The second command
requires the build from the first. It creates a new disposable SCRAM-authenticated
cluster, runs the integration, stops the database and removes its password.
Only the public scalar-1 test key is used, and all synthetic chain data is in
memory. No backup or existing database is opened. The writer fixture uses the
disposable cluster administrator; production role restrictions retain their
earlier, separate acceptance evidence.

The node's test settings explicitly permit either one or ten transactions per
block; this run selects ten. The code uses existing block import helpers and
adds nine zero-value self-transfers after each ticket purchase. It never starts
the mining worker or ticket auto-buyer. Peer listening/dialing/discovery are
disabled, with all exposed service listeners on loopback and Windows reaching
Linux services through WSL localhost forwarding. No networking configuration
or firewall rules are changed.

`check-windows-processes.ps1` and Linux `check-linux-processes.py` recorded zero
matching fixture processes; the former includes temporary Playwright browser
processes and the exact disposable database path. The cluster is stopped, its
password removed, and the node, collector and browser have exited. Run
`verify.py` to check the frozen accepted evidence while its recorded source,
runtime, binary and build bytes are still available.

The 128 KiB input / 256 KiB pending-output / 64 KiB snapshot limits are this
one-node fixture's settings. Larger bounded workloads, full field validation,
compact chart retention, multiple simultaneous reporters, mining during
collector loss, production runtime/supervision/TLS and enrollment remain open.
