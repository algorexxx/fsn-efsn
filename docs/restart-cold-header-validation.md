# Cold header validation and the launch synchronization path

25 September 2026, candidate baseline `04ad861`. This investigation adds tests
and documentation only. The permanent patch inventory remains P1–P9.

## Finding

The earlier three-header test in [P9's evidence](restart-parent-isolation.md)
shares a process with its block builder. The global ticket cache can supply the
successor ticket sets, even though the receiving database lacks those states.
That test proves explicit parent routing with those cached sets; it does not
prove that a newly started node can validate the same headers from headers alone.

Fresh-process checks now establish the distinction. After a known state,
validating the first new header succeeds. Validating the second needs the ticket
set after the first block's purchases and ticket removals. Headers alone do not
contain the purchase data needed to reconstruct that set. The existing commitment
check refuses the incomplete reconstruction with `AddCachedTickets: hash mismatch`.

The same eight cases have the same outcomes with the three P9 runtime files
replaced by their pre-P9 versions from `bcbd1ce`. This limitation predates P9.
No validation bypass or new runtime correction is added here.

## Fresh-process matrix

Each scenario starts with a separate small LevelDB containing a common synthetic
anchor and its account state. A builder produces three valid successor blocks,
each containing a ticket purchase, and exports them through RLP. The checking
process asserts that none of their ticket sets is already cached and none of
their account-state roots is available locally. Each scenario uses a new process
and database; a separate process also checks the result of full import.

| Data or operation | Observed outcome |
| --- | --- |
| Three unstored headers only | Reject second header: ticket commitment mismatch |
| Stored headers and receipts, without bodies | Reject second header: receipt metadata cannot be derived without the corresponding body; ticket commitment mismatch |
| Stored headers and bodies, without receipts | Reject second header: ticket commitment mismatch |
| Stored headers, bodies and receipts, without successor account states | Validate all three: reconstruct ticket sets from the known state and native receipt logs, checking commitments |
| Stored headers/bodies and later receipts, but first successor's receipt absent | Reject second header: ticket commitment mismatch |
| Insert first header alone, then validate second alone | First insertion succeeds; second rejects with the same mismatch. Splitting batches does not supply the missing purchase data |
| Second header has gas used above its gas limit | Reject at index 1 with the expected gas-limit error |
| Full import of the three blocks, then cold reopen | Execute/import all three; canonical indexes, available state roots, ticket commitments, successful receipts and persisted full/header/fast heads agree |

Header validation leaves the full and fast heads at the anchor. The incremental
case advances the header head only for its explicitly inserted first header;
the subsequent rejection does not advance it again. Other validation cases
leave the header head unchanged. A passing characterization of a rejection is
not a claim that headers-only synchronization succeeded.

Current Windows: eight cases pass in 1.69 seconds. Pre-P9 overlay on Windows:
eight cases pass in 1.55 seconds. Current Linux with race detection: eight cases
pass in 16.11 seconds, including the separate cold reopen. Raw results, overlay
source identities, commands, binaries' hashes and checksums are in
[`restart-cold-headers-2026-09-25`](evidence/restart-cold-headers-2026-09-25).

## Release implication

Use full block synchronization from a verified restored state as the launch
candidate path. Normal execution supplies each parent's ticket state before
checking its child. The previously passing actual-peer rehearsals also use this
full-sync path. This bounded three-block test does not establish full historical
replay or synchronization from genesis.

The source already makes this distinction:

- `eth/downloader/modes.go`: `FastSyncSupported()` returns `false`, including in
  original `master` at `c5f0174`.
- `eth/ethconfig/config.go`: the configured default is `downloader.FullSync`.
- `eth/sync.go`: the normal peer scheduler starts with full sync; the fast-sync
  branch is behind `FastSyncSupported()`.
- `eth/downloader/downloader.go`: immediate header-chain insertion belongs to
  the fast/light branches. Full sync schedules bodies and executes blocks.
- `light/lightchain.go`: the restart candidate refuses light mode when an
  anchor is configured.

The mode parser still recognizes `fast` and lower-level fast/receipt/pivot APIs
still exist. This is not evidence that the CLI rejects every unsupported mode,
nor an end-to-end fast-sync test. Launch configuration should explicitly use
`--syncmode full`; do not advertise fast/light state acquisition based on the
presence of those APIs or the earlier warm-cache header check.

Supplying bodies and receipts directly in the reconstruction test is controlled
fixture preparation, not a new trust model for downloaded receipts or a tested
network state-acquisition protocol. The test does not establish how a release
would securely acquire all those artifacts. Public download/distribution,
full-history continuation, pruning/freezer behavior and independent validation
review remain separate gates. No preserved backup, real key or W: restore was
accessed, and no large dataset was copied.
