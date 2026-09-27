# Observer evidence, 27 September 2026

See [scope, usage and limitations](../../restart-observer.md). This is validation
of the separate read-only executable using local RPC adapters and preserved
synthetic evidence. No database was restored/opened, no new mining occurred, and
no alert was sent. The node's P1–P15 source is unchanged from `406d545`.

- `run-windows.ps1`: offline Go 1.21.3 tests/build with the existing Windows cache.
- `run-linux.sh`: offline Go 1.21.3 race tests/build in `FusionRehearsal`, invoked
  as root through `unshare --net -- bash <script>`. Only loopback is enabled;
  tests/build run as `rehearsal`. No external RPC or package downloads.
- `windows.txt`, `linux-race.txt`: final passing output for both packages.
  Empty `*-build.txt` files mean the successful compiler emitted no messages.
- `reports/`: JSON emitted by the final Windows tests. These are fixed-time
  adapter observations, not reports from live nodes at the displayed times.
- `inputs.sha256.json`: eight collector/CLI source files plus 571 retained
  inputs; verified unchanged after the successful checks. Retained inputs are
  referenced in their existing directories rather than copied here.
- `verify.py` and `checks.json`: input preservation, log/report checks and hashes
  of the two locally built executables under `tmp/restart-observer`.

The adapters supply preserved block/receipt/transaction/ticket/account data.
Genesis and status fields are adapter fixtures, and ordinary total difficulty
is a placeholder. The equal-weight test uses the recorded heads and cumulative
difficulty from the prior equal-weight rehearsal. Mutated responses in other
cases are explicit faults; this is not full consensus validation of those variants.

## Retained initial failure

`initial-null-receipt-failure/` preserves both failing platform logs, reports,
the input hashes, and the pre-correction `transaction.go.txt`. After adding
explicit receipt-status validation, four absent-receipt cases failed: both nonce
gap/funding fixtures, expiry and queued-pool classification. The existing
`rpc.Client.CallContext` decodes into an interface; a JSON null response leaves
the supplied raw-message variable unchanged. An uninitialized raw message was
therefore treated as invalid JSON rather than an absent receipt.

The one-line correction initializes that raw message to JSON `null`. RPC errors
remain unknown, a successfully absent receipt is absent, and a non-null receipt
with missing status remains unknown. Final Windows and Linux race suites pass;
the preserved chain evidence did not change. No runtime RPC library correction
was needed. The original failure logs contain diagnostic Go struct formatting,
including byte-array hashes; final reports carry hexadecimal identifiers.

The Windows command wrapper subsequently attempted to write a null output array
after a successful silent build. Its log-writing expression was corrected to an
empty array and the build was rerun successfully. This was an evidence wrapper
error, not a test or executable failure; the passing tests were not rerun for it.

This evidence does not cover actual full-node service integration, elapsed
incident transitions, log rotation, notifications, production thresholds,
executable attestation or a new finality rule. Those remain explicit next gates.
