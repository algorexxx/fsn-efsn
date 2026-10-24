# Fusion restart launch plan

22 October 2026. This is the working plan from here to a running restarted
mainnet. It replaces the "next steps" in [restart-plan.md](restart-plan.md),
which remains the record of Codex's investigation. Branch details, PR messages
and review findings are in [restart-upstream-branches.md](restart-upstream-branches.md).

## 1. Goal

Restart Fusion mainnet from the stalled tip, block 15,130,080, with:
- **producers:** two nodes run by Peter:
  - **A:** Peter's wallet;
  - **B:** the original backup wallet;
- **consensus:** unchanged DaTong rules;
- **protection:** the restart blocks are pinned as check points, so an older chain with more total difficulty cannot replace them;
- **reachability:** others can join.

Not in scope: ongoing finality, ticket economics changes, the F5/F11 consensus
defects. Those are preserved as historical behaviour, and fixing them needs an
activation height.

## 2. Decisions

| Topic | Decision |
| --- | --- |
| Upstream | Fusion-Community/efsn, base `develop` = v5.0.3 (`c5f0174d`). |
| Branch structure | Independent branches on develop. A branch that needs another sits on top of it; no merge commits. Only changes justified by a demonstrated failure. |
| Compiler | Go 1.27.3 for releases, once the ticket gzip writer and FSN log JSON encoder are frozen to Go 1.21.3. An audit found no other compiler-dependent consensus output. Go 1.21.3 builds remain equivalent. |
| Restart protection | Check point pinning (`feature/restart-checkpoints`) instead of a new anchor mechanism. It pins 15,130,080 now; the recovery block hashes are added in the release. It refuses reorganisations back below a pinned height. There is no startup guard. |
| Automatic ticket buying | Minimal fix: a 5-second retry, a pool check instead of the per-block cache, and a resend of the pending purchase to peers (`feature/autobuy-retry`). |
| Recovery tool | The full rehearsed tool on `tools/restart-recovery`, a never-merged branch on Fusion-Community, tagged at the commit used for signing. |
| Discovery | Minimal fixes (`fix/p2p-discovery`), including "skip an unresolvable bootnode instead of exiting": the old `bn1`–`bn4.fusionnetwork.io` names no longer resolve, so stock v5.0.3 nodes exit at startup. |
| Bootnodes | Two slots, each = DNS name + port + dedicated node key, movable to another machine later. Both start on one Contabo VPS: `bn1.fsnex.net:40407` (discovery-only `bootnode`) and `bn2.fsnex.net:40408` (a full node, the network's public peer). Producers peer statically and do not depend on them. |
| Home exposure | Nothing at home accepts P2P connections: no port forward, and the producers and the explorer node run `--nodiscover --nat none` and dial out to static peers. The VPS is the public face for P2P, so the home IP is never advertised in discovery and a P2P flood hits the VPS, not the home line. The explorer's websites and RPC are still served from home. |
| One VPS | Accepted for cost (owner, 24 October). `bn2` is the only node outsiders can connect to, so while the VPS is down outside nodes get no new blocks, new nodes cannot join, and transactions sent through outside nodes do not reach the producers; the producers and the explorer carry on. The cheapest second node would be another Storage VPS 10 in a different Contabo region (about €4.40/month): it covers a host or datacenter failure, not a Contabo-wide one. Independence comes from community operators taking slots (section 7). |
| JWT / test-fixture branch | Optional scanner hygiene; the JWT handler is never enabled in efsn. |
| F5 / F11 | Unchanged; recorded as known issues and future hard-fork candidates. |

## 3. Branches

```
develop
├─ fix/ticket-encoding-compat ─ fix/fsn-log-json-compat ─ build/go-toolchain
├─ fix/jwt-and-test-fixtures            (optional)
├─ fix/p2p-discovery
└─ fix/chain-consistency ─┬─ feature/restart-checkpoints
                          ├─ feature/autobuy-retry
                          └─ tools/restart-recovery   (never merged)
```

The explorer node also needs `feature/historical-tracing` (one commit on
`develop`, read-only tracing). Either merge it with the others or build the
explorer's binary from the release plus that branch; decide before the freeze.

**Merge order:**
1. `fix/ticket-encoding-compat`, `fix/p2p-discovery` and `fix/chain-consistency`, in any order.
2. `fix/fsn-log-json-compat`, then `build/go-toolchain`.
3. `feature/restart-checkpoints` and `feature/autobuy-retry`.

The branches are in the local `efsn` clone. Rewritten branches need a force-push
wherever earlier versions were pushed.

## 4. Infrastructure

| Role | Machine | Notes |
| --- | --- | --- |
| Producer A (Peter's wallet) | Peter's server | Restart release, restored database, `--mine --autobt --nodiscover --nat none --nodekey <own key>`, static peers B, the explorer node and `bn2`. |
| Producer B (backup wallet) | Peter's server (separate host preferred) | Same as A, with the backup wallet. |
| Explorer node | fsnexrebirth VM (`192.168.1.212`), at home | The explorer's RPC and trace node. Restart release plus the historical-tracing fix its trace endpoint depends on (`feature/historical-tracing`, [historical-tracing.md](historical-tracing.md)), `--nodiscover --nat none --nodekey <own key>`, static peers A, B and `bn2`. No port forward. It runs in Docker today ([gateway-endpoint.md](gateway-endpoint.md)); check that its container can pass these flags, since the release image's entrypoint cannot (section 8). Stays local: the explorer's tracing and backfill make many calls per block, which a WAN round trip and the VPS's two cores would slow down, and the `debug` API must not be exposed on an internet host. |
| VPS | Contabo Storage VPS 10: 2 vCPU, 4 GB RAM, 300 GB SSD, 200 Mbit/s, about €4.40/month on a 24-month term. EU region. One only (section 2). | Hosts both slots below. UFW: deny incoming except SSH (keys only) and the two P2P ports. Holds no wallet keys and has no access into the home network. |
| Bootnode slot 1 `bn1.fsnex.net` | VPS | `bootnode -nodekey bn1.key -addr :40407 -nat extip:<VPS IP>` as a systemd service. UDP 40407 open. |
| Bootnode slot 2 `bn2.fsnex.net` | VPS | Full efsn node on the restart release, `--port 40408 --nat extip:<VPS IP> --cache 512`, TCP+UDP 40408 open, as a systemd service. `trusted-nodes.json` lists A, B and the explorer node so they always get a slot. Starts from the backup database uploaded before launch, then imports `recovery.rlp` like the producers. |
| DNS | Simply.com (fsnex.net) | A records for `bn1`/`bn2`, both the VPS IP, TTL about 300 s. |

The VPS's setup, database and checks are in [restart-vps.md](restart-vps.md).

**Peer files:** the home nodes' `static-nodes.json` and `bn2`'s
`trusted-nodes.json` use IP addresses, not hostnames. efsn resolves a hostname
in these files once, at startup, and silently drops an entry that fails to
resolve; with discovery off, a home node would then never dial `bn2` until
restarted. Trusted entries match by node ID only, so their IP need only parse.

**Clocks:** every node runs chrony. A block timestamped even slightly in the
future is queued for at most 30 seconds and then dropped.

If the VPS is down, A, B and the explorer carry on through their static peers.
Outside nodes that have run for a while reconnect to one another from their own
discovery databases ([restart-discovery-cache.md](restart-discovery-cache.md)),
but none of them reaches the producers until it is back (section 2, "One VPS").

**Keys:**
- **Wallet keys:** producer wallets and the recovery signing keys stay offline except where needed. The recovery signing follows the tool's journal procedure.
- **Never sign two different blocks on the same parent.** Fusion deletes a ticket from a miner reported for it.
- **Node keys:** each node has its own, made with `bootnode -genkey` and passed with `--nodekey`: `bn1.key`, `bn2.key`, the explorer's and each producer's. The backup database holds a `nodekey` of its own; nodes restored from it must not use it, or A and B share an ID and refuse each other. All are backed up. The bootnode keys define the slots in every release.

## 5. Pre-launch testing

The final code differs from what Codex rehearsed:
- the anchor is replaced by check point pinning;
- automatic buying is a new, smaller implementation;
- discovery lost the DNS-bootstrap and address rework;
- two node fixes were dropped;
- the FSN log JSON encoder is new;
- releases move to Go 1.27.3.

Unit and integration tests cover each change, and the JSON encoder is proven
byte-identical. But the parts that changed are the ones that run the restart, and
none of them has run as a whole, on real data or for longer than minutes.

| ID | Test | Why | Pass criteria | Rough cost |
| --- | --- | --- | --- | --- |
| T1 | Replay blocks 7,170,976 → 15,130,080 from the existing fallback database, with the final release source built on Go 1.27.3. | Exercises the final consensus code and compiler on 8 million real blocks, including every post-London and FSN-call receipt (the JSON encoder) and the check point lookups. | Tip header, state root, ticket commitment and receipts match the preserved backup at 15,130,080; no errors. | About 4 days unattended at the measured ~23 blocks/s (CPU-bound, one core), plus a 45-minute copy of the fallback database. Codex's own segmented replay of this range also took days. |
| T2 | Full dress rehearsal on a private network built from a copy of the real backup, with the stalled owners' tickets re-owned to public test keys (Codex's full-state fixture method). | Exercises the actual launch sequence with the final binaries: recovery tool, pinned hashes, two producers, buying, discovery, joining and refusal of a rival chain. | Recovery blocks import on every node; both producers sustain production and buy every block for 48 h. A restarted or `kill -9`'d producer resumes. A 30-minute partition heals. A fresh node joins via the bootnode from a snapshot. A node holding a rival pre-restart chain is refused and rewinds. | Setup about 1 day; 48 h soak. |
| T2b | The launch topology on the T2 network: a `bn2` role (discovery on, `trusted-nodes.json` = A, B, explorer), A, B and the explorer with `--nodiscover --nat none` and static peers by IP, a joiner given only the bootnode. | T2 runs every node with discovery on and reachable, so its joiner found the producers directly. At launch the producers are unreachable and `bn2` is the only public peer. | The joiner syncs from `bn2` alone. After a `bn2` restart the home nodes reconnect within about a minute. A 30-minute `bn2` outage: the joiner falls behind, then catches up. A node at the stalled tip receives the recovery blocks from peers (section 8). | Half a day on the T2 setup. |
| T3a | Package check before the release: the Docker image and binary on the VPS (as `bn1` and `bn2`) and one fresh host, with `--bootnodes` given explicitly. | Confirms the artifacts, flags, NAT/ports and outside discovery. | The fresh host finds peers through `bn1.fsnex.net`/`bn2.fsnex.net` alone and syncs. | A few hours. |
| T3b | The release binary on a fresh host with no flags. | Confirms the bootnode list built into the release. | Same as T3a. | Under an hour. |

T2 uses a rehearsal build with the rehearsal's own recovery hashes pinned. Do not
use the custom check point file for this: it raises `LastCheckPoint` and would
skip seal verification.

## 6. Launch sequence

1. **Freeze:** review, push and merge the branches in the order above. Run T1, T2 and T2b on the merged source.
2. **Bootnodes:**
   1. Generate `bn1.key` and `bn2.key` and read their enode IDs: `bootnode -genkey bn1.key`, then `bootnode -nodekey bn1.key -writeaddress`; the same for `bn2.key`.
   2. Upload the backup database to the VPS ([restart-vps.md](restart-vps.md#4-database)).
   3. Set the DNS records.
   4. Run T3a.
3. **Recovery blocks:** with `tools/restart-recovery` rebased onto the merged source and built from there (the bare branch lacks the frozen encoders, so its Go 1.27.3 build would produce blocks every node rejects), on a stopped copy of the backup database:
   1. Build the three blocks: the purchase block timestamped while the signer's tickets were valid, the timestamp-jump block, and the cleanup block.
   2. Review them.
   3. Sign them, following the journal procedure.
   4. Import every exported block into a scratch node before going further.
   5. Tag the tool commit.
4. **Release commit:**
   - add the recovery block hashes to `mainnetCheckPoints`;
   - replace `MainnetBootnodes` with `enode://<bn1 id>@bn1.fsnex.net:40407` and `enode://<bn2 id>@bn2.fsnex.net:40408`;
   - bump the version.

   Then build the binaries and Docker images with Go 1.27.3, and run T3b.
5. **Start:**
   1. Check every node's clock (`timedatectl`: synchronised).
   2. Import the recovery blocks into producers A and B (restored database), the VPS node and the explorer node. `efsn import` fails in v5.0.3 (it opens chaindata twice: "resource temporarily unavailable"), so start each node with `--nodiscover --maxpeers 0 --nat none` and no mining, run `admin.importChain("recovery.rlp")`, then stop it. This worked in the T2 smoke test. The four imports are independent and can run side by side.
   3. Start A and B with mining and static peers to each other.
   4. Confirm blocks and automatic purchases on both.
   5. Start the `bn2` node and the `bn1` bootnode on the VPS, and the explorer node at home.
   6. Confirm `bn2` and the explorer follow the producers' head.
6. **Publish:**
   - the release;
   - the database snapshot (with a trusted manifest; where it is served from is open, section 8);
   - a peer list (GitHub file and the explorer);
   - the recovery evidence, i.e. the tools tag and the signed blocks.

   Announce that all producers and services must upgrade.
7. **Watch:**
   - production on both producers and buying every block;
   - ticket counts;
   - peer counts;
   - explorer head versus producer head.

   Keep repair funds available for the producers.

## 7. After launch

- **Outside monitoring:** from the VPS, check the public sites and `bn2`'s head and peer count. The home monitoring VM reaches the sites through the router, so it cannot see the home connection or a port forward fail.
- **Bootnode slots:** hand them to community operators by moving the key file and the DNS record. The new host must listen on the slot's port. Retire one only after the current release lists 2–3 other reliably run entries.
- **Neutral domain:** register a community domain with multiple admins and a long registration, then add its names in a later release.
- **Follow-ups:**
  - re-resolving bootnode hostnames periodically;
  - ethstats current-head reporting;
  - the inherited `TestParseNode`/`TestForwardCompatibility` failures;
  - the wall-clock check (`time.Now()`) in the TimeLockToAsset state transition;
  - signed DNS node lists (EIP-1459), if the network grows.

## 8. Open items

- **Push:** push the branches (rewritten ones need `--force`).
- **Bootnode IDs:** the `bn1` and `bn2` enode IDs, and the VPS IP.
- **VPS:** order the Contabo Storage VPS 10; T3a needs it. Setup in [restart-vps.md](restart-vps.md).
- **Snapshot hosting:** about 110 GB per download. The VPS's firewall has no web port and its 200 Mbit/s port is shared with `bn2`; home means the home upload. Decide where, and take the snapshot from a stopped home node or stream it straight from `bn2`'s stopped database (`tar | zstd`): a raw copy beside the database does not fit 300 GB with an archive as well.
- **Recovery blocks over P2P:** T2 imports the recovery blocks into every node by hand (`t2-soak-claudedev.sh`, `import_recovery` for a, b, x and j). No test has a node at the stalled tip receive them from peers, which is how a community node upgrading its own old database would get them. T2b covers it; until it passes, the release notes tell operators to import `recovery.rlp`.
- **Recovery hashes:** available only after signing.
- **Testing:** paused on 22 October to move to a dedicated Ubuntu VM. T1 stopped cleanly at block 7,376,672 with no mismatch so far; its image `W:\FusionRestart\t1-final-replay-2026-10-22\replay.ext4` (now `/mnt/fusion/t1/replay.ext4` on `claudedev`) resumes from there (`t1-resume.sh`). Scripts and logs: `docs/evidence/restart-final-tests-2026-10-22/`. T2 smoke test (27 min, unprivileged, loopback) passed: the recovery blocks imported on every node, 118 blocks were produced by both producers with a purchase in every block, and a fresh node joined via the bootnode. The 48 h soak needs root (W: image, network namespaces).
- **Tools branch test data:** `tests/restart/testdata` on `tools/restart-recovery` lacks the genesis observation (id 2) and `context.rlp`, so its full-state tests cannot run from the branch as-is.
- **Bootnode code:** the bootnode is built from the restart source, so it carries the discovery fixes.
- **Docker image (T3 local check):** the image builds on Go 1.27.3, but `docker-entrypoint.sh` only accepts `-u`/`-e`/`-a`/`-tn`/`--disable-mining`, so `--nat`, `--bootnodes` and `--autobt` cannot be passed, and it hardcodes ethstats to the dead `node.fusionnetwork.io`. Either fix the wrapper (a few lines) or document running the binary directly.
