# Complete-state partition with bounded purchase retry

27 September 2026. Production baseline:
`be8661276e77d2756e3048f7fcbd2c87605b8383`.
This investigation adds tests, evidence and documentation only. The fifteen
production candidates and the agreed one-backup-block launch remain unchanged.

With the P4 resend candidate enabled, two continuously mining complete-state
nodes reconnect after packet loss and converge on the heavier branch. The
displaced entrant retains a seven-purchase nonce gap and cannot afford its first
repair purchase. All seven originals remain retrievable through existing RPC.
Both canonical databases and the retained competing branches pass independent
account/ticket interval checks. **This is not a successful manual-repair run.**

## Starting state and isolation

Fresh D: copies start from the ten-block checkpoint of the
[participant-entry experiment](restart-full-state-participant.md), at
15,130,090, hash
`0x71fda3d5913b4f0ae5ea48fb1512bf3f1706a2b42a4d9358b1cd890f95ff8674`.
The later failed and passing continuations are preserved separately; this
earlier branch is an independent experiment, not a rewind of them.

The donation fixture starts with nonce 8, two tickets and 2,021.978086712 FSN
liquid. The entrant starts with nonce 4, one ticket, 2,021.039457552 FSN liquid
and 5,000 FSN of usable uncommitted time-lock value. These are public synthetic
keys 2 and 3, not the real wallets. The original participant funding remains
the only funding: 10,000 FSN converted from existing mature rights and an
ordinary 2,020.102-FSN transfer. No mint, additional transfer or reserve edit
is used in this investigation. That earlier synthetic contribution does not
authorize spending the real backup owner's funds.

Each attempt copies and hashes 560 files / 1,040,745,262 bytes. All source files
still match afterward. Both copies receive the previously verified 90,000
genuine ancestor blocks below the fixture parent, from the retained 90,001-block
export. Its SHA-256 is
`99185867e8dd894c27bf8bf304193d3247c8ef76bbc86cd4387d48342265c73d`.
Head markers and the synthetic parent remain unchanged during installation.
The compact database still lacks earlier history required by the bloom indexer;
the retained `canonical block #1 unknown` background-index errors are not a
claim of a production-ready archival node.

Actual node services run in a private Linux network namespace with loopback
only. No real keys or public peers are used. Go 1.21.3 race detection is enabled.
Builds, copies and the WSL filesystem use D:; C: receives only small source and
evidence files. No new original-backup restore or replay runs here.

## Results and the failed test gates

| Run | Result |
| --- | --- |
| Initial live attempt | Fails after 124.34 seconds, before injecting any outage. The reserve guard demands another funded purchase even though the entrant already has two eligible tickets. This is a preflight limitation, not a demonstrated insolvent node. |
| Initial cold audit | Passes in 12.44 seconds. Both databases agree on all thirteen blocks through 15,130,093, hash `0x03f8218bc67a6fee046661f5e75407e26b44d7c449201d782155350fa3c1582d`. |
| Second live attempt | Reaches the reserve gate, injects 90.252 seconds of packet loss, reconnects and converges automatically. Fails after 286.42 seconds during repair preparation because the harness retained branch bodies only through the end of the packet drop. No manual repair transaction was submitted in this run. |
| Second cold audit | Passes in 23.13 seconds. Both canonical 23-block histories and both isolated 19-block histories reconcile; the two canonical JSON/RLP sets match byte-for-byte. |
| Displaced-block diagnostic | Passes in 6.98 seconds on a separate stopped-node copy. Audits the losing branch through block 22, retrieves originals 7–13 through the actual service RPC, and reproduces the first purchase's funding rejection. |

The initial guard source is retained separately. The revised guard accepts an
eligible ticket plus immediately funded replacement, or two eligible tickets
whose aggregate liquid/time-lock backing covers two prices across the sampled
month after ordinary selection returns. This second condition is conditional
backing, not spendable cash or protection against first-retreat losses. The
second attempt exercised the first condition for both owners; it does not test
the alternative two-ticket branch of the guard.

At the second attempt's common pre-outage block 15,130,093, each owner has one
eligible ticket and no saved nonce gap. Donation has 2,022.603086712 liquid FSN
plus 5,000 FSN of covering locks; the entrant has 7,021.351957552 liquid FSN.
The sampled next month is fundable for both. This preflight does not promise
that either owner can survive losses during a partition.

## Reconnection, rollback and custody of original bytes

Kernel packet loss drops 44 packets. Both branches advance to 15,130,099 during
isolation and diverge at 15,130,095. Mining and automatic buying remain enabled.
After packet flow resumes, both continue producing while peer reconnection and
ordinary synchronization take place. At height 15,130,101 their total weights
are 63,370,514,725 and 63,370,514,719: this is not the earlier equal-weight case.
No manual synchronization request, miner restart or forced fork choice is used.

The entrant rolls back eight blocks to the common parent 15,130,094 and imports
the heavier branch. Both nodes then agree on 15,130,102, hash
`0x5db6e13a09084a88dc5785fa993345ff5e3bf9cbb59b7714b8999792a5c83221`.
The repair gate observes canonical entrant nonce **7**, saved nonce **14** and
an empty pool for ten seconds while the common chain advances. The saved hash is
`0x71f7c8320feac7fc0a2fcb6378cace0dd38d95a790233ab0abe42f16d5988396`.
P4 deliberately preserves that signed intent and does not guess its predecessors.

The live test retrieves originals 7–10, then reports
`missing displaced block for original purchase`. Originals 11–13 were mined at
heights 15,130,100–102 while reconnection was underway, beyond the harness's
pre-heal branch-body capture. This is an evidence-capture defect. The node still
stores the bodies. The independent diagnostic enumerates noncanonical headers
on a copy of the stopped database, rejects conflicting originals, walks and
audits the losing ancestry, then starts the real service with mining/buying off.

All seven transactions are recovered byte-for-byte with
`eth_getRawTransactionByBlockHashAndIndex`. Transaction-hash lookup and canonical
receipt lookup correctly return nothing; absent block and out-of-range index
checks return null. The first nineteen losing-branch JSON/RLP records still
match the original isolated audit; blocks 20–22 extend it. This establishes
retrieval from this retained database, not a new production archive or a generic
live block-search API. Operators must retain hashes through reconnection and
synchronization, not stop when packet flow resumes.

## Funding and final accounting

The common cold head is **15,130,103**, hash
`0x1a52a5d9fec08c0c5aa2adddf62dcaf115991f74919877c88e6756b771d67aaf`,
state root
`0x7cc95eeec83f2d765734fd34b9bcf1eb78245301a8eb8cf03380d044f5cebd50`.
All original ten block records still match the source in both attempts.

| Synthetic owner | Canonical nonce | Tickets | Liquid FSN |
| --- | ---: | ---: | ---: |
| Backup | 233429 | 0 | 1,205.752763845480158626 |
| Donation | 18 | 1 | 2,025.415586712 |
| Entrant | 7 | 0 | 2,021.664457552 |

The accepted branch applies two first retreats to entrant tickets at heights
15,130,097 and 15,130,098. Each removes the current 5,000-FSN ticket interval
without an ordinary selected-ticket refund. Future rights remain: the entrant
has 5,000 FSN beginning **27 October 2026 08:39:55 UTC**, then 10,000 FSN from
08:40:06 UTC onward. Those rights do not cover a purchase beginning now.
The losing branch instead records two first retreats of donation tickets.
The interval ledger accounts for both outcomes using unchanged consensus rules;
these are interval losses, not a new permanent token-burn policy.

The actual restarted service rejects the entrant's original nonce-7 transaction:
liquid balance `2021664457552000000000` wei; required liquid
`5000000021224000021224` wei, including its full gas budget. The immediate
shortfall for that exact transaction is **2,978.335563672000021224 FSN**. This
number is not a sufficient reserve for the whole repair or another outage.
The rejection leaves head, canonical nonce, empty pool and exact saved intent
unchanged. Mining and auto-buy stay disabled in this diagnostic; it does not
claim continuous-miner repair success or wait for future rights to mature.

The independent audits cover rewards, fees, selected-ticket returns, first
retreats, original funding, all affected account fields and future interval
boundaries. No new funding transaction appears, and the backup signs no further
block. No race report occurs in these runs; two live test failures remain
explicitly preserved rather than relabelled as passes.

## Next bounded work

Complete-state live convergence and nonce rollback are now observed with the
P4 resend candidate. Successful complete-state manual repair and automatic
successors remain open. Next retain original block locations throughout healing,
then rehearse a funded continuation from this exact retained failure using only
explicitly accounted synthetic transfers from preserved rights. Check canonical
funding first, then sequential missing-nonce inclusion, the unchanged saved
intent, fresh automatic purchases and both cold ledgers. No real funding source
or amount is approved by this experiment.

Keep this no-funding outcome as a control. Do not clear the saved record, assume
rebroadcast fills a nonce gap, treat pending admission as native success, change
ticket penalties, or add finality rules to make it pass. Equal-weight convergence,
wider outage schedules, operational funding/monitoring and independent release
review remain separate open gates.

Evidence: [scripts, source identities, logs, ledgers and raw transactions](evidence/restart-retry-partition-2026-09-27/).
Each main attempt uses about 1.04 GB of copied input. The final diagnostic adds
300 verified files / 573,925,069 bytes, leaving about 161.4 GB free on D: at copy
time. The hash manifest covers the retained small artifacts; database copies
remain at:

```text
D:\FusionRehearsal\retry-partition-2026-09-27
D:\FusionRehearsal\retry-partition-2026-09-27-attempt-02
D:\FusionRehearsal\retry-partition-2026-09-27-displaced
```

No process from these experiments remains running. Preserve these directories
and use new copies for any continuation.
