# Live observer reorganization evidence — 3 October 2026

Baseline `ff8984c4`. Changes are confined to Linux investigation tests and docs.
The runner builds the observer and service-test executable with race detection,
uses a private network namespace with loopback only, disables dependency downloads,
and uses compact synthetic state with public test keys 1 and 2. It reads no backup
and performs no large restore.

`attempt-1` retains the initial failed run and affected test source files. It
stopped before live observer collection because the new test mistakenly required
a positive lab signature counter. Ordinary keystore mining bypasses that counter;
the node logs show mined blocks despite the zero. The corrected test verifies
the distinct post-anchor blocks and their producer addresses directly.

`attempt-2` passed snapshot invalidation and unstable backfill, then stopped at
the older financial-audit helper's no-genesis-ticket restriction. This valid
fixture retained one genesis ticket. Its log, observations and affected source
are retained. The final test compares ticket inventories directly; the financial
helper and runtime are unchanged.

`attempt-3` contains the corrected run, followed by the ordinary-mining regression
for the shared HTTP gate helper. Both passed with Linux race detection:
161.11 seconds for the reorganization case and 160.03 seconds for ordinary mining.
All eight child service runs exited cleanly, with no race reports. Final evidence
verification passed; see [checks.json](checks.json). The new case settled at block
30 and preserved both histories' original evidence while catching up.

Each attempt retains source/executable hashes, exact runner, build diagnostics,
isolation records, logs and exit codes. The successful reorganization output is
organized into `snapshot` and `backfill` histories. Each has pre-production anchor
observations, isolated backfill, the held read's window and replacement header,
original/during/final exports, settled IPC backfills, final/cold wallet timelines
and command state captures. The complete histories are temporary; JSONL exports
are retained evidence, not supported import packages.

`verify.py` compares source hashes and result identities, both inventory baselines
against independently prepared anchor state, invalidation statuses, unchanged
history prefixes, final/cold wallet inventories against executed state, open
canonical-change incidents, and clean child-process exits with no race reports.
It writes `checks.json` only after both integration tests pass.
The first wallet's final query precedes the second node's last backfill, so its
global history sequence differs from the cold query by one. The verifier checks
those sequences against their respective histories and requires equality of
every other wallet timeline field. All 22 stopped-node before/after captures match.

Incident explanatory text exposes a raw-byte hash formatting defect, documented
as an open follow-up in the report. Structured hashes remain intact; the verifier
does not treat the explanatory string as a source of block identity.

Repeat using an unused attempt name; existing evidence/build paths are rejected:

```powershell
wsl -d FusionRehearsal -u root -- unshare --net -- bash /mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-observer-reorg-2026-10-03/run-linux.sh attempt-4
```

The test induces read delays and an initial ordinary peer join. It does not
inject false RPC responses, invoke the controlled downloader, or require automatic
purchase recovery after the reorganization. See the [report](../../restart-observer-reorg.md)
for scope and outstanding release gates.
