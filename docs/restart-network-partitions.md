# Network partition and reconnection rehearsal

Investigation dates: 25–26 September 2026. Runtime baseline: `27b1186` with
P1–P14. This follow-up adds P15, a three-line discovery-table admission check
that rejects the node's own identity. It changes no timer, wire format,
chain-selection rule or ticket rule.

## Self-contact defect and narrow correction

A valid discovery neighbor reply can include the requesting node itself. The
existing common `Table.add` path accepts that identity, including a different
advertised address. It can occupy an active entry or a replacement slot and
consume a subnet reservation. Once real contacts disappear, a sole self-entry
keeps the table nonempty. `lookup` skips asking the local identity, while its
empty-table refresh is only requested when the table has no entries. This
combination can suppress the normal route back to configured contacts.

Four deterministic cases fail before the correction and pass after it: ordinary
admission, admission through ping, replacement admission into a full bucket,
and a lookup whose sole self-entry suppresses refresh. A fifth test reproduces
the admission through actual signed UDP neighbor packets on simulated public
subnets; before the fix the local address incorrectly gains a reservation,
while after it only the real seed remains admitted.

P15 returns from `Table.add` when `n.ID == tab.self.ID`, before locking or
changing bookkeeping. This is identity-based, so another local/NAT address does
not evade it. It covers contacts learned from neighbors, verified pings and the
configured nursery. The existing `stuff` path already excludes self; database
seed selection already excludes the database's local identity. No record-format
change or database rewrite is needed. This is a candidate for independent review,
not a consensus upgrade or new finality mechanism.

The initial packet-loss runs were timing-sensitive: ordinary outbound dialing
fixed the full-partition fixture, but a fresh-node UDP recovery still exceeded
90 seconds. A trace-enabled retry and three repeats succeeded without a runtime
change. Those successful retries are retained alongside the failures; they do
not establish that the baseline was reliable. The deterministic and signed-UDP
before/after cases establish the self-admission defect without relying on a
particular random revalidation schedule.

## Retained inbound-only limitation

The first run passed the three static-connection cases but failed both discovery
recovery expectations. In each failing fixture the community node had
`NoDial: true`, no static peers, a literal UDP-only bootstrap contact and no
mature saved peer database. It did not reconnect within 90 seconds after a
45-second full partition. In the UDP-only case, the fresh client's DNS bootstrap
worker reported the seed recovered, yet the client still did not connect to the
community within 90 seconds after UDP returned.

The [initial source](evidence/restart-network-partitions-2026-09-25/initial-fixture.go.txt),
[failed log](evidence/restart-network-partitions-2026-09-25/live-race.txt) and
initial binary identity are retained. The ordinary-dialing fixture enables
outbound dialing on that community in those two cases. Its first run still used
the unchanged runtime and passed four cases but failed fresh-node UDP recovery.
Subsequent corrected runs retain that fixture, loss duration and recovery
deadline and add only P15 to the node. Either peer can initiate the connection
after discovery.

Source inspection explains a possible recovery gap: dead-contact revalidation
can remove entries, `NoDial` sets the dynamic-dial allowance to zero and removes
the normal dialer's lookup demand, and a literal contact does not have P12's DNS
worker. The table still has its 30-minute periodic refresh. The failed run does
not establish permanent disconnection or measure the full refresh interval.
Do not use this inbound-only configuration for the continuing producer; keep
outbound dialing enabled and keep explicit initial static contacts. P15 does
not add a new periodic refresh for inbound-only nodes. The corrected live
fixtures use ordinary outbound dialing, so they do not claim this alternate
configuration now recovers promptly.

## Corrected results

The complete five-case Linux race run passes. No case uses shortened node
timers, a manual reconnect, a node restart or a production key.

| Case | Observed result with P15 |
| --- | --- |
| Three-second complete loss | A successful local write was not received while packets were dropped. TCP delivered it after healing, and both original protocol connections survived. |
| 45-second two-way static-peer partition | Both sessions detected loss after 30 seconds; new sessions connected about 30 seconds after healing and exchanged messages in both directions. Discovery was disabled. |
| 45-second one-way static-peer partition | A message crossed in the permitted direction during the fault. Both old sessions ended, then automatic reconnection and bidirectional messages succeeded about 30 seconds after healing. |
| 45-second full loss with dynamically discovered peers and UDP-only seed | Sessions timed out, then the same running nodes recovered in 8.50 seconds after healing and exchanged messages. No static contact or bootstrap TCP service supplied recovery. |
| Fresh DNS-configured node while seed UDP is blocked | DNS questions and an independent static TCP message succeeded, but the fresh node remained peerless during the fault. After UDP returned, it discovered the community and exchanged a message in 24.40 seconds. |

These timings are measurements of this run. The kernel dropped 9, 34, 30, 76
and 9 packets respectively; the assertions require nonzero counters and actual
authenticated message receipt. The short write/receive control demonstrates why
local write success is insufficient evidence of remote delivery.

Three further runs of the previously inconsistent fresh-node UDP case also
pass with the corrected binary and normal logging. Recovery after healing took
20.40, 20.45 and 20.40 seconds. They are separate fresh fixtures, not repeated
partitions of one long-running network.

The four deterministic cases also pass natively on Windows, and the signed-UDP
case passes under Linux race detection. The complete `p2p/discover`, `p2p` and
`cmd/utils` rerun retains exactly the three previously recorded failures:
`TestParseNode`, `TestForwardCompatibility` and `TestProtocolHandshake`. No data
race is reported. This is not a claim that the broad suites are green.

The [evidence directory](evidence/restart-network-partitions-2026-09-25) retains
the unsuccessful baseline runs, successful baseline trace retries, exact source
and executable identities, and corrected outputs. The directory keeps its
25 September name because that is when the investigation began; correction
checks ran on 26 September. `check.sh`, `check-final.sh` and the trace scripts
record the earlier P1–P14 runs. `check-correction.sh` / `check-correction-all.sh`
run the correction checks; the signed-UDP baseline mode applies the saved
`baseline-table.go.txt` through a Go overlay. Reproducing the earlier runs
requires their recorded baseline and fixture, not silently substituting the
current source. `write-manifest.py` verifies outcomes and the exact three-line
runtime delta before writing identities and checksums.

## Method

The [rehearsal](../tests/restart/network_partition_linux_test.go) uses actual
`p2p.Server` instances, signed discovery v4 packets and encrypted/authenticated
RLPx connections. Its small `restartprobe` protocol sends numbered messages.
Linux `tc netem` silently drops selected IPv4 packets at the kernel interface;
healing removes that rule. The tests do not call `Disconnect`, `RemovePeer`,
`AddPeer` or restart a server to induce or repair a failure. Static contacts,
where used, are present in the original startup configuration.

Each run creates a disposable network namespace with only loopback enabled. The
test requires explicit opt-in, root, exactly one loopback interface and a network
namespace different from PID 1's. Compilation runs as the ordinary rehearsal
user; only the synthetic test process runs as root inside the isolated namespace
to configure packet loss. Each fault rule has cleanup, and namespace destruction
removes its network configuration. Host routes/firewalls are unaffected. The
test binary does not open a chain database, real wallet or public endpoint.

The priority queue sends unmatched traffic through an unaffected band; matched
traffic goes to a separate 100%-loss queue. Every healed fault must report a
positive kernel drop counter. The one-way case also delivers an authenticated
message in the allowed direction during the fault. The UDP-only case leaves DNS
resolution and an independent static TCP connection working, showing that its
fresh client's failure to discover peers is specifically a UDP-path failure.

## Existing timing and operational consequences

These values are source observations, not service-level guarantees:

| Mechanism | Current source behavior | Operational consequence |
| --- | --- | --- |
| RLPx read/write deadlines | 30 seconds per frame read; 20 seconds per frame write | A connection can remain counted while communication has already failed. A successful small TCP write can be buffered locally without remote receipt. |
| Base-protocol keepalive | Ping every 15 seconds | Idle connections still generate traffic and can detect an outage through the ordinary read deadline. |
| TCP dialing and retry history | Dial timeout 15 seconds; a completed attempt enters history for 30 seconds | Restoring connectivity does not immediately trigger a new attempt. Failed/in-flight attempts and history expiry can delay recovery. |
| Discovery lookup scheduling | A lookup at most once per four-second interval when more peers are needed | Normal outbound discovery can search again after contacts fail. |
| Literal bootstrap fallback | Eligible literal contacts with nonzero TCP ports become direct-dial candidates after 20 seconds without peers | A UDP-only contact or hostname does not establish that TCP fallback works; the dynamic tests deliberately exclude it. |
| Bootstrap DNS worker (P12) | Five-second lookup deadline; failure retry starts at 10 seconds, doubles to five minutes; success refresh every 30 seconds | Healthy DNS alone cannot overcome blocked UDP; recovery can wait for the next attempt. |
| Table revalidation and persistence | Revalidation scheduled randomly up to 10 seconds apart; contacts must mature five minutes before copying to the database | A short-lived in-memory contact is not a guaranteed cold-restart fallback. Revalidation may forget unreachable contacts during a partition. |
| Periodic table refresh | 30 minutes, with additional refresh requests from lookup/hostname paths | An inbound-only node with no active lookup or hostname worker has fewer ways to reintroduce itself after its contacts disappear. |

The sources are [server](../p2p/server.go), [peer](../p2p/peer.go),
[RLPx](../p2p/rlpx.go), [dial scheduling](../p2p/dial.go),
[table](../p2p/discover/table.go) and [bootstrap DNS](../p2p/discover/bootstrap.go).
The evidence pins their exact blob identities.

For the proposed launch, keep normal outbound dialing and v4 discovery enabled
on the donation node, publish its continuing P2P identity, and configure a
reviewed static connection between the two initial nodes. Once other operators
join, retain usable community contacts and mature peer databases. A fresh node
still needs an initial reachable contact; a network outage is not solved by DNS
resolution alone. See the [operator network profile](restart-network-profile.md)
for port, identity, restored-peer-list and NAT handling.

After an outage, assess successful remote observations and continuing head
progress as well as local process/peer counts. Do not use the static-pair retry
timing as a fixed deadline for every public node. Endpoint changes, old contact
lists, DNS backoff, NAT and firewall failures require their own diagnosis.

## Boundaries and next check

This is transport/discovery evidence. It does not mine competing blocks, invoke
the downloader or exercise purchase recovery during the packet-loss interval.
Earlier [peer reorganizations](restart-purchase-storage-and-peers.md) and
[two-purchase rollback/miner continuation](restart-purchase-nonce-rollback.md)
remain separate evidence. A fixed restart anchor rejects incompatible recovery
history; it does not prevent ordinary reorganizations between compatible
post-anchor branches. This work adds no ongoing finality design.

Next combine controlled loss and healing with the synthetic two-miner fixture:
preserve each side's blocks, purchases and nonces, then check convergence,
receipts, saved purchase intent and the documented missing-nonce repair path.
That should use public test keys, since conflicting production signatures can
have multiple-mining-report consequences. It does not require another large
backup copy.

Public IPv4/IPv6 routing, actual firewall/NAT behavior, endpoint changes during a
partition, long or repeated outages, probabilistic loss, delay/reordering, and
native Windows packet-loss behavior remain outside these cases. The existing
three inherited broad networking-suite failures remain recorded in the earlier
reports and the affected-suite rerun; this correction does not fix them.
Independent review, release packaging and real launch acceptance remain open.
