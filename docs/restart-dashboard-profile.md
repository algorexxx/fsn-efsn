# Dashboard larger-report and multiple-node profile

3 October 2026. Eight simulated reporters now pass through the collector,
PostgreSQL and HTTP API with 714 transaction hashes per head and fifty-block
history replies of about 2.81 MB each. One history batch runs while persistence
is active. Four successive heads retain complete hashes and aligned charts.
G6 remains open; the candidate budgets below are not production defaults.

The [evidence bundle](evidence/restart-dashboard-profile-2026-10-03/README.md)
preserves exact sources, attempts, measurements, the small dashboard patch and
cleanup checks. The only production file changed is the dashboard snapshot
writer: unexpected transport close/error now reaches its existing error callback.
No efsn, consensus, schema, dependency or frontend code changes.

## Coordinated limits

| Case | Reporters | Collector input | Pending output per connection | Snapshot frame/message | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| Small receiver | 2 | 4 MiB | 1 MiB | 64 KiB | 114,210-byte inventory refused; close 1009; no save; API 503 |
| Small sender budget | 8 | 4 MiB | 256 KiB | 1 MiB | About 457 kB inventory refused by output guard; client close 1006; no save; API 503 |
| Aligned candidate | 8 | 4 MiB | 1 MiB | 1 MiB | Four complete saves and all API assertions pass |

The candidate uses eight explicit telemetry credentials, a sixteen-connection
collector cap, 100 application messages/s per connection, five-second login
deadline, 250 ms snapshot interval, 1,500 ms request deadline, five-second
snapshot lifetime and thirty-second report lifetime. These are fixture settings.
Enrollment count and TCP connection count are different limits.

The final eight-node run sends fifty-block history from every reporter twice:
at initial head 1000 and at 1001 with the writer active. Ordinary updates then
advance all heads to 1002 and 1003. Each history message contains 35,700 hash
objects and measures 2,811,901–2,811,902 application bytes; no payload exceeds
the configured input limit. The modeled gas fields use a 15,000,000 gas limit
and 714 minimum-cost transfers. These are telemetry objects, not signed or
executed blocks, and this does not establish Fusion transaction throughput.

The four saved snapshots preserve each identity's distinct version, peer and
pending counts. Both `/nodes` and `/blocks` preserve every current-head hash;
all forty chart counts remain 714 and match their heights. Stopping collection
and advancing the API's injected clock beyond the snapshot lifetime returns
503. This is a controlled expiry check, not a live outage or mining test.

## Measurements

| Final run quantity | Observed result |
| --- | ---: |
| Largest head report | 56,283 bytes |
| Largest collector inventory | 457,084 bytes |
| Largest stored snapshot JSON | 461,205 bytes |
| HTTP `/nodes` | 483,281 bytes |
| HTTP `/blocks` | 474,540 bytes |
| HTTP `/charts` | 5,700 bytes |
| PostgreSQL save times | 12.7–17.1 ms |
| Eight-node history-batch acknowledgement | 241.9 / 291.9 ms |
| Later eight-node head-only acknowledgements | 23.7 / 16.3 ms |
| Collector startup RSS | 133,042,176 bytes (126.9 MiB) |
| Highest sampled collector RSS | 250,060,800 bytes (238.5 MiB) |
| Highest sampled heap used | 63,534,400 bytes (60.6 MiB) |
| Event-loop delay p99 / maximum | 73.1 / 102.3 ms |

The collector has 555 memory observations from a 25 ms timer plus message/write
hooks. Instrumentation parses messages again and adds overhead. These are
sampled maxima, not guaranteed peaks, a soak or an approved resource allocation.
Component maxima may occur at different times; do not add them together.
Database, driver and browser processes are outside the collector measurements.
Runtime is Windows Node 22.11.0 with PostgreSQL 18.6 and pg 8.23.1.

Common reported history leaves 54 chart heights/variants and no retained
transaction/uncle arrays. The separate [retention experiment](restart-dashboard-retention.md)
covers 18,000 variants offline; this network profile does not repeat that worst
cache population or simulate a slow public network or many public viewers.

## Transport diagnostics

The first profile attempt incorrectly waited for `onError` to observe a byte
limit failure. The WebSocket receiver instead emitted a close event, and the
writer silently retried with no saved snapshot. Close-event diagnostics proved
both independent limit failures before changing production code.

The fix reports unexpected closes/socket errors through the existing callback
and logger. It redacts raw reasons and exception text, reports each connection
failure once, and avoids warnings for deliberate stop or an already-reported
timeout/rejection/write failure. Retry and storage behavior are unchanged.
This supplies a diagnostic; it does not configure operator notifications.

Two new tests fail on the preceding writer and pass with the correction. All
**161 contracts**, **12 socket tests**, **six database scenarios**, the two
constrained profiles and final successful profile pass. Failure attempts and
earlier measurements remain in the bundle. All nine disposable databases are
stopped and their password files removed; all matching Windows test processes
are gone. No WSL node, real chain data or real key was used for this work.

## Admission review and next step

Source inspection confirms remaining gaps relevant to selecting budgets:

- `server.js` accepts object-shaped `hello.info` and copies all its fields;
  `node.js` retains them. Metadata has no separate field or byte policy.
- Validated current heads retain unknown extensions for compatibility. A
  nearly 4 MiB head and nearly 4 MiB metadata can each be accepted independently;
  ordinary eight-node profile success does not imply every accepted inventory
  fits 1 MiB. Chart projection already discards those extensions.
- `node-ping.clientTime` is echoed without a separate type/size check. The
  output guard still applies, but this is not an explicit ping field contract.
- Persistence checks `SNAPSHOT_MAX_NODES` after receiving inventory. Credential
  roster and retained inactive identities must fit it; the TCP cap alone does
  not establish that bound.

Next: bound/project registration and ping fields, then establish an explicit
per-head/extension budget preserving required transaction hashes. Verify the
aggregate maximum roster against inventory, pending-output and snapshot limits,
including inactive rows, envelopes and chart/fan-out headroom. Keep the 4/1/1
MiB profile as test evidence until that admission policy is reviewed and measured.
Test the chosen proxy/TLS route with it before deployment. Runtime review,
supervision, alert delivery and collector loss during mining remain open.
