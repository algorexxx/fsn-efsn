# Full-state handover and automatic production

Status: isolated rehearsal, 24 September 2026. No real signing keys, public
transactions, production anchor or consensus changes are involved.

The selected one-backup-block arrangement now passes complete-state execution,
independent imports and actual mining-worker/automatic-buyer operation on
Windows and Linux. Both platforms produce two automatic blocks, close the
process, reopen the same data in a new process and produce two more. An injected
first submission failure recovers without a new head and retries the identical
signed transaction. Linux runs with race detection in a private network namespace.

The rehearsal also confirms a startup trap: omitting the replacement purchase
from the present-day jump can create an accepted block with **no usable ticket**.
The recovery constructor must require that purchase and verify a surviving
successor ticket before signing or publishing the block. The next cleanup block
rejects an absent replacement instead of advancing to an empty ticket set.

## Complete state and synthetic substitutions

Each execution starts from a fresh copy of the verified 230-file preserved-head
state artifact. All copied files match its retained manifest before mutation.
The state is from block 15,130,080, hash
`0xe93ffded087a79097d4309c7831690161db6ed136f4b1a22c4c83a99db80f99f`.
The original backup and exported artifact remain preserved. All new state
copies and block artifacts are on C:; no additional chain data is placed on D:.

The existing three-account substitution relocates the backup wallet's FSN
balance, time locks, nonce and two ticket ownerships to public test key 1. Other
assets, storage, code and unrelated fields remain unchanged. A second, separately
audited two-account substitution debits the donation wallet's 12,020.102 liquid
FSN and credits that exact amount to public test key 2, preserving nonce zero.
There is no duplicated funding. The donation wallet has no time-lock balance.
Its original account is retained with zero FSN in this disposable fixture.

The two stages retain separate ledgers (`fixture.json` and `handover.json`),
including complete account-trie differences and intermediate/final roots.
The final synthetic parent is:

| Field | Value |
| --- | --- |
| Hash | `0xe463e592a96c93420fbf155824b4ee95ba418ee29312637e8dd08eea43951458` |
| State root | `0x450331936bd2612adb4e4aec236796cd25d18a3518c5f33985da421ea6bd59aa` |
| Ticket commitment | `0x7ddb42f1edd476fbe4176f6251cb817669320e9bedec051f1487dec5ba06d4b3` |

This altered parent is an explicit test boundary with an invalid historical
seal for its changed fields. Its body and 256-header context are retained for
real execution/worker behavior, not offered as valid replacement history.
Synthetic addresses and this changed parent affect ticket ordering and IDs.

## Execution and restart

1. The first donation-key purchase enters the real transaction pool at the old
   head. The backup test key signs exactly one historical block, 15,130,081,
   including that long-lived purchase and no backup-wallet transaction.
2. The donation key signs 15,130,082 at the fixed test jump, 23 September 2026,
   including its replacement. The stored ticket count falls from 485 to 480.
3. Its next block clears expired historical tickets, leaving one donation-key
   ticket. The constructed sequence continues to 15,130,086 with replacements.
4. The actual miner/DaTong worker and automatic ticket buyer take over with
   the complete state. The first submission deliberately fails; the controller
   retries its saved signed transaction and produces blocks 15,130,087–088.
5. The process closes. A fresh process opens the database and starts its worker
   and controller with an empty in-memory pool, producing 15,130,089–090.
6. An independently prepared database imports all ten blocks in another
   process. Every header, receipt, ticket set and complete account difference
   matches the producer's ledger.

The first six blocks match byte-for-byte between platforms. The last four use
each runtime's real clock, so Windows and Linux have different legitimate test
suffixes. Their independently verified final identities are:

| Run | Final block hash | State root |
| --- | --- | --- |
| Windows | `0xa01622aee2984bfdae56e3aa31b9f12900689fe8ee199e40bdf7e1ed74a95cdc` | `0xb91841d808e8594054d5437bd326d5ad4173a8b981604adfc3d416bb1fbfc143` |
| Linux/race | `0x7db1156c56147d9b7fc773930f38a4200366d4bd50682e928e60422181786160` | `0x7bbdeaab3af17dd16e021bd4e884202414232d7f862c1b36809f6d28cf454812` |

These are synthetic evidence identities, not candidate mainnet anchors.
The six constructed blocks are a test sequence, not a requirement that all six
be constructed manually at launch. The worker has not yet been demonstrated
starting directly after the first historical block; ordinary auto-buy defaults
at that old head do not construct the required jump-spanning purchase.

## Accounting checks

An independent ledger audit opens no database. It decodes the recorded blocks,
transactions, receipts, native logs and account RLP, verifies the two funding
substitutions, then checks each owner across every relevant future time boundary.
At each boundary it adds liquid FSN, time-lock value and ticket rights before
and after the block. Differences must equal ordinary rewards, paid/received
fees and the normal first-retreat penalty. This checks all intervals, not a
single sampled 30-day coverage window. The first block has 1,014 boundaries;
later blocks have four or six after old rights expire.

All ten purchases are from the donation test key, with sequential nonces 0–9.
Receipt success alone is insufficient: the audit checks native error absence,
logged ticket ID/owner and agreement with the transaction and live ticket.
Total rewards are 3.125 FSN. Each observed transaction pays 0.000042448 FSN in
gas, credited to its block producer. Only the first payment crosses between
the two wallets; subsequent donation-key fees return to the same producer.

The backup test account's nonce remains 233,427. Its complete account bytes
remain unchanged after its first block. No other asset, notation, code or storage
changes. Both runs end with one successor ticket and donation nonce 10.
The real backup and donation addresses are never used for signing.

The model preserves future ownership rights; it does not describe the two
5,000-FSN liquid debits as permanent destruction of principal. Exact
real-address refunds and retreat ordering still need review before signing the
actual recovery sequence.

## Startup omission counterexample

`TestHandoverMissingRecoveryPurchase` independently imports a jump block with
its replacement deliberately omitted. The block is accepted and leaves 479
stored tickets, all expired at the new timestamp, and no successor ticket.
The donation signer cannot prepare another block. No other surviving ticket
can validate a successor at that timestamp. Publishing this recovery prefix
would require replacing it or changing rules; adding a transaction to the pool
alone cannot restart production.

The cause is the existing parent-time expiry rule: during the jump, cleanup uses
the historical parent timestamp, so expired-at-present tickets still count as
stored tickets. They mask the missing usable replacement. This is a demonstrated
core-path trap; the test does not claim a measured worker race frequency.

The following cleanup block behaves differently. With a correctly purchased
jump replacement but no cleanup purchase, `UpdateTickets` detects an empty
remaining set and rejects finalization. Adding the purchase allows construction
and independent import to continue. Preserve this distinction in tooling and
operator instructions.

The launch plan therefore keeps early construction controlled: require the
expected donation purchase and surviving ticket on the historical handover,
jump and cleanup blocks, review their accounting, and only then enable ordinary
unattended production. No new consensus rule is introduced by this rehearsal.

## Cold integrity and remaining gates

Windows cold verification compares all ten canonical blocks, receipts, tickets,
complete ledgers and three head markers after reopening. With all ten suffix
states unavailable in the test wrapper, ticket reconstruction matches direct
state back to the retained synthetic parent. Removing that parent and historical
fallback context fails with `ErrUnknownAncestor`.

Both complete final-state traversals passed with 801,357 accounts,
2,886,305 storage leaves, 33,437 code/data references and 262,347,430 referenced
bytes (563.86 seconds for the producer, 509.81 seconds for the verifier).
The two added accounts are the public test signers. Linux separately
executes/imports the full state and audits both platform ledgers under race
detection; complete trie traversal is performed natively on Windows.

The subsequent [guarded recovery and two-node rehearsal](restart-recovery-construction.md)
now covers the actual service/IPC/P2P handover and starts ordinary production
directly after cleanup. Its unsigned command verifies required purchases and
surviving tickets without changing the source database. Both nodes agree on
cold ledgers after a forced donation-process restart. The compact fixture still
lacks historical data needed for general sync and complete log indexing.

The [offline-signing follow-up](restart-offline-signing.md) repeats the three
controlled blocks against complete-state copies, with forced process termination
after signing completion, export and import at every stage. Exact artifact
recovery, independent imports, cold ledgers and owner-by-owner accounting pass;
unfinished signing attempts remain blocked. The separate
[complete backup package/restore](restart-snapshot-restore.md) now passes local
readback, index comparison and actual node service checks. Public distribution
and final recovery-data production remain open.

Remaining launch work includes:

- Controlled recovery construction and review with real addresses/parameters,
  including mandatory purchases and usable-ticket checks before signatures.
- Published recovery data and an operator download/restore/synchronization path.
  The passing local restore does not establish arbitrary full-history sync or
  replace the production data-distribution gate.
- Backup-wallet purchase/journal inventory, durable disabled startup and key
  custody. The compact state fixture does not contain the original node's
  pending pool or automatic-purchase journal.
- Supported data distribution/sync, production-anchor integration and the
  remaining release gates in the main plan. This does not extend the historical
  replay beyond 2,700,000 or prove power-loss recovery.

Evidence: [restart-full-state-handover-2026-09-24](evidence/restart-full-state-handover-2026-09-24).
