# Restart VPSs

24 October 2026. The public P2P hosts for the restarted network: two identical
Contabo VPSs, one per bootnode slot in the
[launch plan](restart-launch-plan.md#4-infrastructure), so nothing on the home
network accepts a connection from the internet.

## 1. Role

Each VPS runs one efsn full node with discovery on. That node is both a bootnode
entry in the release and a public peer that the home nodes dial out to. A full
node answers discovery itself, so there is no separate `bootnode` process.

| Slot | Host | Region |
| --- | --- | --- |
| `bn1.fsnex.net:40408` | VPS 1 | European Union (Germany) |
| `bn2.fsnex.net:40408` | VPS 2 | A second Contabo region (UK or US), whichever carries no surcharge at checkout |

While one VPS is down, the other keeps outside nodes connected to the producers.
A Contabo-wide failure or a problem with the account takes out both; the
producers and the explorer carry on, and outside nodes fall behind until one is
back.

The VPSs hold no wallet keys, mine nothing, serve no RPC, front no websites and
have no access to anything at home.

## 2. Machine

| Item | Choice |
| --- | --- |
| Plan | Contabo Storage VPS 10, twice: 2 vCPU, 4 GB RAM, 300 GB SSD, 200 Mbit/s. About €4.40/month each on a 24-month term (Contabo's figure, including VAT); confirm currency and term at checkout. It costs the same as the smallest Cloud VPS, whose 100 GB disk cannot hold the chain. |
| OS | Ubuntu 24.04. |
| Disk | The chain database is about 110 GB (the backup: 109.1 GiB) and grows slowly. |
| RAM | `--cache 512` (the default is 1024). Expect roughly 1–2 GB; measure after launch. A 2 GB swap file is the safety net. |

## 3. Setup

The same on both, except the slot's key, name and identity.

1. **Account:** 2FA on the Contabo account; its control panel can reset root passwords.
2. **SSH:** the owner's PC key only; `PasswordAuthentication no`, `PermitRootLogin no`, a `peter` user with sudo. Contabo's VNC console is the way back from a lockout.
3. **Firewall (UFW):** deny incoming except 22/tcp (`ufw limit`) and 40408/tcp+udp.
4. **System:** `unattended-upgrades`, chrony (a block from a node whose clock runs ahead is dropped after 30 seconds), a 2 GB swap file.
5. **Node:** the release's `efsn` in `/opt/fusion/<version>/` with a `current` symlink, run by a system user `fusion` that owns `/var/lib/fusion`. `fusion-node.service`, with `User=fusion`, `Restart=on-failure`, `NoNewPrivileges=yes`, `ProtectSystem=strict` and `ReadWritePaths=/var/lib/fusion`:
   ```text
   efsn --datadir /var/lib/fusion/node --nodekey /var/lib/fusion/bn<N>.key \
        --nat extip:<VPS IP> --syncmode full --cache 512 --identity bn<N>.fsnex.net
   ```
   No `--http` or `--ws`; status over IPC:
   `sudo -u fusion efsn attach /var/lib/fusion/node/efsn.ipc`.
6. **Trusted peers:** `/var/lib/fusion/node/efsn/trusted-nodes.json` lists producer A, producer B and the explorer node, so they get a slot even when the default 25 peers are taken. Entries use an IP address, not a hostname: matching is by node ID, and a hostname that fails to resolve at startup drops the entry silently.
7. **Key:** `bn1.key` or `bn2.key`, made with `bootnode -genkey` and backed up to the NAS. The key is the slot's identity in every release; `bootnode -nodekey <key> -writeaddress` prints the ID.
8. **DNS:** an A record for the slot's name, TTL about 300 s. No AAAA record: efsn's discovery has not been checked over IPv6.

## 4. Database

Both start from the stopped backup database the producers start from (block
15,130,080), well before launch: upload it once from home to VPS 1, timing the
upload, then copy it from VPS 1 to VPS 2 with a one-off SSH key that is removed
afterwards. At launch each imports `recovery.rlp` the way the producers do
(launch plan, step 5.2), then starts as `fusion-node.service`.

A sync from genesis instead would take over a week: T1 replays about 23 blocks/s
on one core.

## 5. Before launch

| Check | Pass |
| --- | --- |
| `ss -tulpn` on each, and a port scan from the PC | Only 22/tcp and 40408 answer. |
| T3a (launch plan, section 5) | As stated there. |
| Reboot each | The service comes back by itself, and the home nodes redial it within about a minute. |

## 6. After launch

- **Upgrades:** one VPS at a time: stop, switch the `current` link, start, and wait until it follows the head before doing the other. Keep the previous version until the new one has run a day.
- **Rebuild:** this document, the slot's key from the NAS, and a database copied from the other VPS.
- **Moving a slot:** move its key and point its DNS record at the new host, which listens on 40408. The home nodes list the VPSs by IP, so their `static-nodes.json` changes and they restart; running outside nodes keep the old address until they restart, since efsn resolves bootnode names once.

## 7. Open

- **Who administers them.** claudedev is trusted by no host, by the owner's decision of 22 October. An SSH key for it would let a session run T3a and the checks above; without one, the owner runs them from the PC.
