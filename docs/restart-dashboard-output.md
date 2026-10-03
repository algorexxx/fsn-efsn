# Dashboard output queue acceptance

3 October 2026. The isolated dashboard candidate now bounds pending output
bytes per collector connection. Dashboard commit
`57d77791acc3af21160697efb45aa854f0e66066` follows `6893caa`; the
exact patch and verification are in the
[evidence bundle](evidence/restart-dashboard-output-2026-10-03/README.md).
**151 contracts, 12 real socket tests and six PostgreSQL pipeline scenarios
pass.** G6 remains open.

## Small explicit change list

1. Require `COLLECTOR_MAX_BUFFERED_BYTES`, independently of the input message
   limit. It is a positive integer byte budget configured at startup.
2. Install a short guard on each collector TCP socket's writes before upgrade.
   Count encoded byte length plus existing `writableLength`; accept equality,
   refuse an overflow before enqueueing it and destroy only that connection.
3. Preserve native write results and callbacks for accepted data. On refusal,
   return false and fail the supplied callback asynchronously. Draining restores
   capacity; no extra message queue, retry loop or timer is introduced.

Runtime changes are confined to the new output helper, one configuration field
and its collector wiring. Tests and operating documentation accompany them.
Dependencies, frontend, snapshot schema, efsn, chain data and validator keys are
unchanged. Nothing is pushed or deployed.

## Why this layer

Source inspection of the locked Primus 6.1.0 / ws 1.1.5 transport found direct
sends without a queue limit. The old `bufferedAmount` getter only reports the
underlying socket buffer. The installed transport encodes JSON synchronously,
has compression disabled and writes data/control frames through the same
socket. Guarding that write boundary therefore also covers Primus and WebSocket
control replies, which bypass application-message filtering.

The evidence includes inspected source hashes and a two-write in-memory stream
probe: two eight-byte writes remain queued as sixteen bytes without a guard.
That probe illustrates queue behavior; it is not a network saturation test.

Destroying the socket avoids waiting for the old transport's close handshake
while output is stuck. The peer sees closure code 1006. Telemetry disconnection
releases the node's session identity; it can authenticate again and send fresh
reports. This has no effect on blockchain peer connections or block production.

## What passed

Six new contract tests cover the exact limit, encoded multibyte text, typed byte
views, native backpressure, asynchronous rejection callbacks, restored capacity
after draining, per-connection isolation and required-setting wiring.

The real collector tests use a test-only corked socket to hold output without
depending on operating-system buffer capacity. Two replies queue **6142 bytes**
under an **8192-byte** limit. The third reply closes only that socket, with the
peak still 6142 bytes. Another viewer stays usable and the same producer identity
reconnects successfully. The queue is empty after closure.

On each of `/api`, `/primus` and `/external`, one Primus reply plus three small
WebSocket control replies queues **404 bytes** under a **512-byte** limit. The
next control reply closes that socket without raising the peak. Corking and
inspection commands exist only in the test fixture. These checks use a handful
of bounded local messages; they do not measure internet throughput or latency.

The unchanged six-scenario PostgreSQL pipeline also passes with the guard
enabled (seven TAP passes including the outer test). It covers normal snapshots,
chart windows, identity, receipt freshness, permissions, reconnects and expiry.
The small disposable database is stopped and its password file removed.
The frontend is unchanged, so compiled-browser/build checks were not repeated.
All 697 non-Markdown source files in the test manifest match the committed
candidate. Original checkout preservation and unchanged dependency locks pass;
no owned collector fixture process remains running.

## Scope and next work

This limits pending socket-write bytes, not total process memory. Serialization
and framing occur before the check; object overhead, kernel buffers and reverse
proxy buffers have separate costs. It adds no drain deadline, global traffic
quota or connection-rate limit. HTTP handling and paths bypassing `socket.write`
need their own controls. Transport/compression changes require renewed testing.

The fixture budget of 262144 bytes is not a production recommendation. A valid
large snapshot can exceed a configured budget and disconnect too. Production
sizing must include real node reports, aggregate inventories, charts and bursts,
along with the independent incoming and snapshot-reader limits. Actual efsn/RPC
comparison and payload measurement are next. Finish full telemetry-schema,
runtime/dependency, supervision and proxy/TLS acceptance before public use.
