# Joining the recovered Fusion chain

Draft operator kit, 4 October 2026. This is for a later producer joining the
accepted recovery chain. The backup signer remains stopped. It does not describe
creating recovery blocks or authorize spending either launch wallet's funds.

The final binary, recovery package, endpoints and host configuration are not yet
selected. Fill the release sheet below from the approved release before using
this on a public network. Never substitute the investigation's public test keys,
synthetic anchor or historical-backup manifest. Local rehearsal coverage and its
limits are in [the kit test report](restart-operator-kit-rehearsal.md).

## 1. Obtain the release sheet and verify the files

The release maintainer supplies these items together, with independently
authenticated checksums/signatures and the source/build provenance:

| Item | Required information |
| --- | --- |
| Software | Linux amd64 `efsn`, exact source/toolchain/build identity, checksum and signature verification instructions; approved profile and restore helper with their hashes |
| Chain | Genesis hash, chain ID, P2P network ID, fixed recovery anchor height/hash and package head hash/state root/ticket commitment |
| Data | Complete flat-LevelDB recovery package: `manifest.json`, `source.json`, every part JSON/ZIP, trusted manifest SHA-256, archive/restored sizes and free-space reserve |
| Connection | Approved DNS enode, numeric static fallback, P2P port and operator contact; actual advertised address/NAT configuration |
| Operation | Supported distribution/storage, cache/pruning settings, service start/stop instructions, log limits, dashboard enrollment and supervised response contact |

Download to a staging directory using the release's documented resumable route.
Compare the software/helper/profile hashes with the authenticated release sheet;
verify its signature as directed. A checksum downloaded from the same unverified
location is not independent authentication. Keep the immutable package separate
from the running database. Public download, mirror and signature commands will
be added once their owners and endpoints are selected.

Reserve space for the downloaded archives, the full restored database and the
reviewed operating reserve. The restore helper's default reserve is 100 GiB;
pass the release's explicit byte value. A small synthetic test's space use does
not size a production node.

## 2. Restore into a new datadir

Use an ordinary dedicated Linux account. `DATA`, `PACKAGE` and `RESTORE_HELPER`
below are absolute paths from your setup; `DATA` must be new. Set `MANIFEST_SHA256`
from the authenticated release sheet, not by trusting a newly computed digest.

```sh
umask 077
mkdir -- "$DATA"
python3 "$RESTORE_HELPER" restore \
  --source "$PACKAGE" \
  --destination "$DATA/efsn" \
  --manifest-sha256 "$MANIFEST_SHA256" \
  --reserve-bytes "$RESERVE_BYTES"
test -f "$DATA/efsn/restored.json"
```

The existing [restore helper](../tests/restart/snapshot_package.py) verifies the
manifest, archives and every restored file, then rereads the files before writing
`restored.json`. An error or missing marker means stop; do not start an incomplete
target. It refuses an existing destination. Retain failed targets for diagnosis
and retry to a new destination. Do not run `efsn init` on a restored chain.

The package contains database files only. Do not copy someone else's `nodekey`,
keystore, password, static/trusted peer files or service credentials into the new
operator environment. Do not manually transplant a different wallet's pending
automatic-purchase record.
The restored database itself may contain historical local purchase records;
inspect their owner before operating, following the
[record/nonce response procedure](restart-monitoring-response.md). Never delete
or rewrite one just to make automatic buying resume.

## 3. Start as a reader and check identity

Use the reviewed [network profile](restart-network-profile.toml) and selected
service invocation. A command template for the initial reader is:

```sh
"$EFSN" --config "$PROFILE" --datadir "$DATA" \
  --syncmode full --networkid "$NETWORK_ID" \
  --port "$P2P_PORT" --nat "$NAT_SETTING" \
  --v5disc=false --bootnodesv5= --bootnodesv4="$BOOTNODE" \
  --autobt=false --ipcpath "$IPC"
```

Keep mining disabled and wallets locked at this stage. Apply the release's
explicit cache/pruning/service settings too; the template above is not a tested
final host service. HTTP/WS remain disabled in the profile. Protect local IPC and
the datadir with account/filesystem permissions. A fresh datadir generates its
own P2P key; preserve it for later restarts. Once generated, record its actual
path and use the explicit `--nodekey` path in the reviewed service invocation.

Do not carry over old easy-node/Docker entrypoints: they include inherited
Foundation images, endpoints and telemetry defaults. See the
[network profile](restart-network-profile.md) for DNS changes, TCP/UDP and NAT.
Omit `--nodiscover` to use v4 discovery; `--nodiscover=false` has inherited
surprising behavior. Keep outbound dialing enabled. Test advertised TCP and UDP
from another network before offering your node as a public contact.

Attach over local IPC:

```sh
"$EFSN" --datadir "$DATA" attach "$IPC"
```

In that console, inspect these values. `ANCHOR_HEIGHT`, `REFERENCE_HEIGHT`,
`OWNER` and `STATIC_ENODE` are values supplied by the release/operator, not literal
names that the console predefines.

```js
admin.nodeInfo
net.version
eth.getBlock(0).hash
eth.getBlock(ANCHOR_HEIGHT)
eth.getBlock(REFERENCE_HEIGHT)
eth.syncing
eth.blockNumber
eth.getBlock("latest")
net.peerCount
admin.peers
eth.mining
fsn.isAutoBuyTicket()
```

Match genesis, chain/network IDs, anchor and reference block to the release
sheet. A below-anchor node must catch up first. Compare a common numbered block
and its state root/mixHash with the continuing producer; repeat to demonstrate
recent progress and check system time. `eth.syncing === false`, a peer count or
a green dashboard alone does not establish readiness.

The compiled recovery anchor is intentionally not a console/TOML setting. An
expected hash at that height is necessary, but only the approved executable
identity establishes that the mandatory rule is present. Do not add an anchor
override or accept a rewind to make a mismatching chain connect.

For the approved static fallback:

```js
admin.addPeer(STATIC_ENODE)
```

Then repeat the peer and common-block checks. A successful `addPeer` return only
accepts a connection target. Keep any permanent fallback in the reviewed profile.

## 4. Prepare your own funded wallet

Create or import only a wallet you control through the release's approved key
workflow. For a new local account, the existing CLI provides a hidden password
prompt:

```sh
"$EFSN" --datadir "$DATA" account new
```

Back up the encrypted keystore separately and confirm its public address. The
P2P key is different from this signing wallet. No validator private key or
password is needed by the dashboard or another operator. Existing-wallet import,
custody and unattended restart credentials need the final release/host review.

With `OWNER` set to your public address in the IPC console:

```js
var FSN_ASSET = "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
fsn.getBalance(FSN_ASSET, OWNER, "latest")
fsn.getTimeLockBalance(FSN_ASSET, OWNER, "latest")
fsn.allTicketsByAddress(OWNER, "latest")
eth.getTransactionCount(OWNER, "latest")
eth.getTransactionCount(OWNER, "pending")
txpool.status
```

Keep native balances as decimal strings/BigNumbers; do not convert wei balances
to JavaScript `Number`. One ticket costs 5,000 FSN under the retained rules.
Eligible rights must cover the purchase interval, and liquid FSN must cover gas
and applicable native fees. Review the exact proposed start/end, current nonce,
pending transactions and replenishment reserve. Exactly 5,000 liquid FSN is not
a sufficient operational guarantee. Another operator's test funding is not a
source of funds for you.

## 5. Buy the first ticket, then enable production

Wait for continuing producer progress and agreement first. Use the local IPC
console's hidden prompt to unlock your wallet for the supervised operation:

```js
personal.unlockAccount(OWNER, null, 0)
miner.setEtherbase(OWNER)
eth.coinbase
```

Duration zero leaves this account unlocked until it is locked or the process
stops. Do this only on the reviewed private host/IPC setup. Do not put a password
in the console history, shell arguments or a shared script. Confirm the returned
coinbase is your address.

For an ordinary current-head purchase after reviewing its interval:

```js
var purchase = fsntx.buyTicket({from: OWNER});
purchase
eth.getTransactionReceipt(purchase)
fsn.allTicketsByAddress(OWNER, "latest")
```

The defaults use the current parent's timestamp through 30 days later. A stale
head or interval-specific funding requires review before signing. Keep the
returned transaction hash; if the outcome is uncertain, inspect that transaction
and nonce before retrying. Do not blindly submit another purchase.

Wait for a non-null successful receipt. Inspect its canonical block and native
BuyTicket result in the console:

```js
var receipt = eth.getTransactionReceipt(purchase);
eth.getBlock(receipt.blockNumber).hash === receipt.blockHash
receipt.logs.filter(function(log) {
  return log.address.toLowerCase() === "0xffffffffffffffffffffffffffffffffffffffff" &&
    log.topics[0] === "0x0000000000000000000000000000000000000000000000000000000000000004";
}).map(function(log) { return JSON.parse(web3.toAscii(log.data)); })
```

Require a native result with the correct `TicketOwner`, a `TicketID` and no
`Error`, and compare the numbered block with the continuing producer. Receipt
status alone is insufficient because native-call errors can be encoded in logs.
The ticket may
already have been consumed by mining; inspect its purchase/mining events rather
than assuming a missing current ticket means the purchase failed.

After that first ticket is confirmed:

```js
miner.start(1)
eth.mining
```

Wait for `eth.mining` to be true, then:

```js
miner.startAutoBuyTicket()
fsn.isAutoBuyTicket()
```

Verify an accepted block whose miner is your address, a subsequent successful
automatic purchase, advancing account nonce and agreement with the continuing
producer. Enabling these flags alone is not evidence of production or buying.
Keep enough reviewed funds/rights for replacement tickets, fees and possible
retreat losses. Compatible forks still follow ordinary Fusion fork choice;
the fixed recovery anchor adds no ongoing finality.

## 6. Stop, restart and hand over operation

For a supervised stop:

```js
miner.stopAutoBuyTicket()
miner.stop()
eth.mining
fsn.isAutoBuyTicket()
personal.lockAccount(OWNER)
```

Stop the node cleanly with the service's normal SIGTERM/stop command and wait
for shutdown before backing up its database. Preserve the signing keystore,
P2P key and pending automatic-purchase record. A clean database backup gets a
new manifest; `restored.json` only attests to the initial restore.

Restart with the same approved binary/profile/datadir and P2P identity. Recheck
anchor, a common canonical head, state/ticket commitments, receipt lookups,
wallet/nonce and purchase status before unlocking and enabling production again.
Never reset a journal, database or saved purchase as routine troubleshooting.
Use the [response runbook](restart-monitoring-response.md) for stalls, nonce gaps,
lost peers, uncertain purchases or incompatible histories.

During launch, Peter supervises through SSH and the self-hosted fsn-stats
dashboard. A later owner records their own availability and response contact;
this does not require a hosted monitoring subscription. Dashboard enrollment
uses separate telemetry credentials and is not a consensus permission. Compare
its reports with direct IPC/RPC, and ensure production continues through a
dashboard outage. The backup signing process stays stopped throughout entry.
