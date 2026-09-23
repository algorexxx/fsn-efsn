# Restart investigation — 23 September 2026

The reviewed implementation roadmap and current decision register are in
[restart-plan.md](restart-plan.md). Raw read-only RPC evidence is retained in
[the evidence directory](evidence/restart-2026-09-23/metadata.json).

Status: read-only source investigation and RPC observations. No restart rules have
been implemented, no signing keys accessed, and no transactions submitted. This
is not a security audit or a demonstrated production restart. The initial pass
had no Go toolchain; subsequent [synthetic tests](restart-bridge-experiment.md)
now run with a portable Go 1.21.3 toolchain. They confirm the refund mechanism,
exercise purchase construction/admission, and reproduce reconstruction defects
without changing production source. Detailed test limitations and the auto-buy
retry risk are recorded in the linked experiment report.

## Required behavior

The recovered backup need not be declared the final historical truth. Before
launch, additional independently validated history can inform the chosen restart
point. Once the community accepts a restart and begins using it, a previously
unknown incompatible continuation must not replace it merely by accumulating
greater total difficulty.

This requires an agreed, enforced restart boundary before public use. A checkpoint
at the common backup block alone cannot distinguish its competing descendants.
An exact restart-block anchor excludes incompatible old continuations, but does
not provide finality against competing descendants of that same restart block.
These are separate requirements.

Agreed scope: implement only the restart boundary and the minimum ticket
transition needed to resume. Ongoing finality redesign, changes to disputed
holdings, and unrelated consensus fixes are outside this restart investigation's
implementation scope unless separately approved.

## Live observations

Read-only JSON-RPC through the documented localhost gateway returned:

- Block: 15,130,080 (`0xe6dde0`).
- Hash: `0xe93ffded087a79097d4309c7831690161db6ed136f4b1a22c4c83a99db80f99f`.
- State root: `0x1526799d6f10f4a4467e4dd4f3b1f81ca1479822bb2c24aa541ac66f889ccffc`.
- Peer count: zero; mining: false.
- `fsn_allTickets` at that exact height: 491 tickets across eight owners.
- Earliest expiry: 2025-11-05 21:45:42 UTC.
- Latest expiry: 2025-11-06 08:43:37 UTC.

The operator reports control of the key for
`0x9fc4c40e50f902b9aa641b4a32ebaafa5c9386a1`. Key control was not independently
verified or exercised. `fsn_allTicketsByAddress` returned:

| Ticket ID | Purchase height | Start UTC | Expiry UTC |
| --- | ---: | --- | --- |
| `0x7ac0cdfed0c0337f910fcaafadbab8bb34fdf43a5b62cf446095a2f59501c293` | 15,129,832 | 2025-10-07 07:49:50 | 2025-11-06 07:49:50 |
| `0xe9d35cbc573308b366497a6f6b63e88b177652cd8696f7be6ed5a352cf89aceb` | 15,129,681 | 2025-10-07 07:17:07 | 2025-11-06 07:17:07 |

Each reports a value of 5,000 FSN. They remain recorded in the saved state;
wall-clock passage has not executed retreat or cleanup. All saved tickets are
expired relative to present-day block timestamps. Ordinary `checkTicketInfo`
validation therefore cannot authorize a present-day successor from these tickets.

Further read-only balance queries at the same height returned:

- Liquid FSN: `3225543308109480158626` base units, or
  3,225.543308109480158626 FSN.
- Raw time locks include 10,000 FSN from Unix timestamp `1762415391`
  (2025-11-06 07:49:51 UTC) through `TimeLockForever`.
- `fsn_getTimeLockValueByInterval` for 2026-09-23 00:00:00 UTC through
  2026-10-23 00:00:00 UTC returned exactly 10,000 FSN.

This establishes recorded funds covering a present-day ticket interval, not a
successful purchase or automatic conversion to liquid balance. The same raw
time-lock balance has gaps earlier in its history. A purchase spanning the old
parent time through the present cannot be assumed fundable from that balance.

## Immediate milestone: executable transition specification

One candidate is an explicitly authorized transition block at current time,
funded by ordinary signed purchases from existing balances. It is not yet a
selected or implemented protocol change. The operator's old ticket would be used
only to authorize the specified transition, not extended into renewed stake.

Second-review finding: test a short historical-timestamp bridge first. Ordinary
selection of either old ticket before its expiry would refund 5,000 FSN of
time-lock value. Independent interval arithmetic shows that adding either refund
to the saved time locks closes the coverage gap over the sampled interval through
23 October 2026. That could fund a long-lived ticket in a later bridge block.
This does not establish a valid block sequence; independent import, other-owner
effects, fees, replenishment, and cold ticket reconstruction remain untested.
See the two-candidate comparison and derived evidence in the full plan.

If the current-time transition is selected, its specification must resolve these
narrowly scoped exceptions together:

1. Allow the explicitly designated transition signer/ticket despite its expired
   timestamp, while retaining signature, selection/difficulty, and other checks
   wherever compatible. Bind the transition to the agreed parent and height.
2. For transition ticket purchases, use the transition timestamp as the timing
   reference, so existing present-day time locks can fund new tickets. Check
   RPC construction, pool admission, block execution, and replay consistency.
   Do not globally change the native-operation time reference.
3. Remove expired tickets using transition time before its successor's selection.
   Otherwise old tickets may still be chosen by `calcDisInfo`. Preserve explicit
   accounting for selected/retreated tickets, refunds, and the ordinary reward.
4. Enforce the exact accepted transition block as a separate anchor, without
   raising the legacy validation-shortcut checkpoint range. The block must be
   constructed and reviewed before its final hash is distributed for launch.

The first ordinary successor must have a live parent ticket and enough funded
purchases to satisfy finalization. The one-purchase-per-address-per-block rule
remains in force. Two tickets' worth of recorded funds is promising but does not
prove continuous mining; test replenishment, refunds, fees, and eventual expiry.

The next deliverable is a failing-then-passing test rehearsal with synthetic
keys and disposable state, followed by an isolated rehearsal against a copy of
the backup. Access to the live signing key is not needed for specification or
synthetic tests. Real-data rehearsal must use a dedicated copy, not the explorer
gateway database or preservation backup.

## Source findings

- `core/blockchain.go`, `writeBlockWithState`: canonical selection prefers greater
  total difficulty. Network population does not vote on branch selection.
- `core/headerchain.go`, `WriteHeader`: header-chain selection also uses total
  difficulty.
- `eth/downloader/downloader.go`, ancestor search: bounded ancestry can prevent
  automatic reconciliation; this is not a network-wide finality rule.
- `consensus/datong/consensus.go`, `calcBlockDifficulty`: selection uses parent
  tickets. Buying a ticket in a block cannot authorize that block.
- `checkTicketInfo`: selected-ticket expiry is checked against the new timestamp.
- `Finalize`: consumes selected/retreated tickets, uses time-lock refunds, and
  calls `UpdateTickets` with parent time. Restart accounting must cover both the
  transition block and its successors, not just bypass the first expiry check.
- `common/fsnparams.go`, `BuyTicketParam.Check`: purchase start must not exceed
  the reference timestamp by three hours. A restart that jumps time must account
  for this parent-time constraint and transaction-pool wall-clock checks.

## Existing checkpoints are not a neutral finality facility

`consensus/datong/checkpoints.go` allows custom checkpoint files. However,
`CheckPoint` reports every height at or below `LastCheckPoint` as in range,
including heights without an explicit hash entry.

In `consensus/datong/consensus.go`, `verifyHeader` returns from that path before
`verifySeal`. This omits normal ticket selection/difficulty/expiry validation
through the checkpoint range, although preceding header and signature checks
still run. In `core/block_validator.go`, `ValidateBody` skips
`ValidateRawTransaction` throughout that range. Raising the checkpoint to the
restart height therefore expands validation shortcuts; it is not just adding a
hash restriction.

Additional review concern: `reorg` builds `newChain` from tip toward ancestor,
then passes it to `CheckPointsInBlockChain`. The latter stops at the first height
above `LastCheckPoint`, so this reorg-local check can miss a lower checkpoint.
Import/header paths have separate checks; this observation does not demonstrate
an end-to-end bypass. Tests must cover pre-existing side chains and all import
paths before claiming protection.

Do not raise the current checkpoint height as a restart implementation shortcut.
Prefer a separately specified anchor/ancestry rule that leaves ordinary historical
validation unchanged and makes any exceptional transition rule explicit.

## Proposed next experiments

1. On full disposable state copies, reproduce the present-time continuation
   failure and synthetic bridge behavior already demonstrated in memory.
2. Compare an explicitly specified transition against historical-time bridging;
   audit ticket funding, refunds, expired time locks, rewards, and purchase timing.
   Candidate A now has synthetic import and purchase-admission evidence; neither
   approach has passed the full-state rehearsal or been selected for launch.
3. Enforce an agreed restart-block identity/ancestry before accepting public use.
   Define behavior for existing incompatible databases as well as fresh sync.
4. Verify rejection of a valid but heavier old continuation through full import,
   header sync, available fast-sync paths, and pre-existing side-chain selection.
5. Verify compatible descendants still undergo full validation and ordinary fork
   choice. A restart anchor must not accidentally act as a broad validation bypass.
6. Keep ordinary post-restart fork choice unchanged. Ongoing finality mechanisms
   are outside the agreed scope. Confirm that the anchor excludes incompatible
   old continuations without claiming to finalize all later descendants.

Before launch, publish the accepted history, exact transition, anchor, software
release, and validation evidence. Invite additional historical evidence before
that boundary is accepted, rather than silently changing it after economic use.
