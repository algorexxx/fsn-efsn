# Paused-wallet retrieval, admission and expiry

Status: diagnostic pass, 27 September 2026. All missing signed purchases remain
retrievable, but their actual pool submissions fail for funding. This is not
a purchase-recovery pass. The [coordinated-pause result](restart-equal-weight-pause.md)
and its prior unattended-convergence failure remain unchanged. No production
code, consensus rule, real wallet or launch decision changes.

## Input and scope

The experiment uses fresh copies of the paused result at
`D:\FusionRehearsal\equal-weight-pause-2026-09-27`, retained separately at
`D:\FusionRehearsal\paused-purchases-2026-09-27`. The copy contains 596 files,
1,148,147,219 bytes. Every copied source is hashed before copying, the copy is
verified, and all source files are rehashed after the experiment.

Both copied databases have the same block 15,130,126:
`0x0e01aeb3c7e60ad34d818e6fe784af1aaf72e09602975815dcac263a4feaea91`.
The synthetic donation owner has canonical nonce 8 and saved nonce 39; the
synthetic entrant has canonical/saved nonce 40. The donation has zero tickets
and insufficient currently spendable stake backing.

Two real services run inside a loopback-only network namespace. Mining and
automatic buying stay disabled. They are queried independently through local
RPC, without connecting peers. These are pool-admission checks, not propagation,
mining, automatic resumption, or sequential repair. No transaction is newly
signed, no funding is added, and no canonical block is produced or replaced.

## Original-byte retrieval

The cold preflight scans stored noncanonical block hashes on the donation copy
and finds every purchase at missing nonces **8–38**. It verifies the transaction
identities and locations against the independently retained pre-pause branch.
The saved nonce-39 intent is read from its existing durable record and checked
against the source's exact bytes and signer.

The existing RPC helper retrieves each of the 31 originals using
`eth_getBlockByHash` followed by `eth_getRawTransactionByBlockHashAndIndex`.
It requires byte-for-byte equality with the stored signed transaction,
matching nonce and hash, and a different canonical block at the same height.
Transaction-hash lookup and canonical receipt lookup return no result.
Unknown blocks and out-of-range transaction indexes also return no bytes.

All 31 checks pass again after a clean stop and restart of the donation node.
That is **62 successful original-byte retrieval checks**. The recovered files
are retained individually. These checks rely on the losing node's stored
displaced bodies; they do not establish that every peer holds those bodies or
that transaction-hash lookup is a substitute for preserving their locations.

## Admission and funding

At the unchanged canonical head, each original and the saved intent has a valid
native purchase payload, the expected signer and adequate gas price relative
to the block's base fee. The test submits each of these **32** exact signed
transactions through `eth_sendRawTransaction` on each node. All **64** calls
return the same native insufficient-balance error.

| Quantity at this fixed synthetic state | FSN |
| --- | --- |
| Donation liquid balance | 2,021.978065487999978776 |
| Usable free time-lock coverage for each tested interval | 0 |
| Required liquid for one purchase, including its encoded gas limit and price | 5,000.000021224000021224 |
| Additional liquid needed for that first admission | 2,978.021955736000042448 |

The raw error is retained verbatim:

```text
insufficient balance(2021978065487999978776), need 5000000021224000021224 = (gas:21224 * price:1000000001 + value:5000000000000000000000 + fee:0)
```

Each purchase uses gas limit 21,224, gas price 1,000,000,001 wei and zero native
purchase fee. The verifier independently computes the amount from those signed
fields. Raw normalized time locks provide zero covering value over each
purchase's interval starting at the later of its encoded start and the sampled
wall clock, matching the pool's funding rule.

The entrant's unchanged, funded nonce-40 intent is admitted as a positive
control on both nodes and becomes the only pending transaction. Both copies
therefore exercise a functioning pool at the same canonical state. The
donation's own pool remains empty and neither durable intent changes.

The 64 rejections are independent attempts against the same canonical nonce 8.
They do not model state after earlier purchases execute. The stated shortfall
is for the first purchase's current admission, not a 31-purchase reserve,
funding recommendation or guarantee of continued buying. Normal selection,
new retreats, changing intervals and fees can change later requirements.

## Original purchases have a limited admission window

There is a separate timing constraint in the existing native purchase check.
At the applicable fork rules, `BuyTicketParam.Check` requires the encoded end
to be at least **29 days after the latest block timestamp**. It also requires
the original interval to span at least 30 days and its start not to be more
than three hours ahead of the latest block. These are unchanged existing rules
in `common/fsnparams.go`, called by the pool in `core/tx_pool.go`.

For every recovered purchase and the saved intent, the diagnostic checks the
native parameter validator at `end - 29 days` and one second later. The boundary
passes exactly and the next second fails with the latest-block-time error.
These are native parameter-validation checks; the test does not create future
blocks or claim execution at those timestamps.

The earliest boundary belongs to nonce **8**:

| Timestamp | UTC |
| --- | --- |
| Encoded start | 2026-09-26 21:19:32 |
| Encoded end | 2026-10-26 21:19:32 |
| Recorded canonical head | 2026-09-27 12:20:41 |
| Last latest-block timestamp accepted by this parameter check | **2026-09-27 21:19:32** |

The recorded head has **32,331 seconds**, or **8 hours 58 minutes 51 seconds**,
before that boundary. This is a property of the synthetic fixture's block
timestamps, not a wall-clock deadline for a real wallet. A stopped head and a
running head behave differently, and pool funding also consults wall time.
The saved nonce-39 intent has a later boundary, 2026-09-28 12:19:46 UTC.

Adding funds after an original's admission window closes will not make its
unchanged payload valid again. A retained raw transaction is evidence and a
possible repair input, not a promise that it remains usable indefinitely.
Check every predecessor's window before starting a long sequential repair;
the newest saved intent's window alone is insufficient.

## Verification and next work

The race-enabled diagnosis passes in **9.58 seconds**. The separate cold audit
passes in **30.45 seconds**. Both **46-block** canonical ledgers, their full
account differences, receipts, tickets and future interval accounting pass.
All **184 JSON/RLP canonical artifacts** match the preceding pause experiment
byte-for-byte, as do both cold inventories and both saved-intent snapshots.
No race warning occurs. All 596 source files remain unchanged.

This closes the missing-data question for this 31-purchase rollback and
confirms the funding rejection. It does not resume the donation producer.
Keep nonce-gap recovery, current funding and original-payload validity as
separate conditions in the [operator procedure](restart-operator-recovery.md).

The [explicit-abandonment follow-up](restart-expired-nonce-neutralization.md)
now rejects an already unsuitable synthetic probe through actual pool RPC and
consumes the 31 missing nonces using existing zero-value self-transfers. Their
total gas is 0.001302 FSN; both 50-block cold ledgers pass. The historical
originals had not yet expired, and the action deliberately abandons them. The
saved nonce-39 intent stays exact and the buyer remains unfunded. This does not
prove fresh purchasing after resolution of an unsuitable saved intent, which
is the next distinct case. A funded replay of still-valid originals remains a
separate scenario with explicit funding and timing assumptions. No production
validation or automatic replacement behavior changes.

All diagnostic services are stopped. D: has about **143.3 GB** free and the WSL
filesystem about **64.0 GB**. No W: workload was needed. Native logs use UTC+02;
structured observations use UTC.

[Evidence and reproducible runner](evidence/restart-paused-purchases-2026-09-27/)
include the recovered signed transactions, raw errors, timing boundaries,
copy proofs, source identities and cold ledgers. The 246-file SHA256 manifest
is checked by `verify-evidence.py`; `--index` also checks staged Git bytes.
