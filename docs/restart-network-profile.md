# Operator network profile and inherited configuration limits

25 September 2026. Source baseline: `c6ab88e576da531be8c5486df22a4e05a3e39bc1`.
This follow-up adds tests, evidence and an operator template. **It adds no node
runtime changes and no P15.** The existing P1–P14 list still requires review.
This is the networking portion of the restart procedure, not a complete launch
command, release approval or instruction to begin mining.

## Minimal two-node arrangement

Use the long-lived donation node as the initial public DNS introduction. Its
P2P identity and endpoint can remain available when the temporary backup node
finishes its role. Discovery does not require that the node is already mining.
The approved backup-wallet block and donation-wallet handover remain unchanged.

| Instance | P2P port when sharing an IP | Role |
| --- | --- | --- |
| Donation node | 40408 TCP **and** UDP | Long-lived peer and initial public DNS contact; donation-wallet producer at the approved handover |
| Backup node | 40409 TCP **and** UDP | Temporary peer and producer for its approved block |
| Optional later dedicated bootnode | 40407 UDP | Introduction only; not needed in addition to the donation node for initial launch |

The two nodes need separate datadirs and separate P2P keys. A P2P `nodekey` is
independent of the validator wallet key. Retain each P2P key across restarts and
IP moves. Avoid distributing or duplicating a snapshot's old `nodekey`: this
client reads a legacy root-level key before the instance-directory key when the
old file exists. Explicit `--nodekey` paths remove that ambiguity. The node's
public enode identity must not be confused with a 40-character wallet address.

For containers or manual NAT, preserve each port number end to end: donation
40408 outside to 40408 inside, backup 40409 outside to 40409 inside, separately
for TCP and UDP. Run the backup process with `--port 40409`; merely mapping
external 40409 to an unchanged internal 40408 does not make this client advertise
40409. This NAT interface has no advertised-external-port override. Avoid
`--port 0` for published discovery nodes: UDP and TCP are bound separately and
are not guaranteed to receive the same ephemeral port.

The public introduction is an enode with the donation node's public P2P key:
`enode://<PUBLIC_P2P_KEY>@<REVIEWED_DNS_NAME>:40408`. The name and key are not yet
selected. If a UDP-only bootnode is used later, publish its contact with TCP zero
and explicit discovery port: `enode://<PUBLIC_P2P_KEY>@<DNS_NAME>:0?discport=40407`.
TCP connection checks do not test that UDP-only service.

## Explicit configuration inputs

[restart-network-profile.toml](restart-network-profile.toml) is the tested base
template. It clears HTTP/WS listeners and telemetry and explicitly sets empty
bootstrap, static and trusted lists. Fill only the reviewed peer lists; provide
bootstrap contacts through `--bootnodesv4` or the TOML `BootstrapNodes` list.
Empty lists leave a fresh node without an introduction until one is supplied.

The networking arguments to integrate into the reviewed launch commands are:

```text
--config <reviewed-network.toml>
--datadir <this-instance-only-datadir>
--nodekey <this-instance-only-p2p-key-file>
--syncmode full
--port <40408-for-donation-or-40409-for-backup>
--nat extip:<numeric-public-IP>
--v5disc=false
--bootnodesv5=
--bootnodesv4=<reviewed-enode-list>
```

`extip` changes the advertised IP; it does not create router mappings, change
the listening interface or open a firewall. `extip` accepts a numeric IPv4 or
IPv6 address, not a hostname. If binding directly to a stable public interface,
an explicit `Node.P2P.ListenAddr` and `--nat none` are alternatives; validate the
actual advertised address. With wildcard listening and no successful external-IP
selection, the startup enode can contain an unspecified address such as `[::]`.

Both UDP discovery and TCP peer traffic need reachability. An established/static
TCP peer can work even when discovery is disabled or unavailable; that does not
prove inbound discovery is working. Keep HTTP/WS/admin signing access private as
specified in the main restart plan. The template is only one configuration layer:
later flags can enable services or replace lists, so retain the exact invocation.

Review restored `static-nodes.json` and `trusted-nodes.json` in both the datadir
root and instance directory. With nil lists, `node.New` loads these files into the
actual server while the original input configuration still has zero entries.
`dumpconfig` therefore cannot establish that no persistent peers will be loaded.
Explicit non-nil empty TOML arrays suppress both file-based lists, as tested.
Static peers are connection targets; trusted peers bypass the normal peer limit
and are not an independent discovery mechanism. Neither confers consensus trust.

## Configuration defects and current disposition

| Finding | Evidence / disposition for this launch profile |
| --- | --- |
| External-IP `dumpconfig` output cannot be reloaded | Actual reload rejects the serialized NAT array with `cannot unmarshal TOML array into nat.Interface`. Keep NAT in explicit CLI arguments and maintain the reviewed template; do not reuse the full dump as the configuration file. |
| Disabled and automatic NAT both disappear from diagnostic output | Runtime configuration tests confirm omitted TOML NAT retains `node.DefaultConfig`'s automatic adapter, while explicit `--nat none` clears it. A missing NAT field in a dump does not distinguish these states. |
| Empty v5 bootstrap list is omitted | Reloading an empty-list dump restores the four legacy v5 contacts. Keep `--bootnodesv5=` and `--v5disc=false` explicit. v5 is off by default for the full-node profile, so retained contacts alone do not mean they were contacted. |
| `--nodiscover=false` still disables v4 | The code checks whether this flag was supplied. Omit it to retain v4 discovery; use the tested TOML `NoDiscovery = false`. |
| `--nodiscover` does not override explicit `--v5disc` | Actual command produces v4 disabled/v5 enabled. Do not equate the former with all discovery disabled. |
| External IP is sampled at startup | Recording NAT tests show one query per start; the same P2P identity advertises the new address after restart. The server does not refresh its own external IP when a router address changes. |
| NAT errors do not make startup fail | A recording adapter returning mapping/external-IP errors still permits startup and leaves the local address advertised. A running process is not a public-reachability check. |

These inherited configuration/tooling limitations are explicitly avoided by the
profile. They remain candidates for separate usability fixes if those alternate
workflows are required; none needs a consensus change. NAT mapping lifetime and
refresh are 20 and 15 minutes respectively in the source. The rehearsal verifies
initial map/delete requests, not a real router or the 15-minute renewal cycle.

P12 refreshes a client's configured bootstrap DNS. After the server's public IP
changes, update the DNS record and the server's numeric external-IP configuration,
then restart that server with its existing P2P key. DNS alone does not refresh
its advertised address. For two nodes behind a router without NAT loopback, use
reviewed local-address static contacts for their mutual connection and test the
published contact from another network.

Keep ordinary outbound dialing enabled; do not carry `NoDial = true` into the
continuing producer's configuration. The [packet-loss follow-up](restart-network-partitions.md)
retains two baseline cases where an inbound-only community peer did not recover
within 90 seconds after connectivity returned. Ordinary dialing also exposed a
separate self-contact defect, corrected by P15. Its corrected fixtures keep
outbound dialing enabled; they do not prove prompt inbound-only recovery.
Keep explicit static contacts between the two startup nodes, and verify remote
communication/head progress after an
outage; process status and a briefly retained peer count are insufficient.

## Old infrastructure inventory

The [machine-readable inventory](evidence/restart-network-profile-2026-09-25/endpoint-inventory.json)
records 52 references in 22 files from 766 scanned tracked files. It excludes
investigation evidence, vendored material and tests, distinguishes hostnames,
literal bootstrap addresses, image namespaces and original-repository links,
and does not contact any endpoint or record telemetry credentials.

| Surface | Remaining references / release action |
| --- | --- |
| `params/bootnodes.go` | Four mainnet `bn1`–`bn4.fusionnetwork.io` contacts on 40407; two `boottestnode1`/`boottestnode2` testnet names; four literal v5 entries at `35.177.226.168:40404` and `40.118.3.223:30304/30306/30307`. Replace release v4 defaults only once operator-owned identities/names are selected; explicit profile overrides work now. Do not enable the inherited v5 contacts. |
| Three `docker-entrypoint*.sh` scripts | Construct telemetry targets at `node.fusionnetwork.io` or `devnodestats.fusionnetwork.io`, with embedded old credentials. Bypass these entrypoints or replace them during release packaging. Supplying ordinary efsn networking flags to these wrappers is not supported by their option parser. |
| `QuickNodeSetup/fsnNode.sh`, `QuickNodeSetup/fsn.yml`, root README | Old `fusionnetwork/*` images and a script downloaded from the original GitHub organization. Freeze community-owned build/package inputs before publishing installer instructions. The existing isolated historical gateway remains separate. |
| Root README and Dockerfiles | Several Docker command examples publish only P2P TCP; the standalone bootnode example suggests a TCP/telnet check for a UDP service. Gateway examples publish RPC/WS broadly. Dockerfile `EXPOSE` metadata does not supply host port mappings. Do not treat these as the launch runbook. |
| Source/reference links and `common.SystemAsset.Description` | Original repository/API links are provenance/reference material. The `https://fusion.org` system-asset description is metadata, not a bootstrap endpoint. Do not bulk-replace such strings as infrastructure cleanup. |

## Verified scope and next deployment check

The final Linux race run passes 17 leaf cases: seven live network-profile cases,
four configuration-input cases and six existing DNS/command cases. Ten additional
actual `efsn dumpconfig` cases pass their expected acceptance/rejection checks.
The [evidence directory](evidence/restart-network-profile-2026-09-25) pins the
source, reused node binary, test executables and output checksums.

The live tests run with only a loopback interface in a separate network namespace.
They verify a fixed external-IP advertisement, mapping callbacks and restart,
failed-mapping startup, two identities on one IPv4 address at distinct ports,
IPv6 UDP-only seed introduction followed by authenticated RLPx messaging, and
static TCP messaging with UDP discovery disabled. The NAT adapter is synthetic;
no real router, Foundation service, chain data or production wallet is used.

The later [partition rehearsal](restart-network-partitions.md) records kernel
packet-loss behavior and the inbound-only limitation separately. Public IPv4/IPv6
routing, firewall and NAT translation, DNS from another network and the actual
release deployment remain unverified. Mining and chain convergence during a
partition also require separate coverage.
Once hosts and a domain are selected, use a disposable fresh public client to
verify signed UDP discovery and a real peer handshake against the published enode,
then repeat after a seed IP move and after the temporary backup node is stopped.
Separate these networking checks from recovery-block acceptance and mining checks.
The earlier three known broad networking test failures remain documented; this
follow-up does not rerun or claim to fix the full suites.
