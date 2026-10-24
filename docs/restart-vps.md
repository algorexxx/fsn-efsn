# Restart VPS

24 October 2026. The public P2P host for the restarted network. It carries both
bootnode slots from the [launch plan](restart-launch-plan.md#4-infrastructure),
so nothing on the home network has to accept a connection from the internet.

## 1. Role

| Does | Does not |
| --- | --- |
| `bn1.fsnex.net:40407`: discovery-only `bootnode`. | Hold wallet keys or mine. |
| `bn2.fsnex.net:40408`: full efsn node, the network's public peer. The producers and the explorer node dial out to it. | Serve RPC to anyone. The explorer's RPC and trace node stays at home ([launch plan](restart-launch-plan.md#4-infrastructure)). |
| Host T3. | Front the websites. That is a separate, open question in `dromkaken-industrivagen` (`docs/PUBLIC-SITES.md`). |
| Later: watch the network and the public sites from outside. | Reach anything at home. No tunnel, SSH key or allow-list entry into the LAN. |

One VPS, not two. A second Contabo VPS would likely share the host, the network
and the provider, so it guards against little. If this one is down, the
producers and the explorer carry on through their static peers and outside nodes
fall behind until it is back. Independence comes from community operators
taking over slots (launch plan, section 7).

## 2. Machine

| Item | Choice |
| --- | --- |
| Plan | Contabo Storage VPS 10: 2 vCPU, 4 GB RAM, 300 GB SSD, 200 Mbit/s, unmetered incoming and fair-use outgoing traffic. |
| Price | About €4.40/month on a 24-month term (Contabo's figure, including VAT); confirm the currency and term at checkout. Cloud VPS 6 (6 vCPU, 12 GB, 200 GB SSD, €6.00) is the fallback if snapshots turn out to matter: Contabo lists them for Cloud VPS only. |
| Region | European Union (Germany). |
| OS | Ubuntu 24.04. |
| Disk | The chain database is about 110 GB (the backup: 109.1 GiB) and grows slowly, so 300 GB leaves room for a published snapshot file as well. |
| RAM | The T2 nodes use about 110 MB each with `--cache 128`. 4 GB is plenty for one node and the bootnode. |

## 3. Setup

1. **Account:** 2FA on the Contabo account. Its control panel can reset the root password, so the account is as much a way in as SSH.
2. **SSH:** the owner's PC key only; `PasswordAuthentication no`, `PermitRootLogin no`, a `peter` user with sudo. Contabo's VNC console is the way back from a lockout.
3. **Firewall (UFW):** deny incoming except 22/tcp, 40407/udp and 40408/tcp+udp. Nothing else listens publicly.
4. **Updates:** `unattended-upgrades` for security updates.
5. **User:** a system user `fusion` without login owns `/var/lib/fusion`.
6. **Binaries:** `efsn` and `bootnode` from the release, in `/opt/fusion/<version>/`, with a `current` symlink so an upgrade and a rollback are one link change. Production runs the binaries under systemd. The Docker image is checked in T3 only (its entrypoint cannot pass `--nat` or `--bootnodes`; launch plan, section 8).
7. **Services:**

   `fusion-bootnode.service`:
   ```text
   bootnode -nodekey /var/lib/fusion/bn1.key -addr :40407 -nat extip:<VPS IP>
   ```

   `fusion-node.service`:
   ```text
   efsn --datadir /var/lib/fusion/bn2 --nodekey /var/lib/fusion/bn2.key \
        --port 40408 --nat extip:<VPS IP> --syncmode full --identity bn2.fsnex.net
   ```
   No `--http` or `--ws`; status is read over IPC with `efsn attach`.
   `/var/lib/fusion/bn2/efsn/trusted-nodes.json` lists producer A, producer B
   and the explorer node, so they always get a slot even with the default 25
   peers taken.
8. **Keys:** generate `bn1.key` and `bn2.key` with `bootnode -genkey`, read the enode IDs with `bootnode -nodekey <key> -writeaddress`, and back both keys up to the NAS. They define the slots in every release.
9. **DNS:** A records for `bn1` and `bn2.fsnex.net` to the VPS IP, TTL about 300 s. No AAAA records: efsn's discovery has not been checked over IPv6.

## 4. Database

The VPS gets the same stopped backup database the producers start from (block
15,130,080), uploaded well before launch with `rsync --checksum`, so the launch
does not wait on about 110 GB crossing the home upload. Measure the upload time
when it happens. At launch, the VPS node imports `recovery.rlp` the way the
producers do (launch plan, step 5.1: `--nodiscover --maxpeers 0`, no mining,
`admin.importChain`), then starts as `fusion-node.service` and follows the
producers.

A sync from genesis instead would take over a week: T1 replays about 23 blocks/s
on one core.

## 5. Before launch

| Check | How | Pass |
| --- | --- | --- |
| Ports | `ss -tulpn` on the VPS; from the PC, `nc -z <VPS IP> 40408` and a port scan of the VPS. | Only 22/tcp and 40408/tcp answer from outside; 40407/udp and 40408/udp are proven by T3's discovery. |
| Path to home | `mtr` from the PC to the VPS; `iperf3 -c <VPS IP>` and `iperf3 -c <VPS IP> -R` from the PC, with `iperf3 -s` on the VPS and 5201/tcp opened for the test only. | Recorded for the database upload estimate; no target. |
| T3 | Launch plan, section 5. | As stated there. |
| Restart from cold | Reboot the VPS. | Both services come back by themselves and `bn2` reconnects to the producers. |

## 6. After launch

- **Watch:** `bn2`'s head against the producers' and its peer count, from the VPS, reported to the owner.
- **Upgrades:** stop `fusion-node`, switch the `current` link, start; the bootnode the same way. Keep the previous version until the new one has run a day.
- **Rebuild:** this document, the two keys from the NAS, and a database copied from the explorer node or a producer.
- **Moving a slot:** move its key and point its DNS record at the new host, which must listen on the same port.

## 7. Open

- **Who administers it.** claudedev is trusted by no host by the owner's decision of 22 October. Giving it an SSH key to the VPS would let a session run T3 and the checks above; leaving it out means the owner runs them from the PC. The owner decides.
- **Recovery blocks over P2P.** See the launch plan, section 8. The VPS avoids the question by importing `recovery.rlp`.
