# Fusion node manager

For the recovered gateway already running on Ubuntu, see the
[endpoint operations guide](../docs/gateway-endpoint.md). It covers the SSH
tunnel, daily start/stop, verified results, and troubleshooting.

Run the manager from a checkout with Bash:

```bash
bash QuickNodeSetup/fsnNode.sh
```

Use your normal Ubuntu user, not `sudo bash`. The manager invokes sudo for Docker
and systemd. Keep the whole checkout: the manager uses the adjacent helper and
service files. Do not use the former download-and-execute command for a single script.

## Historical gateway recovery

This mode serves an existing mainnet database without mining or joining peers.
It does not change consensus, balances or historical blocks. efsn still writes its
database during recovery and normal operation: always use a working copy.

Start with an isolated Ubuntu VM, provisionally 4 vCPUs, 16 GiB RAM and 350 GiB
usable SSD storage. Keep the preservation backup outside the VM. This budget does
not include an explorer database or host-side VM snapshots.

Install Docker Engine, Git, Bash, curl, jq, locate and lsb-release before running the manager.
Docker must be running and accessible through sudo. The first image build needs
internet access for container images, Alpine packages and Go modules; the running
gateway is attached only to an internal Docker bridge with no external route.

1. Check out the reviewed recovery commit. The setup requires a clean checkout,
   including untracked files, so the recorded revision identifies the build source.
2. Run the manager. Choose **Set up isolated historical gateway**: option 3 on the
   initial menu or option 9 when a configuration already exists.
3. Setup resolves the historical Go 1.21.3 and Alpine 3.18 image tags to digests,
   builds this checkout and pins the container to the resulting image ID. Build
   references and source revision are saved in `~/fusion-node/node.json`.
   Existing configuration is copied beside it before replacement.
4. Setup leaves the container **stopped**, with automatic restart and systemd
   auto-start disabled. It refuses to replace a running container or a container
   from another mode. Stop/remove an older container through the menu first;
   removal now preserves configuration and data.
5. Copy the complete backed-up `data/efsn/chaindata` directory into
   `~/fusion-node/data/efsn/chaindata`. Include `CURRENT`, its manifest, journals
   and all table files. Do not merge two databases. If the destination already has
   a different database, preserve it separately while the container is stopped.
   Ensure your Ubuntu user can read the metadata and Docker can write the copy.
6. Verify the copied file inventory, sizes and checksums against the source before
   starting. The manager checks only the CURRENT/manifest pair; this is not an
   integrity or completeness check.
7. Choose **Start the node**, then **Show node logs**. Record the startup output,
   especially database recovery, rewinds, missing state and the accepted head.
   Stop if recovery fails; retain the logs and original backup rather than deleting
   files or initializing a new genesis over the restored database.

You can copy the backup before setup too: setup preserves it. Only chaindata is
mounted into the container. The old node identity, peers, wallet keystore and
password files are not mounted. A new container generates its own runtime identity.

The historical base images intentionally match the old build environment. This is
not a modernization/security upgrade. Image IDs pin the installed artifact, but
future source rebuilds are not promised byte-identical because package installation
can resolve newer packages. Keep the built image and recorded metadata with the
recovery artifacts. Do not expose this historical client publicly.

## Access and checks

A systemd TCP proxy listens on the VM's loopback address, 127.0.0.1:9000.
The node itself has no published ports and remains on its internal bridge. WebSockets,
P2P port publishing, discovery, staking, ticket auto-buy, signing keys and official
node-stat reporting are not enabled. The internal network and container settings
are checked before menu-driven starts. Do not attach additional Docker networks or
change the container manually. Docker/systemd commands outside the manager bypass
its pre-start database checks.

On the VM:

```bash
curl --fail --silent --show-error http://127.0.0.1:9000 \
  -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]}'
```

Check `eth_chainId` (mainnet 32659 / `0x7f93`), `eth_getBlockByNumber` for block zero
and latest, `net_peerCount` (zero) and `eth_mining` (false). Compare genesis with
`0xc2422b1d9d16331be2a5b207c0783027d4419498003f729f4b9e9c5c1838623a`.
Then sample early and late blocks/receipts and probe tip state. A head number alone
does not establish complete history, correct state or a successful recovery.

From your workstation, tunnel RPC over SSH:

```bash
ssh -N -L 9000:127.0.0.1:9000 YOUR_USER@YOUR_VM
```

The exposed namespaces are `eth,net,web3,fsn`. This is a private non-producing
gateway, not a method-filtered public read-only API: `eth` includes transaction
submission. Do not add public firewall rules for RPC.

Use the menu to stop the gateway before copying its database or taking a consistent
backup. Shutdown is allowed up to five minutes. Check the logs for clean closure;
if Docker had to kill the process after that timeout, do not call it a clean backup.

## Updates and existing modes

Historical mode never checks the official Docker Hub repository for updates. The
normal Update action refuses to replace it with a public image. To rebuild, stop
the gateway, check out the desired reviewed commit and run historical setup again.
The new container remains stopped for explicit review/start.

The existing miner and ordinary gateway modes retain their original public image
selection and networking. Installation now refuses an existing node directory;
configuration remains available through its menu. Neither installation nor removal
purges chaindata. Old-layout data directories are left for manual migration.
The bundled systemd service replaces the former foundation-hosted download.

## Script verification

```bash
bash -n QuickNodeSetup/fsnNode.sh
bash -n QuickNodeSetup/isolatedGateway.sh
bash QuickNodeSetup/isolatedGateway.test.sh
bash QuickNodeSetup/fusion-rpc-proxy.test.sh
```

The tests require Bash, jq and standard Unix utilities, run as a non-root user, and
stub Docker/systemd. They exercise data preservation, failed builds/stops, image
pinning and isolation checks without a Docker daemon or real chaindata. They leave
small fixtures under the system temporary directory for inspection. A real image
build and a VM recovery test are still required before treating this as validated
against a Fusion backup.

## Bootstrap startup failure

Historical startup must not resolve the Foundation bootstrap hostnames. The
upstream v4 bootstrap parser treated an explicitly empty bootnodes value as an
invalid URL; omitting the option instead loaded the default hostnames. The
recovery client uses the existing SplitAndTrim helper for v4 as well as v5, so
an explicitly empty list disables bootstrap nodes without DNS resolution.

For either Bootstrap URL invalid error, update the checkout and rerun historical
gateway setup while stopped. This rebuilds the client and recreates the container
with an empty bootnodes list, preserving the restored database. Discovery remains
disabled, maxpeers is zero, and the Docker network remains internal. The historical
image build runs the empty-bootstrap regression test before building efsn.

## Stable private RPC on Ubuntu

Docker may ignore published ports for a container attached only to an internal
bridge. The manager installs `fusion-rpc.socket`, `fusion-rpc.service`, and a
root-owned helper using Ubuntu's `/usr/lib/systemd/systemd-socket-proxyd`.
The socket binds only `127.0.0.1:9000`. The helper checks the running container's
mode and sole internal network, discovers its current IPv4 address, and forwards
TCP to port 9000. No second network is attached to efsn. The helper uses Docker's
privileged socket, so its service runs as root; the interactive manager still
runs as the normal user. This is TCP forwarding, not authentication or RPC method
filtering. Only trusted local users and SSH clients should have access.

For an already running historical gateway, update the checkout and choose **R:
Configure private RPC**. This installs and verifies the endpoint without stopping
or rebuilding the node. If Docker really publishes the old port mapping, setup
refuses the conflicting endpoint; stop the node and use option 9 once to recreate
it without that mapping. An unused legacy loopback mapping is accepted for this
migration; public bindings and extra networks are rejected.

Menu-driven starts refresh the proxy target and probe `eth_chainId` before
reporting RPC ready. Probe failure closes the endpoint and leaves the node running
for diagnosis; a long database recovery can require retrying R after it finishes.
Menu-driven stop, removal, and recreation close the proxy first. The socket and
node are not enabled at boot. After reboot, start through the manager. If using
Docker commands outside the manager, rerun R after a restart/recreation to refresh
the target. Do not rely on a saved container IP.

From Windows or the Fsnex host, use an SSH tunnel:

```bash
ssh -N -o ExitOnForwardFailure=yes -L 9000:127.0.0.1:9000 peter@VM_IP
```

Use `http://127.0.0.1:9000` from that machine while the tunnel runs. A containerized
indexer needs its own explicit tunnel/network configuration; its loopback is not
the host's loopback. No public RPC firewall rule is needed.

On Ubuntu, diagnose with:

```bash
sudo systemctl status fusion-rpc.socket fusion-rpc.service
sudo journalctl -u fusion-rpc.service -n 50 --no-pager
sudo ss -ltnp 'sport = :9000'
```

The listener should be on `127.0.0.1:9000`, never `0.0.0.0:9000` or `[::]:9000`.
A stopped service before the first request is normal: the socket activates it.
