# Explicit observer capacity-copy acceptance

Scope: add one offline observer operation that preserves every original event in
a new history with an explicitly larger budget. The source, its budget and all
incident/baseline identities must stay unchanged. Nothing is pruned, no budget
is raised automatically and no collector is switched automatically. This is
capacity recovery within the existing 1 GiB ceiling, not rolling retention.

Acceptance declared before execution:

- An exhausted history can be copied, reopened and continued with the next event;
  the source still refuses that oversized append and keeps the same export.
- Raw events, ticket baseline/timeline, incident identity and acknowledgement
  survive. Only the destination metadata budget and derived logical byte count
  change. Existing recorded mining/fork fixtures provide accounting expectations.
- Stale/missing sequence, unchanged/smaller/oversized budget, relative/nested
  destination, occupied destination and cancelled operation fail without a
  successful report or modification of the original events.
- An interrupted copy has no FORMAT marker and cannot be opened as complete;
  a fully published copy reopens normally. Partial outputs remain for inspection
  and are never overwritten on retry.
- CLI copy is an offline operation with explicit flags, excludes collection and
  review combinations, and needs no endpoint credentials or signing keys.

The change belongs only to `fsn-observe` and its internal package. No normal node,
consensus, recovery-anchor, mining, purchase-controller or dashboard behavior is
changed. Stop collection, preserve a closed source copy, inspect the returned
status and independently reopen/compare before selecting the new history.
Physical disk capacity and growing replay time remain separate limits.

## Results

Baseline: `e2b071e7e2c52d11f8d47f6eff8f2be632781c58`.
Both runtimes use the existing Go 1.21.3 installation and cached dependencies,
with downloads disabled. No real wallet keys, node datadirs or public endpoints
were used. No dashboard work is included.

| Check | Retained result |
| --- | --- |
| Windows observer + CLI suites | `attempt-3/windows/tests.txt`: pass, 7.885 s / 2.000 s |
| Linux race observer + CLI suites | `attempt-2/linux/tests-race.txt`: pass, 21.961 s / 1.747 s |
| Windows and Linux standalone observer builds | Both exit 0; binary SHA-256 retained, binaries outside the bundle |
| Linux existing 4,096-block/64-block replacement regression | `attempt-2/linux/backlog.txt`: pass, 8.81 s; same export hash as the earlier accepted backlog |
| Copy cancellation and incomplete-publication refusal | Pass on Windows and Linux |
| Destination alias through a directory symlink | Pass on Linux; Windows case skipped because OS symlink creation privilege is unavailable |

The new exhaustion test uses 64 KiB and 128 KiB budgets, including an unresolved
acknowledged incident. The ticket-preservation test copies the retained mining
fixture from 16 MiB to 32 MiB and compares both wallet timelines with their
pre-copy values and the independently captured executed block-29 ledger.
These are acceptance sizes, not production budget recommendations or a 1 GiB
load test. The backlog test is structural observer evidence, not consensus
execution of a 4,096-block mined chain.

Windows attempts 1 and 2 failed with `Access is denied` while resolving the
source path inside the restricted execution sandbox. Attempt 2 added contextual
error reporting; unchanged test expectations then passed outside that sandbox
in attempt 3. Preserve those failed logs and the corresponding source snapshots.
Do not remove destination-path validation to accommodate sandbox permissions.
Linux attempt 1 passed; attempt 2 repeats acceptance against the final source
hashes after that diagnostic change. Attempt 1's build/backlog may overlap that
edit, so only attempt 2 is accepted as final-source evidence.

`verify.py` validates final tested source hashes, expected test passes and exits,
the Linux loopback-only network, retained failures and unchanged backlog export.
It writes `verification.json`. Of 1,008 pre-existing source/module files, only
the observer command and history creation file changed; the other 1,006 remain
byte-identical. New implementation and tests are confined to those observer
packages. The [operator runbook](../../restart-observer-capacity.md) records
selection, inspection, manual switch and failure handling. G4 stays open for
production sizing/retention policy, alert delivery and collector-loss response.
