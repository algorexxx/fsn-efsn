# Equal-weight branch investigation

27 September 2026, baseline `3cfdba3`. Production candidates P1–P15 and the
one-backup-block launch remain unchanged. This investigation concerns ordinary
peer convergence after a fork, not a new finality rule or a different accepted
restart anchor.

## Existing behavior

Three separate paths matter:

1. `eth/sync.go` compares the peer's advertised total difficulty with the local
   canonical total difficulty. Equality returns without invoking the downloader.
   The ten-second periodic sync tick does not override that comparison.
2. `eth/handler.go` processes propagated blocks and advertises the parent's
   proven difficulty. Its downloader trigger also requires strictly greater
   weight. `eth/fetcher/fetcher.go` can import a received block when its parent
   is known, but abandons that import if the parent is missing; it does not
   recursively fetch the missing branch there.
3. If a block actually reaches full block insertion, `core/blockchain.go`
   prefers greater total difficulty. At equal difficulty it prefers a shorter
   height; at equal height it preserves the current locally authored block.
   Otherwise a locally authored replacement wins, or a random comparison may
   choose the remote block. `eth/backend.go` defines local authors using the
   configured etherbase and `txpool.locals`. This is not a common deterministic
   hash tie-break. Header-only insertion has its own random equal-weight rule.

Consequently, connected idle equal-weight peers need not select one common head.
Import tie-breaking cannot help a branch that is never downloaded. A new block
may resolve the split, but its delivery path and the other producer's progress
matter. That is why the previous equal-weight stopped-node result cannot be
treated as proof of live convergence or permanent live deadlock.

## Retained-branch test

The source is `tmp/full-state-partition-2026-09-26`, whose two independently
audited branches stopped at **15,130,106**, total difficulty **63,370,514,724**:

- Donation test signer: `0x06091659c936675419b4f309db8aa243d1d0107d9c6ed1bdc866cfbed891cc5d`.
- Entrant test signer: `0xdbb89fb52cd078d8390be3f5f4e30976472d5847831627a98178c790dbccf320`.

Both copies already contain the genuine 90,000-block ancestry segment installed
by the [history investigation](restart-partition-history.md). That earlier
explicit downloader also stored the entrant's branch at the donation node,
without replacing its canonical head. This asymmetry is retained and reported
by preflight. This test therefore resumes the retained diagnostic state; it is
not a first encounter between nodes lacking the opposite fork.

The new copy contains 549 files / 1,147,442,592 bytes at
`D:\FusionRehearsal\equal-weight-2026-09-27`. Every copied file is hashed and the
source is rehashed afterward. Preflight requires the exact original heads and
difficulty, the shared recovery anchor, and all genuine historical block/TD
records. It records balances, interval rights, tickets and saved purchases.

Two real services connect inside a private loopback-only network namespace,
with only public synthetic keys 2 and 3. The test observes 45 seconds with
miners/buyers stopped, requiring unchanged distinct heads and one peer each.
It then starts both ordinary miners and automatic buyers and allows 150 seconds
for a shared descendant followed by three additional common descendants.
Per-second evidence records local heads/weights, peer reports, mining flags,
nonces, saved purchases and both pools. There is no explicit sync, funding
transfer, manual transaction repair or canonical-head override.

The nodes stop before a separate cold audit of both complete canonical account
ledgers. That audit runs even if live convergence fails. A passing convergence
test alone does not imply that the losing owner's automatic purchase recovers
from a nonce gap or funding loss; those remain separately visible conditions.

## Retained-branch result

The live test passes in **243.26 seconds**, including 102.86 seconds validating
the two copied history segments. The idle control lasts **45.317 seconds**;
both peers advertise the opposite original head and the same total difficulty.

Both miners then seal distinct blocks at 15,130,107. The entrant rejects the
donation block's import because its parent is unknown there. The donation node
already knows the entrant parent: it stores the entrant's equally weighted
15,130,107 block as a side block, keeping its own canonical head. At
15,130,108 the entrant's heavier continuation is imported and replaces 18
donation-branch blocks with 19 entrant-branch blocks. This is visible in the
native fetcher, side-insertion and reorganization logs. The first observed
shared descendant is 15,130,107 after **24.276 seconds** of live operation; the
three-additional-descendant condition passes after **55.615 seconds**.

The separate cold audit passes in **16.83 seconds**. Both databases agree on
all **31** suffix blocks, receipts, ticket inventories and complete account
differences. No additional transfer occurs. Final identity:

- Height: **15,130,111**.
- Hash: `0x0a03300af2f25eed21cae80573c634a8b1c394c96179952b1384dbc402a1b91a`.
- State root: `0x42fb0fb0c9dd9476bf24e05ccf9c969a747bfa9289685ca0beebc86809084118`.
- Ticket commitment: `0x1d994f0579f18cfbdcadf52db3db1e9dfd8487c8b5dcea9702b1e059dc876a75`.

The losing donation owner has canonical nonce **8** and saved nonce **25**;
the winner has canonical/saved nonce **25**. Exact saved bytes and canonical
nonces survive cold reopening. This is a convergence pass with a remaining
17-purchase nonce gap, not an automatic replenishment-recovery pass. All 549
source files remain unchanged and no race report occurs.

## Fresh reconstruction

To remove the prior downloader's influence, a second attempt starts from two
verified copies of `tmp/preserved-head-state`. It applies the existing audited
synthetic wallet substitutions, imports the original recovery prefix and
reexecutes original signed blocks 15,130,084–15,130,106 separately for each
branch. It requires the exact old head, state and ticket commitments. The
original synthetic saved purchase record is restored only after checking its
signature's owner, native purchase type and canonical nonce; this metadata
restoration does not change account state or replace a transaction.

Both copies receive genuine history and must lack the opposite fork tip before
the same idle/live test begins. No fork body is fabricated, no side-branch record
is deleted, and no new signing is used to reconstruct the old fork. The copied
source files total 1,058,557,692 bytes at
`D:\FusionRehearsal\equal-weight-fresh-2026-09-27`. The second test and its
separate cold audit have completed.

## Fresh first-contact result

The strict live test **fails** in **447.56 seconds** overall, after successful
preparation, reexecution and history validation. The initial idle control lasts
**45.266 seconds**. During **150.572 seconds** with both miners/buyers enabled,
the two connected services each produce **13** more blocks, reaching
**15,130,119**, total difficulty **63,370,514,750**, on different branches.
All **148** live samples show different hashes at equal weight, one peer at
each node and both miners/buyers enabled. No sample advertises a peer weight
greater than the receiving node's local weight. These are observations at the
recorded times, not a claim about every instant between samples.

Native logs repeatedly record `Unknown parent of propagated block` in both
directions. The newly received block cannot be imported without the opposite
branch's parent, while the advertised parent difficulty does not cross the
strictly-heavier synchronization gate. The test invokes no explicit downloader,
overrides no head, provides no new funding and submits no manual purchase.
The 150-second failure is retained; a longer observation is not silently
substituted for its result.

The separate cold audit **passes in 17.42 seconds**. Each database has **39**
audited recovery-suffix blocks, with complete interval/accounting and native
receipt checks. They are two valid ledgers, not a common canonical history.
Both continue ordinary buying on their respective branches, with matching
canonical/saved nonces: donation **37/37**, entrant **33/33**. Exact saved bytes
survive cold reopening. This failure is neither a missing-nonce repair case nor
a producer unable to replenish. No race report occurs; all 337 unique source
files remain unchanged.

| Identity | Donation branch | Entrant branch |
| --- | --- | --- |
| Head | `0x0b7a9403295c31f79a3141da6510ae0437a6e600c2359b48e31eedfd1a784795` | `0x30c87783b92511a852750c9b49ac163db92b33a7fcb8c33ab70bf98e0a1b15f5` |
| State root | `0xb17ea49a0b56a695f8cc551e3601e06339225801e46d385810d55ba84f187842` | `0x9831e19b305d7ed92aa707dbdb7f34699673f056d82835ec7b836d66fd4ccde9` |
| Ticket commitment | `0x551ead5e5a95deee7ee3be10c70651aeb8d787209481dd0f75cba1a80c876066` | `0xeabc685227a5dee99612c38647160910d146ef44e7bf32b8762f53126a062af9` |

## Remaining distinction

The retained state includes previously fetched opposite-branch data. The fresh
reconstruction separates that advantage from first-contact behavior. Do not
infer a universal convergence bound or permanent deadlock from one bounded
schedule. The combination of a passing known-branch case and failing fresh
first-contact case makes missing branch delivery a concrete release concern;
it is no longer only a possible consequence of the earlier sparse fixture.

Next use fresh copies of this failure to test a **coordinated pause of one
synthetic producer**, allowing the other to gain enough weight for ordinary
peer synchronization. Keep that assisted case separate from unattended
two-producer convergence, retain both branches, and audit any resulting nonce
gap or interval loss. Do not use a rewind, anchor change or automatic head
override as the recovery mechanism. No production workaround or consensus
tie-break is added by this investigation. The selected single-producer launch
arrangement is unchanged; an operational response for later competing
producers remains open.

Both experiments are stopped and preserved. D: has about **145.7 GB** free;
its WSL filesystem has about **64.0 GB** available. No W: workload was needed.
Native logs use UTC+02 and structured observations use UTC. The verifier in the
first evidence directory accepts either evidence directory as its optional
positional argument; `--index` also checks staged Git bytes. It verifies the
source identities, idle peer advertisements, live flags, linked cold blocks,
receipts and exact stopped/cold purchase records, including the retained live
failure. Top-level manifests cover 153 and 185 files respectively.

Evidence: [runner, source hashes, observations and cold ledgers](evidence/restart-equal-weight-2026-09-27/).
Fresh reconstruction: [replay, live observations and cold ledgers](evidence/restart-equal-weight-fresh-2026-09-27/).
