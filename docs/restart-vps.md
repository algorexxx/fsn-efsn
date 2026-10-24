# Restart VPS

24 October 2026. The public P2P host for the restarted network. It carries both
bootnode slots from the [launch plan](restart-launch-plan.md#4-infrastructure),
so nothing on the home network has to accept a connection from the internet.

## 1. Role

| Does | Does not |
| --- | --- |
| `bn1.fsnex.net:40407`: discovery-only `bootnode`. | Hold wallet keys or mine. |
| `bn2.fsnex.net:40408`: full efsn node, the network's public peer. The producers and the explorer node dial out to it. | Serve RPC to anyone. The explorer's RPC and trace node stays at home ([launch plan](restart-launch-plan.md#4-infrastructure)). |
| Host T3a and T3b. | Front the websites. That is a separate, open question in `dromkaken-industrivagen` (`docs/PUBLIC-SITES.md`). |
| Later: watch the network and the public sites from outside. | Reach anything at home. No tunnel, SSH key or allow-list entry into the LAN. |

One VPS, accepted for cost (owner, 24 October). `bn2` is the only node outsiders
can connect to, so while the VPS is down outside nodes get no new blocks, new
nodes cannot join, and transactions sent through outside nodes do not reach the
producers. The producers and the explorer carry on, and the chain does not stop.
If that becomes a problem, the cheapest second node is another Storage VPS 10 in
a different Contabo region (about €4.40/month), which covers a host or datacenter
failure but not a Contabo-wide one. Independence comes from community operators
taking over slots (launch plan, section 7).

## 2. Machine

| Item | Choice |
| --- | --- |
| Plan | Contabo Storage VPS 10: 2 vCPU, 4 GB RAM, 300 GB SSD, 200 Mbit/s, unmetered incoming and fair-use outgoing traffic. |
| Price | About €4.40/month on a 24-month term (Contabo's figure, including VAT); confirm the currency and term at checkout. Cloud VPS 6 (6 vCPU, 12 GB, 200 GB SSD, €6.00) is the fallback if snapshots turn out to matter: Contabo lists them for Cloud VPS only. |
| Region | European Union (Germany). |
| OS | Ubuntu 24.04. |
| Disk | The chain database is about 110 GB (the backup: 109.1 GiB) and grows slowly, so 300 GB leaves room for a published snapshot file as well. |
| RAM | `--cache` defaults to 1024 MB; the unit sets 512. Expect roughly 1–2 GB for the node and a few MB for the bootnode; measure after launch. A 2 GB swap file is the safety net. (The T2 nodes use about 110 MB each, but with `--cache 128` on a private network.) |

## 3. Setup

1. **Account:** 2FA on the Contabo account. Its control panel can reset the root password, so the account is as much a way in as SSH.
2. **SSH:** the owner's PC key only; `PasswordAuthentication no`, `PermitRootLogin no`, a `peter` user with sudo. Contabo's VNC console is the way back from a lockout.
3. **Firewall (UFW):** deny incoming except 22/tcp (`ufw limit`), 40407/udp and 40408/tcp+udp. Nothing else listens publicly.
4. **Updates and time:** `unattended-upgrades` for security updates; chrony for the clock (a block from a node whose clock runs ahead is dropped after 30 seconds).
5. **Swap:** a 2 GB swap file.
6. **User:** a system user `fusion` without login owns `/var/lib/fusion`.
7. **Binaries:** `efsn` and `bootnode` from the release, in `/opt/fusion/<version>/`, with a `current` symlink so an upgrade and a rollback are one link change. Production runs the binaries under systemd. The Docker image is checked in T3a only (its entrypoint cannot pass `--nat` or `--bootnodes`; launch plan, section 8).
8. **Services:** both run as `User=fusion` with `Restart=on-failure`, `NoNewPrivileges=yes`, `ProtectSystem=strict` and `ReadWritePaths=/var/lib/fusion`.

   `fusion-bootnode.service`:
   ```text
   bootnode -nodekey /var/lib/fusion/bn1.key -addr :40407 -nat extip:<VPS IP>
   ```

   `fusion-node.service`:
   ```text
   efsn --datadir /var/lib/fusion/bn2 --nodekey /var/lib/fusion/bn2.key \
        --port 40408 --nat extip:<VPS IP> --syncmode full --cache 512 \
        --identity bn2.fsnex.net
   ```
   No `--http` or `--ws`; status is read over IPC:
   `sudo -u fusion efsn attach /var/lib/fusion/bn2/efsn.ipc`.
   `/var/lib/fusion/bn2/efsn/trusted-nodes.json` lists producer A, producer B
   and the explorer node by enode with an IP address, not a hostname, so they
   always get a slot even with the default 25 peers taken. Matching is by node
   ID; the address only has to parse.
9. **Keys:** generate `bn1.key` and `bn2.key` with `bootnode -genkey`, read the enode IDs with `bootnode -nodekey <key> -writeaddress`, and back both keys up to the NAS. They define the slots in every release.
10. **DNS:** A records for `bn1` and `bn2.fsnex.net` to the VPS IP, TTL about 300 s. No AAAA records: efsn's discovery has not been checked over IPv6.

## 4. Database

The VPS gets the same stopped backup database the producers start from (block
15,130,080), uploaded well before launch with `rsync --checksum`, so the launch
does not wait on about 110 GB crossing the home upload. Measure the upload time
when it happens. At launch, the VPS node imports `recovery.rlp` the way the
producers do (launch plan, step 5.2: `--nodiscover --maxpeers 0 --nat none`, no mining,
`admin.importChain`), then starts as `fusion-node.service` and follows the
producers.

A sync from genesis instead would take over a week: T1 replays about 23 blocks/s
on one core.

## 5. Before launch

| Check | How | Pass |
| --- | --- | --- |
| Ports | `ss -tulpn` on the VPS; from the PC, `nc -z <VPS IP> 40408` and a port scan of the VPS. | Only 22/tcp and 40408/tcp answer from outside; 40407/udp and 40408/udp are proven by T3's discovery. |
| Path to home | `mtr` from the PC to the VPS; `iperf3 -c <VPS IP>` and `iperf3 -c <VPS IP> -R` from the PC, with `iperf3 -s` on the VPS and 5201/tcp opened for the test only. | Recorded for the database upload estimate; no target. |
| T3a | Launch plan, section 5. | As stated there. |
| Restart from cold | Reboot the VPS. | Both services come back by themselves, and the producers and the explorer redial `bn2` within about a minute. |

## 6. After launch

- **Watch:** `bn2`'s head against the producers' and its peer count, from the VPS, reported to the owner.
- **Upgrades:** stop `fusion-node`, switch the `current` link, start; the bootnode the same way. Keep the previous version until the new one has run a day.
- **Rebuild:** this document, the two keys from the NAS, and a database copied from the explorer node or a producer.
- **Moving a slot:** move its key and point its DNS record at the new host, which must listen on the same port. The home nodes list `bn2` by IP, so their `static-nodes.json` changes too and they restart; running outside nodes keep the old address until they restart, since efsn resolves bootnode names once.

## 7. Open

- **Who administers it.** claudedev is trusted by no host by the owner's decision of 22 October. Giving it an SSH key to the VPS would let a session run T3 and the checks above; leaving it out means the owner runs them from the PC. The owner decides.
- **Snapshot hosting.** See the launch plan, section 8. Serving it from here needs a web port and shares the 200 Mbit/s port with `bn2`.
