# Remove the shared DaTong parent-header context

25 September 2026. Baseline `bcbd1ce`; additional permanent candidate **P9**.
This is a concurrency/availability correction, not new finality or ticket policy.

## Reproduction

The [two-miner investigation](restart-purchase-nonce-rollback.md) initially
completed with no race warning. A repeated run still converged and produced
valid purchases, but Linux's race detector reported concurrent writes from
`core.BlockChain.insertChain` through `datong.SetHeaders` and reads from
`DaTong.Finalize` in the real miner worker. Both stacks are retained in
[`pre-fix-competing-race.txt`](evidence/restart-purchase-rollback-2026-09-25/pre-fix-competing-race.txt).
An earlier passing run did not rule out the race.

The original `master` at `c5f0174` already contains the package-global
`glb_parents`, its setter, and the reads in `VerifyHeader` and `Finalize`.
The global list belongs to whichever import most recently assigned it. It does
not belong to the particular branch, chain instance or mining operation reading
it. Adding a mutex alone would not fix that ownership error.

A deterministic regression pauses a real two-block batch import immediately
before processing its second block. While the import has its parent context set,
another fixture verifies and finalizes a valid block on a different branch.
Both operations fail with `unknown ancestor` before the correction. The test
then releases the import and requires it to finish normally. The channel
barrier makes this a functional isolation test, independent of whether the race
detector happens to catch a simultaneous memory access.

The existing parent hash/height check prevents using a mismatching parent.
The reproduced effect is erroneous rejection of valid concurrent work, alongside
the data race. Invalid-block acceptance or persistent state corruption was not
demonstrated and is not claimed.

## Narrow correction

- `consensus/datong/consensus.go`: remove the global parent list and setter.
  Single-header verification and finalization resolve their own parent through
  the supplied chain reader using the existing hash/height checks.
- `core/blockchain.go`: remove the four global setter calls around verification
  and processing. Full block import persists each processed block before moving
  to its child, so the previous parent is available through the chain reader.
- `core/headerchain.go`: use the existing `Engine.VerifyHeaders` API and consume
  its indexed results. That API passes the current batch's parent prefix
  explicitly, which remains necessary for headers not yet in the database.
  Existing interruption, banned-hash and checkpoint checks remain in place.

The runtime diff adds five lines and removes twenty-two across those three
files. It retains parent validation, difficulty, ticket selection, expiry,
rewards, transaction encoding and anchor policy. It changes concurrent valid
work from accidental cross-branch rejection to use of the correct parent.
`SetHeaders` is removed as a Go API; all in-repository callers, including the
obsolete test reset, are updated. External code calling that setter would need
to use the existing explicit batch API or its own chain reader.

## Verification and limits

The deterministic isolation regression fails in both independent operations
before the fix, then passes five times on Windows and five times under Linux's
race detector. A companion test verifies three linked headers absent from the
receiver database, requires successful batch validation and checks that
validation does not persist them or advance the full head. It also passes five
times on each platform. This specifically guards the header-batch behavior
while removing the global state.

That original batch test shares the builder's process and ticket cache. The
[cold-process follow-up](restart-cold-header-validation.md) now distinguishes
parent routing from state availability: headers alone reject a missing purchase
history both before and after P9; stored bodies/receipts permit reconstruction,
and full block import plus cold reopen succeeds.

The corrected real competing-miner rehearsal passes under the race detector
(98.37 seconds). Both wallets continue purchasing after their forks converge.
The existing nine anchor-entry characterizations also pass, including header,
receipt, stored-fork and startup paths. Five actual-node regressions pass together
in 79.68 seconds: mining/crash readiness, compatible peer synchronization, the
two-purchase nonce rollback and repair (49.95 seconds), a heavier stored fork,
and rejection of an incompatible database at startup. The last case deliberately
expects a child process to fail; the enclosing assertion passes.

An attempted broader `core` package run is **not passing**: it fails to compile
in unchanged `core/bench_test.go`, which still calls obsolete `IntrinsicGas`,
`CalcGasLimit`, `ethdb.NewMemDatabase` and related APIs. The requested test filter
cannot avoid compiling that file. These files/signatures were not changed in
this correction. The failure is retained rather than excluding or rewriting
legacy tests to claim a green suite.

The new tests use public keys and disposable synthetic databases. They do not
replace full historical replay, full-history synchronization, extended network
stress or independent consensus review. P9 must be reviewed separately from
P2's expiry reconstruction and P3's receipt copying, despite nearby code paths.

Commands, failing baseline, final source identities, binary hashes and raw
results are in
[`restart-parent-isolation-2026-09-25`](evidence/restart-parent-isolation-2026-09-25).
