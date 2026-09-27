# Explicit abandonment of missing purchase nonces

Status: bounded synthetic pass, 27 September 2026. Existing transaction RPCs can
consume the 31 missing nonces with explicitly signed zero-value self-transfers.
The later saved purchase remains unchanged and still fails for funding. This
establishes nonce-gap removal by deliberately abandoning purchases; it does not
restore their tickets or demonstrate resumed staking. Production P1–P15 and
consensus rules are unchanged.

## Input and limits of the expiry test

The experiment uses fresh copies of the [coordinated-pause result](restart-equal-weight-pause.md)
at `D:\FusionRehearsal\equal-weight-pause-2026-09-27`. Its separate working root
is `D:\FusionRehearsal\expired-nonce-neutralization-2026-09-27`. All 596 copied
source files, totaling 1,148,147,219 bytes, are checked before/after copying and
after the run. The source remains unchanged. Only synthetic keys 2 and 3 sign;
two real services run inside a loopback-only network namespace.

Both start at block **15,130,126**:
`0x0e01aeb3c7e60ad34d818e6fe784af1aaf72e09602975815dcac263a4feaea91`.
The donation role has canonical nonce 8, saved nonce 39, zero tickets and
2,021.978065487999978776 liquid FSN. The entrant remains an eligible funded
producer. Both pools initially contain no transactions; mining and automatic
buying are disabled.

The [original-purchase diagnosis](restart-paused-purchases.md) established that
the oldest original remains acceptable to the native parameter check until the
latest block timestamp exceeds 27 September 2026 21:19:32 UTC. This rehearsal
runs around 12:53 UTC, before that boundary. It does **not** claim that those
historical transactions have expired or create future-dated blocks.

Instead, it separately signs a synthetic nonce-8 BuyTicket probe with a 30-day
interval beginning two days before the preserved head and ending 28 days after
it. Existing pool RPC rejects it with:

```text
BuyTicket end must be greater than latest block time + 1 month
```

The probe is retained as evidence, never becomes the saved intent, and never
executes. It demonstrates actual pool rejection of an already unsuitable
interval, alongside the earlier exact boundary checks. The nonce-consuming
transactions below deliberately abandon the historical predecessors even
though their payloads are still within that parameter window.

## Existing-RPC sequence and observed result

The owner signs each self-transfer using `eth_signTransaction`, explicitly
providing sender, recipient, nonce, gas, gas price, zero value and empty data.
The RPC uses the already unlocked synthetic account. The returned raw bytes
and decoded transaction must agree, and their recovered signer must be the
expected owner. All 31 signed transactions are retained before submission.

| Field | Reviewed value |
| --- | --- |
| Nonces | 8 through 38, inclusive |
| Sender and recipient | Same synthetic donation owner |
| Value / data | 0 / empty |
| Gas limit and actual gas used | 21,000 per transaction |
| Gas price | 2,000,000,000 wei |
| Aggregate gas cost | **0.001302 FSN** |

The recipient admits every exact raw transaction through
`eth_sendRawTransaction`; its pool records all 31 as pending. Peers then connect
and only the entrant starts normal mining and automatic buying. All 31 execute
in block **15,130,127**, together with an ordinary entrant purchase. Both nodes
return matching successful canonical receipts with 21,000 gas and no logs for
each self-transfer. Donation nonce advances from 8 to 39.

This is a controlled batch on an agreed branch with initially empty pools and
an already specified complete nonce list. It does not replace the operator
runbook's sequential review/recheck policy. It does not test price replacement
against an existing conflicting pending transaction or recovery without a
surviving eligible producer.

The donation buyer is then enabled for 12 seconds with the existing **test-only
held signing worker**, which lets the buyer run while denying block signatures.
All 12 observations retain the exact saved nonce-39 bytes, canonical nonce 39
and an empty donation transaction pool. Its log reports insufficient balance.
The node's mining flag is true in these samples because of that test fixture;
this is not evidence that donation block production resumed. The entrant signs
all four new canonical blocks and advances its own nonce from 40 to 44.

Both workers are stopped and the shared head is observed stable for 35 seconds
before clean process shutdown. The final block is **15,130,130**:

```text
hash:    0x1c856076d9f7d8ab6f426a50684e581f48688e5dc41bb4bc81cee0f4d0d977cc
state:   0x5a2fbd102bbb17ba25f3e0a92f23fa91fe26d28e43c4abfcfe03b8ff0639dd92
tickets: 0xf132b799b7845aa96e751e2315c65e1e76649329c218a04a3aa1e87b3222485b
```

## Accounting and independent verification

The race-enabled live test passes in **81.79 seconds**, and the separate cold
audit passes in **16.87 seconds**, without race warnings. Both **50-block**
canonical suffixes agree byte-for-byte. All **184 JSON/RLP artifacts** covering
the preceding 46 blocks remain byte-for-byte identical to the paused result.
The full account, receipt, ticket and future interval ledgers pass on both
databases. No new retreat occurs in the four-block continuation.

Donation liquid falls by exactly 1,302,000,000,000,000 wei, leaving
**2,021.976763487999978776 FSN**. Its ticket count remains zero and its free
time-lock intervals remain identical. The backup account is unchanged. These
transfers create no native BuyTicket log or ticket, move no value between
owners, and recover no stake lost on the adopted branch.

The only shared-harness change allows a zero-value self-transfer in the cold
ledger when its exact hash and canonical inclusion height are explicitly
listed. Existing positive-value funding checks remain. The inherited evidence
field `AdditionalFunding` holds those 31 transaction hashes and their heights;
in this experiment it is an allowlist of ordinary transactions, **not added
funding**. The independent verifier requires all 31 raw transactions and both
sets of canonical receipts, checks their fields and inclusion, recomputes gas
cost, and checks unchanged donation rights and saved bytes.

## Operational meaning and remaining work

An owner can choose to abandon a missing purchase nonce with an ordinary signed
self-transfer. This uses existing consensus rules, needs liquid gas funding and
a functioning producer, and does not require another 5,000-FSN purchase for each
missing nonce. Once that transaction is canonical, the original purchase at the
same nonce cannot execute on that continuation. This is a deliberate transaction
decision; it is not a refund, purchase retry, token burn or network finality
guarantee. Preserve the old signed bytes and branch evidence.

The automatic buyer does not make this decision. The tested gap ends immediately
before the saved nonce, so its durable intent remains byte-identical and is
retried normally. Current funding and validity are still separate requirements.
If the saved intent itself has become unsuitable, this test has not resolved
it. Existing controller code distinguishes a consumed nonce from a confirmed
purchase, but complete-state recovery through that case still needs its own
explicit test. Do not delete or rewrite the durable record as a shortcut.

The [saved-intent follow-up](restart-stale-intent.md) now separately seeds an
unsuitable nonce-39 record on fresh copies, verifies that actual funding cannot
fix its interval, then passes explicit self-transfer abandonment and three
fresh automatic purchases with actual donation mining. Both 60-block cold
ledgers pass. Its retained failed attempt also demonstrates why a surviving
producer's funding transfer must follow its next pending purchase. The fixture
record injection is test setup; recovery makes no manual record edits. The
[normal-restart continuation](restart-recovered-buyer-restart.md) also passes
exact saved-byte recovery, two fresh successors and actual mining without new
funding, with matching 72-block cold ledgers. Funded original replay, unattended
equal-weight convergence, real funding and owner-approved response policy
remain distinct questions.

All rehearsal processes are stopped. D: has about **142.1 GB** free and the WSL
filesystem about **64.0 GB**. No W: workload was needed. Native logs use UTC+02;
structured observations use UTC. The [233-file evidence manifest and runner](evidence/restart-expired-nonce-neutralization-2026-09-27/)
include source preservation checks, signed inputs and both cold ledgers;
`verify-evidence.py --index` also verifies staged Git bytes.
