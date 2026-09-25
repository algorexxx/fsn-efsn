# Remembered peers after the original seed disappears

25 September 2026. Baseline `31433ca`, including P10 discovery initialization.
This follows the [discovery resilience investigation](restart-discovery-resilience.md).
The scenario assumes that independent community operators remain online. Keeping
a chain alive after its sole participant leaves is outside scope.

The subsequent [bootstrap DNS candidate](restart-bootstrap-dns.md) implements
the outage/retry work below as P12 and fixes a further restored-seed interaction
as P13. This document retains the P11 baseline findings and acceptance criteria.

## What the live test establishes

A node can reconnect from its own persisted discovery database after the original
seed is switched off, without configured bootstrap or static peers. The baseline
test passes with race detection in 370.82 seconds. It uses genuine network-learned
contacts, normal production timers and an actual separate OS process for restart.
The same scenario passes after combined P11 in 370.31 seconds. The full rehearsal,
including the earlier DNS/outage cases, passes in 400.69 seconds with race
detection. The captured results are recorded in the evidence manifest.

The setup runs inside a private Linux network namespace with enabled loopback
only. It has a seed, a community peer and disposable subprocess nodes, using
public synthetic keys 1–5. The community peer's outbound dialing is disabled.
It cannot rescue the restarted node by connecting to it first. No blockchain
database, staking key, mining service, public peer or large dataset is involved.

| Phase | Assertion |
| --- | --- |
| Short initial visit | Child discovers the community peer through the seed and completes a real RLPx connection. |
| Close and inspect short-visit database | Recent pong metadata exists, but the complete community endpoint has not been persisted. |
| Short-visit cold restart | New process receives no seed/static addresses and remains disconnected for 25 seconds. |
| Mature visit | Another child stays connected for 340 real seconds, allowing the intended five-minute eligibility period and a 30-second persistence tick. |
| Close and inspect mature database | A read-only reopen verifies the exact learned community identity, IP, TCP/UDP ports and recent pong metadata. |
| Original seed stops | The remaining community peer continues listening with outbound dialing disabled. |
| Mature cold restart | New process, same local identity/database, no bootstrap or static peers, reconnects and sends test message 42 to the community peer. |
| Brand-new node | Empty peer database and no initial contacts: stays disconnected for 25 seconds despite the reachable community peer. |

The cold child knows the expected public identity only for its assertion. No
community address is supplied in its configuration. It gets the endpoint from
the persisted database. Each child is a separate process; the log records the
PIDs and zero bootstrap/static counts. The cache was not populated by direct
database writes. Small disposable databases are removed after normal test cleanup.

This is a discovery/RLPx test using a probe subprotocol, not a block propagation
or production test. The 25-second negative observations are bounded checks,
not an assertion about indefinite runtime. It does not establish behavior after
power loss, public NAT changes, a community peer changing address, or all cached
peers disappearing. Cold subprocesses use explicit empty bootstrap lists, so
the existing unresolved-DNS startup failure is deliberately not bypassed by an
unimplemented fix: it remains a separate problem described below.

## Cache age is not indefinite

Source and targeted tests distinguish three mechanisms:

- `copyLiveNodes` runs every 30 seconds and is intended to save endpoints that
  have spent at least five minutes in the discovery table. It does not save every
  short connection during shutdown. Ping/pong metadata alone is insufficient
  to reconstruct an endpoint.
- Initial seed selection admits saved endpoints whose last pong is at most five
  days old. The targeted cold-database test admits contacts aged one hour and
  two days, and excludes a contact aged six days.
- The database cleanup pass deletes contacts with pongs older than 24 hours.
  Its timer runs hourly; it is started after seed loading. The same test invokes
  cleanup directly and confirms only the one-hour contact remains. This direct
  call checks the cleanup rule, not a one-hour live timer observation.

Therefore a two-day-old contact can be eligible immediately after cold restart
and still need a fresh successful pong to survive later cleanup. A six-day-old
cache is not a dependable introduction source even if those operators are still
online. Do not remove all other contact mechanisms on the strength of peer caching.

`node/node.go` normally supplies `config.NodeDB()` when no explicit peer-database
path is set. This follows the node data directory's `nodes` location. A temporary
or empty-data-directory node is a different persistence choice. Release operating
instructions must retain the correct node data directory, not only blockchain
files, and retain explicit reachable fallback contacts as appropriate.

## P11: retain useful peers in a small network

The maturity test exposed an inherited bookkeeping defect. `bucket.bump` moves
an existing peer to the front when the same identity is observed again, replacing
the node object. The replacement can have a zero `addedAt` timestamp. The next
copy then treats a one-minute-old contact as old enough to persist. That means
the intended five-minute filter was not reliably enforced before this fix.

The deterministic baseline test reports both the lost timestamp and premature
persistence. The first P11 hunk adds one line in `p2p/discover/table.go`:
copy the previous entry's `addedAt` onto its replacement before moving it. It
preserves the existing age across repeat observations; it does not restart the
five-minute clock. The original `bucket.bump` implementation was unchanged by
earlier investigation work, including P10.

The live test caught an interaction: **the timestamp correction alone failed**
to save the community endpoint after 340 seconds, despite its continuing RLPx
connection. The failed run is retained as `timestamp-only-race.txt`; it must not
be mistaken for evidence that the one-line patch is sufficient.

The source showed a second inherited defect. A FINDNODE query collects up to 16
neighbors. A healthy small network may return fewer; its reply-collection timer
then expires. The transport returned the valid nodes together with `errTimeout`,
and the table counted that as a failed lookup. Repeated lookup failures evict the
peer, preventing stable table residence. Losing the age timestamp had allowed
early persistence that masked this interaction.

The second P11 hunk changes `udp.findnode` to return success after its collection
timeout **only when at least one validated neighbor was received**. Other errors
remain errors. Missing replies and responses containing only invalid neighbors
still fail. The response wait and validation checks remain in place; it does not
accept arbitrary nodes or change the wire format. Together, the two hunks add
six production lines and remove one across two files.

Three age tests cover young/mature persistence through reopen, repeat observations
and seed-selection versus cleanup age. Five additional cases cover a one-neighbor
reply, replies split across two packets, an invalid-only reply, no reply, and the
table's failure counter. Before the transport correction, valid partial replies
return `RPC timeout` and the responding peer's failure counter increases. After
it, the valid cases pass and both negative controls remain failures. Discovery
table, bucket, UDP and node-database regressions also pass with race detection.

P11 corrects peer-cache bookkeeping and sparse discovery replies together. It is
not required to make the baseline cold reconnection succeed; it makes useful
small-network replies compatible with the existing maturity policy. Review both
hunks together and keep the timestamp-only regression visible. It changes neither
ticket economics nor consensus, wire formats, configured seeds, DNS policy or
the stored database schema. It is
not an audit of discovery poisoning or a new Sybil-resistance guarantee.

## Remaining DNS work, now with a proven fallback

Peer caching is useful, but current startup still resolves CLI bootnode hostnames
before opening that cache. One failed lookup causes a fatal error, including when
another seed or saved peer could work. The previous subprocess tests establish
that behavior; P11 does not change it.

There is also a configuration-file boundary: `cmd/efsn/config.go` decodes TOML
before applying CLI flags. `BootstrapNodes` contains `discover.Node` values whose
`UnmarshalText` resolves DNS. An unresolved hostname in that TOML list can thus
fail before a command-line empty-bootstrap override is applied. This is a source
finding, not a new command-line end-to-end test. Remove or repair such a TOML
entry as well as selecting a reachable fallback; a flags-only workaround is
insufficient in that case.

The next networking patch should meet these concrete conditions:

1. Validate enode scheme, public identity and ports without requiring successful
   DNS. Preserve configured hostnames through configuration serialization; do not
   replace them permanently with the IP found during one successful lookup.
2. Start discovery from usable cached/static/literal contacts while hostname
   resolution is unavailable. Keep unresolved configured seeds for later attempts.
3. Resolve asynchronously with finite deadlines and bounded retry/backoff. A
   stalled DNS server must not block startup, the peer loop or shutdown. Cancel
   work when the server stops and avoid repeated identical failure logs.
4. Feed resolved endpoints into ordinary discovery. A UDP-only bootnode must
   remain useful; treating a DNS result only as a TCP static peer is insufficient.
   Preserve configured node identities, discovery ports and network restrictions.
5. Cover both CLI and TOML configuration paths, one/all failed seeds, malformed
   configuration, timeout/NXDOMAIN/SERVFAIL, changed addresses, multiple answers,
   DNS recovery after a completely disconnected start, and graceful shutdown.
6. Reuse this cold-cache fixture to prove startup and reconnection while the
   original seed's hostname cannot resolve. Separately test a fresh node joining
   through an independent community seed with every Peter-operated contact absent.

Simply replacing the existing fatal log with a warning would discard unresolved
seeds and omit retry and configuration-file behavior. That small-looking edit is
not a complete solution. The DNS implementation remains pending; no such change
is included in P11. No new finality, staking or chain-recovery policy is proposed.

Evidence, runner scripts, source identities and checksums are in
[`restart-discovery-cache-2026-09-25`](evidence/restart-discovery-cache-2026-09-25).
The three previously documented broader P2P test failures remain outside this
change. Passing targeted checks do not make the full package suites green.
