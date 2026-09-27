# Funded continuation of the complete-state nonce gap

27 September 2026. Production baseline `e444056`.
This follow-up uses the stopped failure from the
[complete-state partition](restart-retry-partition.md). All code edits are test
harness changes; the fifteen production candidates and launch sequence remain
unchanged.

## Exact starting state

Both nodes start at 15,130,103, hash
`0x1a52a5d9fec08c0c5aa2adddf62dcaf115991f74919877c88e6756b771d67aaf`.
The donation fixture has canonical/saved nonce 18, one ticket and
2,025.415586712 liquid FSN. The entrant has canonical nonce 7, exact saved nonce
14, no tickets and 2,021.664457552 liquid FSN. Its future locks cannot fund a
purchase now. The synthetic backup has 1,205.752763845480158626 liquid FSN.

The previous no-funding failure remains preserved. This run copies 648 files /
1,148,278,054 bytes to `D:\FusionRehearsal\funded-gap-2026-09-27`, with source,
destination and source-after hashes checked. D: had about 160.2 GB free afterward.
No new original-backup restore or history export is required. The node services
use only public synthetic keys 1–3 and an isolated loopback-only namespace.

## Capture correction

The partition harness now observes heads throughout reconnection and the
nonce-gap observation window. It fetches each observed head by hash, walks back
to already retained ancestry and preserves bodies under their original hashes.
It does not replace losing bodies when canonical heights change. Repair searches
this retained set rather than only the branch at the moment packet loss ended.

The test-only node service exposes a block-by-hash helper for this capture.
There is no new production RPC. Existing production block/transaction RPC is
still used to recover and verify each signed purchase before repair.

A regression starts from the previous incomplete nineteen-block branch capture
and asks for the known losing head at 15,130,102 after rollback has already
completed. It recovers the three omitted blocks and all seven missing purchases,
without changing the accepted head. This checks capture by retained hash; a new
packet-loss run of the observation loop is a separate exercise. Polling heads is
not a guarantee of archival capture for every possible intervening fork.

## Funding procedure

The experiment uses two ordinary signed transfers of existing liquid balances:

| Synthetic sender | Transfer to entrant | Sender nonce |
| --- | ---: | ---: |
| Backup | 1,200 FSN | 233429 |
| Donation | 1,800 FSN | 19, after its exact saved purchase at nonce 18 |

Both transfers use 21,000 gas at 2 gwei. Their admission is checked in the real
cold-state pool before starting the live services. The entrant's first original
purchase is separately rejected for insufficient funds before the transfers.
The donation's saved purchase and the two transfers are submitted to its node,
then both miners and buyers are enabled. Funding is accepted only after matching
successful canonical receipts on both nodes.

The backup signs the synthetic transfer only: it has no ticket, starts no node,
mines no block and buys no ticket. No balance is edited and no mint occurs. These
synthetic signatures do not authorize a transfer from the real backup owner or
establish an available real emergency fund.

The existing repair procedure retrieves all missing originals before submitting
any. It submits nonces 7–13 sequentially and requires native purchase success on
both nodes before advancing. It retains saved nonce 14 unchanged. Insufficient
funding is retried only while the owner has a ticket, for at most 120 seconds per
purchase; a zero-ticket funding failure stops the repair. That wait is an
experiment bound, not an approved production response time.

## Results

Both runs pass with Linux race detection. The live test takes **468.15 seconds**;
the separate cold audit takes **41.69 seconds**. No race report occurs.

The two funding transfers and donation's exact saved nonce-18 purchase execute
at 15,130,104. The entrant then has 5,021.664457552 liquid FSN. Its seven missing
originals, nonces 7–13, execute sequentially with unchanged signatures and
successful native purchase receipts on both nodes. Six intervening funding waits
end after ordinary ticket selection/return. Last rejected samples span about
12–78 seconds; the two-second retry interval places admission roughly two
seconds after each final rejected sample. Waiting succeeds because a live ticket
returns stake, not because the rejection is bypassed.

The exact saved nonce-14 purchase executes automatically at **15,130,130**, hash
`0x31156d09280c72a7e7d2c47a63bc5e4bc99f9f836fd58bb1a7865479724fdb2f`.
Two fresh automatic purchases, nonces 15 and 16, follow without another start
command. The donation also continues replenishing. No missing original is
re-signed, no saved record is cleared manually, and there is no manual reconnect
or submission to the receiving node during the repair.

After disabling the buyers/miners, waiting for a stable common head and stopping
both processes, both databases finish at **15,130,138**, hash
`0xc1e65214e958ea0b6d56c7b4db66d07d2944fd571f1295b431cb239b6ed5553f`,
state root
`0xb9d8c86b7b2c987ba484ad5ba447af99bafc34ebb233335ad4a4413e249a4001`.
The continuation adds 35 blocks: donation signs 25 and entrant signs 10; backup
signs none. There are no new retreats in those blocks.

| Synthetic owner | Final canonical nonce | Tickets | Liquid FSN |
| --- | ---: | ---: | ---: |
| Backup | 233430 | 0 | 5.752721845480158626 |
| Donation | 44 | 1 | 233.228149936000021224 |
| Entrant | 17 | 0 | 24.789436327999978776 |

Donation's next signed nonce-44 purchase is saved and pending at shutdown. The
entrant has no saved intent; its final ticket is selected after buying has been
disabled, leaving covering time locks in its account. Zero tickets at this
deliberately stopped point is not an observed automatic-buyer failure. The
complete lock schedules are retained in the cold account inventories.

Both canonical 58-block JSON/RLP histories match byte-for-byte. The independent
ledger reconciles original funding, the two new transfers, every purchase,
ordinary returns, rewards, gas fees, historical first-retreat losses and future
interval boundaries. Both original isolated 19-block branches also pass again.
The original 23 canonical records and all 648 source files are unchanged. Each
owner's cold nonce and saved bytes match its stopped-service observation, and
all seven repaired transaction files match the earlier no-funding diagnostic.

All seven changed Go files are tests: hash-based branch capture and its local
test API, an observation callback, shared funding-receipt/cold-audit helpers,
and the new funded continuation. No node runtime, consensus, wallet balance,
ticket price or penalty rule changes. The retained
[evidence directory](evidence/restart-funded-gap-2026-09-27/) includes scripts,
source/binary identities, full logs, signed funding transactions, canonical
blocks, account differences, intent checks and hashes.

## Remaining boundary

This is one passing **funded manual repair after restarting the preserved
failure**. It is not unattended nonce repair or a fresh uninterrupted
partition-to-repair test. The 3,000-FSN transfer works for this exact inventory
and selection schedule; it is not a universal reserve recommendation. Another
first retreat can remove the next purchase's usable interval. The previous
unfunded failure remains a necessary control.

Next exercise the corrected observation loop through a fresh live partition,
retain block locations until synchronization finishes, and apply the same
funding/receipt/intent checks without restarting the services between rollback
and repair. Keep equal-weight convergence and repeated-loss cases separate.
Production still requires a chosen monitored-repair policy, actual authorized
funding, operator response coverage and independent review. Nothing here changes
the agreed minimal launch or authorizes retention of the borrowed real key.

Both services are stopped. Preserve the D: result and earlier failures; any
continuation must use fresh copies.
