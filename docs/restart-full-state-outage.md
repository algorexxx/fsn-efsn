# Complete-state recovery with one producer

26 September 2026, baseline `fb4039ba08891bf44d389b0f560b01f5d6eadb06`.
Tests, evidence and documentation only; production candidates remain P1–P15.

The selected launch topology now passes a live complete-state network outage
and producer-crash rehearsal. The donation producer restores its exact saved
purchase, executes it and two fresh automatic successors, and the non-producing
verifier catches up through normal peers. Both cold databases and the complete
account ledger agree. No external transfer or manual purchase resubmission is
needed in this case.

## Scope and setup

This case represents an accidental outage with one active producer, not a
competing-producer reorganization. It does not resolve the known multi-nonce
rollback pause. Keeping that distinction preserves the user's minimal startup
arrangement instead of introducing another funded validator as a test premise.

The source is the verified compact export of complete preserved state at
15,130,080. It has 230 files and 528,817,080 bytes, with the original historical
block `0xe93ffded087a79097d4309c7831690161db6ed136f4b1a22c4c83a99db80f99f`.
Two fresh C: copies consume 1,057,634,160 bytes. Source and copy files pass the
original SHA-256 manifest; source files are checked again after the run.
About 81.7 GiB remains on C: after copying. D: and W: receive no new chain data.

Both copies receive the existing audited public-key substitutions: backup
ownership to public key 1 and the donation wallet's exact 12,020.102 liquid FSN
to public key 2, without duplicated funds. They independently execute the first
three retained full-state recovery blocks. Both reach cleanup at 15,130,083:
`0x94ed041a999c47e4a3797f3f33067e3cdf011add53b786832f3ad334d9727345`, state root
`0xea437527f99ff52f682abfe458941f2a4a56b8023d8fd7f3d4e99dd7efaf6cf4`.
The test anchor is this synthetic cleanup block, not a selected production anchor.

Two actual services then run in a private loopback-only network namespace.
Only the donation service mines and buys tickets. The backup-key service is a
verifier; it never enables mining or automatic buying. Its presence verifies
replication and does not imply a second producer is required at launch. This
turn imports the backup-signed recovery block; it does not sign a new one.

## Observed result

The race-instrumented Linux test passes in **237.85 seconds** with no skipped
cases or reported data races. It uses Go 1.21.3 and cached offline dependencies.

| Phase | Observation |
| --- | --- |
| Network loss | 90.35 seconds before the crash step; producer reaches 15,130,093 while verifier remains at 15,130,085 |
| Crash cut | `SIGKILL` after observing a saved 117-byte purchase at canonical nonce 13, also present in the pool |
| Reopen | Exact saved bytes and nonce 13 remain; pool is empty and automatic-buy startup configuration is enabled |
| Producer downtime | 20.52 seconds through reopen; isolated non-producing verifier does not advance |
| Network healing | Kernel filter reports 44 dropped packets; static peer reconnects and ordinary downloader catches up |
| Purchase recovery | Saved nonce 13 executes, followed by new automatic purchases at nonces 14 and 15 |
| Final stop | Both heads remain equal for 35 seconds; no delayed head changes observed in this run |
| Cold verification | Both databases agree on all 16 suffix blocks, receipts, ticket sets and complete account differences |

The pending transaction is
`0x198a69c09daab8c2c2e1590b84be3100444b348c493b55b6a30dbbf1e84a4887`.
Its fresh successors are
`0xb50a44a24709b3c440ad21c8841ac061b348f22cea8ce5b2ca9de5ffb267eef8` and
`0xd9b9af903d3ce14a2709b6253b4d3fca98877292c92ce46e8f48b095b13a246c`.
Both peers confirm their canonical native-success receipts.

The reopened service receives the normal `miner_start` action once. Its retained
automatic-buy configuration handles purchase recovery; no additional buyer-start
command, raw transaction submission, funding transfer or forced-sync API is used.
The rehearsal does not test an operating-system service manager automatically
restarting the process or launching mining after reboot.

Final height: **15,130,096**. Hash:
`0x51918b710ab15132c05924739f8c606807fc643af9ef74da671b7c342a16472c`.
State root:
`0x89bd4348d3a767ba9651e78f9a32fe31497503009762f752620b4daf4734ad2c`.
Ticket commitment:
`0x13f772163c1704793e9b70864a2447189e307246d23347a533c03fd93fa7f512`.

The independent ledger reconciles all future FSN interval rights through the
16-block suffix, including 5 FSN total ordinary rewards, fees and the historical
recovery retreats. Unrelated account fields are preserved and the backup account
remains unchanged after its first recovery block. This audit compares complete
account-trie differences; it does not repeat a full storage/code traversal.

## Limits and next work

The compact fixture retains complete state and recent execution context, not
complete historical bodies. As in earlier rehearsals, the bloom indexer reports
`canonical block #1 unknown`. That known fixture limitation is retained in the
logs; this result does not establish public bootstrap distribution or general
full-history synchronization. The successful downloader step is bounded to the
already shared recovery suffix.

A process kill is not a power-loss or disk-corruption test. This run also does
not cover ticket expiry, unavailable original transactions, real-key custody,
public discovery, competing fork choice or manual nonce repair after rollback.
The earlier observation that already-signed work can publish after `miner_stop`
still requires clean process shutdown for key handover.

Next construct the complete-state competing-producer case with an explicitly
audited source of ordinary funded tickets. Keep it separate from the day-one
deployment requirement. Then apply the [manual recovery procedure](restart-operator-recovery.md)
if that case creates a missing-nonce gap. Monitoring, real reserve availability
and the release decision on manual recovery remain open.

Raw logs, copy proofs, executable/source identities and all 16 block/ledger pairs
are retained in [the evidence directory](evidence/restart-full-state-outage-2026-09-26).
