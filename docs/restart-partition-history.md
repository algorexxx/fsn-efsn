# Partition rehearsal with genuine historical ancestry

26–27 September 2026. Baseline `12651ceaf3c1bf35ee8bda9bfd1ff95ccdfa1357`;
production candidates remain P1–P15. Changes are investigation tests,
documentation and evidence only.

The [previous complete-state partition](restart-full-state-partition.md) did
not converge within its observation window. Its stopped-node diagnostic reached
a missing header at 15,085,106 during binary ancestor search. This follow-up
supplies genuine history for the ordinary downloader without changing its
90,000-block search window, fork choice, consensus or restart anchor.

## Source, validation and storage

The extractor opens the verified disposable backup at
`/home/rehearsal/data/efsn/chaindata` through a read-only bind mount and a read-only
LevelDB handle. It runs unprivileged in private mount/network namespaces with
loopback disabled. The complete original backup is not copied again.

It first measures, then exports blocks **15,040,080–15,130,080**: 90,001 blocks,
90,020 transactions and **70,098,887 bytes (66.85 MiB)**. Both passes produce
SHA-256 `99185867e8dd894c27bf8bf304193d3247c8ef76bbc86cd4387d48342265c73d`.
The completed export passes in 89.93 seconds. The segment remains at
`tmp/partition-history-2026-09-26/history.rlp`; its size and identity are retained
with the evidence rather than committing the 67-MiB data file.

Every block must match its canonical database key, contiguous parent link,
transaction root and stored cumulative difficulty. Fusion blocks must have an
empty uncle list: their header's `UncleHash` is a PoS sorting commitment, not
Ethereum's ordinary empty-uncle-list hash. The linked segment must end at the
previously observed preserved head and its trusted total difficulty. A cold
reader also rejects missing/trailing records and checks the complete file hash
against the export report before any destination write.

Two fresh 230-file state copies total 1,057,634,160 bytes before added history.
Preparation verifies the original manifest and each copied file, retaining a
50-GiB host free-space reserve. The copies and segment use C:; no new large
workload is placed on D: or W:.

After the reviewed three-block recovery prefix, each disposable database receives
90,000 original blocks through height 15,130,079. Existing canonical hashes must
agree. The original block at 15,130,080 authenticates the segment but is not
installed over the audited synthetic parent at that height. The active block,
header and fast-head markers must remain unchanged. Each database is closed
before the actual node services open it.

This adds historical headers, bodies, number mappings and difficulty records.
It does not add historical state or receipts, reexecute 90,000 blocks, or turn
the compact fixture into a public bootstrap package. The existing complete
preserved state and audited suffix account ledgers remain the execution evidence.

## Test and initial corrections

The live run keeps both miners and automatic buyers enabled through 90 seconds
of kernel packet loss, then allows ordinary reconnection. Every ten seconds
during the recovery gate it records local heads, total difficulty, mining/buying
flags and advertised peer heads/difficulty. Child services also emit debug sync
logs. The original stable nonce-gap, exact-byte retrieval, funding, native
receipt and cold-accounting requirements remain in force.

The first measurement failed because the new extractor incorrectly applied
Ethereum's uncle-hash equality rule. Its binary hash, source and log are retained.
The corrected validator preserves the original header field and requires an
empty uncle list. Six focused race checks pass: valid repurposed field, missing
block, height gap, wrong parent, altered transactions and unexpected uncles.

Two shell-wrapper failures are retained separately. The first focused test
printed PASS but its inline exit-status quoting failed; the saved runner then
passed. The corrected measurement printed PASS and wrote its report, but an edit
to the running script caused its wrapper to fail afterward. The unmodified
export runner subsequently exited 0 and its data matched the measurement exactly.
The measurement is not presented as a successful wrapper execution.

## Live result and cold recovery

The strict partition test **failed after 223.67 seconds**: the donation service
did not advance sufficiently during isolation. It therefore never entered the
ordinary live-healing/nonce-repair gate; the added ten-second recovery samples
were not reached. No repair was submitted and no extra funding was supplied.
The retained warm-up logs already show competing branches and purchase funding
rejections before the packet cut. This is not a successful rollback/repair test.

Cold audits then passed on both stopped suffixes: the donation database had
nine blocks through 15,130,089, and the entrant database had sixteen through
15,130,096. Their total difficulties were 63,370,514,683 and 63,370,514,696.
The entrant branch contains two first-retreat losses for the donation owner,
at 15,130,087 and 15,130,091. Each forfeits a 5,000-FSN ticket interval. Exact
accounting reconciles both branches with the existing preserved balances,
ordinary funding transfers, rewards, fees and ticket returns.

Fresh services opened those stopped databases with mining and buying disabled.
They connected and automatically joined the heavier entrant branch in **9.08
seconds**, without the explicit downloader API. The full diagnostic passed in
19.91 seconds. Its common head is 15,130,096,
`0x48212779e0851316084461094494cffcbb2c380362d1877a450c874913034291`,
state root `0x0775498339f8ecd2a231f36be037af5f4e0e58047b7ec133e8c09299dd128a41`.
This sync found a recent stored side-branch ancestor at 15,130,089; it did not
itself exercise the previously missing binary-search header.

A further cold check passed in 6.16 seconds. Both databases agree on every
block, receipt, ticket commitment and account difference in the sixteen-block
canonical suffix. Their own saved 117-byte purchases remain byte-identical to
the records before synchronization. Against that common canonical state:

| Check | Donation test owner | Entrant test owner |
| --- | --- | --- |
| Canonical / saved nonce | 7 / 7 | 11 / 11 |
| Remaining tickets | 0 | 1 |
| Liquid FSN | 2,021.665544264 | 2,023.227 |
| Free lock coverage for saved interval | 0 FSN | 5,000 FSN |
| Liquid needed for that purchase, including gas budget | 5,000.000042448 FSN | 0.000042448 FSN |
| Real local pool admission | Rejected: insufficient balance | Accepted |

Both head-time and current-time coverage checks agree. The donation owner has
10,000 FSN of future rights starting at timestamp 1,793,051,362, but its saved
purchase needs coverage before that date. Those future rights cannot fund this
purchase. The saved nonce is already correct: there is no missing-nonce repair
to perform in this final state. A restart or deleting the saved record cannot
replace unavailable funds. Pool acceptance for the entrant is not a mined
receipt; this final check starts no miner and transmits nothing to a network.

## Exact missing-header case

The original stopped fork from the prior investigation was then augmented with
the same verified history. Its two original heads at 15,130,106 and total
difficulty 63,370,514,724 were required to remain unchanged before startup.
The exact earlier explicit-downloader request was repeated with signing and
buying disabled. This time it fetched **15,085,106**, completed binary search,
found the common ancestor at 15,130,089 and stored the remote branch successfully.
The focused recheck passed in **70.26 seconds**, including both history installs.

Both canonical heads and roots remained unchanged afterward. This proves that
the missing-history failure is removed for the same stopped fork; it does not
prove automatic convergence of equal-weight producers. The explicit downloader
call remains a test diagnostic, not a proposed operator command or production
bypass. The prior failed logs and immutable block/account artifacts remain intact.

## Implications and next work

The original single-producer handover remains the selected launch plan. This
experiment demonstrates a complete-state funding failure with two competing
producers; it does not overturn the earlier single-producer outage pass.
The initial 12,020.102 FSN balance is not an assured reserve through repeated
ticket-interval losses. No universal minimum balance or real sponsor is established.

For the next live rollback/repair exercise, retain this failed small-reserve
case and explicitly define the additional producer's authorized funding and
available interval reserve. Check canonical ticket eligibility, actual pool
admission and both saved nonces immediately before the fault. Keep observed
failures even if they arise during warm-up. Equal-weight behavior and a complete
live nonce repair remain separate from the stopped heavier-peer recovery here.
Monitoring must distinguish zero-ticket/insufficient-funds stalls from nonce gaps.
No funding transfer, automatic-repair feature or consensus change is implemented.

The [existing-funds follow-up](restart-existing-funds.md) uses fresh copies of
this stopped failure to test a bounded 3,000-FSN contribution from the existing
test accounts. It preserves this failure and separates funding-only recovery
from a missing-nonce repair or an assured operating reserve.

Logs, copy proofs, history identities and source/executable hashes belong in
[the evidence directory](evidence/restart-partition-history-2026-09-26).
