# Uninterrupted repair after an injected recipient rejection

27 September 2026, baseline `2519cde`. The previous
[uninterrupted funded repair](restart-uninterrupted-delivery.md) passes, but every
manual original propagates normally. This follow-up deliberately requires the
recipient-delivery intervention. All new Go code is in tests; production P1–P15,
consensus rules, the launch sequence and funding amounts are unchanged.

## Controlled stimulus and required outcome

The test begins with another verified copy of the preserved complete-state
participant checkpoint at 15,130,090. The two copies contain 560 source files /
1,040,745,262 bytes. The previously verified 90,000 genuine ancestor bodies are
installed again. Databases and the race-instrumented binary use D:; evidence
files are retained in the workspace. All node networking is inside a private
loopback-only namespace and only public synthetic keys 1–3 are used.

The existing reserve condition, 90-second packet-loss interval, automatic
reconnection, displaced-original retrieval and 1,200/1,800-FSN synthetic funding
sequence remain in place. The fault is introduced only after funding, while the
losing owner has zero tickets and cannot mine its first repair purchase locally.
The test requires matching current heads before introducing it.

Through existing `miner_setGasPrice`, the receiving producer's minimum price is
temporarily set one wei above that original transaction's tip cap. The original
is submitted locally at the sender. Its signed bytes, nonce, price and interval
are unchanged. JSON trace output from the actual receiver must identify that
exact transaction and the actual pool error `transaction underpriced` within
ten seconds; absence from a pool alone does not satisfy this gate.

The original minimum price is restored and read back. For at least 15 seconds,
the test requires the purchase to remain pending only at its origin, with the
same canonical nonce and unchanged later saved intent. Both miners and buyers
stay enabled. The existing delivered-repair helper then observes ordinary
propagation for another 15 seconds before it may submit the exact original bytes
to the receiving node through `eth_sendRawTransaction`. Its matching-head,
accepted-ancestor, saved-intent, recipient-pool and production raw-byte RPC
checks still apply.

The complete test requires successful direct delivery of the **specific first
original whose rejection was observed**, successful native receipts on both
canonical chains, all remaining original purchases, automatic execution of the
unchanged saved intent without direct submission, and at least two fresh
automatic purchases by the repaired owner. Both stopped canonical databases
and both isolated branches must pass accounting. The separate cold reopen runs
even if the live test fails.

The temporary price policy affects remote admission at that producer and can
affect other remote transactions. This is a deliberately isolated test with
known synthetic accounts, not an operator recovery recommendation. Restoration
is registered for test cleanup as well as the normal path. The new `lab` method
only reads the pool's current minimum price; policy changes and recovery
submissions use existing production RPC.

## Result

The first attempt passes. The race-instrumented live test completes in
**743.91 seconds**, including both canonical account ledgers and both isolated
branch ledgers. The separate cold reopen passes in **37.63 seconds**. The two
services stay running through partition, convergence, funding and repair.

The unchanged reserve gate passes at 15,130,094. The packet-loss interval lasts
90.407 seconds and drops 44 packets. Both isolated heads reach 15,130,099, with
their first differing block at 15,130,095. Normal reconnection adopts the
entrant's heavier branch. At the stable common head 15,130,102, the synthetic
donation owner has canonical nonce 11 and saved nonce 18. All seven displaced
originals are recovered through existing RPC before funding or resubmission.
The ordinary 1,200/1,800-FSN transfers both execute at 15,130,104.

The exact first original is
`0x876f4b74f7d2350e0e0aa9146e0d9dd1e834e876e25969c18604f2ba4ac57103`.
The receiver's minimum is raised from 1 wei to 1,000,000,002 wei, one wei above
the original's price. Its native trace records `transaction underpriced` for
that hash. The normal minimum is restored before the negative control starts:
the purchase remains only in its origin's pool for **15.169 seconds**. The
existing helper then waits another **15.269 seconds** before direct submission
of the unchanged bytes. Both chains confirm its successful native purchase.

| Purchase | Canonical block | Direct recipient submission |
| --- | --- | --- |
| Original nonce 11 | 15,130,107 | Yes; deliberately rejected original |
| Original nonce 12 | 15,130,109 | No |
| Original nonce 13 | 15,130,111 | No |
| Original nonce 14 | 15,130,116 | No |
| Original nonce 15 | 15,130,118 | No |
| Original nonce 16 | 15,130,121 | No |
| Original nonce 17 | 15,130,124 | Yes; later local-only purchase |
| Unchanged saved automatic nonce 18 | 15,130,127 | No |

The last original also needs direct delivery after 15.410 seconds pending
locally. No price fault is injected for this transaction. The sender's native
trace records zero broadcast recipients when it is manually resubmitted; the
receiver records admission after direct submission. This is additional delivery
evidence, not a second observed underprice rejection or proof of the historical
insufficient-balance ordering. The exact saved intent executes automatically,
followed by two fresh automatic purchases at nonces 19 and 20.

Both cold databases agree on the **54-block** recovery suffix. The accepted
branch accounts for two donation-ticket first retreats at 15,130,096 and
15,130,098, with no further retreat during funded repair. Rewards, fees,
transfers, future interval rights and unrelated account fields reconcile.
Final identity:

- Height: **15,130,134**.
- Hash: `0x36c203213462703fa078eb2dd3b4decd395630e5b78202e4894c5375beff847d`.
- State root: `0x7d5ebd7906a1237a57469bfa3f286a5e31a6f3cf2c5be5333575a0dc673141bf`.
- Ticket commitment: `0x9b8def0d23b132330b64fc7a49ed4aaaf67b34cb1d884a6de1936d053e99af41`.

The stopped donation owner has nonce 21 and no saved intent; the entrant has
nonce 36 and its next saved purchase. Both cold records preserve those exact
nonces and saved bytes. The 560 source files and original ten canonical blocks
remain unchanged. No race report occurs. All rehearsal processes are stopped;
D: has about **148.1 GB** free and its WSL filesystem has **64.0 GB** available.
W: was not needed. Preserve
`D:\FusionRehearsal\injected-manual-delivery-2026-09-27`; use a fresh copy for
another experiment. Native trace timestamps use UTC+02; structured traces use
UTC.

## Scope

This stimulus is a deliberate price-policy rejection, not a reproduction of the
historical insufficient-balance ordering. The earlier controlled peer-handler
test remains the evidence for that precise rejection/known-peer sequence. This
live test does not inspect private peer-known maps; it measures actual remote
rejection, sustained local-only pending status after readiness is restored, and
the effect of explicit recipient delivery.

This pass establishes a bounded manual recovery case, not unattended operation,
a universal funding reserve or recovery after repeated retreat losses. Real
funding authorization, monitored response responsibility, equal-weight forks,
public networking and broader outage coverage remain separate release gates.

The uninterrupted recipient-delivery intervention is now exercised. No further
repetition of this same case is needed without a new failure or code change.
Next resolve equal-weight convergence and the actual monitored funding/response
policy, while retaining the separate release and public-network gates.

`verify-evidence.py` checks the observed rejection, restored-price negative
control, direct-submission bytes and ordering, canonical native receipts,
stopped/cold records, source identities and all 142 files in `SHA256SUMS`.
Run with `--index` after staging to verify the exact Git blob bytes as well.

Evidence: [runners, source identities, fault trace, pool observations and cold ledgers](evidence/restart-injected-manual-delivery-2026-09-27/).
