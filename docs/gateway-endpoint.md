# Using the recovered Fusion gateway

Verified on 22 September 2026. The historical node and private RPC endpoint are
working. For ordinary development, keep the node running and open the SSH tunnel;
there is no need to repeat the restore, build, or setup steps.

## How the connection works

```text
Windows Fsnex / RPC client
  http://127.0.0.1:9000
          |
          | SSH local forward to peter@VM_IP
          v
Ubuntu VM fsnexrebirth
  127.0.0.1:9000 (fusion-rpc.socket)
          |
          | fusion-rpc.service / systemd-socket-proxyd
          | resolves the running container address on activation
          v
Docker internal bridge fusion-history
  fusion container :9000
          |
          v
  working database mounted from
  /home/peter/fusion-node/data/efsn/chaindata
```

There are two different localhost addresses: Windows localhost is the SSH tunnel
entry; Ubuntu localhost is the systemd proxy listener. SSH carries traffic between
them. The original backup on Windows is not involved in serving RPC.

The proxy exists because Docker did not activate the requested published port
for the node's internal-only bridge. Host-to-container access did work. The proxy
keeps a stable host endpoint without giving the node another network or depending
on a fixed container IP. It forwards TCP only; it is not an authentication layer,
a transaction filter, or a general outbound proxy.

The node has discovery disabled, zero maximum peers and an empty bootstrap list.
Mining is disabled. The original identities and keystore are not mounted. The
internal bridge blocks ordinary external routing, but is not total isolation
from the Docker host or other containers attached to that same bridge.

## Connect from Windows

In a dedicated PowerShell window, replace `VM_IP` with the Ubuntu VM address:

```powershell
ssh -N -o ExitOnForwardFailure=yes -L 9000:127.0.0.1:9000 peter@VM_IP
```

No output after authentication is normal. Leave this window open. Applications
on Windows use `http://127.0.0.1:9000`. Closing the window or losing SSH removes
access; the gateway itself keeps running. If local port 9000 is occupied, use
`-L 19000:127.0.0.1:9000` and connect to Windows port 19000 instead.

Test from another PowerShell window:

```powershell
$payload = '[{"jsonrpc":"2.0","id":1,"method":"eth_chainId","params":[]},{"jsonrpc":"2.0","id":2,"method":"eth_blockNumber","params":[]},{"jsonrpc":"2.0","id":3,"method":"net_peerCount","params":[]},{"jsonrpc":"2.0","id":4,"method":"eth_mining","params":[]}]'
Invoke-RestMethod -Uri 'http://127.0.0.1:9000' -Method Post -ContentType 'application/json' -Body $payload | ConvertTo-Json
```

Expected results, by ID: `0x7f93`, `0xe6dde0`, `0x0`, `false`. The head is
15,130,080, dated 7 October 2025 at 08:43:50 UTC. This isolated historical node
should not advance. It is the recovered backup head, not proof of the final
canonical network block.

## On Ubuntu

Use the normal account, not a root shell:

```bash
cd ~/fsn-efsn
bash QuickNodeSetup/fsnNode.sh
```

- **3: Start the node** validates the historical container and starts private RPC.
- **4: Stop the node** closes private RPC first and allows database shutdown.
- **6: Show node logs** displays the node output.
- **R: Configure private RPC** installs/refreshes the endpoint on a running node
  without rebuilding or restarting it. This also refreshes the target address.
- **9: Set up isolated historical gateway** rebuilds/recreates the node and is
  only needed for deliberate node updates, not ordinary endpoint use.

After manually restarting/recreating containers outside the manager, use R to
refresh the proxy.

## Start at boot

Enable once through the manager: **7: Configure node**, then **4: auto-start**.
This installs root-owned copies of the manager scripts in
`/usr/local/libexec/fusion-gateway/` and enables `fusion-gateway@peter.service`.
The copies do not follow the checkout. After updating the checkout, run option 9
or toggle auto-start off and on again to refresh them. Enabling also runs the
start below at once. When the node is already running, private RPC is briefly
closed and re-verified.

At boot the unit runs after `docker.service` and `network-online.target`, so the
LAN address exists before the socket binds. It then does what option 3 does:
validates the historical container, starts it, opens private RPC and waits up to
15 seconds for `eth_chainId` = `0x7f93`. If the node is still loading its
database, it repeats option R's proxy refresh every 30 seconds, for up to 40
attempts (roughly half an hour). It stops retrying if the container exits. At
shutdown it does what option 4 does: closes private RPC, then gives the node up
to 300 seconds to close its database before Docker stops.

The unit stays active even when its start fails, so shutdown still stops a node
that was started by hand afterwards. A failed start shows only in the log:

```bash
systemctl status fusion-gateway@peter.service
journalctl -u fusion-gateway@peter.service -b --no-pager
```

Options 3 and 4 still work while auto-start is enabled. A LAN drop-in on the VM,
`/etc/systemd/system/fusion-rpc.socket.d/lan.conf`, adds
`192.168.1.212:9000` for the explorer host 192.168.1.240. Reinstalling the units
leaves it in place.

`fusion-rpc.socket` sets `DefaultDependencies=no`. With the defaults, systemd
stops the socket after every ordinary service at shutdown. The gateway unit's
stop would then wait on the socket, and the socket on the gateway unit, until the
stop timed out and the node was killed. A systemd 255 simulation reproduced that
timeout. Without the default dependencies the socket is still stopped at
shutdown, but nothing orders it against the gateway unit.

A clean stop also needs ESXi to shut the guest down rather than power it off. On
the `fsnex-node` VM, the host's autostart stop action must be *Shut down* (it
needs VMware Tools in the guest), with a stop delay of at least 6 minutes.

Test locally on Ubuntu:

```bash
curl --fail --silent --show-error http://127.0.0.1:9000 \
  -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]}'
sudo ss -ltnp 'sport = :9000'
```

The listeners must be `127.0.0.1:9000` and, from the LAN drop-in,
`192.168.1.212:9000`. The loopback listener was verified live, with systemd and
systemd-socket-proxyd holding the socket. The service activates on the first
connection, so an inactive proxy service before a request is not itself a fault.

## Troubleshooting in order

1. If Windows cannot connect, check that the SSH window is still connected and
   its port forward did not fail. Test localhost on Ubuntu before changing efsn.
2. If Ubuntu localhost fails, inspect the proxy and node:

   ```bash
   sudo systemctl status fusion-rpc.socket fusion-rpc.service
   sudo journalctl -u fusion-rpc.service -n 50 --no-pager
   sudo docker ps -a --filter name=fusion
   sudo docker logs --tail 100 fusion
   ```

3. After a reboot, read `journalctl -u fusion-gateway@peter.service -b` first: it
   shows whether validation, the container start or the RPC wait failed. If the
   node is running but the proxy target is stale, choose R. If the node is
   stopped, start through the manager and read its logs. Do not delete or restore
   the database merely because a tunnel or proxy failed.
4. No output from `docker port fusion` is expected for the current design. The
   host endpoint is provided by systemd, not Docker publishing. Do not attach an
   external Docker network or open a public firewall port as a workaround.

The node's APIs are `eth`, `net`, `web3`, and `fsn`. Access is private but not
method-filtered: `eth` includes transaction submission. Development probes should
be read-only. A containerized client cannot use its own localhost to reach the
Windows/Ubuntu host; configure its tunnel/network deliberately.

## Data and implementation status

The preserved Windows source is `C:\Users\Peter\Documents\CODING\fusion-node`.
The Ubuntu database is a writable working copy, including during recovery and
non-mining operation. Stop the node cleanly before copying it as a new backup.

Current deployment: binary built from `a9fa178`, manager/proxy from `846fa28`,
branch `feature/isolated-gateway`. Later documentation-only revisions do not
change the running binary. Fixes to bootstrap parsing let an empty list suppress
Foundation DNS lookups; no balances or consensus rules were changed.

The [recovery record](historical-gateway-recovery.md) documents the verified
samples and remaining coverage gaps. The next development task is Fusion-specific
Fsnex support; the sibling checkout has
[the development handoff](../../fsnex-rebirth/docs/fusion-development-handoff.md).
Do not run bulk indexing in this 200 GiB gateway VM or reuse another chain's
index database/checkpoints. Keep RPC URLs in local configuration/user secrets.
