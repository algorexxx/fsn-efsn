# Bounded observer backlog and closed-copy recovery — 4 October 2026

The existing observer passes a 4,096-block backlog, a 64-block replacement branch
and closed-history copy/reopening checks on Windows and Linux, including Linux
race detection. Only a test and evidence/documentation were added. All 1007
previously tracked Go/module files are unchanged; no node or observer runtime
patch is required by this result.

## Scope and acceptance

The fixture starts with the already executed five-block mining history and its
independent block-29 wallet ledger. It adds 4,096 generated block/transaction/
receipt records, each containing one ordinary transfer outside the monitored
wallets. The real observer backfill collects them through the existing loopback
HTTP fixture in 32 batches of 128. Ticket timelines are checked at suffix lengths
128, 1,024 and 4,096 against the original captured inventory.

These generated extensions are structural observer fixtures, not signed/mined
valid chains. State execution and foreign ticket ownership are not modeled.
The check exercises RPC collection, transaction/receipt commitments, ancestry,
scoped ticket reconstruction and storage. Earlier actual-node mining and
reorganization tests remain the evidence for those separate behaviors.

Replacing the final 64 blocks creates an open canonical-change incident. The
test acknowledges it without resolving it, verifies every displaced block remains
in the export and checks the complete prior export remains an unchanged prefix.
After closing the database, it copies and byte-checks every file into a new
directory. Reopening that copy preserves the complete status, acknowledgement,
incident identity, baseline and final ticket timeline. Logical exports match
byte for byte across the original/restored pair and all three platform/build runs.

## Results

| Appended blocks | Logical history bytes | Windows ticket timeline median | Linux ticket timeline median |
| --- | ---: | ---: | ---: |
| 128 | 408,046 | 15.99 ms | 14.90 ms |
| 1,024 | 2,501,611 | 109.12 ms | 109.64 ms |
| 4,096 | 9,681,277 | 439.68 ms | 378.13 ms |

Each timeline requests the final 128 blocks but reconstructs the earlier prefix
to obtain its inventory. Medians use three samples with Go garbage collection
before, outside, the timed operation. These are local measurements, not public
RPC or production latency guarantees. The largest Linux timeline cumulatively
allocates 241,952,016 bytes; that is neither peak nor retained RAM.

Linux backfill batches took a median 143.93 ms, maximum 205.83 ms. Its 64-block
replacement took 187.37 ms. After replacement and acknowledgement the history
uses 9,833,913 logical bytes within the fixture's unchanged 16 MiB budget. The
closed database copy contains eight files totaling about 2.91 MB; physical file
lengths and the logical budget measure different quantities.

The whole dedicated test passed in 10.77 seconds on Windows, 9.12 seconds on
Linux and 79.61 seconds with Linux race instrumentation. Existing observer and
command suites also pass on Windows and with Linux race detection. Race timings
are correctness instrumentation, not capacity measurements. There are no retained
failed attempts in this slice. Temporary histories are managed by the Go test
cleanup; no production database or account key was opened.

The [evidence bundle](evidence/restart-observer-backlog-2026-10-04/) contains the
predeclared acceptance, runners, test source, source/fixture hashes, raw test
outputs, measurements and verifier. The fixture makes 4,160 raw-transaction and
4,160 receipt reads; every recorded RPC method is read-only. No package download,
public service, dashboard change or historical-chain replay was performed.

## Consequence for G4

This closes the declared longer retained-backlog/replacement case and demonstrates
lossless recovery from a closed whole-history copy. It does not implement rolling
retention or free active capacity. Replaying growing history still costs more;
the result does not justify silently increasing budgets or deleting old evidence.

Next select bounded collection/retention settings and preserve wallet baselines,
unresolved incidents, review identity and displaced evidence across the chosen
procedure. Finish actual collection-failure, missed-cadence and incident alert
delivery. These remain explicit G4 items in the [launch plan](restart-plan.md).
Do not expand this measurement into another benchmark programme unless the
selected launch workload exceeds its bounds or a new failure warrants it.
