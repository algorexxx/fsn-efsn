# Discovery address changes and stale probes

25 September 2026. Follow-up to [bootstrap DNS](restart-bootstrap-dns.md).
Baseline: `a5a6bea5670a2da51a3dd938cc3921b7f57b7731`. P14 is a proposed
discovery-table correction, not a release approval. The agreed two-node launch,
ticket economics and restart ancestry are unchanged.

## Findings

An existing peer can announce a new endpoint while its old endpoint has a ping
or FINDNODE request in flight. The baseline replaces the stored address by node
identity, but does not transfer the table and bucket subnet reservations. This
both leaves unused capacity occupied in the old subnet and bypasses the existing
limit in the new subnet. Loopback moves in the earlier DNS rehearsal could not
detect this because loopback addresses are exempt from these limits.

The old probe can then overwrite or evict the new entry. Comparing only node ID
does not distinguish the entry that was probed from the entry received during
that probe. This also applies to a port change, a fresh observation at the same
endpoint, and removal followed by re-addition.

Related replacement-list paths have the same bookkeeping problem: an existing
waiting identity ignores address refreshes; promoting it into a vacancy reserves
its address a second time; and promotion after a failed ping leaves `addedAt`
zero, bypassing the existing five-minute active-table maturity filter. Repeated
deletion of an absent entry can also release a different peer's reservation in
the same subnet. These are local discovery defects, not chain-history defects.

## P14 implementation boundary

All runtime changes are in `p2p/discover/table.go`: 63 added and 23 removed lines
relative to the baseline, including a shared identity lookup helper.

- Transfer a reservation under the existing table lock. Release the old slot,
  attempt the new one, and restore the old slot if either quota rejects it.
  A same-subnet move at capacity therefore remains possible. A rejected active
  move keeps its previous endpoint and cannot create a duplicate replacement.
- Apply the same transfer rule to waiting replacements. Promotion reuses the
  existing reservation. Dead-entry replacement starts the normal active-table
  residence interval when the replacement is promoted.
- Apply revalidation only if the selected entry is still the exact tail entry.
  Apply FINDNODE failure accounting and eviction only to the exact active entry
  queried. Read/update its failure count under the table lock. A newer observation
  supersedes the older probe even when its endpoint is unchanged.
- Delete and release a reservation only when that exact entry is present.
- Extend P13's cache-preservation check to waiting replacements, so an old disk
  record cannot undo a current replacement address after refresh support is added.

The existing limits remain two addresses per bucket per /24 and ten per table
per /24, including their existing IPv6 prefix policy and LAN exemptions. No new
limit, failure threshold, packet format, database schema or persistent generation
field is introduced. Failure counts for obsolete/unadmitted lookup entries are
ignored; valid returned neighbors are still processed. Counts previously recorded
for an identity are not reset merely because its endpoint changes.

This changes local peer retention after recovery as well as during startup.
It does not change consensus, fork choice, validation, tickets, rewards, balances,
the anchor, bootstrap configuration or signer custody.

## Evidence

The [evidence directory](evidence/restart-peer-addresses-2026-09-25) contains the
before/after logs, reproduction scripts, source/binary identities, result summary
and checksums. The baseline runs substitute only the committed baseline
`table.go` through a Go source overlay; they execute the same final test sources.

| Check | Baseline | Corrected candidate |
| --- | --- | --- |
| Deterministic address/replacement/stale-probe matrix | 23 of 31 cases fail; eight controls pass | All 31 pass with Linux race detection |
| Actual signed UDP move between two /24 subnets | Endpoint changes but reservation remains in old subnet | New endpoint and both reservation sets agree; bidirectional ping/pong succeeds |
| Focused discovery, bucket, database, dialing, server and CLI regressions | Earlier baseline evidence retained separately | Pass with Linux race detection |
| Native Windows deterministic matrix | Linux baseline failures retained above | All 31 cases pass on this machine; cross-compiled with CGO disabled, without Windows race detection |
| Existing DNS live/command rehearsal | P12/P13 evidence retained separately | Six leaf cases pass with Linux race detection in 44.31 seconds using a newly built `efsn` |

The DNS rerun covers real-command TOML/CLI handling, failed-name recovery through
a UDP-only seed, multiple answers, address refresh, network restriction and
shutdown cancellation. The earlier 340-second maturation/cold-process rehearsal
was not repeated in this follow-up; focused cache/maturation tests pass here.

The complete affected networking suites still fail exactly the three previously
recorded tests: `TestParseNode`, `TestForwardCompatibility` and
`TestProtocolHandshake`. Their output is retained in `broad-race.txt`; no race
report appears. This is not a full-suite green claim. The actual Linux `efsn`,
Linux rehearsal executable and Windows discovery test executable all build.

The deterministic tests cover accepted and rejected bucket/table quota changes,
same-subnet changes at capacity, LAN/public changes, IPv4/IPv6 accounting,
released-capacity admission, replacement refresh/promotion, cache preservation,
promotion maturity, delayed ping success/failure, delayed FINDNODE success/failure,
normal current-entry controls, and repeated deletion. Bucket placement in these
unit tests is deliberate test data; the live UDP case uses real identity hashes.

The live UDP runner creates only a loopback interface in a new Linux network
namespace and assigns `172.0.1.1`, `172.0.2.1` and `172.0.3.1` to it. These addresses
exercise the non-LAN reservation path; there is no interface or route to a public
network. Keys are public deterministic test keys. No chain database, real wallet
key, mining, signing of blocks, remote deployment or large disk job is involved.

## Remaining boundaries

Public TCP/UDP reachability, NAT announcements, firewalls, real IPv6 connectivity,
partitions and independently operated contacts remain to demonstrate. IPv6
bookkeeping tests do not establish IPv6 connectivity. The delayed-probe tests
control completion inside the transport interface; the separate live UDP case
establishes packet-to-table behavior without claiming every packet ordering.

This correction does not authenticate arbitrary neighbor advertisements or add
anti-replay rules to the discovery protocol. Existing transport trust and endpoint
proof behavior remain separate review surfaces. An exhausted subnet quota can
legitimately reject a moved address; DNS retry does not override discovery limits.
Literal fallback configuration continues to be explicit operator input. Static/
trusted parsing and v5 discovery are unchanged.

Review P14 with P11's maturity correction and P12/P13's DNS/cache behavior before
extracting the release patch set. The broader restart gates remain in the
[plan](restart-plan.md); the investigation branch is not a selected release.
