# T2 results on claudedev, 23–26 October 2026

The 48 h soak (`t2-soak-claudedev.sh`, run `soak-20261024T051755Z`, 24 Oct 05:17Z – 26 Oct 05:22Z) and the
rival test (`t2-rival-early-claudedev.sh`, 26 Oct 05:27Z), with the final binaries (`efsn` e94ad0ec) and the
rebuilt recovery blocks (`recovery.rlp` bd101c83, byte-identical to the PC's).

| Launch-plan T2 criterion | Result |
| --- | --- |
| Recovery blocks import on every node | Pass: a, b, x, j imported; all six nodes hold 15,130,081 `0xd2cf…` and 15,130,083 `0x1d68…`. |
| Both producers sustain production and buy every block for 48 h | Partly: 13,297 blocks, every one with a purchase, no failed calls. Only B produced after A's kill -9 (A 850, B 12,447). |
| A restarted or kill -9'd producer resumes | B (clean restart): pass. A (kill -9): rejoined and synced, but never produced again (below). |
| A 30-minute partition heals | Pass: A rejoined and agreed. |
| A fresh node joins via the bootnode from a snapshot | Pass: j (launch snapshot, bootnode only) and k (live copy of x). |
| A node holding a rival pre-restart chain is refused and rewinds | Soak: not exercised (the rival joined after the restarted chain outweighed it). Rival test: refused while heavier (below). |

All six nodes agreed at 15,143,380 at the end; no `panic`, `Fatal`, `BAD BLOCK` or check point mismatch.

## Producer A after kill -9

1. **Its tickets were gone and it had no spendable funds.** A held 2 tickets when killed and 0 five minutes
   later, while still down. With 2,286 FSN liquid against the 5,000 FSN price, and its time-locked FSN usable
   only after the lost tickets' expiry about 30 days later, `BuildBuyTicketSendTxArgs` fails with "not
   enough time lock or asset balance". `AutoBuyTicket` discards that error without logging it.
2. **It restarted 1,668 blocks stale and signed a second block on an old parent.** After the kill its
   database fell back to 15,130,083, the state last written on a clean stop. It mined at once, sealed a new
   15,130,084 on the same parent as its own original 15,130,084, and on syncing logged `multiple block mined`
   for its own address, which sends a `ReportIllegal` (ticket deletion). A had no tickets left, so the soak
   was unaffected; on mainnet this costs a crashed producer its tickets.

## Rival test

The rival node joined 30 s after the producers with total difficulty 63,370,514,765 against the restarted
chain's 63,370,514,642. Both producers refused it 40 times each (`check point failed, block hash mismatch:
number=15130081`, peer dropped) and kept 15,130,081 `0xd2cf…`. About six minutes in, the restarted chain
outweighed the rival (15,130,113, 63,370,514,782), and the rival node, whose build pins only 15,130,080,
switched to it by ordinary fork choice; the ten-minute check therefore reports FAIL for "rival node stayed on
its own chain", and the pinned-build restart found nothing to rewind. Both are the test's timing, not node
behaviour: a three-minute first phase would check the rival node and restart it while it still holds the
rival chain.

## Files

- `soak-summary.txt`, `soak-events.log`: the final soak.
- `rival-early-events.log`: the rival test.
- `soak-dry-run.log`: the 0.03-scale dry run of the whole schedule (same two A findings).
- `soak-console-all-attempts.log`: all soak attempts, including the two stopped by script bugs (in_ns `$!`,
  hourly check reading killed producer A), both fixed in the claudedev scripts.
- `prep.log`: rebuilding the operator blocks, seeds and rival chain.

## Fixes and re-checks, 28 October

Three efsn changes came out of these results, each tested on the T2 build (`~/t2/src-node` with the
change applied, `efsn` 82866815) against the unchanged binary:

- **`fix/restart-double-seal` (new branch).** In `t2-crash-restart-claudedev.sh` producer A is killed
  after 15 minutes and comes back on 15,130,083 instead of 15,130,154 with either binary. The fixed
  node refused to seal 15,130,084 the moment it restarted ("refusing to seal block 15130084: this node
  already sealed block 15130154"), ten seconds before its sync started; no node logged a double block.
  The unchanged binary's sync won the race this time, so the control shows the stale restart but not
  the double block itself.
- **`feature/restart-checkpoints`, third commit.** With the three-minute rival test the unchanged
  binary passed the five original checks (`rival-early-3min-unfixed.log`), but its restarted rival
  node logged no "check point mismatch" and stayed on the rival chain for about 100 seconds: the check
  point table was loaded after the chain was opened. With the fix it rewound at startup (three
  mismatch lines) and all six checks pass.
- **`feature/autobuy-retry`, third commit.** A's failing purchases now log "Automatic ticket purchase
  failed ... not enough time lock or asset balance". A in these fixtures can buy only right after its
  own blocks, so the warning recurs each time it runs dry again (24 times in 22 minutes).

`fix-checks.log` holds the three runs (control, fixed crash test, fixed rival test).
