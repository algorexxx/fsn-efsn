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
| Bootnodes | Two slots, each = DNS name + dedicated node key, movable to another machine later: `bn1.fsnex.net` (discovery-only `bootnode` on a small Contabo VPS) and `bn2.fsnex.net` (the FSNEX explorer's full node). Producers peer statically and do not depend on them. |
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

**Merge order:**
1. `fix/ticket-encoding-compat`, `fix/p2p-discovery` and `fix/chain-consistency`, in any order.
2. `fix/fsn-log-json-compat`, then `build/go-toolchain`.
3. `feature/restart-checkpoints` and `feature/autobuy-retry`.

The branches are in the local `efsn` clone. Rewritten branches need a force-push
wherever earlier versions were pushed.

## 4. Infrastructure

| Role | Machine | Notes |
| --- | --- | --- |
| Producer A (Peter's wallet) | Peter's server | Restart release, restored database, `--mine --autobt`, static peer to B and to the explorer node. |
| Producer B (backup wallet) | Peter's server (separate host preferred) | Same as A, with the backup wallet. |
| Bootnode slot 1 `bn1.fsnex.net` | Contabo VPS, smallest size | `bootnode -nodekey bn1.key -addr :40407 -nat extip:<VPS IP>` as a systemd service. TCP+UDP 40407 open. |
| Bootnode slot 2 `bn2.fsnex.net` | FSNEX explorer server (217.211.35.199) | Explorer's efsn node on the restart release, `--nat extip:217.211.35.199`, port 40407 open. Back up its `nodekey`. |
| DNS | Simply.com (fsnex.net) | A records for `bn1`/`bn2`, TTL about 300 s. |

**Keys:**
- **Wallet keys:** producer wallets and the recovery signing keys stay offline except where needed. The recovery signing follows the tool's journal procedure.
- **Never sign two different blocks on the same parent.** Fusion deletes a ticket from a miner reported for it.
- **Node keys** (`bn1.key`, the explorer's `nodekey`, each producer's `nodekey`) are backed up. The bootnode keys define the slots in every release.

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
| T3 | Package check on clean machines: the release Docker image and binary on the Contabo VPS (as `bn1`) and one fresh host. | Confirms the artifacts people will download, the flags, NAT/ports and outside discovery. | A fresh host finds peers through `bn1.fsnex.net`/`bn2.fsnex.net` alone and syncs. | A few hours. |

T2 uses a rehearsal build with the rehearsal's own recovery hashes pinned. Do not
use the custom check point file for this: it raises `LastCheckPoint` and would
skip seal verification.

## 6. Launch sequence

1. **Freeze:** review, push and merge the branches in the order above. Run T1–T3 on the merged source.
2. **Bootnodes:**
   1. Generate `bn1.key` and read its enode ID: `bootnode -genkey bn1.key`, then `bootnode -nodekey bn1.key -writeaddress`.
   2. Read the explorer node's enode ID from `admin.nodeInfo.enode`.
   3. Set the DNS records.
3. **Recovery blocks:** with `tools/restart-recovery` rebased onto the merged source and built from there (the bare branch lacks the frozen encoders, so its Go 1.27.3 build would produce blocks every node rejects), on a stopped copy of the backup database:
   1. Build the three blocks: the purchase block timestamped while the signer's tickets were valid, the timestamp-jump block, and the cleanup block.
   2. Review them.
   3. Sign them, following the journal procedure.
   4. Import every exported block into a scratch node before going further.
   5. Tag the tool commit.
4. **Release commit:**
   - add the recovery block hashes to `mainnetCheckPoints`;
   - replace `MainnetBootnodes` with `enode://<bn1 id>@bn1.fsnex.net:40407` and `enode://<explorer id>@bn2.fsnex.net:40407`;
   - bump the version.

   Then build the binaries and Docker images with Go 1.27.3.
5. **Start:**
   1. Import the recovery blocks into producers A and B (restored database). `efsn import` fails in v5.0.3 (it opens chaindata twice: "resource temporarily unavailable"), so start each node with `--nodiscover --maxpeers 0` and no mining, run `admin.importChain("recovery.rlp")`, then restart it with mining. This worked in the T2 smoke test.
   2. Start both with static peers to each other.
   3. Confirm blocks and automatic purchases on both.
   4. Start the explorer node and the `bn1` bootnode.
6. **Publish:**
   - the release;
   - the database snapshot (with a trusted manifest);
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

- **Bootnode slots:** hand them to community operators by moving the key file and the DNS record. Retire one only after the current release lists 2–3 other reliably run entries.
- **Neutral domain:** register a community domain with multiple admins and a long registration, then add its names in a later release.
- **Follow-ups:**
  - re-resolving bootnode hostnames periodically;
  - ethstats current-head reporting;
  - the inherited `TestParseNode`/`TestForwardCompatibility` failures;
  - the wall-clock check (`time.Now()`) in the TimeLockToAsset state transition;
  - signed DNS node lists (EIP-1459), if the network grows.

## 8. Open items

- **Push:** push the branches (rewritten ones need `--force`).
- **Bootnode IDs:** the `bn1` and explorer enode IDs, and the VPS IP.
- **Recovery hashes:** available only after signing.
- **Testing:** paused on 22 October to move to a dedicated Ubuntu VM. T1 stopped cleanly at block 7,376,672 with no mismatch so far; its image `W:\FusionRestart	1-final-replay-2026-10-22eplay.ext4` resumes from there (`t1-resume.sh`). Scripts and logs: `docs/evidence/restart-final-tests-2026-10-22/`. T2 smoke test (27 min, unprivileged, loopback) passed: the recovery blocks imported on every node, 118 blocks were produced by both producers with a purchase in every block, and a fresh node joined via the bootnode. The 48 h soak needs root (W: image, network namespaces).
- **Tools branch test data:** `tests/restart/testdata` on `tools/restart-recovery` lacks the genesis observation (id 2) and `context.rlp`, so its full-state tests cannot run from the branch as-is.
- **Bootnode code:** the bootnode is built from the restart source, so it carries the discovery fixes.
- **Docker image (T3 local check):** the image builds on Go 1.27.3, but `docker-entrypoint.sh` only accepts `-u`/`-e`/`-a`/`-tn`/`--disable-mining`, so `--nat`, `--bootnodes` and `--autobt` cannot be passed, and it hardcodes ethstats to the dead `node.fusionnetwork.io`. Either fix the wrapper (a few lines) or document running the binary directly.
