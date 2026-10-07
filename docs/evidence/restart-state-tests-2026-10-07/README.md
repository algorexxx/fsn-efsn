# State fixture qualification

7 October 2026. Port the existing core/state test suite to the selected Fusion
APIs without changing runtime code or its expectations to match observed output.
Retain original failures from the preceding language/default review. Use the
same test-only overlay against both immutable D1 and experimental x/text source
trees, Go 1.27.1, two workers, race detection, offline dependencies and a private
network namespace. Limit each package run to five minutes and each invocation
to seven minutes. Require 30 GiB Linux / 60 GiB D: free; no blockchain data copy,
private key, actual wallet or public service is involved.

Preserve the original sync ordering/delay/incomplete-subtrie cases. Adapt only
the test transport to separate node/code queues and the current batch API.
Calculate the Fusion dump fixture independently of efsn's state/trie/RLP code,
first validating the calculation against the original Ethereum fixture root.
Record failures and any newly exposed runtime behavior before deciding whether
it is a fixture problem. Do not relax assertions to make the suite pass.

## Result

The compilation gap is repaired, but the state suite does **not** pass. The
final active five-file test overlay is preserved in `qualified/`: 15 top-level
tests pass and three fail on each build, with race detection, no skips and no
race report. The gocheck aggregate includes five passing cases. Runs complete
in 3.840 seconds on D1 and 3.813 seconds on the text experiment. These identical
failures are inherited state rollback defects, now tracked as F11. They are
not evidence that the language/dependency experiment introduced a regression.

No runtime file or module manifest changed. P1-P17+B1+D1 remains selected and
the text update remains unselected. `report.py` checks the immutable source
inventories and prior binary hashes through the preceding report, verifies
seven relevant source files byte-for-byte against upstream
`c5f0174d88ab2b9c3086c6a9cc9ccf38a072992f`, and records the one production
`Suicide` call in the selected source. Its checks only read saved evidence;
they do not execute the node or rerun the tests.

## Test repairs and independent expectations

Four existing files now use the actual memory database, explicit FSN asset ID,
ticket-root constructor argument, dump configuration and iterator APIs. Sync
fixtures retain the original ordering, batching, delay and incomplete-subtrie
checks while using separate code/node queues and batch commits. Iterator
coverage accounts for prefixed contract-code keys. This is internal state-sync
coverage, not approval to support fast/light sync at launch.

`dump-vector.go` implements a small independent RLP/MPT calculation for the
original three-account fixture. It imports no efsn state, trie or RLP code. It
checks known empty Keccak/trie values, then reproduces the original Ethereum
root before using Fusion's eight-field account encoding. Its independently
calculated Fusion root is
`09c81cf1049993c874a455403e5e8440c32ba09a4356f98bb443a127d6a9f2a2`.
`dump-vector.json` was generated before executing the repaired state suite.
The dump test compares the complete decoded JSON documents to avoid property
ordering and whitespace differences. The report checks the saved literal
against the independent output. The generator was run with the selected
Go compiler, cached D1 module context, `GOPROXY=off`, `GOSUMDB=off`, two workers,
and a 90-second limit in the private network namespace.

The randomized snapshot test also had two harness defects: generated arguments
used values as indexes and a global RNG, and its reverse storage comparison
compared the reference state with itself. Correcting those uses the supplied
RNG with seed 1 and retains the 1,000-case maximum. The retained failure occurs
before that maximum, so this is not 1,000 passing cases.

## F11: inherited snapshot restoration defects

The direct tests use newly created in-memory accounts with synthetic addresses
and amounts. Expected state is the literal state before the snapshot.

- With no balance entries, marking an account for deletion appends no deletion
  journal record. Reverting its snapshot retains the deletion flag. The seeded
  existing test and the new minimal case both fail on this behavior. A control
  that first reads the FSN balance passes. The production EVM caller reads that
  balance before deletion, so the no-entry direct-API failure alone does not
  prove an ordinary EVM transaction can retain the deletion flag.
- A time-locked asset's deletion journal entry omits its time-lock discriminator.
  Reversion consequently treats it as an ordinary balance entry. For an asset
  without an ordinary balance, the minimal fixture restores its time lock but
  also adds a nil ordinary balance. This violates the pre-snapshot state.

These are transaction-state snapshots, distinct from the chain fork-choice
or fixed-anchor design. Correcting runtime behavior could change execution
results and requires explicit historical compatibility and activation review.
No correction, activation height or waiver is selected here.

## Retained phases and unfinished follow-up

| Folder | What it records | Status |
| --- | --- | --- |
| `api/` | Four existing tests ported; original seeded snapshot failure | 15 top-level passes, one failure per build |
| `qualified/` | Same suite plus two minimal state-API regressions | 15 top-level passes, three failures per build; final active test files |
| `verified/` | Additional synthetic local EVM call/parent-rollback probe | Incomplete; initial assertion mistake and a runtime panic retained |

The phase names are historical directory labels, not acceptance claims.
The EVM probe's successful-parent control passed. Its reverted-FSN control
incorrectly expected a zero entry from `GetAllBalances`; source inspection
shows that this API omits zero balances. The other-asset case panicked while
reading balances through `CopyBalances` after the EVM call returned. Both
versions show that outcome, consistent with the independently proven nil
entry, but the panic prevents later assertions from completing. Do not count
this as a completed EVM regression or proof of an accepted-block failure.

The user reported repeated Astra/Daybreak content restrictions during this
follow-up. Further failure-reproduction runs stopped. The incomplete EVM test
was removed from the active package and preserved with its exact overlay,
patch and logs in `verified/`; the established five-file state suite remains
unchanged from `qualified/`. No attempt to change model/access controls or
disguise the blocked work was made. EVM fixture correction and completed
transaction-impact checks remain pending; saved failures have not been waived.

Next technical work on this finding is a narrowly reviewed runtime disposition:
correct the observation contract, establish transaction/commit effects in an
authorized testing context, and specify any correction's historical boundary
before changing production code. Other F1 console/tracer/RPC coverage and F10
dependency/CI acceptance remain open. The 3,600,000-block baseline replay
checkpoint and original backup are unchanged; no large disk workload ran.

The saved overlays and patches are the exact inputs for each phase.
`port-api.py` preserves only the initial mechanical editing helper; it is
not the complete migration or a script to rerun on the current checkout.
