# Historical anchor inventory evidence — 27 September–3 October 2026

Source baseline: `eb408de`. Runtime edits belong only to the external observer.
The existing two-node service rehearsal has an opt-in extension for historical
inventory acquisition; node runtime and consensus source are unchanged.

`attempt-3/windows` retains the complete observer/CLI tests and Windows build.
`attempt-4/linux` retains the complete observer/CLI tests with race detection,
observer and service-test builds, and the isolated actual-service extension.
Both platforms pass 142 tests/subtests. The service extension passes with race
detection and 27 unchanged before/after node-state comparisons.
Dependency downloads are disabled. The Linux namespace contains only loopback.
The fixture uses compact synthetic state and public test keys 1 and 2, without
a production backup or large restore.

`inventory.json`, `timeline.json` and `history.jsonl` must be byte-identical across
platforms. Their source is the prior retained ordinary-mining fixture with its
anchor snapshot marked ineligible, followed by a new historical RPC observation.
The independently saved anchor and block-29 ledger provide expectations.
`services` contains actual IPC/HTTP command outputs, before/after node-state
captures, independently prepared anchor/current state, and empty-wallet evidence.

Attempt 1 passed both observer suites and acquired matching historical inventories
on both real services. Its timeline stopped at a legitimate automatic FSN maturity
conversion in the ordinary self-transfer receipt. That failed output and the exact
block/receipt are retained. The observer now excludes `TimeLockFunc` logs from
ticket mutation outcomes, because those logs change balances/time locks, not tickets.
The three-line correction changes only the observer.

Attempt 2 failed the new regression fixture precondition on both platforms: the
older chosen block did not contain a maturity conversion. Attempt 3 uses the exact
retained receipt from attempt 1, verifies its block/receipt commitments, and tests
ordinary, purchase, failed-purchase and unrelated-native-log cases. Both suites
passed; the runtime correction was not broadened to make that test pass.

Attempt 3's services then passed both acquired inventories and derived timelines,
but failed a test assumption about raw JSON `null`. The inherited single-call RPC
client unmarshals into an interface wrapper; a null response leaves the caller's
`json.RawMessage` empty. The collector's newly initialized map is correctly nil
in that case. Attempt 4 changes only the service test to use the existing batch
RPC decoder to preserve the literal null, and repeats the Linux checks and service
rehearsal. No RPC client or observer runtime correction is made for this capture.
The Windows suite need not be rerun: its observer sources and tests are identical
to the final Linux run and are compared by the verifier.

The original focused test compile failure and correction are summarized in
[preliminary.txt](preliminary.txt); the expected helper arity was corrected, not
the runtime behavior or expected ledger. Full run attempts are not overwritten.

Run with an unused attempt name:

```powershell
./docs/evidence/restart-observer-anchor-2026-09-27/run-windows.ps1 -Attempt attempt-5
wsl -d FusionRehearsal -u root -- unshare --net -- bash /mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-observer-anchor-2026-09-27/run-linux.sh attempt-5
```

`verify.py` checks the committed attempt, pinned source/input hashes, cross-platform
exports, real-service state comparisons and inventory reconciliation, then writes
`checks.json`. The runners record executable hashes; executable files remain in
the ignored temporary build directory.

These results cover controlled endpoints with retained historical state. They
do not establish production historical-state availability, proof of remote state,
live competing miners during acquisition, large-state performance, full financial
accounting or release readiness. See the [report](../../restart-observer-anchor.md)
for the new history-event compatibility boundary and RPC consistency limits.
