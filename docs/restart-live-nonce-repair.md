# Manual purchase repair during continuous mining

26 September 2026, runtime baseline `e0a002b`, retaining P1–P15. This follows the
[failed unattended-replenishment checks](restart-continuous-partitions.md).
Only tests, documentation and evidence change. The automatic buyer, transaction
pool, consensus and launch sequence are unchanged.

## Experiment

Two ordinary node services use the complete synthetic genesis-to-24 fixture,
public test keys, separate LevelDBs and the existing devnet rules. Both miners
and automatic buyers remain enabled through a 90-second kernel packet-loss
outage, ordinary static-peer reconnection/full synchronization and manual repair.
The test does not force synchronization or hold block signatures.

Before and during reconnection the harness preserves original signed purchases
from the saved record, pool and original blocks. It rejects conflicting signed
transactions at the same nonce. Repair starts only after a common branch has
advanced beyond both isolated heads and one buyer has retained the same future
nonce for ten seconds with an empty pool. This is a bounded reproduction of the
known pause, not a production monitoring threshold.

For each missing nonce, the test checks the unchanged saved later intent, current
canonical nonce, empty pool, decoded native purchase interval and base fee. It
submits the exact original bytes through `eth_sendRawTransaction`. Normal pool
admission and execution provide the funding checks. Both peers must report a
canonical receipt with the expected successful native ticket result before the
next missing nonce is submitted. No replacement transaction is signed by the
harness and no saved intent is deleted.

The saved later purchase must then execute automatically with its exact original
hash. At least two newly generated automatic successor purchases must execute
after it, alongside continued buying by the other owner. These checks distinguish
renewed automatic buying from reinclusion of old purchases. Both miners are
stopped only after those checks. The test then waits for the existing bounded
quiet-head condition and cold-opens both databases, comparing heads, state/ticket
roots, account nonces, saved bytes and successful repair/successor receipts.

Ticket snapshots use the existing `fsn_allTicketsByAddress` RPC at explicit block
numbers, with the block hash rechecked. They report stored tickets and tickets
satisfying DaTong's height/lifetime predicates at that block's time plus one
15-second period. These are samples, not a continuous minimum or a promise that
a particular owner wins the next block. The fixture requires surviving tickets
for both owners at every sample.

## Results

The Linux race build and live case pass. The case finishes in 339.07 seconds
with no race report. Its kernel fault lasts 90.19 seconds and drops 44 packets;
the isolated heads are 32 and 33. After ordinary reconnection, both nodes reach
block 37 while wallet 1 remains at canonical nonce 30 with an empty pool and
the saved nonce-34 purchase. The stable-gap check completes about 76 seconds
after healing, with common block 36 below the live tip.

| Step | Observed result |
| --- | --- |
| Original missing purchases | Nonces 30, 31, 32 and 33 succeed at blocks 38–41, one at a time |
| Unchanged saved intent | Nonce 34 succeeds automatically at block 42, hash `0x41eb86272f535dec6b8fa64d306ee283e510910ccb1c9315cef53f23b49f62ef` |
| New automatic purchases | Two fresh successors succeed after that saved intent; both owners continue purchasing on the shared chain |
| Tickets before repair | At common block 36, each owner has 13 stored tickets satisfying the next-period height/lifetime checks |
| Tickets during repair | The four inclusion snapshots retain 14–15 for wallet 1 and 14–16 for wallet 2; both have 17 at block 44 after fresh successors |
| Cold state | Both databases agree at block 46; wallet nonces are 38 and 44, saved bytes are unchanged and pools initially empty |
| Cold receipts | Both nodes retain all seven checked successful purchases: four originals, the saved intent and two successors |

The final block is
`0xfc4cef49ec8c215465f367bd2e94c9e691faa2685723f2fc2e006553a032522c`,
with state root
`0x996390261382bbdfd621ce613d49692a767d58efb8716d2ce320cf621bc2cba8`
and ticket root
`0xdf1b90fdd762ecff0253b1deeb5858e7f123ab3986ae09f83c41ff00b43c39e9`.
Two head changes occur after the stop requests before the 35-second quiet
condition. This is consistent with the earlier delayed-seal observation; it
does not turn `miner_stop` into a signer-handover barrier.

This is one passing bounded repair case. The earlier unattended tests remain
failures. No broad-suite, native Windows, repeated-outage repair or production
funding result is claimed.

## Operator procedure and remaining prerequisites

The existing procedure remains sequential: preserve the original signed data;
confirm the current branch, nonce, pending transactions and surviving producer;
review each missing transaction's identity, payload, interval and funding;
resubmit one nonce; verify canonical native success; then repeat. Retain the
later automatic intent and verify its recovery plus fresh successor purchases.
The [earlier nonce-rollback report](restart-purchase-nonce-rollback.md) describes
the cases requiring separate review, including expired, conflicting or unavailable
original transactions. A generic successful receipt alone is insufficient for a
native Fusion operation; inspect the native result log too.

Source inspection identifies an existing retrieval path for displaced mined
purchases when their block bodies are still stored. `eth_getBlockByHash` can read
the old block, and `eth_getRawTransactionByBlockHashAndIndex` can return its signed
transaction bytes. Retain the old block hash and transaction index; a canonical
block-number lookup now refers to the replacement branch. Ordinary reorganization
removes displaced transaction lookup entries, so `eth_getRawTransactionByHash`
alone may no longer find a purchase absent from the pool. This follows
`internal/ethapi/api.go`, `eth/api_backend.go` and `core/blockchain.go`; this live
test uses preserved bytes and does not yet validate post-reorg RPC retrieval.

The subsequent [retrieval and small-reserve follow-up](restart-small-reserve-and-retrieval.md)
now verifies that RPC path before and after a cold restart and uses the retrieved
purchase to repair the gap. It also tests the existing read-only `efsn db get`
command for the latest saved intent, with unchanged chain-database file hashes
and rejection of a locked database. These are existing interfaces, not new RPCs.

The test's `lab_purchaseState` endpoint exposes the private saved record only in
the rehearsal service. Production does not gain that endpoint. A complete
operator runbook still needs a supported way to preserve/inspect the live saved
intent and identify displaced transaction bytes, with clear responses to missing
or conflicting data. Do not assume the automatic record is a history of every
purchase: it retains the current intent.

## Limits and release decision

This fixture starts with one million synthetic FSN per owner and many setup
tickets. Its observations do not establish the real donation wallet's recovery
runway, prolonged operator absence, ticket exhaustion, or recovery when no
available signer has a usable ticket. Those are separate from whether sequential
resubmission works while eligible miners remain active.

The small-reserve follow-up demonstrates a further failure: the missing purchase
can be unfundable even with its original bytes and another eligible producer.
The initial 12,020.102-per-wallet synthetic case reaches a common advancing chain
but normal admission rejects the stalled owner's first repair purchase with only
about 2,057.60 liquid FSN remaining. Do not generalize this generous-reserve pass
to the real donation wallet's post-partition recovery budget.

The manual repair pass does not change the failed unattended-replenishment
result. Before release, decide whether monitored manual repair is acceptable or
whether a separately reviewed automatic recovery mechanism is necessary. Wider
fork/outage patterns, unavailable original bytes, public networking and real-key
custody remain separate gates. This work accesses no production key, preserved
backup or W: dataset, and performs no large restore/replay workload.

Evidence is in
[`restart-live-nonce-repair-2026-09-26`](evidence/restart-live-nonce-repair-2026-09-26).
Run `check-linux.sh build` then `check-linux.sh repair <unique-label>` in the
documented WSL environment. An initial environment-capture command encountered
Git's repository ownership check before compilation; the runner now scopes
`safe.directory` to that single read-only Git command without changing global
configuration.
