# Bootstrap DNS outages and recovery

25 September 2026. Baseline `d7fa207`. This follows the
[peer-cache investigation](restart-discovery-cache.md). P12 and P13 are review
candidates on the investigation branch, not an approved release.

## Result and intended scope

The bootstrap path now keeps configured hostnames and resolves them in the
background. An unavailable bootstrap hostname no longer prevents CLI or TOML
configuration from loading or stops discovery using other contacts. A fresh node
can wait for DNS to recover and join without restarting. The actual `efsn
dumpconfig` command preserves the hostname, applies an explicit empty CLI override,
and still rejects malformed configuration.

The live rehearsal uses a private Linux network namespace with loopback only,
synthetic public keys and tiny disposable peer databases. It exercises real UDP
discovery and RLPx probe messages. It neither mines blocks nor accesses the backup,
real wallets, public peers, W: restore or a chain database.

The final combined result and exact durations are recorded in the
[evidence directory](evidence/restart-bootstrap-dns-2026-09-25). The corrected
combined run passes all seventeen live leaf cases with race detection: 44.47
seconds for the DNS group and 404.24 seconds for discovery/cache, including
370.37 seconds for genuine cache maturation and cold restart. Native Windows
checks and focused Linux regressions also pass. The earlier
DNS-only run passed in 44.48 seconds; it predates the extra cache corrections and
explicit in-flight shutdown case. Do not substitute that earlier result for final
candidate verification.

## P12: bootstrap-specific parsing and resolution

`discover.ParseBootnode` parses and validates a complete enode without looking up
its hostname. It validates the public key, hostname syntax, IP literals, ports and
URL suffix. A UDP port is required; TCP zero is permitted for a UDP-only seed.
CLI v4 bootstrap flags use this parser. The existing `BootstrapNodes` TOML key and
array-of-enode-strings format remain the same; its Go slice type now has a
bootstrap-specific TOML decoder. Hostname-based entries retain their name when
serialized, even after successful resolution.

Ordinary `ParseNode`, static/trusted peer decoding and v5 discovery retain their
existing resolution behavior. `Node` has private hostname metadata for configured
bootstrap entries. Resolved discovery-table nodes contain numeric addresses. A
test compares the RLP bytes against the original exported-field layout; the
on-disk peer record format is unchanged. This is not Ethereum DNS-tree discovery
and introduces no DNS signature scheme or dependency.

| Resolver behavior | Bound / effect |
| --- | --- |
| Workers | One worker per configured hostname entry, owned by its discovery table. Literal contacts need no worker. |
| DNS lookup | Context deadline of five seconds. Other seeds, startup and the peer loop proceed independently. |
| Failed contact retry | Ten seconds after a failed attempt, then exponential backoff capped at five minutes. Successful contact resets backoff. |
| Successful contact refresh | Resolve again after thirty seconds; retain the configured hostname throughout. |
| Multiple answers | Try at most sixteen addresses from the resolver result, continuing past unreachable answers. Stop at the first authenticated, allowed responding endpoint. |
| Admission | Validate address and configured network restriction before sending a ping; require a reply from the configured public identity before the resolver inserts its endpoint. Ordinary inbound discovery rules remain in force. |
| Recovery | Add the endpoint to normal discovery and request refresh, including for UDP-only seeds. It is not converted into a mandatory static TCP connection. |
| Logging | Warn on entry into a failure period, suppress repeated failures, report recovery. |
| Shutdown | Cancel outstanding lookups/retry timers, close transport, wait for resolver workers before closing their database. |

TCP fallback receives only literal, TCP-capable bootstrap entries. Deferred names
enter through discovery after resolution. The existing dial scheduler itself is
unchanged. With discovery disabled, bootstrap names are retained but no resolver
workers run. Syntax errors remain configuration errors even in that mode.

## P13: restored contacts must not compete with current endpoints

Review of DNS address moves exposed two cache-loading issues:

1. The seed iterator decoded a stored node without reconstructing its private
   routing hash. That placed a restored copy into a different bucket from a
   freshly observed copy of the same public identity. The regression records
   both old and new endpoints simultaneously. Recompute the hash from the node ID
   after decoding, as the existing single-node database reader already does.
2. Periodic seed loading could replace a current in-memory endpoint with the
   old cached endpoint. Cache insertion now checks identity under the table lock
   and keeps an existing entry. Explicit literal fallback configuration retains
   its existing insertion behavior.

The targeted test seeds a tiny database with the old endpoint, runs resolution
with a responding test transport, then performs cache loading. Before correction
it finds two entries with the same identity at different addresses. Afterwards
there is exactly one entry at the current address. This is a synthetic cache test,
distinct from the real UDP move and separate-process cold restart.

P13 changes local discovery bookkeeping, not the database schema or maturity/age
limits. P12/P13 do not change consensus, fork choice, ticket purchases, rewards,
balances, the restart anchor, configured default seed identities or wire packets.

## Verification cases

- Bootstrap parser and TOML round-trip with unresolved names, IPv4, IPv6 syntax
  and a UDP-only seed; malformed key, host, port and suffix rejection.
- Actual `efsn dumpconfig` with unresolved TOML bootstrap, empty CLI override and
  malformed configuration. This closes the previous source-only TOML finding.
- CLI matrix with one/all failing names in either order, discovery disabled,
  empty lists and malformed input. Well-formed unresolved names now succeed;
  malformed input still fails.
- Actual five-second lookup deadline and cancellation against a blocked resolver.
- Fresh client initially has NXDOMAIN, SERVFAIL and nonresponding DNS contacts.
  Once one name recovers, its first A answer is unreachable and the second leads
  to a UDP-only seed. The client reaches a community node whose outbound dialing
  is disabled and exchanges probe message 51.
- The same running client contacts that seed at a new IP with its identity and
  port unchanged, without reparsing configuration. The replacement seed starts
  with an empty discovery table.
- A DNS answer outside `NetRestrict` is not contacted. Server shutdown cancels an
  in-flight nonresponding lookup within one second.
- The genuine cache rehearsal waits 340 real seconds, closes and inspects the
  peer database, stops the original seed, and starts a separate process retaining
  an NXDOMAIN bootstrap entry. It must reconnect using saved contacts and send
  message 42 to the nondialing community node. Short-visit and fresh-cache controls
  remain disconnected during their 25-second observation windows.
- Focused discovery, bucket, database, dialing, server and CLI regression suites
  pass with Linux race detection. The complete affected networking suites were
  also rerun and retain exactly `TestParseNode`, `TestForwardCompatibility` and
  `TestProtocolHandshake` as the three previously documented failures, with no
  race report. This is not a full-package green claim.
- Native Windows checks pass for bootstrap parsing/TOML round-trip, unchanged RLP
  encoding, cache refresh and resolver deadline/cancellation. The executable was
  cross-compiled with CGO disabled and run on this Windows machine; Linux race
  detection is separate. Windows observed a five-second lookup deadline and
  cancellation in approximately 61 milliseconds.

## Limits and next checks

The DNS and IP-move tests use IPv4 loopback. IPv6 syntax is covered, but public
dual-stack reachability, NAT mappings, firewall behavior and real independent
operators are still deployment checks. Resolver order and the sixteen-answer cap
are explicit limits; the client does not promise to try every possible record in
an arbitrarily large answer. The refresh interval is a local policy, not DNS TTL
tracking. Backoff also means recovery need not be immediate after a long outage.

There is a separate inherited public-subnet accounting concern in `bucket.bump`:
it can replace a peer's IP without adjusting the table/bucket subnet counters.
Loopback is exempt from those limits, so the passing move rehearsal does not
resolve this concern. The next targeted investigation must cover admitted and
rejected moves between public subnets, same-subnet moves at capacity, and stale
revalidation results during a move before claiming public migration readiness.
No correction for that separate path is included here.

Failed hostname-based static/trusted configuration can still use the old blocking
parser, and v5 still requires IP addresses. The scoped behavior here applies to
v4 bootstrap configuration. Use literal static fallbacks where needed and review
all final release configuration paths.

Fresh installations still need some working introduction. Independent community
seed identities and domains must be added as other operators join; multiple
addresses controlled by Peter do not establish independence. The agreed minimal
initial launch remains unchanged. Continuing the chain after its sole participant
leaves remains outside scope.
