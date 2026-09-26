# Complete-state competing-producer partition

26 September 2026, baseline `92a561bd276158b26dd3af7afa9a61d746907900`.
Investigation tests and documentation only; production candidates remain P1–P15.

This follow-up extends the [funded participant entry](restart-full-state-participant.md)
with packet loss, competing branches, ordinary reconnection and an attempt to
repair the affected automatic buyer using its original signed purchases.
It uses the complete preserved account state with the existing audited public-key
substitutions. It does not change the agreed day-one launch arrangement.

## Setup and acceptance

Two fresh copies of the compact export execute the reviewed recovery and
participant-funding prefixes. The latter hypothetically contributes existing
backup-fixture rights through two ordinary transactions to a new public test key.
This is not authorization to use the real backup owner's funds. No additional
repair funding is provided in this test.

The live donation and entrant services first purchase tickets on a shared chain.
A kernel filter drops loopback IP traffic for 90 seconds inside a private
namespace while both miners and buyers remain enabled. The test records both
branches and their signed purchases, then removes the filter and waits for
ordinary peer reconnection and synchronization. It does not force synchronization
through a test API or stop/restart the buyers to resolve the fork.

The manual-repair gate requires a stable saved-intent nonce above the canonical
nonce, an empty affected wallet pool, and a compatible advancing common chain.
Every missing original must be retrieved through the existing block-hash raw
transaction RPC before any resubmission. The original bytes are submitted in
nonce order with canonical native-success receipts checked on both peers.
Success additionally requires the exact saved intent and two fresh automatic
successor purchases.

An insufficient-balance rejection is sampled against a fixed block hash, liquid
funds, free time locks covering the complete signed interval, full gas budget
and ticket inventory. A ticket awaiting selection can justify a bounded wait;
zero tickets cannot produce a selection refund. The test records a funding
failure, then continues through clean shutdown and independent cold accounting
before reporting the recovery test as failed.

Both cold databases must agree on the complete canonical suffix. Both isolated
branches are separately reconstructed from their retained blocks and audited.
The account audit checks all future interval boundaries, ordinary rewards,
fees, ticket-selection returns and first-retreat losses, plus unrelated assets,
code, storage, notation and nonce increments. Automatic purchase-record bytes
and canonical nonces must also survive cold reopen unchanged.

## Observed result

The strict live test failed after **306.24 seconds**, before the manual-repair
gate. Packet loss lasted 90.218 seconds and dropped 49 packets. Both isolated
heads reached 15,130,094, with the first differing block at 15,130,090. During
the following 150-second observation both miners and buyers remained enabled,
but their branches did not converge. At shutdown both were at 15,130,106 with
different hashes. Neither a stable canonical nonce gap nor repair funding was
tested; no repair transaction was submitted.

A separate cold diagnostic retained and independently audited all 26 suffix
blocks from **each** stopped database. Both audits passed, including the three
recovery blocks, ordinary participant funding, ticket purchases, rewards, fees,
selection returns and first-retreat interval losses. Each branch contains 17
blocks after the last shared block. The donation branch retained nonce 24 and
the entrant branch nonce 20; both had a 117-byte saved automatic purchase.
These are two separately valid account ledgers, not matching canonical heads.

Both stopped heads had total difficulty **63,370,514,724**. With mining and
buying disabled, fresh services connected successfully and reported one efsn
peer each, advertising the correct opposite head and equal difficulty. They
did not converge during 45.43 seconds. The existing periodic synchronization
gate in `eth/sync.go` requires strictly greater peer difficulty; equality does
not trigger it. New-block propagation in `eth/handler.go` advertises the
parent's proven difficulty. Equal weight is therefore relevant, but these cold
observations do not establish the original live run's complete peer/TD history.

The diagnostic then explicitly invoked the existing test-only downloader API
once, with no signing. It failed with:

```text
action from bad peer ignored: multiple headers (0) for single request
```

Debug logs place the failure in ancestor discovery. The downloader falls back
to binary search across its 90,000-block full-sync ancestry window. From these
equal-height heads the logs show its first binary probe at **15,085,106**, matching
`(15,130,106 - 90,000 + 15,130,106) / 2`; that is outside the compact fixture's
recent history. The peer returns no header, producing this error. This repeats
the sparse-history limitation already identified in the
[continuous-miner investigation](restart-continuous-partitions.md).

The cold diagnostic also reports failure, after 60.69 seconds. Both head/root
sets remain unchanged before and after its automatic and explicit sync attempts;
neither service signs a block or enables buying. Both builds succeeded with
race instrumentation and neither run reports a race. The source export's 230
files are rehashed against the original manifest by the evidence verifier.

## Next investigation

Provide genuine historical headers and bodies from the verified preserved
backup across the downloader's applicable ancestor-search window, or run on
the existing complete restored database after checking capacity. Measure the
incremental storage first; avoid another full backup copy merely for this test.
Validate continuity and original identities. Do not fabricate ancestry, reduce
the search window or change fork choice to make the rehearsal pass.

Repeat the partition with peer counts, advertised heads/difficulties and sync
diagnostics recorded during healing. Keep equal-weight and strictly heavier
cases distinct. Only after ordinary convergence may the test assess nonce
rollback, original-byte retrieval, funding and manual recovery. A deliberately
assisted rejoin, if needed for diagnosis, must remain a separate experiment.

No new consensus correction, finality mechanism or production candidate follows
from these results. The selected day-one producer/verifier arrangement and its
passing single-producer outage evidence are unchanged.

## Limits

This is one bounded two-producer case. It does not establish a universal reserve
balance or recovery from arbitrary fork depths. A first retreat forfeits the
ticket's remaining interval rights; that must not be confused with destroying
all future rights in the original principal. Funding available after an interval
ends does not make an old expiring signed purchase usable indefinitely.

The compact fixture retains complete state and recent execution context, not
the full historical block archive. The known bloom-index error about missing
canonical block 1 is a fixture limitation. This is not public bootstrap or
full-history synchronization evidence. It adds no consensus, automatic-repair
or production-runtime change.

Raw logs, copy proofs, signed block transactions, both cold branch ledgers and source
identities are retained in [the evidence directory](evidence/restart-full-state-partition-2026-09-26).
