# Dashboard: local TLS proxy acceptance

Date: 2026-10-03. G6 remains open. This slice adds a reviewed configuration
candidate and local transport evidence; it does not publish the dashboard.

Dashboard commit: `4ca1f59bb273569e5b82a1390e93b36e1fdd4b01` on the existing
`codex/dashboard-telemetry-auth` branch, based on `63d1b14`.

The isolated dashboard branch now has `deploy/nginx.conf.template` and
`docs/proxy-tls.md`. The only deployment addition is nginx configuration. All
JavaScript changes are test fixtures or test assertions. Collector, writer, API,
frontend, database schema and efsn/consensus behavior are unchanged.

## Accepted local behavior

- TLS 1.2 and 1.3 both serve the compiled frontend bytes. Clients reject an
  untrusted certificate and a wrong certificate hostname; a wrong HTTP host is
  refused. The temporary CA is passed only to individual test clients.
- Public `/api` accepts authenticated WSS telemetry. Exact `/stats-api/nodes`,
  `/stats-api/blocks`, `/stats-api/info` and `/stats-api/charts` reach the real API.
  Twenty normal HTTP/upgrade route checks refuse private or undeclared collector
  routes. The private writer still uses direct loopback `/primus`.
- Forwarded headers are reconstructed from the TCP peer. A fixture supplying all
  five forwarding-header families plus synthetic Cookie/Authorization values
  reaches the collector with only nginx's six non-WebSocket-key/version headers.
  The complete stored metadata contains the observed loopback IP.
- Eight concurrent identities each report a 65,536-byte head and 2,048-byte
  metadata. A 3,276,956-byte fifty-head history message passes through WSS. Every
  supported head field, transaction hash and uncle field survives the real
  collector/writer/API path. The snapshot is 554,505 bytes; HTTPS node and block
  responses are 588,759 and 549,890 bytes.
- Twelve reporter connections are admitted; a thirteenth receives 503. Missing
  hello closes at 5,003 ms. A wrong credential for a freed identity is refused;
  the correct credential reconnects.
- API read inactivity returns 504 at 5,005 ms. Stale snapshots still return 503
  with `no-store`. A separate silent WebSocket upstream closes at 45,884 ms.
  All eight normal reporters remain connected for 48,113 ms, with 24 replies to
  pings sent at efsn's fifteen-second cadence.
- The final proxy test passes, as do all thirteen existing socket tests on both
  Linux and Windows. No new dependency or application-code changes were needed.

The memory store substitutes only for PostgreSQL. The compiled frontend is
served and byte-compared, not executed by a browser. Report payloads are synthetic
native-shaped values; the padded uncle used to exercise byte limits is not a
consensus-valid header. Earlier actual-node/PostgreSQL/browser evidence remains
separate. This run is not a mining, public-network load or memory-capacity claim.

## Findings preserved during testing

`attempt-1` passed certificate and route checks, then failed because the fixture
included Primus's internal `primus::req::backup` object in a header comparison.
The fixture now captures the original HTTP `rawHeaders`.

`attempt-2` passed header normalization, payload and API timeout checks, but its
silent synthetic reporters had disconnected by the long-lived connection check.
Local source explains the mistaken assumption: Primus defaults to closing a
client after 35 seconds without inbound activity; it does not periodically send
the server ping this fixture expected. Actual efsn reports every fifteen seconds
and includes a node-ping exchange. The corrected fixture reproduces that cadence
without changing collector or proxy timeouts.

`attempt-3` passes the complete proxy check. Its subsequent Linux socket suite
fails one inherited assertion requiring close code 1006 for an oversized message;
the transport supplied 1009. Installed `ws` initiates the 1009 close before
emitting its error, while the collector error handler destroys the socket. The
test now permits these two refusal outcomes and also asserts no inventory reply
was accepted. `wire-1` passes all thirteen cases on both platforms. The failed
logs are retained; the whole `attempt-3` runner is correctly marked failed even
though its proxy subtest passed. Inherited Node deprecation warnings remain.

## Candidate and outstanding work

Ubuntu nginx `1.24.0-2ubuntu7.18` was downloaded from the configured Ubuntu package
repository and extracted into workspace scratch, without installing a service.
Its package SHA-256 is
`6a169148442f2180cd9676f92e033ec8411d3a82d39c5613d380aaab06226f5b`.
Node is 22.11.0; exact nginx build, OpenSSL details, linked libraries, hashes and
rendered configurations are retained. These versions are test inputs, not a
completed supported-runtime or advisory review.

The template binds only numeric loopback, serves only the compiled public
directory, enables TLS 1.2/1.3, disables response buffering and reconstructs
upstream headers from an allowlist. Its 1 KiB HTTP body limit does not constrain
upgraded WebSocket messages; the collector enforces the 4 MiB input cap. The
8-node / 64 KiB-head / 4/1/1 MiB candidate remains coordinated across processes.
nginx active-request and worker limits are not a total memory guarantee, and
timeouts represent inactivity between operations, not a total session duration.
See the dashboard's `docs/proxy-tls.md` for the complete settings and trust boundary.

Next, carry actual efsn WSS through PostgreSQL and the compiled browser, then drill
collector loss during actual mining. Keep runtime/dependency review, service
supervision, certificate renewal, log retention and public deployment acceptance
open. A CDN or additional proxy would change the client-address trust boundary.
Public domain, host, certificates and deployment approval are still unselected.

All test processes were stopped and the temporary certificate/private-key
directories removed. No global certificate trust, original dashboard checkout,
chain backup, wallet key, external service or public infrastructure was changed.

Evidence: [local bundle](evidence/restart-dashboard-proxy-2026-10-03/), including
the dashboard commit/patch, three attempts, cross-platform socket checks, source
and runtime hashes, cleanup and verifier. The consolidated work order is in
[restart-plan.md](restart-plan.md).

Directive references: [nginx WebSockets](https://nginx.org/en/docs/http/websocket.html),
[proxy headers/buffering/timeouts](https://nginx.org/en/docs/http/ngx_http_proxy_module.html),
[connection limits](https://nginx.org/en/docs/http/ngx_http_limit_conn_module.html),
[HTTP limits](https://nginx.org/en/docs/http/ngx_http_core_module.html),
[TLS](https://nginx.org/en/docs/http/ngx_http_ssl_module.html).
