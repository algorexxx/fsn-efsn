# Discovery resilience and operator departure

25 September 2026. Investigation baseline `0df4014`; original upstream local
`master` is `c5f0174`. Evidence is in
[`restart-discovery-2026-09-25`](evidence/restart-discovery-2026-09-25).

Fusion's existing discovery can introduce peers through one seed, and connected
peers can continue communicating after that seed stops. A new node still needs
a reachable initial contact. DNS names help move a service, but neither a name
nor several servers under one person's control guarantees survival after that
person leaves. This work preserves the selected minimal initial launch and adds
a concrete path toward independent operation.

## Results against the actual client

The opt-in Linux rehearsal uses a private network namespace with only loopback,
public test keys 1–5, a controlled local DNS responder, and real UDP discovery
and authenticated RLPx connections. It opens no preserved blockchain database,
uses no staking keys and copies no large data. Ten leaf cases pass with race
detection after P10 in 30.44 seconds.

| Scenario | Observed behavior |
| --- | --- |
| V4 enode with a resolvable hostname | Parsing resolves it and retains one IP; the hostname is absent from the resulting node representation. |
| DNS address changes, same public node identity | Previously parsed node keeps the old IP; parsing the original hostname URL again obtains the new IP and retains the identity. |
| Two IPv4 answers, only the second endpoint accepts TCP | Parser selects the first returned address; the TCP dial fails without trying the second. Explicitly parsed new endpoint connects. This is not DNS load balancing or automatic failover. |
| V5 enode with the same resolvable hostname | Rejected with `invalid IP address`. |
| V4 CLI: healthy seed | Configuration succeeds. |
| V4 CLI: unresolved seed before or after a healthy seed | Both orders exit with status 1 at `Bootstrap URL invalid`. |
| V4 CLI: all configured seeds unresolved | Exits with status 1. |
| V4 CLI: unresolved seed with `--nodiscover` | Still exits with status 1; parsing precedes disabling discovery. |
| V4 CLI: explicit empty lists, with or without `--nodiscover` | Configuration succeeds with zero bootstrap entries. |
| V4 CLI: malformed enode | Exits with status 1. |
| Two fresh nodes, one reachable seed | Discover each other without static links, complete RLPx and exchange a test subprotocol message. |
| Seed stopped after introduction | Other peers exchange messages immediately and after a further 25 seconds. |
| Fresh node with only the stopped seed, or with no seeds | Starts but remains disconnected during the 25-second observation, beyond the existing 20-second fallback-dial threshold. |
| Reachable literal-IP static peer supplied to each stranded node | Both connect and exchange messages without restarting or restoring the seed. |

The live messages use a small test subprotocol, not Fusion block production or
synchronization. The CLI cases call the real `SetP2PConfig` in subprocesses to
observe its fatal exits; they are not full command-line node launches. DNS
NXDOMAIN is exercised, not DNS timeouts, SERVFAIL, IPv6 ordering, public NAT or
firewalls. Persistence across process restart and simultaneous peer outages are
not established by this test.

Source boundaries: `p2p/discover/node.go`, `cmd/utils/flags.go`, `p2p/server.go`,
`p2p/dial.go`, `p2p/discover/table.go`, and `node/api.go`. A static dial's existing
`resolve` operation searches discovery by node ID; it does not re-query the
original DNS hostname. Persistent static-node file parsing logs and skips an
unresolvable entry, whereas CLI v4 bootstrap parsing is fatal. Neither behavior
supplies ongoing hostname refresh. Serialized parsed enodes contain IPs, so
operators must retain original hostname configuration when expecting subsequent
startup resolution.

## P10: initialize discovery before starting its background work

The first live run reported a race between `newUDP` assigning `udp.Table` and a
background `findnode` reading through that pointer. `newTable` starts its loop
before returning to `newUDP`; seed lookups can therefore begin before the UDP
transport receives its table. These runtime files were byte-equivalent through
Git to upstream `master` before this correction. A premature nil dereference is
a possible consequence of the ordering, not an observed crash in these runs.

The production correction moves the existing `go tab.loop()` from `newTable`
to `newUDP`, after `udp.Table` assignment and UDP loop startup: one deleted line
and one added line in two files. The six table-unit-test constructor callers now
start their own loop. There are no wire-format, consensus, fork-choice, ticket,
DNS-resolution-policy or bootstrap-default changes.

An initial test setup incorrectly used separately allocated ephemeral TCP and
UDP ports; its live connection check timed out while also exposing the race.
Both its source and log are retained as `initial-test.go.txt` and
`initial-race.txt`. The fixture was corrected to give the server one explicit
port for both protocols, and to retain the seed identity before stopping it.
The corrected fixture against unchanged production code completed every live
connectivity check but failed race detection in 60.92 seconds
(`baseline-race.txt`). The same fixture after P10 passes in 30.44 seconds
(`current-race.txt`). This comparison isolates the runtime correction from the
earlier fixture mistake.

The focused discovery-table, bucket, UDP, dial and server tests pass with Linux
race detection (`package-focused-race.txt`). Full `p2p/discover` and `p2p` suites
are **not green**. Their failures are retained and reproduced with the pre-P10
source overlay:

- `TestParseNode`: legacy expected errors differ from the DNS-enabled parser
  and current Go URL error formatting.
- `TestForwardCompatibility`: inherited Ethereum test vectors use packet types
  1–4; Fusion's decoder uses packet types 40–43.
- `TestProtocolHandshake`: disconnect-message encoding/expected-size mismatch
  (`got 2, want 1`). The relevant runtime and test files are unchanged from
  upstream `master`; this follow-up does not establish or repair its wider impact.

P10 is an additional separately reviewable operational correction in the
[permanent patch inventory](restart-node-patch-review.md). It does not cure the
DNS startup failure policy. Do not describe the full repository suite as passing.

## Minimal operating procedure with the current implementation

Keep one reachable discovery-v4 endpoint for the initial launch, possibly on the
continuing producer. Configure a stable P2P identity, an explicit listening port
and the appropriate public address/NAT announcement. Its DNS enode identifies
that public key; changing an A record cannot substitute a different node key.
Each additional independent seed should have its own identity and enode entry.
A seed or non-producing full node requires no staking ticket.

If a seed service stops but its DNS still resolves, existing nodes and reachable
alternative contacts can operate. If its hostname stops resolving, current
startup fails even when cached peers or another configured seed could have
worked. Until that behavior is changed, operators must remove the failed entry
or explicitly override bootstrap lists, for example
`--bootnodesv4="" --bootnodesv5=""`, and supply a reachable peer. Leaving
discovery enabled allows that initial contact to introduce more peers.

A running node can receive a reachable enode through the existing private
`admin.addPeer` interface. That API parses the URL at the time it is called;
re-adding a hostname can therefore resolve a changed address. Persist deliberate
static fallbacks in the node configuration for restarts. Do not expose the
administrative interface publicly. The live rehearsal tests the underlying
`Server.AddPeer` path with literal IPs; it does not exercise the admin RPC itself.

No public hostname, provider, node identity or deployment is selected here.

## Proposed resilience work and a retirement test

The user's concern is that an already participating community should survive
Peter shutting down all his infrastructure. Assume other operators are active
when evaluating that departure. Preserving a chain after its sole participant
leaves is explicitly outside this investigation. This does not require finding
a validator fleet before the agreed two-node launch.

1. **Remove the avoidable startup dependency.** Design a separate networking
   change so temporary DNS failures are visible but do not prevent using cached
   peers, static peers or other seeds. Retain unresolved hostname entries for
   bounded retries and re-resolution when disconnected. Keep malformed URLs and
   invalid node identities as configuration errors. Simply skipping a failed
   lookup permanently is insufficient. This is proposed, not implemented by P10.
2. **Retain working contacts.** Verify actual on-disk discovery peer persistence
   and cold restart with all original seeds unavailable. Existing code has a
   node database and seed loading; the live test above uses fresh in-memory
   databases and does not prove this restart behavior. Test persistence maturity,
   aging, cold restart and all-seeds-down recovery before relying on it.
3. **Add independent introductions as people join.** Encourage reachable
   community nodes to serve discovery, publish their enodes and put independently
   controlled endpoints into release configuration. Two or three operators on
   separate domains/providers is a reasonable eventual target, not a guarantee
   or an initial launch gate. Several names under Peter's single domain still
   share ownership risk. A discovery endpoint can be a lightweight Fusion
   bootnode or an ordinary reachable full node; it is not required to mine.
4. **Make contact information portable.** Publish operator instructions and
   reviewed fallback enodes in the organization repository and independently
   maintained copies. Let users replace the seed list. Provide shared project
   maintenance and domain continuity, while also supporting domains owned by
   independent operators. A website or signed directory should not become the
   only route into the network.
5. **Prove departure with an outage rehearsal.** Once independent operators
   exist, disable every Peter-operated seed and endpoint. Verify that existing
   peers remain connected, a previously connected node restarts from its own
   peer database, and a brand-new installation finds independent peers. Observe
   the existing independent operators continuing their normal operation.

The cold-cache and fresh-install tests should be repeated with Peter's DNS names
returning errors, not merely with his servers refusing connections. A fresh
installation already covers having no local peer cache. Whole-chain shutdown
and recovery after the sole participant leaves are outside this work; the current
25-second seed outage establishes only the connectivity behavior described above.

## How other networks approach this

Bitcoin combines community-operated DNS seeds, address exchange between peers,
a persistent local peer database, and built-in/manual fallback contacts. The
layering lets returning nodes use known peers and gives new nodes more than one
introduction source. The [Bitcoin developer guide](https://developer.bitcoin.org/devguide/p2p_network.html#peer-discovery)
describes those mechanisms; its exact timing examples are historical and are not
requirements for Fusion. Bitcoin Core also publishes
[expectations for seed operators](https://github.com/bitcoin/bitcoin/blob/master/doc/dnsseed-policy.md).

Ethereum's execution-layer Geth uses bootnodes to introduce peers and discovery
to exchange contacts, with configurable static peers as another option.
[Geth networking documentation](https://geth.ethereum.org/docs/fundamentals/peer-to-peer)
describes those roles. Ethereum also has
[signed, updateable DNS node lists](https://eips.ethereum.org/EIPS/eip-1459), with
links between independently maintained lists; the Ethereum project's
[published lists](https://github.com/ethereum/discv4-dns-lists) are an implementation
example. Those lists are distinct from Fusion's current one-hostname-to-one-IP
parsing. Their support must not be inferred from Fusion's Geth ancestry.

My recommendation for this restart is to harden the existing discovery path and
prove independent contacts before adopting a larger discovery subsystem. Signed
DNS lists are a possible later improvement, requiring their own compatibility,
update, failure and trust review. They still require somebody to operate the
lists and reachable peers. None of this needs a new consensus or finality rule.
