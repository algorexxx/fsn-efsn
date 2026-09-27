# Observer ordinary-mining evidence

Baseline `c1536fb`. See the [report](../../restart-observer-mining.md) for the
scenario, accounting findings and boundaries. Only three Linux integration-test
files and documentation are added; node and observer runtime source is unchanged.

`run-linux.sh attempt-N` is invoked through
`wsl -d FusionRehearsal -u root -- unshare --net -- bash <absolute-script> attempt-N`.
It refuses to overwrite an attempt, enables only loopback, builds both binaries
with offline Go 1.21.3 and race detection, and runs `TestObserverOrdinaryMining`.
Both nodes use temporary compact synthetic databases and public test keys 1/2.
Backup input is explicitly cleared. No large disk copy or restore is performed.

- Attempt 1 stopped at compilation: an unused import in the new test. No service
  run occurred; its compiler log and original source manifest are retained.
- Attempt 2 passed in 171.19 seconds, with four purchases, five selections and
  five retreats across blocks 25–29. A new test summary printed a hash as raw
  bytes using `%s`; the original log therefore contains non-UTF-8 bytes. It is
  preserved exactly. The test summary now explicitly uses `.Hex()`.
- Attempt 3 passed the final source in 113.69 seconds, with four purchases, five
  selections and two retreats across blocks 25–29. All four initial/cold child
  service runs exited cleanly and race detection reported no race. Empty build
  logs mean successful builds with no compiler output. Variations in retreat
  count follow actual mining order/timing, not a changed consensus rule.

Every observer CLI invocation is a separate process reopening the same history.
The 13 `*-command.json` files record expected mining flags, heights, signature
counts and start/end times. Heads and pools may change during ordinary mining;
the checks require monotonic progress, unchanged control flags and no verifier
signatures, rather than frozen node state. `moving-*-window.json` records the
test proxy's deliberate read delay and natural head advancement. Response bodies
come from the real service, unchanged.

`history-export.jsonl` contains metadata and eight immutable events.
`cold-history-export.jsonl` preserves that exact prefix and adds two rechecks.
`block-*.rlp`, `ledger-*.json`, `anchor-snapshot.json` and `native-events.json`
retain the inputs/results for the test-only native inventory reconstruction.
The Go test compared every reconstructed inventory with both nodes and separately
audited future interval rights. It covers only the documented synthetic scope;
the production observer does not yet derive these native events.

`verify.py` checks attempt 3, matches all 135 pinned test/observer/module files,
confirms all 15 observer Go files are unchanged from the baseline, validates the
commands, moving-head windows, contiguous exports and inventory replay, and
writes [checks.json](checks.json). Build binaries remain in ignored
`tmp/restart-observer-mining`; their hashes are recorded and checked if present.
Capacity snapshots record the small test footprint, not a production retention
estimate. Attempt 2's source manifest intentionally predates the log-only fix.
