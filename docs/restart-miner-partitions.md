# Miner convergence after packet loss

26 September 2026, runtime baseline `8d84a04` (P1–P15). This extends the
[transport partition tests](restart-network-partitions.md) to separate actual
node services, miners, automatic ticket buyers and the ordinary sync scheduler.
Only tests, documentation and evidence change; there is no new runtime patch.

## Rehearsal

Two isolated node processes start from the same synthetic anchor with separate
public test keys and LevelDB databases. They connect through an ordinary static
peer registration before the fault. A Linux `tc netem` rule then drops all IPv4
loopback traffic for at least 45 seconds. Private Unix-socket RPC remains usable.
The test requires a separate network namespace containing only enabled loopback,
explicit opt-in and root for the temporary queue configuration. Each healed
fault must have a positive kernel packet-drop counter.

Both normal miners and automatic buyers run during the fault. Each miner is
stopped after its first confirmed purchase, bounding each isolated branch to
one to three blocks and one purchase. The branches must differ, share the accepted
anchor and have unequal total difficulty obtained through ordinary consensus.
No artificial block weight or shorter consensus/network timer is used.

Both P2P sessions must disappear before healing. Removing the loss rule is the
only reconnect intervention: there is no new `admin_addPeer`, `lab_sync`, manual
transaction resubmission, block insertion or process restart during convergence.
The existing static-peer dialer reconnects and the ordinary full-sync scheduler
adopts the heavier compatible branch. Both nodes must agree on canonical head
markers, account-state root, ticket root and the winning purchase's native receipt.
The displaced purchase must lose its former canonical receipt.

Both miners and buyers then resume. The test requires at least three further
blocks and at least two successful canonical native purchases from each owner.
The original isolated purchases must appear on the common chain. Every purchase
in the checked suffix must have a successful native result on both peers.

After stopping both miners, the test observes a common head unchanged for 35
seconds before inspecting the final state. Only then does it hold new block
signatures to examine each buyer's next-nonce saved intent and matching pool
entry across a retry interval. Both services undergo clean cold restart with
pool journaling disabled: the head/roots and exact signed intent must survive,
the initial pool must be empty, and the buyer must recover the same signed bytes.

## Recorded results

Both final Linux race-enabled runs pass. They used the same executable in
separate disposable namespaces and databases, launched concurrently. The setup
timestamp and isolated branches happened to match; subsequent production differed,
so their final block hashes/state roots differ across runs as expected. Within
each run, both peers and both cold reopenings agree.

| Observation | Run `drained` | Run `repeat` |
| --- | --- | --- |
| Complete test duration | 189.35 s | 189.63 s |
| Packet-loss interval | 45.01 s | 45.01 s |
| Kernel-dropped packets | 39 | 39 |
| Healing to ordinary reconnect/full-sync convergence | 33.85 s | 33.85 s |
| Joined height / final height | 15,130,097 / 15,130,101 | 15,130,097 / 15,130,101 |
| Canonical native purchases, key 1 / key 2 | 3 / 5 | 4 / 5 |
| Head changes observed across both nodes after stop | 4 | 4 |
| Cold heads, roots, saved bytes and pool recovery | Pass | Pass |

There are no race reports in either final run or the three retained failed
attempts. The earlier failures are not counted as passes. This is focused
Linux service evidence; broader suites and native Windows execution were not
rerun. The three inherited networking-suite failures remain unresolved.

The test helper now allows each child service six minutes rather than three,
covering outage, normal retry and cold inspection without changing production
deadlines. The existing namespace guard is shared with the transport fixture.

## Miner stop is not a completed shutdown

One retained run reconnected and continued mining successfully, then failed the
final snapshot assertion: the expected head was 15,130,098, but a stopped node
subsequently published 15,130,099 while reporting `Mining:false`. This is actual
existing worker behavior, not a state-root mismatch between copies of one block.

`worker.stop` only clears the running flag. It does not cancel every sealing
operation already in progress. DaTong signs before waiting for its publication
time, and the worker result loop can still accept a completed result while the
running flag is false. The task loop also deliberately retains some first-ranked
work across new tasks. See [worker lifecycle and results](../miner/worker.go)
and [DaTong sealing](../consensus/datong/consensus.go).

The 35-second unchanged-head observation is a bounded test-fixture allowance;
it is not a guaranteed production drain time or a new node setting. The final
test records head changes seen after stop instead of assuming the RPC creates
an immutable snapshot. No worker behavior was changed to make the check pass.

For backup-key handover, disable automatic purchases, inventory already-signed
purchases and sealing work, shut down the old signer process cleanly and confirm
it has exited before allowing another process to use that key. Inspect the
persisted head and continuing peer's view after shutdown. Stopping a process
cannot revoke a signature or transaction already sent elsewhere. The guarded
one-backup-block recovery command remains separate from ordinary mining and
continues to enforce its signed-artifact quota.

The first attempt also retained a simpler fixture failure: an ordinary miner
sealed an empty block before its automatic purchase reached the pool, then
included the purchase in its next block. A later attempt also observed a delayed
empty third block after stop. The final fixture inspects the isolated heads
after the outage interval and permits one to three blocks while retaining
exactly one purchase per wallet. All failed attempts remain in the evidence.

## Scope and remaining checks

The test bounds production before healing; it does not demonstrate uninterrupted
mining throughout a reorganization, long/deep forks, repeated partitions or equal
weight fork resolution. The existing [two-purchase nonce rollback](restart-purchase-nonce-rollback.md)
still demonstrates a different case requiring manual repair. A one-purchase
partition passing here does not remove that limitation or settle the release's
monitored-repair policy.

The subsequent [continuous-miner follow-up](restart-continuous-partitions.md)
uses complete small synthetic history and leaves both miners running through
reconnection. Its repeated-outage probe reaches a common advancing chain while
the losing buyer remains paused on a nonce gap. The bounded passes above do not
imply unattended recovery from those multi-purchase rollbacks.

This uses the existing sparse two-owner fixture: one million synthetic FSN per
owner and fourteen normally executed setup blocks. It does not validate the
donation wallet's real funding, unavailable deep ancestry, full historical sync,
or execution of the candidate against complete mainnet history. Expected sparse
history bloom-index errors are retained in the process logs. Public IPv4/IPv6,
DNS/NAT deployment, Windows packet-loss execution and real key custody remain
separate checks. No original backup, complete-state dataset or network storage
copy is accessed.

The fixed anchor rejects incompatible recovery history. These branches share
that anchor and undergo ordinary fork selection; this adds no ongoing finality.
Independent review and final launch acceptance remain open.

Scripts, all attempts, executable/source identities and checksums are in
[`restart-miner-partition-2026-09-26`](evidence/restart-miner-partition-2026-09-26).
