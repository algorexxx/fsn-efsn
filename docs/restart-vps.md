# Restart VPSs

24 October 2026. The public P2P hosts for the restarted network: two identical
Contabo VPSs, one per bootnode slot in the
[launch plan](restart-launch-plan.md#4-infrastructure), so nothing on the home
network accepts a connection from the internet.

## 1. Role

Each VPS runs one efsn full node with discovery on. It is both a bootnode entry
in the release and a public peer that the home nodes dial out to. A full node
answers discovery itself, so there is no separate `bootnode` process.

| Slot | Region |
| --- | --- |
| `bn1.fsnex.net:40408` | European Union (Germany) |
| `bn2.fsnex.net:40408` | A second Contabo region (UK or US), whichever carries no surcharge |

While one VPS is down, the other keeps outside nodes connected to the producers.
A Contabo-wide failure or an account problem takes out both: the producers and
the explorer carry on, and outside nodes fall behind until one is back.

The VPSs hold no wallet keys, mine nothing, serve no RPC, front no websites and
have no access to anything at home. The owner administers them from the PC;
whether claudedev gets an SSH key is open.

## 2. Machine

Contabo Storage VPS 10, twice: 2 vCPU, 4 GB RAM, 300 GB SSD, 200 Mbit/s, about
€4.40/month each on a 24-month term (Contabo's figure, including VAT). Ubuntu
24.04. The chain database is about 110 GB (the backup: 109.1 GiB) and grows
slowly.

`--cache 512` is required: without `--cache`, efsn on mainnet raises the cache
to 4096 MB (`cmd/efsn/main.go`, "Bumping default cache on mainnet"), more than
the VPS has. Measure the node's memory during T3a. A 2 GB swap file is the
safety net.

## 3. Setup

The same on both, except the slot's key and name.

1. **Account:** 2FA on the Contabo account; its control panel can reset root passwords.
2. **SSH:** the owner's PC key only; `PasswordAuthentication no`, `PermitRootLogin no`, a `peter` user with sudo. Contabo's VNC console is the way back from a lockout.
3. **Firewall (UFW):** deny incoming except 22/tcp (`ufw limit`) and 40408/tcp+udp.
4. **System:** check that `unattended-upgrades` and `systemd-timesyncd` are enabled (Ubuntu's defaults); add a 2 GB swap file.
5. **Node:** the build's `efsn` in `/opt/fusion/<version>/` with a `current` symlink, run by a system user `fusion` that owns `/var/lib/fusion`. `fusion-node.service` has `User=fusion`, `After=`/`Wants=network-online.target` (the bootnode names resolve once, at start), `Restart=always`, `RestartSec=5`, `TimeoutStopSec=300`, `NoNewPrivileges=yes`, `ProtectSystem=strict` and `ReadWritePaths=/var/lib/fusion`:
   ```text
   /opt/fusion/current/efsn --datadir /var/lib/fusion/node \
        --nodekey /var/lib/fusion/bn<N>.key --nat extip:<VPS IP> \
        --cache 512 --maxpeers 50
   ```
   `--maxpeers 50` allows 34 inbound peers. At the default 25 it would be 17,
   three of them taken by the home nodes. No `--http` or `--ws`; status over IPC:
   `sudo -u fusion efsn attach /var/lib/fusion/node/efsn.ipc`.
6. **Trusted peers:** `/var/lib/fusion/node/efsn/trusted-nodes.json` holds the bare IDs of producer A, producer B and the explorer node (`"enode://<id>"`, no address), so they get a slot even when the node is full. efsn matches trusted peers by ID only.
7. **Key:** `bootnode -genkey bn<N>.key`, backed up to the NAS; `bootnode -nodekey bn<N>.key -writeaddress` prints the ID for the release. The key is the slot's identity in every release.
8. **DNS:** an A record for the slot's name, TTL about 300 s. No AAAA record: efsn takes the first address a name resolves to, and its discovery has not been checked over IPv6.

## 4. Database

Upload only `efsn/chaindata` from the 23 September verified backup copy, which
holds no keystore, node key or peer database
([restart-local-linux.md](restart-local-linux.md)). The full backup directory
would put the original wallet's keystore on an internet host. Upload it once
from home to VPS 1, timing it. Then copy it from VPS 1 to VPS 2 with a one-off
SSH key that is removed afterwards. On each, check it against that copy's
`sha256sum.txt`. The node directory then holds only `efsn/chaindata` and
`efsn/trusted-nodes.json`.

A sync from genesis instead would take over a week: T1 replays about 23 blocks/s
on one core.

**Recovery import at launch** (launch plan, step 5.2), only if T2b has not shown
that a node at the stalled tip takes the recovery blocks from peers. Run it with
the service stopped and `recovery.rlp` in `/var/lib/fusion/`:

```text
sudo -u fusion /opt/fusion/current/efsn --datadir /var/lib/fusion/node \
     --nodekey /var/lib/fusion/bn<N>.key --nodiscover --maxpeers 0 --nat none --cache 512
sudo -u fusion efsn attach /var/lib/fusion/node/efsn.ipc --exec 'admin.importChain("/var/lib/fusion/recovery.rlp")'
```

Then stop it and start `fusion-node.service`. It runs as `fusion` so that the
new database files stay readable by the service.

## 5. Before launch

- A port scan from the PC: only 22/tcp and 40408 answer.
- A reboot: the service comes back by itself.
- T3a (launch plan, section 5), then stop both nodes until launch.

## 6. After launch

- **Upgrades:** one VPS at a time: stop, switch the `current` link, start, and wait until it follows the head before doing the other.
- **Rebuild:** this document, the slot's key from the NAS, and the published snapshot or a stopped home node's `chaindata`. Not the other VPS, which would have to stop for the copy.
- **Moving a slot:** move its key and point its DNS record at the new host, which listens on 40408. On the home nodes, update `static-nodes.json` and run `admin.addPeer` with the new address, so no restart is needed. Running outside nodes keep the old address until they restart, since efsn resolves bootnode names once.
