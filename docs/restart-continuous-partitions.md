# Continuous miners during network partitions

26 September 2026. Runtime baseline `0148d5e`, retaining P1–P15. This follows the
[bounded miner-partition rehearsal](restart-miner-partitions.md). All changes
are test helpers, investigation documentation and evidence; production code and
the selected launch design are unchanged.

## Why a different fixture is needed

The earlier high-height fixture has only a short suffix of history. Once both
isolated miners produce several blocks, the downloader can exhaust its initial
ancestor sample and search below that suffix. Failure to answer those requests
would characterize missing fixture data rather than a real complete node.

This follow-up constructs a complete small synthetic chain from genesis. Two
separate LevelDB databases independently execute and import 24 setup blocks,
then enforce the same block-24 restart anchor. Every block from genesis through
the anchor is present and linked. Both cold node services must agree on the
anchor and on each public test wallet's 24 executed purchase nonces.

The fixture uses existing devnet selection rules and chain ID 55555, with the
configured EVM/Eco forks active from genesis. DaTong retains its ordinary
15-second period, delays, ranking and difficulty calculation; P2P and automatic
buyer retry timings are unchanged. Both public test wallets receive one million
synthetic FSN; key 1 starts with two genesis tickets and both owners buy tickets
in every setup block. This deliberately funds concurrency testing. It does not
reproduce mainnet's height-dependent rewards or the donation wallet's runway.
The synthetic genesis is test-only and is not a proposed production genesis.

The test-service configuration accepts this explicit synthetic genesis. Existing
fixtures retain their default configuration and six-minute child-process limit;
the new continuous case alone requests a twelve-minute child-process limit.
Neither facility exists in a production command.

## Fault and recovery checks

The two real services connect over encrypted devp2p, enable ordinary miners and
automatic buyers, and first establish shared progress. Linux kernel packet loss
then cuts all IPv4 loopback traffic for 90 seconds. A second 60-second outage is
planned after the first recovery. During both outages and recovery, the test
keeps the miner and buyer flags enabled. It does not hold signatures, call
`miner_stop`, force downloader synchronization or add a peer again to heal.

The fault must drop actual packets, remove both established peer sessions, and
produce divergent multi-block branches. Healing only removes the loss rule.
The ordinary static-peer dialer and full-sync scheduler must reconnect and
establish an advancing common branch. Native purchase receipts are sampled on
both peers and resampled when a live reorganization changes their block mapping.

Saved purchase records, canonical nonces, pool counts, heads and enabled flags
are logged before healing and on a progress failure. These distinguish chain
convergence from the losing wallet's ability to resume replenishment. The
[previous multi-purchase rollback](restart-purchase-nonce-rollback.md) demonstrates
why a retained future-nonce purchase can require manual repair.

## Results

The complete fixture and both cold service startups pass with Linux race
detection. The initial continuous probe failed its replenishment requirement
after 400.71 seconds. Its two kernel faults lasted 90.35 and 60.22 seconds and
dropped 44 and 34 packets. Both miners and buyers remained enabled.

After the second healing, both nodes reported exactly block 53,
`0xa6dc3fb7e50d77757979b56a9ed20f9574ebe9ecdea4896518216e5a7ca3d314`.
Key 1's canonical nonce was still 28, its saved signed purchase required nonce
32, and its pending and queued pools were empty. The saved hash was identical
before and after the second outage. Key 2 continued purchasing and reached
nonce 52. The chain's recovery therefore did not restore both buyers.

The initial probe's first-cycle success marker was too weak: it accepted an old
purchase being included again as evidence of replenishment. That marker must
not be read as successful automatic-buyer recovery. The final test additionally
requires each wallet to include a purchase at or beyond its canonical nonce
sampled immediately before healing. It retains normal mining during reconnect
and gives replenishment 150 seconds after peer recovery.

The strict run also failed, after 303.05 seconds. Its 90.33-second fault dropped
44 packets. At the final observation both services agreed on block 47,
`0x0c3c1bc899b6acb1bc02fd2dd649283850f3bb07ae53fc8a27a7b060da216f5d`.
Key 1 remained at canonical nonce 28 with a saved nonce-30 purchase and an empty
pool; key 2 reached nonce 46. Both mining and buyer flags remained enabled.
The stricter test fails on this first recovery, so its second outage and final
cold-state acceptance checks are not reached.

| Check | Result |
| --- | --- |
| Complete fixture, original executable | Pass, 4.42 s |
| Complete fixture, final executable | Pass, 4.19 s |
| Fixture followed by the existing mainnet-configured heavier-peer case in one parent process | Both pass, 10.16 s total; test global rules are restored |
| Initial continuous 90 s + 60 s outage probe | Fail: chain advances, key 1 remains at nonce 28 with saved nonce 32 |
| Final strict continuous 90 s outage | Fail: chain advances, key 1 remains at nonce 28 with saved nonce 30 |

All these checks use Linux race detection and report no data races. The two
live failures remain failures; neither is counted as successful unattended
replenishment. No broad-suite or native Windows rerun is claimed.

This follows the already-characterized one-ticket-per-owner pool limit: a
compatible reorganization can displace several purchases while the pool restores
only one. After that lower-nonce purchase is included, the latest saved intent
can remain ahead of the canonical account nonce. The buyer retains its signed
intent and pauses; ordinary new blocks do not manufacture the missing nonces.

The investigation does not silently convert this failure into a passing
availability claim or add automatic nonce repair. Before release, resolve the
existing decision between monitored manual repair and a separately reviewed
recovery mechanism. For the minimal runtime scope, the tested manual procedure
in the [nonce rollback report](restart-purchase-nonce-rollback.md) is the starting
point: preserve original signed transactions, verify current validity and funding,
resubmit the missing nonces individually, and require canonical native success.
The subsequent [live nonce-repair experiment](restart-live-nonce-repair.md) now
passes a bounded version of this workload: four original purchases are submitted
individually while both miners remain enabled, the unchanged saved intent then
executes, and two fresh automatic successors follow. Both cold databases retain
the repaired receipts and state. This requires preserved original bytes and
surviving eligible miners; it does not change the unattended failures above.

The opt-in `TestRestartNodeRehearsal/continuous_partition_miners` deliberately
retains the strict requirement and currently exits unsuccessfully on this
limitation. Use `check-strict.sh build`, then `check-strict.sh continuous` with a
new evidence label in the documented WSL environment to reproduce it. Do not
weaken it to peer count, block progress or a single displaced transaction's
re-inclusion. The live repair follow-up samples surviving tickets and checks
renewed successors; operator access to original bytes and the real wallet's
ticket runway remain separate work.

Monitoring must detect buyer warnings and stalled purchase/nonce progression in
addition to process state, peer count, head progression and enabled flags. This
experiment shows all those latter indicators can look healthy while one wallet
cannot replenish. Its remaining eligible tickets may permit temporary mining;
the generously funded fixture does not establish a production recovery runway.

## Boundaries

This is an isolated IPv4 experiment with fixed static contacts and public test
keys. It does not use the preserved backup, its private keys, production peers,
W: storage, public DNS or real NAT. It does not prove continuous availability
through arbitrary fork depths, ticket exhaustion, unavailable original signed
transactions, power loss or a sole producer's outage. A fixed restart anchor
still permits ordinary compatible reorganizations after that anchor.

The fixture is intentionally small enough to retain all its history. Full
mainnet historical execution, public deployment, real-key custody and independent
review remain separate release gates.

Raw attempts, exact source/executable identities and checksums are retained in
[`restart-continuous-partitions-2026-09-26`](evidence/restart-continuous-partitions-2026-09-26).
