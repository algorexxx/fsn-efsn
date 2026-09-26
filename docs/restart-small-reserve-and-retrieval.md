# Purchase retrieval and small ticket reserves

26 September 2026, baseline `c79b227`. Tests, evidence and documentation only;
production patches remain P1–P15. This extends the
[live manual-repair experiment](restart-live-nonce-repair.md).

## Existing retrieval paths

The actual-node nonce-rollback case now queries the discarded block through
normal RPC, both before and after a cold restart. For the missing nonce-15
purchase, `eth_getRawTransactionByHash` and `eth_getTransactionReceipt` return no
result. `eth_getBlockByHash` still returns the original block and its transaction
hashes. `eth_getRawTransactionByBlockHashAndIndex` returns the exact 122 signed
bytes; decoding them preserves the original hash and nonce. The canonical
block-number lookup identifies the replacement block instead. An unknown block
hash and an out-of-range transaction index return no bytes.

After the cold check, the test submits the RPC-retrieved transaction through the
ordinary raw-transaction API and verifies native purchase success. The retained
automatic successor recovers unchanged. This case passes in 54.48 seconds; the
default complete-history fixture also passes in the same parent process (4.17
seconds, 58.66 seconds total), with no race reports.

The saved automatic intent has a separate existing access path: `efsn db get`.
A test builds the actual production command with race detection, writes a signed
public-test-key purchase into a tiny disposable database, closes the database,
and invokes the command. It returns the exact signed bytes without changing any
chain-database file hash. A missing record exits unsuccessfully without changing
those files; an open writer's database lock also prevents extraction. The record
remains intact. This command test passes in 1.86 seconds with no race report.
It does not add a public RPC method or alter the saved-record format.

For an operator, the two retrieval paths serve different purposes:

1. Preserve old head/block hashes before a reorganization or from retained logs.
   Query the old block by hash, find the relevant owner's transaction index, and
   retrieve its raw bytes by that block hash and index. Check decoded sender,
   nonce, chain ID, native payload and hash before considering resubmission.
   A discarded block's transaction is not proof of canonical inclusion.
2. For the latest local automatic intent, cleanly stop the node and use the
   reviewed executable against its actual datadir, with matching network/path
   configuration and `--syncmode full`. The key is ASCII `fsn-auto-ticket-v1-`
   followed by the wallet's raw 20-byte public address, not its ASCII hex text:

   ```text
   efsn --datadir <stopped-datadir> --syncmode full db get 0x66736e2d6175746f2d7469636b65742d76312d<40-address-hex-digits>
   ```

   The output is `key 0xKEY: 0xSIGNED_TRANSACTION`. Preserve and decode the value;
   do not delete the record to clear a warning. This is an offline inspection
   step and requires clean shutdown, not just `miner_stop`.
3. Confirm the canonical nonce, pool contents, interval validity and funding on
   the current branch. Resubmit missing purchases individually and require
   canonical native-success logs before advancing. Then verify the exact saved
   intent and fresh automatic successors. Keep another eligible signer available
   while inspecting a stopped node if continued block production is required.

Old block bodies must still exist. This does not prove recovery after pruning,
rewind deletion or loss of the old block hashes. The saved record contains the
current intent, not every previous purchase. A missing, corrupt or conflicting
record requires separate review; `db get` is an exact-byte reader, not a semantic
validator or an automatic repair tool.

## Small-reserve construction

The complete synthetic devnet fixture now has an optional setup purchase limit.
The existing generous fixture retains its behavior. The small case allocates
12,020.102 synthetic FSN to each public wallet, executes/imports all 24 setup
blocks independently in both databases, and buys only while an owner's stored
ticket count is below two. It asserts one or two tickets per owner at the anchor.
There is no ticket deletion, post-genesis balance overwrite or fabricated
consensus weight. The genesis retains its two synthetic bootstrap tickets.

The live workers and automatic buyers have no new ticket cap. They use ordinary
funding checks, ticket selection, rewards, refunds, retreats, networking and
retry behavior. The test runs the same 90-second outage, reconnection and
sequential-repair procedure. It now records zero-ticket owners without aborting
while another owner still has valid tickets. Before each repair submission it
logs liquid balance, time locks and whether they cover the purchase interval at
the current wall clock. Native pool admission remains the deciding check.

The numeric initial balance matches the preserved donation balance, but this is
not a complete-state donation-wallet replay. Synthetic genesis tickets, devnet
heights/rewards, setup purchases and two similarly funded wallets differ from
the real launch. It cannot establish a required production reserve by itself.

## Results

The initial small case fails its manual-repair requirement after 185.60 seconds.
After 90.14 seconds of packet loss (44 drops), the isolated heads are 33 and 34.
Each isolated branch has removed the other owner's tickets. After ordinary
reconnection both nodes reach block 38, but wallet 1 remains at canonical nonce
15 with saved nonce 22 and an empty pool. The common block-37 snapshot has zero
wallet-1 tickets and one wallet-2 ticket. Both mining and buyer flags are enabled.

The first missing purchase is rejected by normal pool admission:

```text
insufficient balance(2057601957656000000000), need 5000000042448000000000
```

That is about 2,057.60 liquid FSN available versus 5,000.000042448 required. No
manual repair, saved-intent inclusion, fresh successors or cold acceptance is
claimed for this run. The advancing peer remains available, but original signed
bytes and an eligible producer alone do not guarantee that repair is fundable.

The final diagnostic small case also fails (173.88 seconds). Its 90.16-second
outage drops 44 packets; both isolated heads reach 33. After reconnection both
nodes report block 36, hash
`0x963e9b781b81fbcaa9584c19f71eadfa8bacb7861b38009ef27fad4e929a1299`.
Wallet 1 is at nonce 18 with saved nonce 24 and no pending purchase. The common
block-35 ticket snapshot again shows zero tickets for wallet 1 and one for wallet
2. The first repair submission is rejected with 2,065.10195768 liquid FSN against
the same 5,000.000042448 requirement. Its time-lock entries start at Unix times
1,793,042,189 and 1,793,042,212, each for 5,000 FSN through `TimeLockForever`.
Those future intervals do not cover the current purchase interval; their nominal
sum is not spendable current stake. The diagnostic explicitly confirms inadequate
interval coverage. No repair purchase is admitted in either small run.

The final generous-reserve regression passes in 338.64 seconds. Wallet 2's
missing nonces 28–32 are resubmitted individually; the exact saved nonce-33
purchase executes at block 42 and two fresh automatic successors follow. Both
cold databases agree at block 46,
`0xaf8e00ca440f010337158a971861240cc82ad31743770b19bf02e182a6a64eb5`,
and retain all eight checked native-success receipts. Canonical wallet nonces
are 44 and 37; saved bytes survive and the cold pools start empty. The state root
is `0x2f1adfc3d1cd50064437e57342a522dcd8acb124a5bcfde4db753eaa91048d58`
and ticket root
`0xe31e07f6e2a0431d7270cfbb4f34ae5711644f63e718fd1d0d32ca1ed3bf49a5`.

| Check | Result |
| --- | --- |
| RPC retrieval/repair plus default complete fixture | Pass, 58.66 s total |
| Existing offline saved-record command | Pass, 1.86 s |
| Initial generous repair repeat | Fail, 161.37 s; overly strict worker-state assertion |
| Final generous repair repeat | Pass, 338.64 s; five repaired nonces, fresh successors and cold receipts |
| Initial small-reserve repair | Fail, 185.60 s; first submission cannot be funded |
| Final small-reserve repair | Fail, 173.88 s; funding failure confirmed with interval snapshots |

No completed run reports a data race. Both small-reserve failures remain failures
of the repair requirement, not successful availability checks. The ordinary
unattended-replenishment limitation is unchanged. No broad-suite or native Windows
pass is claimed.

The first generous-reserve repeat exposed an overly strict test assertion:
`miner/miner.go` normally stops the worker on a downloader start event and resumes
it automatically after sync. The sampled pause caused a failure after 161.37
seconds; the log records `Mining aborted due to sync`. That failure is retained.
The corrected repair observer keeps auto-buy enabled, allows at most 30 seconds
for automatic worker resumption, and requires both workers running before it
accepts a stable nonce gap. It sends no extra start/stop or force-sync command.
This is a harness correction, not a runtime change or a successful repair result.
The final small run actually observes this pause and automatic resumption after
253.97 milliseconds before reaching the funding rejection. Auto-buy remains
enabled throughout that sampled pause.

The first command-test approach was also retained: an offline build lacked two
already-pinned dependencies; after caching those versions, the inherited
`cmd/efsn` test package failed to compile because three older tests reference an
undefined `tmpdir`. This work does not fix or claim that suite passes. The final
test instead invokes the actual built `efsn` executable from the isolated
restart harness. Dependencies and production source remain unchanged.

## Release implications

The earlier generous-reserve manual pass is conditional on usable stake and
funding. A successful initial launch with 12,020.102 FSN does not establish
post-partition purchase recovery for that wallet. Monitor eligible ticket count
and purchase funding as well as peers, heads and nonce progression. Keep the
choice between monitored manual repair and a separately reviewed recovery
mechanism open; neither automatically restores unavailable funds.

The [funded-repair follow-up](restart-funded-repair.md) now reconciles first-retreat
losses, selected-ticket returns, rewards, fees and transfers across future
intervals. It tests one ordinary 5,000-FSN transfer and explicitly retains failed
immediate/60-second repair attempts. Starting ticket inventory and the timing of
ordinary returns matter; this evidence does not establish a universal reserve.
Resolve the zero-ticket/two-retreat case and relate reserves to complete-state
launch accounting. These results do not justify a free ticket, refund-rule
change, confiscation or new consensus rule.

Raw attempts, source identities and checksums are in
[`restart-small-reserve-2026-09-26`](evidence/restart-small-reserve-2026-09-26).
No production key, preserved backup, public peer or W: dataset is accessed.
