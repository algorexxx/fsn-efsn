# F11 transaction finalization and persistence

7 October 2026. Bounded phase-4 transaction check against the selected
P1–P17+B1+D1 recovery tree and the unchanged, unselected F11 candidate overlay.
One top-level test and 16 subtests pass per selection with race detection.
The production selection and activation schedule are unchanged.

## Result

The inherited absent-entry defect can reach durable account state in this
synthetic two-transaction fixture. A successful earlier transaction changes
the child account, leaving it pending and dirty after transaction finalization.
A later reverted call leaves an extra nil ordinary-balance entry in memory.
Commit, trie flush, LevelDB close/reopen and a new state cache restore that
extra entry as an ordinary zero. The time lock remains intact.

With the candidate active, the extra entry is absent and the committed state
root differs. With the candidate disabled or before activation, behavior and
roots match the selected baseline. This is evidence that the correction can
change transaction-derived state roots; it supports the explicit activation
requirement. It does not establish that this happened in accepted history.

| Case | Baseline / inactive candidate | Active candidate | Root comparison |
| --- | --- | --- | --- |
| Revert; child initially clean; ordinary entry absent | Nil entry after transaction; no extra entry after reopening | No extra entry at either observation | Equal |
| Revert; preceding transaction changed child; ordinary entry absent | Nil entry after transaction; zero entry after reopening | No extra entry at either observation | Different |
| Revert; preceding transaction changed child; ordinary zero entry pre-exists | Original zero entry retained | Same | Equal |
| Successful deletion after preceding transaction | Child absent after finalization and reopening; beneficiary receives its ordinary FSN | Same | Equal |

All four cases run with no schedule, one block before, at and one block after
the fixture schedule, using London gas rules. The 16 observation pairs have
12 exact matches and four intended differences: the absent-entry revert cases
at/after activation. Only the two dirty-account pairs have different roots.
Gas, receipts, sender nonce/balance, fee recipient, beneficiary, code, storage,
child nonce and time locks match literal expectations in both selections.
The deletion control establishes logical account removal from the state trie,
not physical erasure of historical database data.

## Execution and expectations

[transaction_persistence_test.go](transaction_persistence_test.go) submits
synthetically signed transactions through the actual core.ApplyTransaction
path, including transaction finalization. It uses recovery.NewReader for the
chain context. The account is loaded from a committed seed root into a fresh
cache before execution; setup does not leave it dirty. The prior transaction
transfers one base unit and terminates normally. The tested transaction calls
the same small deletion/parent-revert fixture used in the earlier phase.

[inspect_state_test.go](inspect_state_test.go) is a test-only observation seam:
it reads the raw ordinary/time-lock arrays and journal/pending/dirty membership.
It does not substitute any runtime state operation. After each transaction
sequence, StateDB.Commit and TrieDB.Commit write the root; the LevelDB handle
is closed and reopened read-only, with a new state cache. This is database
reopening within one process, not a fresh node process or a crash/power-loss test.

[gas-vector.json](gas-vector.json) records independent arithmetic. The tested
transaction uses 21,000 intrinsic gas plus the preceding phase's 5,139 warm
execution gas, 2,500 for the cold child, 2,600 for the cold beneficiary, and
19 for the added child branch: 31,258 total. The preceding transaction uses
21,000 + 16 for one nonzero data byte + 18 for its branch: 21,034. London gives
no deletion refund. Gas price is one base unit, and Fusion credits the full
fee to the miner. The expected sender balances are 968,742 without the prior
transaction and 947,707 with it; total fees are 31,258 and 52,292 respectively.
No observed root was copied into an expected root constant: root comparison
is between selections, while account contents and receipt/gas expectations
are independently specified in the fixture.

The [first attempt](../restart-state-rollback-persistence-2026-10-07/README.md)
is preserved with its failed baseline run. Its sole mismatch was nil versus
an empty slice in the expected empty time-lock list. The decoder explicitly
uses reflect.MakeSlice for an empty RLP list (rlp/decode.go:307–315).
[fixture-correction.patch](fixture-correction.patch) changes only this expected
representation; all balance, gas, receipt and persistence expectations remain
as stated before the first run. Candidate execution was skipped in that attempt.

## Provenance and limits

[run.py](run.py) records source/overlay hashes, actual commands, timestamps,
Go environment, exits and free-space checks. [launch.py](launch.py) runs the
unprivileged rehearsal user inside a private network namespace; the recorded
parent and child namespace IDs differ and the only link is loopback, down.
Offline dependency flags supplement that isolation. No public peer/RPC or real
wallet key is used; the transaction signer is the public synthetic scalar two.
Each selection uses two workers, a two-minute Go timeout and a seven-minute
outer limit. Temporary LevelDB fixtures require no restore or large disk job.

[verify.py](verify.py) checks 191 prior evidence files, all 27 retained overlay
input bindings, 19 source/module hashes, the exact fixture correction, every
observation pair and the permitted root differences. Results are retained in
[verification.json](verification.json). SHA256SUMS covers this bundle; prior
evidence and selected runtime files remain unchanged.

The synthetic parent header is installed directly in the fixture database.
No block was mined, sealed, validated or accepted through InsertChain in this
experiment. Consensus rewards, ticket finalization, block/receipt commitments,
cross-node import, pending/RPC/tracing paths and historical replay are outside
this result. Berlin execution is covered by phase 3, not by this persistence
matrix. F11-b is unchanged and remains separately classified.

Next, qualify Prepare → ApplyTransaction → DaTong.Finalize and serialized
InsertChain processing on independent disposable chains, then reopen the
receiver and check its canonical head, state, receipts and tickets. Reuse the
existing restart block-fixture approach, but bind it to the recorded selected
source and candidate inputs. Include dirty and clean absent-entry cases plus
controls across the activation boundary. A synthetic checkpoint must remain
explicitly identified; it cannot stand in for historical-chain verification.
F11 remains open pending that work, supported-path coverage, historical
compatibility and independent consensus review. No production height is chosen.
