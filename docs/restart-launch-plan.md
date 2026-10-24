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
| Bootnodes | Two slots, `bn1.fsnex.net:40408` and `bn2.fsnex.net:40408`, each a full node with discovery on, on its own Contabo VPS in two regions ([restart-vps.md](restart-vps.md)). A slot is a DNS name plus a node key and can move to another machine. Producers peer statically and do not depend on them. |
| Home exposure | Nothing at home accepts P2P connections: no port forward, and the producers and the explorer node run `--nodiscover --nat none` and dial out to static peers, so the home IP is never advertised in discovery. The explorer's websites and RPC are still served from home. |
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
| Producer A (Peter's wallet) | Peter's server | Restart release, restored database, `--mine --autobt --nodiscover --nat none --nodekey <own key>`, static peers B, the explorer node, `bn1` and `bn2`. |
| Producer B (backup wallet) | Peter's server (separate host preferred) | Same as A, with the backup wallet. |
| Explorer node | fsnexrebirth VM (`192.168.1.212`), at home | The explorer's RPC and trace node: the release plus `feature/historical-tracing` ([historical-tracing.md](historical-tracing.md)), `--nodiscover --nat none --nodekey <own key>`, static peers A, B, `bn1` and `bn2`. It stays local because tracing and backfill make many calls per block and its `debug` API must not face the internet. It runs in Docker today ([gateway-endpoint.md](gateway-endpoint.md)); its container must pass these flags. |
| `bn1`, `bn2` | Two Contabo Storage VPS 10 | [restart-vps.md](restart-vps.md). |
| DNS | Simply.com (fsnex.net) | A records for `bn1`/`bn2`, TTL about 300 s. |

**Static peers:** the home nodes' `static-nodes.json` list the VPSs as
`enode://<id>@<IP>:40408`, not by name. efsn resolves a name there once, at
startup, and skips the entry with an error if that fails. With discovery off,
nothing else would find the VPS.

**Clocks:** every node's clock is synchronised (Ubuntu's `systemd-timesyncd`). A
block more than 30 seconds ahead of a receiver's clock is rejected.

**Keys:**
- **Wallet keys:** producer wallets and the recovery signing keys stay offline except where needed. The recovery signing follows the tool's journal procedure.
- **Never sign two different blocks on the same parent.** Fusion deletes a ticket from a miner reported for it.
- **Node keys:** each node has its own, made with `bootnode -genkey` and passed with `--nodekey`. The backup database holds a `nodekey`; nodes restored from it must not use it, or A and B share an ID and refuse each other. All are backed up; `bn1.key` and `bn2.key` define the slots in every release.

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
| T2b | The launch topology on the T2 network: two public full nodes as `bn1`/`bn2` (discovery on, `trusted-nodes.json` = A, B, explorer); A, B and the explorer with `--nodiscover --nat none` and static peers by IP; a joiner given only `bn1`'s enode. | T2 runs every node with discovery on and reachable, so its joiner found the producers directly. At launch the producers are unreachable and the two VPS nodes are the only public peers, and they double as bootnodes. | The joiner syncs and also peers with `bn2`, which it can only have learned through `bn1`'s discovery. With one public node stopped for 30 minutes it stays on the head; with both stopped it falls behind, then catches up. After a public node restarts, the home nodes reconnect within about a minute. A node at the stalled tip receives the recovery blocks from peers (section 8). | Half a day on the T2 setup. |
| T3a | The merged-source build, which already carries the bootnode list (section 6, step 2), on both VPSs and on one fresh host: the PC or a home VM, which only dials out. The fresh host starts from a copy of the backup `chaindata` with no peer files and no flags. | Confirms the binary, the built-in bootnode list, DNS, ports and outside discovery. | Within a few minutes the fresh host shows both `bn1` and `bn2` in `admin.peers` and reports the same head, 15,130,080. The VPS nodes' memory is measured. If the Docker image ships, the same with the image. | A few hours. |

T2 uses a rehearsal build with the rehearsal's own recovery hashes pinned. Do not
use the custom check point file for this: it raises `LastCheckPoint` and would
skip seal verification.

## 6. Launch sequence

1. **Now, alongside T1 and T2:** order the two VPSs, generate `bn1.key` and `bn2.key`, set the DNS records and upload the database ([restart-vps.md](restart-vps.md)). None of it depends on the code, and the upload is the long pole.
2. **Freeze:** review, push and merge the branches in the order above, plus a commit on `fix/p2p-discovery` that replaces `MainnetBootnodes` with `enode://<bn1 id>@bn1.fsnex.net:40408` and `enode://<bn2 id>@bn2.fsnex.net:40408`. Run T1, T2, T2b and then T3a on the merged source. Keep the VPS nodes stopped after T3a.
3. **Recovery blocks:** with `tools/restart-recovery` rebased onto the merged source and built from there (the bare branch lacks the frozen encoders, so its Go 1.27.3 build would produce blocks every node rejects), on a stopped copy of the backup database:
   1. Build the three blocks: the purchase block timestamped while the signer's tickets were valid, the timestamp-jump block, and the cleanup block.
   2. Review them.
   3. Sign them, following the journal procedure.
   4. Import every exported block into a scratch node before going further.
   5. Tag the tool commit.
4. **Release commit:** add the recovery block hashes to `mainnetCheckPoints` and bump the version. Nothing in it touches P2P. Then build the binaries (and the Docker image, if it ships) with Go 1.27.3.
5. **Start:**
   1. Check every node's clock (`timedatectl`: synchronised) and that every node except the producers is at head 15,130,080.
   2. Import the recovery blocks into producers A and B (restored database). Do the same on both VPS nodes and the explorer node, unless T2b showed that a node at the stalled tip takes them from peers. `efsn import` fails in v5.0.3 (it opens chaindata twice: "resource temporarily unavailable"), so start each node with `--nodiscover --maxpeers 0 --nat none --cache 512` and no mining, run `admin.importChain("recovery.rlp")`, then stop it. This worked in the T2 smoke test. On the VPSs, follow [restart-vps.md](restart-vps.md#4-database). The imports are independent and can run side by side.
   3. Start A and B with mining. Their `static-nodes.json` already list each other, the explorer and both VPSs; they redial every 30 seconds until the others are up.
   4. Confirm blocks and automatic purchases on both.
   5. Start both VPS nodes and the explorer node.
   6. Confirm all three follow the producers' head. Restart one VPS node and confirm the home nodes reconnect within about a minute.
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

- **Outside monitoring:** a free external uptime service checking TCP 40408 on both VPSs and the public sites, alerting by email. Nothing runs on the VPSs for it, and the home monitoring VM cannot see the home connection or a port forward fail.
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
- **Bootnode IDs:** the `bn1` and `bn2` enode IDs, and both VPS IPs.
- **VPSs:** order them and upload the database now (section 6, step 1).
- **Snapshot hosting:** about 110 GB per download. The VPSs' firewalls have no web port and each 200 Mbit/s port is shared with its node; home means the home upload. Decide where, and take the snapshot from a stopped node by streaming its database (`tar | zstd`): a raw copy beside the database does not fit 300 GB with an archive as well.
- **Recovery blocks over P2P:** T2 imports the recovery blocks into every node by hand (`t2-soak-claudedev.sh`, `import_recovery` for a, b, x and j). No test has a node at the stalled tip receive them from peers, which is how a community node upgrading its own old database would get them. T2b covers it. If it passes, only the producers import by hand; until then, the release notes tell operators to import `recovery.rlp`.
- **Recovery hashes:** available only after signing.
- **Testing:** T1 and the T2 48 h soak run on `claudedev` as the units `t1-replay` and `t2-soak` (T1 due around 31 October, at about 12 blocks/s over NFS). Scripts and logs: `docs/evidence/restart-final-tests-2026-10-22/`. T2b follows the soak on the same setup.
- **Tools branch test data:** `tests/restart/testdata` on `tools/restart-recovery` lacks the genesis observation (id 2) and `context.rlp`, so its full-state tests cannot run from the branch as-is.
- **Docker image:** the image builds on Go 1.27.3, but `docker-entrypoint.sh` only accepts `-u`/`-e`/`-a`/`-tn`/`--disable-mining`, so `--nat`, `--bootnodes` and `--autobt` cannot be passed, and it hardcodes ethstats to the dead `node.fusionnetwork.io`. Either fix the wrapper (a few lines) before T3a or ship binaries only. The explorer runs its own flags either way.
