# Uninterrupted partition repair with recipient delivery

27 September 2026, baseline `924e3cf`. This extends the
[manual-predecessor delivery investigation](restart-manual-purchase-delivery.md)
through the complete live partition and repair sequence. Production P1–P15 is
unchanged; the additions are rehearsal code, evidence and operating guidance.

## Rehearsal and acceptance

Fresh copies begin at the preserved participant checkpoint 15,130,090,
`0x71fda3d5913b4f0ae5ea48fb1512bf3f1706a2b42a4d9358b1cd890f95ff8674`.
Each pair copies 560 files / 1,040,745,262 bytes and installs the previously
verified 90,000 genuine ancestor bodies below the synthetic parent. Rehearsal
databases and binaries use D:; small evidence files stay in the C: workspace.
The two real services use public synthetic keys 2 and 3
inside a private loopback-only network namespace.

The test requires usable reserve backing before injecting 90 seconds of packet
loss. Both nodes keep mining and buying through isolation and ordinary healing.
Displaced block bodies and purchases are retained through convergence. Every
missing original must be retrieved using existing RPC before funding or repair.
The established synthetic 1,200-FSN backup and 1,800-FSN winner contributions are
ordinary transfers from existing balances; the donor's transfer follows its
exact pending automatic purchase. These amounts and the source wallet are not
authorization to spend real backup funds or a universal reserve recommendation.

After local submission of an original purchase, the delivery check observes both
pools and canonical receipts. If the original stays pending only at its origin
for at least 15 seconds, it requires matching heads, the expected canonical
nonce, the unchanged later saved intent, and the accepted repair ancestor on
both nodes. Production raw-transaction RPC must return the reviewed bytes.
The same bytes may then be submitted to the other producer through existing
`eth_sendRawTransaction`. The trace records the preconditions and actual result.
No replacement is signed and the later saved intent is never cleared.

The saved automatic purchase receives no direct submission by this helper; its
normal controller must execute it. Each receipt must match both canonical
chains and contain a successful native ticket result. Fresh automatic
successors, matching cold accounts/intervals, original-prefix preservation and
cold saved-record equality remain required. Fifteen seconds and the 300-second
receipt/successor windows are bounded test choices, not a production response SLA.

## First attempt: reserve gate stops before the outage

The first attempt fails in **154.87 seconds**, before any packet loss or funding.
The initial progress check returns common block 15,130,092. At the sampled
current purchase interval, donation has a live ticket and free 5,000-FSN
coverage. Entrant has two live tickets, but the harness reports only about
7,021 FSN of combined returned rights and liquid backing and refuses to inject
the outage. That backing calculation is wrong: the independent cold-record
analysis below finds the omitted 5,000-FSN interval and a satisfied reserve
condition. Preserve the failure; do not treat it as evidence of insufficient
real funds.

Both stopped databases pass the **13-block** cold ledger in **16.84 seconds**.
They end at 15,130,093,
`0xf72473ba9fcc45d5a3da248acf810ab1cd51c18ebb49fc6a0e9d392ddc0e6a10`.
All ten initial blocks and all source files are unchanged. No manual repair or
direct delivery is reached. Preserve this attempt at
`D:\FusionRehearsal\delivered-partition-2026-09-27`.

The follow-up uses another fresh starting copy and samples the **same reserve
formula** at subsequent matching live heads for up to 120 seconds. Each examined
head is retained. It injects the outage only if the original criterion becomes
true through ordinary production. It adds no pre-outage funds and does not lower
the gate.

## Second attempt: test-node readiness timeout

The second attempt fails in **96.55 seconds** when the first node does not expose
IPC within the harness's 15-second startup window. Its last process output is
database initialization; cleanup terminates the process before mining or buying.
This log alone does not identify the underlying cause of the slow startup.
Both databases still have the exact original 15,130,090 head and pass the ten-block
cold audit in **29.18 seconds**. No outage or funding is injected. Preserve this
copy at `D:\FusionRehearsal\delivered-partition-2026-09-27-attempt-02`.

A third fresh copy extends the test process's IPC readiness allowance to 60
seconds. It does not extend or change any production-network timeout, consensus
rule, reserve formula or funding amount. The separate process lifetime remains
bounded.

## Third attempt: reserve arithmetic uses the wrong RPC representation

Both services start and continue normal production. The unchanged gate samples
11 common blocks, 15,130,094–15,130,104, during its 120-second wait. Every sample
reports insufficient backing, so the live case fails after **275.09 seconds**
without any outage, funding or repair. Both cold databases pass **24 blocks**
in **22.67 seconds** and agree at 15,130,104,
`0x4eb8c51d3a453b0869bdd76a2836b71e3479ffeeafc55f5d02fd2161d9faab0f`.
All 560 source files and the original ten blocks are unchanged. Preserve
`D:\FusionRehearsal\delivered-partition-2026-09-27-attempt-03`.

The failure exposes a harness bug. `fsn_getTimeLockBalance` returns `ToDisplay()`
output: independent, potentially overlapping intervals sorted for display.
`TimeLock.Add`, `Cmp` and `GetSpendableValue` expect normalized, ordered,
non-overlapping intervals. Applying them directly to the display output
understates the returned-ticket backing in these snapshots. A displayed pair
of 5,000-FSN future tails is not a normalized list of account segments.

The [independent interval check](evidence/restart-uninterrupted-delivery-2026-09-27/audit-reserve-intervals.py)
decodes the retained cold account RLP and sums rights at every interval boundary.
It verifies that the RPC display and raw account represent the same rights,
then adds each eligible ticket's normal-selection return. In all 11 samples,
both owners' recorded backing is low by exactly **5,000 FSN**; the corrected
backing is about **12,021–12,024 FSN**, and the existing reserve condition is
satisfied. The same check passes on the first attempt's failed snapshot.
This is a representation mistake, not an interval-tail shortfall, lost chain
funds or a need to add synthetic funding.

The two rehearsal readers now request the existing `fsn_getRawTimeLockBalance`
RPC and reject invalid interval layouts. The reserve formula, thresholds and
funding amounts are unchanged. The repair purchase's diagnostic coverage check
uses the same correction. Production RPC, consensus and transaction handling
are unchanged. Prior cold ledgers decode actual account state and sum rights
at boundaries; their conservation checks did not use this faulty arithmetic.
Prior live logs that calculated coverage from display intervals should not be
used as funding evidence; actual pool rejection and successful native receipts
remain separate observations.

## Fourth attempt: corrected input representation

A fourth fresh pair uses raw normalized intervals. The first reserve sample at
15,130,094 passes without additional funds. Packet loss lasts 90.240 seconds
and drops 49 packets. Both isolated branches reach 15,130,099, diverging at
15,130,095. Ordinary reconnection converges on the donation producer's branch;
the entrant has canonical nonce 6 and unchanged saved nonce 12. Six displaced
original purchases are retrieved before either funding or repair.

The original 1,200-FSN synthetic backup and 1,800-FSN synthetic winner transfers
succeed together at 15,130,104. The winner's transfer follows its exact pending
automatic purchase at nonce 19. No service is restarted and no extra funding is
introduced. Sequential originals then reach native success on both chains:

| Purchase | Canonical block |
| --- | --- |
| Original nonce 6 | 15,130,105 |
| Original nonce 7 | 15,130,107 |
| Original nonce 8 | 15,130,111 |
| Original nonce 9 | 15,130,114 |
| Original nonce 10 | 15,130,118 |
| Original nonce 11 | 15,130,123 |
| Unchanged saved automatic nonce 12 | 15,130,127 |

All six originals propagate without needing direct recipient submission in this
attempt. The delivered-repair helper observes them but makes **zero** direct
submissions. This does not exercise its intervention branch during the
uninterrupted sequence; the earlier controlled peer test and restarted-copy
direct-delivery pass remain the evidence for that mechanism. The controller
executes the saved intent normally, followed by two fresh automatic purchases
at nonces 13 and 14. Donation production also continues after the saved purchase.

The full live test passes in **834.41 seconds**. Both canonical databases and
both 19-block isolated branches pass the account/interval ledger. A separate
cold reopen passes in **41.77 seconds** and verifies the common **59-block**
recovery suffix. The accepted branch accounts for two first-retreat losses of
entrant tickets at 15,130,095 and 15,130,098, with no additional retreat during
the subsequent funded repair. Rewards, fees, both transfers, unrelated account
fields and future interval rights reconcile. Final identity:

- Height: **15,130,139**.
- Hash: `0xc06fff955d8584caf53328ea64c97d3987eda844a50e0b8d5a7dd0b57af4f800`.
- State root: `0xbab6d506014c6913958d3eda2a31ca5430ae21abe01e16541c173ea12fb580dd`.
- Ticket commitment: `0x99405466c9c3d245b35e7051e4e3d197d2479f85f0dd21d3f19abe37010e045c`.

Both owners' cold nonces and saved bytes match the stopped live records. The
560 source files and original ten canonical blocks remain unchanged. The
corrected reserve snapshot also exactly matches independent arithmetic over
the cold account RLP. No race report occurs in any of the retained attempts.

All rehearsal processes are stopped. D: has about **149.3 GB** free and the
D:-backed WSL filesystem has about **64.1 GB** available. W: was not needed.
Preserve `D:\FusionRehearsal\delivered-partition-2026-09-27-attempt-04` and use a
fresh copy for any continuation. Native logs use local UTC+02; structured traces
record UTC explicitly.

## Boundaries

Pool/saved-record observation remains a test-only interface; original retrieval,
submission and receipt access use existing production RPC. Head polling cannot
guarantee capture of every unseen fork. This passing funded case does not prove
unattended recovery, repeated-loss affordability, equal-weight convergence,
public-network behavior or production monitoring coverage. Those gates remain
separate from this narrow operator-delivery exercise.

The uninterrupted funded manual-repair sequence now has a passing case. Its
recipient-delivery fallback did not need to intervene. The subsequent
[injected-rejection case](restart-injected-manual-delivery.md) uses a fresh copy
and requires a native remote rejection, restored normal price, sustained
local-only pending status and successful direct delivery of that exact original.
It passes seven originals, the unchanged saved intent, two fresh automatic
purchases and both 54-block cold ledgers. This controlled policy fault is
distinct from the historical insufficient-balance ordering. Next define the
actual monitored funding and response policy and address equal-weight
convergence and broader outage coverage. The one-backup-block launch and
production P1–P15 are unchanged.

`verify-evidence.py` verifies the current source identities, interval analyses,
recorded purchase receipts, stopped/cold saved records and top-level SHA256
manifest. Add `--index` after staging to check exact Git blob bytes. The nested
attempt manifests are preserved historical outputs with their original path
layout; use the top-level verifier for this combined evidence package.

Evidence: [source identities, runners, logs and account ledgers](evidence/restart-uninterrupted-delivery-2026-09-27/).
