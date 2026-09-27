# Investigating a surviving Fusion node

27 September 2026. Peter has asked a possible surviving operator for their
enode address. The response is pending. No address has been received or tested,
and continued mining has not been established. Recovery investigations continue
while we wait; this is not a decision to adopt another chain.

## Minimal request to the operator

Ask for the complete public `enode://...` address and for the node to remain
running. A reachable enode is enough to begin our investigation. Do not initially
burden the operator with version, ticket or block-report commands: we can inspect
the advertised client identity and chain over P2P, observe new blocks and attempt
normal validation ourselves. The advertised identity is not proof of the exact
executable or absence of modifications.

For a standard FUSION Node Manager installation using
[`QuickNodeSetup/fsnNode.sh`](https://github.com/FUSIONFoundation/efsn/blob/master/QuickNodeSetup/fsnNode.sh):

1. Choose **8 — Exit to shell** in the Node Manager. This leaves the node running.
2. Paste this single command into the Linux terminal:

   ```bash
   sudo docker exec fusion efsn --exec 'admin.nodeInfo.enode' attach /fusion-node/data/efsn.ipc
   ```

3. Send the complete result beginning with `enode://`. If the command fails, send
   its error instead.

The upstream script names the container `fusion` and uses this IPC path for its
own ticket query. The command reads the public node address and exits; it does
not stop mining or change configuration. No private key, keystore, wallet
password, public RPC endpoint or remote administration access is required.
The script has no dedicated interactive-console menu item.

If the advertised IP is private, unspecified or unreachable, first diagnose
the endpoint with the operator. The normal P2P port is 40408, but their actual
configuration governs. An outbound connection from their node to our reachable
peer is another option. Do not request an upgrade, reinstall or restart merely
to obtain the address.

## What a valid continuation would change

A miner could have continued purchasing tickets and producing valid blocks
without Foundation infrastructure. If we find such a chain, investigate ordinary
synchronization before choosing historical recovery. After validating the chain
and the donation wallet's funding on it, an ordinary ticket purchase could allow
our node to join production without the expired-ticket bridge or borrowed-key
startup. Merely syncing requires neither tickets nor unlocked accounts.

A running process or an enabled mining flag alone is insufficient: observe
advancing blocks with appropriate timestamps, validate their rules and ancestry,
and establish that required history/state can be acquired. Compare genesis,
network identity and the block at the preserved backup height 15,130,080. A
different hash there requires investigation of the common ancestor, not an
automatic declaration that the other chain is invalid. Greater height or
advertised total difficulty alone does not establish validity or social
acceptance. Adopting a valid continuation includes its transactions and rewards.

Use disposable copies of the original preserved data, compatible software with
normal validation and mining disabled for the first synchronization attempt.
Keep synthetic rehearsal databases separate. No production anchor has yet been
selected. If direct synchronization cannot supply the necessary data, assess a
consistent snapshot or export while protecting the operator's surviving copy.

Finding one valid continuation does not rule out another hidden competing chain.
The narrowly scoped accepted-history boundary remains a separate launch decision:
it could anchor reviewed surviving history instead of a constructed recovery
prefix. No broader finality redesign follows from this investigation.

## Next action when the address arrives

Validate and test the supplied endpoint, inspect peer identity and head, compare
ancestry, then attempt isolated normal synchronization. Record actual results
before changing the [restart plan](restart-plan.md). Ask the operator for further
information only when a specific obstacle requires it.
