# Historical ticket reads from the preserved backup

3 October 2026. Source baseline `c4255a21`; test and documentation changes only.
No node, observer runtime, consensus or P1–P16 patch is added.

The preserved backup can supply the launch anchor's ticket inventory, but it
cannot supply arbitrary recent historical state. Capture and preserve both
monitored wallets' observer baselines before starting recovery production.
Do not use an assumed 128-block window as a deadline for that operation.

## Observed availability

The verified LevelDB copy was opened read-only in a private mount/network
namespace. Twelve explicit heights were examined, each in a fresh process.
The unchanged `PublicFusionAPI.AllTicketsByAddress` method was called with a
test-only backend that resolves the canonical header and opens its committed
state. No node service, RPC listener, miner, signer or database copy was started.
This measures the existing API method and state availability, not transport or
the complete running-node backend. Earlier [IPC/HTTP checks](restart-observer-anchor.md)
cover the collector's actual service interaction on compact synthetic state.

| Height relative to head 15,130,080 | Heights | Ticket retrieval |
| --- | --- | --- |
| Head, head − 1, head − 127 | 15,130,080; 15,130,079; 15,129,953 | Available; 491 tickets across 8 owners at each sampled state |
| Head − 2, head − 16, head − 126 | 15,130,078; 15,130,064; 15,129,954 | Missing state-trie root |
| Head − 128, head − 1,024, head − 10,000, head − 100,000 | 15,129,952; 15,129,056; 15,120,080; 15,030,080 | Missing state-trie root |
| Older samples | 14,000,000; 1,000,000 | Missing state-trie root |

All headers were present. All unavailable-state queries returned errors and nil
inventories. A nil result without an error was observed for the donation wallet
at the three available states, correctly meaning that wallet had no tickets.
The backup wallet had two tickets at each of those states. At the head, the
complete inventory matched the previously saved gateway observation.

For each available state, the probe separately fetched the compressed ticket
blob through state storage, checked its Keccak hash against the header's
`MixDigest`, decoded it and compared the wallet inventory with the API result.
That establishes agreement with the stored commitment using the client's trie
and RLP implementation; it is not an independent implementation or a new
historical consensus audit. The counts describe state at the recorded block,
not current-time ticket eligibility or permission to sign with either wallet.

The pattern matches the non-archive [shutdown code](../core/blockchain.go),
which explicitly commits head, head − 1 and head − 127. Other states can be
flushed by time, block interval or memory pressure. Neither this sample nor
`triesInMemory = 128` promises continuous historical availability after closing
and reopening the node. Switching to archive mode later does not recreate
already missing state. Backfill of blocks/receipts also does not reconstruct
that state for the ticket RPC.

## Cost and preservation

For the three available states, the first method call with an empty process
ticket cache took 0.476–0.732 ms; repeating the backup-wallet call took
0.014–0.034 ms. The first call allocated about 332 KB across the process. It
loaded the complete 491-ticket collection before filtering to the wallet. The
head's compressed blob was 21,655 bytes; the backup-wallet map serialized to
441 bytes and the donation-wallet nil result to four bytes (`null`).

Those timings exclude database startup and JSON serialization. Operating-system
disk caches were not cleared. Database-open/identity-check time was 4.07–4.77
seconds across the twelve fresh processes, and whole-process peak RSS was
1.69–1.96 GiB. The latter includes opening the large LevelDB and the test harness;
it is not per-query memory. These are individual local samples, not a throughput,
remote latency, archive-node or concurrent-workload benchmark.

Both runs completed with all probes passing. The 56,107 source filenames, sizes
and modification times were unchanged; the source totals 117,170,022,674 logical
bytes. Read-only mounting enforced write protection for the probes. This metadata
comparison is not a repeat of the earlier full-file checksum verification.
No large disk workload was introduced.

## Launch procedure consequence

1. While the prepared nodes still expose the reviewed anchor state and production
   is stopped, initialize a separate observer history with the accepted chain,
   anchor, node names and both monitored public wallet addresses. See the
   [history initialization commands](restart-observer-history.md#operator-commands).
2. Run `--anchor-inventory <node-name>` for each monitored wallet using its
   matching configuration and explicit timeout. Require `Status: ready` and
   inspect the returned wallet, anchor hash and inventory. The donation wallet's
   empty baseline must be explicit; an unavailable read does not satisfy this step.
3. Close and reopen the history with offline `--ticket-timeline <node-name>
   --ticket-blocks 1` queries. Require a nonzero `BaselineSequence`, `Through`
   equal to the anchor and the expected inventory. Before any post-anchor block
   has been retained, `range_not_retained` is expected; it does not mean the
   baseline is missing. Conflicting/invalid/missing baselines block this check.
4. Preserve a closed copy of that small history database, the matching public
   configuration and its JSONL audit export alongside the reviewed release
   artifacts. The JSONL export alone has no supported import command. Do not
   hand-author or rewrite inventory events to fill a missing baseline.
5. Begin production only after those monitoring prerequisites and the separate
   launch gates are satisfied. Continue bounded block/receipt collection; a
   retained baseline alone does not provide subsequent history coverage.

If monitoring starts later, historical acquisition remains useful when the exact
anchor state is still available. If it is missing, use the retained observer
history or arrange a separately reviewed endpoint from a verified disposable
anchor-state copy. The original backup remains preserved. This probe is an
investigation tool, not a supported observer-history importer or node startup
procedure. Full reconstruction of pruned state is separate work.

[Evidence, measurements and runner](evidence/restart-observer-preserved-inventory-2026-10-03/README.md)
are retained. The [live competing-reorganization test](restart-observer-reorg.md)
now passes crossing-read invalidation and subsequent canonical inventory checks.
Production transport cost, concurrent workload, wider forks, history growth,
notification delivery, full financial accounting and release review remain open.
