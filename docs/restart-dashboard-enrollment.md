# Dashboard complete-head and enrollment limits

3 October 2026. The dashboard now bounds complete retained head reports and the
total credential roster, including disconnected nodes. The measured eight-node
candidate passes with maximum configured heads and metadata, then passes the
concurrent reporter and actual efsn/database/browser checks. No efsn or consensus
code changes are included. G6 remains open for deployment acceptance.

The [evidence bundle](evidence/restart-dashboard-enrollment-2026-10-03/README.md)
contains exact source/build hashes, the local dashboard patch, the failing
baseline, all attempts and cleanup checks. Work remains on the isolated
`codex/dashboard-telemetry-auth` branch; the original dashboard is preserved.

## Small production correction

- Required `COLLECTOR_MAX_HEAD_BYTES` bounds the projected native head before
  collector timing fields are added. Every transaction hash and supported uncle
  field is kept; unknown head/transaction/uncle extensions are discarded.
- Oversized standalone and combined reports are rejected atomically before
  changing heads, chart history or report receipts. No hash truncation occurs.
  The previous head ages normally; the session may later report an acceptable head.
- Required `COLLECTOR_MAX_NODES` checks the entire credential roster at startup,
  before listeners are constructed. Rotating credentials still consume one
  identity slot. Disconnected nodes count because the roster covers every identity
  the process can accept. Roster changes require restarting the collector.
- The address attached after registration must be a bounded IPv4/IPv6 literal
  without a scope suffix. Its provenance still depends on proxy/Primus forwarding
  behavior; this is a size check, not authenticated peer identity.

This changes six production files: a small head-projection helper, collection
admission, deployment configuration, credential loading, registration address
validation and server wiring. History retains its existing compact representation.
There are no dependency, database schema, API or frontend changes.

## Coordinated candidate and measurements

| Setting | Tested value |
| --- | ---: |
| Enrolled identities / persistence node cap | 8 / 8 |
| Complete projected head | 65,536 bytes |
| Projected reported metadata | 2,048 bytes |
| Incoming application message | Strictly below 4,194,304 bytes |
| Pending output per TCP connection | 1,048,576 bytes |
| Snapshot message/frame | 1,048,576 bytes |

The new boundary run uses eight 64-character identities, each with exactly the
maximum metadata and head sizes, and preserves 714 hashes per head. It registers
them sequentially with only three TCP slots. Metadata includes U+2028 to cover
Primus JSON escaping. The run leaves all eight inactive in the
inventory. One identity then reconnects using its next credential and replaces
its head without increasing the row count. Both API routes preserve all expected
native fields. One-byte-over-budget block and combined reports leave the prior
head, receipts and compact cache unchanged. An unconfigured ninth identity cannot
register; a configured roster above the cap is refused before listener creation.

These are synthetic telemetry reports. Extra uncle-header data fills the precise
byte boundary; it is not a claim that those headers satisfy Fusion consensus.
No real wallet, chain backup or public endpoint is involved.

| Observed boundary-run quantity | Bytes |
| --- | ---: |
| Fifty-block history message | 3,276,956 |
| Largest collector inventory | 561,635 |
| Largest stored snapshot JSON | 554,917 |
| Chart message | 8,798 |
| HTTP `/nodes` | 589,075 |
| HTTP `/blocks` | 549,897 |

The earlier ASCII-only boundary also passed (547,065-byte maximum inventory);
the Unicode run adds transport escaping without increasing stored JSON size.
Both all-inactive and reconnected snapshots save with zero writer errors or
output rejections. The eight-concurrent-reporter case also passes: two history
batches, 714 hashes per block and four advancing snapshots. Its largest saved
snapshot is 461,244 bytes. This is bounded sizing evidence, not a soak, public
viewer fan-out test or complete process memory allocation.

A conservative review allowance for this schema is
`N * (H + 8192) + 32768` bytes for one inventory plus charts: **622,592 bytes**
for eight 64 KiB heads. The per-node allowance is 4149 wire bytes for metadata/IP
(including Primus U+2028/U+2029 escaping), 1024 for fixed-width GeoIP output,
1001 for forty propagation numbers, 1024 for scalar stats/uptime/receipts, 256
for collector timing, and 256 for identity/socket ID and outer JSON structure.
That subtotal is 7710 bytes, below the reserved 8192. The
chart reserve includes forty-entry arrays, 78-digit difficulties, histogram bins
and two miners. This does not include arbitrary queued event bursts or guarantee
socket availability: the existing output guard still disconnects slow consumers.

The allowance depends on the current schema, pinned GeoIP/Primus behavior and
bounded native fields. Separate process settings are not cross-validated; the
deployment manifest must keep `SNAPSHOT_MAX_NODES >= COLLECTOR_MAX_NODES` and
coordinate head, input, snapshot and output byte limits. Larger enrollment or
head budgets require another coordinated sizing review. A real chain block can
outgrow the dashboard's chosen limit; the consequence is stale dashboard data,
not rejection of that block by efsn. These values remain a deployment candidate.

## Acceptance and remaining work

All six new regressions fail against the preceding production source. The
candidate passes **173 contracts**, **13 socket tests**, both bounded database
profiles and the actual efsn → collector → PostgreSQL → API → compiled-browser
check. Current-head hashes and fifty historical blocks match direct RPC; all
four browser checkpoints, including writer-loss expiry/recovery, pass with zero
writer errors. The Go source, synthetic node binary and frontend build are unchanged.

The first boundary attempt used an incorrect assertion: it expected `null`
freshness for known reports from disconnected nodes. Existing API code explicitly
returns zero in that case and reserves null for unknown/invalid receipts. The
test expectation was corrected; production freshness behavior was unchanged.
The failed attempt is preserved, including its failure-cleanup close diagnostic.
All five disposable databases are stopped, their password files removed, and
matching Windows/WSL test processes absent.

Next: test the selected proxy/TLS routes, forwarding-header normalization and
matching byte/timeout limits using this candidate profile. Then finish collector
loss during actual mining, runtime/dependency review and service supervision.
Public hosting and operational choices still need acceptance; this is not a
launch approval or a change to independent producers' consensus participation.
