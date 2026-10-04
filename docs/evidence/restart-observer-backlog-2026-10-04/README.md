# Bounded observer backlog and closed-copy acceptance

Declared scope: extend the previously executed five-block mining fixture with
4,096 generated block/ordinary-transaction/receipt records, collected over a
loopback HTTP fixture in batches of at most 128. Measure the last 128-block
ticket timeline at suffix sizes 128, 1,024 and 4,096, then replace the last 64
records with a competing fixture branch. The original captured wallet ledger
at block 29 is the independent inventory expectation for every extension.

The extension is structural observer input, not mined or consensus-valid chain
history: ordinary transaction signatures, state execution and selected-ticket
ownership outside the monitored wallets are not modeled. It tests collection,
commitments, retained ancestry and scoped ticket reconstruction. Earlier live
mining/reorganization evidence remains separate. No real backup, key, public
endpoint, service deployment or dependency download is involved.

Pass conditions fixed before execution:

- All 32 original extension batches reach their requested heads within existing
  128-block/8 MiB limits; the history retains its existing 16 MiB logical budget.
- The three measured timelines match the separately captured block-29 inventory
  and contain no ticket events from the ordinary-transfer suffix.
- A 64-block replacement reaches its new head, records an unresolved canonical
  change and retains every displaced block and the complete prior export prefix.
- Acknowledgement, incident identity, baseline, complete export and final ticket
  timeline survive copying the closed history to a new directory and reopening.
- The copy is byte-checked before opening; original and restored logical exports
  have equal hashes. Reopening may alter LevelDB's internal housekeeping files.

The new test reuses existing retained fixtures, RPC server and measurement helper.
It changes no runtime implementation. Timings include the named operation only;
Go garbage collection runs before each measurement, outside its elapsed interval.
Allocated bytes are cumulative allocations, not peak or retained memory.
The fixture uses one advancing monitored wallet; the other wallet's existing
baseline and evidence stay in the same history. RPC has a ten-second deadline per
batch. The run has a whole-test timeout and does not choose production cadence.

Closed copying preserves evidence but does not prune history, free active capacity,
implement rolling retention or deliver alerts. Those acceptance items remain open.
This is a finite G4 check; it does not authorize a broader monitoring redesign.

## Completed runs

`attempt-1/windows` passes the existing observer/command suites and the dedicated
backlog test. `attempt-1/linux` passes the suites with race detection and both
ordinary/race versions of the backlog test. `verification.json` checks source
preservation, batch/read counts, copy agreement, incident state and identical
logical export hashes across all three results. The Linux directory retains the
exact added test source. Run `verify.py` with Windows Python to recheck the bundle.

Reproduce with `run-windows.ps1 -Attempt attempt-N`, or run `run-linux.sh attempt-N`
in a fresh network namespace of the existing `FusionRehearsal` distro. The Linux
runner enables loopback only and uses the existing Go 1.21.3 toolchain and module
cache as `rehearsal`; Windows uses the existing repository-local Go/runtime cache.
The output directory must be new. No dependencies are downloaded. Performance
numbers come from ordinary builds; race results establish correctness only.

See the [report](../../restart-observer-backlog.md) for measured results and the
remaining retention/alert boundary. All runs passed; no failed run was discarded.
