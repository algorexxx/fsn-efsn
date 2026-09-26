# Funded participant entry on complete state

26 September 2026, baseline `4afa625`. Investigation tests and evidence only;
production candidates remain P1–P15.

This case establishes a funded second participant for the complete-state
competing-producer investigation. The launch arrangement stays one backup block
followed by donation production. The additional participant is a hypothetical
later entrant, using public test key 3 in the isolated rehearsal.

The corrected Linux race-instrumented run passes in **119.58 seconds**. Both
owners purchase tickets and sign live blocks; both cold databases and the
independent account ledger agree across ten suffix blocks and 14 transactions.

## Source of funds

The prior complete-state fixture substitutes public keys for the backup and
donation owners with audited debits and credits. After the three reviewed
recovery blocks, the backup fixture still has 10,000 FSN in time locks covering
the current time through forever, plus its liquid balance. This test spends
existing rights through signed normal transactions; it makes no further direct
balance, ticket or state-root substitution.

| Suffix block | Signer | Extra transaction alongside donation replenishment |
| --- | --- | --- |
| 4 | Donation test key | Backup test key converts 10,000 mature FSN rights to liquid credited to the entrant |
| 5 | Donation test key | Backup test key transfers 2,020.102 liquid FSN to the entrant |
| 6 | Donation test key | Entrant buys its first funded ticket |

Immediately before its first purchase, the entrant has exactly 12,020.102 liquid
FSN and nonce zero. It had no account in the starting state. The backup signs
two funding transactions, pays their gas and the conversion's 0.001-FSN native
fee, and buys no ticket. It signs no block after the original recovery block.

This is **hypothetical funding for the test**. It does not establish permission
to contribute the real backup owner's funds, an agreed reserve source, or a
requirement to retain that key after handover. A real later entrant would need
its own authorized source of funds.

## Validation

Two fresh copies of the compact complete-state export independently execute
the reviewed recovery prefix and the funding prefix. The existing namespace
guard restricts the live services to an enabled loopback-only network. The node
harness now permits public test key 3 alongside keys 1 and 2; it still refuses
arbitrary key values. No real key or public peer is involved.

The live acceptance requires both the donation owner and entrant to buy tickets
and sign canonical blocks, then reach equal stopped heads. Both databases are
reopened separately and compared across every suffix block, receipt, ticket set
and complete account-trie difference.

The first three blocks use the existing handover audit. A separate continuation
audit checks every future interval boundary for each affected owner against
funding transfers, rewards, gas, the native conversion fee and first-retreat
losses. It checks nonce increments, unrelated assets, code, storage and notation,
and requires the backup account to remain unchanged after its funding transfers.
The audit uses complete account differences; it does not repeat a full storage
and code traversal.

## Observed result

The funding prefix ends at 15,130,086 with one ticket per producer. After its
first purchase the entrant holds 7,020.101957552 liquid FSN at nonce one. The
backup fixture holds 1,205.752763845480158626 liquid FSN after paying both funding
transactions. Its account does not change again in the observed continuation.

Four live canonical blocks follow: one signed by the donation owner and three
by the entrant. They include five additional ticket purchases. The seven blocks
after cleanup contain nine successful purchases and the two funding transactions;
none contains a retreat. The three earlier recovery blocks retain their already
audited historical retreats.

Final height: **15,130,090**. Hash:
`0x71fda3d5913b4f0ae5ea48fb1512bf3f1706a2b42a4d9358b1cd890f95ff8674`.
State root:
`0x42dd6716405b53f257393ee2fe305ca11b953654ed28b7c675545d50717ed83b`.
Ticket commitment:
`0xbd643bd4fc43ace98e42f2f6a77ee529fdbe71310fcaeb286dfdcfd70c74b23a`.

The stop observer sees two head changes before both heads remain equal and
unchanged for 35 seconds. This supports the existing requirement for clean
process shutdown at signer handover; miner-stop RPC alone is not a barrier.
Both services then shut down before the independent cold checks. There are no
skipped cases or reported data races. No fresh native Windows run is claimed.

All 230 original export files match their manifest again after the test. The
three attempts retain six fresh C: copies totaling 3,172,902,480 source bytes
(about 2.96 GiB before database growth), leaving about 78.66 GiB free after the
last copies. The original backup is untouched; no chain-database copy is placed
on D: or W:.

## Retained setup failures

The first attempt failed during construction in 26.17 seconds: the initial
appended purchase used a start near the current clock, more than three hours
after the older parent timestamp. The native purchase check rejected it. The
correction uses the parent timestamp for the start and keeps the end 30 days
beyond the constructed block time. These controlled prefix purchases can
therefore span more than exactly 30 days.

The second attempt executed both funding prefixes successfully, then failed in
29.61 seconds because the service harness only permitted test keys 1 and 2.
The explicit key-3 allowance corrects that test restriction. Both failed logs,
source versions, copy proofs and executable identities are preserved alongside
the corrected attempt; none is presented as a passing live run.

## Limits and next work

This entry rehearsal does not inject a network partition, establish a multi-nonce
rollback or run manual repair. The subsequent
[complete-state partition attempt](restart-full-state-partition.md) failed before
the repair gate: the branches kept advancing separately. Both cold account
ledgers passed; a separate stopped-node diagnostic found equal total difficulty
and unavailable historical ancestry in the compact fixture.
The [genuine-history follow-up](restart-partition-history.md) has since supplied
that ancestry and passed the exact missing-header request. Its fresh attempt
exposes a complete-state funding stall after ticket losses, while stopped
heavier-peer synchronization and matching cold ledgers pass. Live nonce repair
remains open; the initial balance is not a guaranteed competing-producer reserve.
The entry result cannot establish a
universal reserve balance, indefinite unattended operation or funds available
from the real backup owner.

As before, the compact fixture contains complete state and recent execution
context but lacks full historical bodies and log indexes. It is not a public
bootstrap package or a full-history synchronization test. Its known bloom-index
`canonical block #1 unknown` error remains in the logs. No production code,
dependencies, consensus rules or release parameters change in this follow-up.

All attempt logs, identities, copy proofs and block/account artifacts are in
[the evidence directory](evidence/restart-full-state-participant-2026-09-26).
