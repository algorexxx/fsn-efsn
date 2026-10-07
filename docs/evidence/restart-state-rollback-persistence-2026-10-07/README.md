# F11 transaction persistence — retained first attempt

7 October 2026. Baseline ran; candidate was not run because the phase stopped
on the unexpected baseline result. Twelve reverting subtests failed only on
the expected representation of an empty time-lock item list; four successful
deletion controls passed. This is not a qualification pass.

The test seeded an empty time lock with a nil Items slice and expected that
same Go representation after loading the seeded trie. rlp/decode.go,
decodeListSlice, explicitly constructs a non-nil zero-length slice for an
empty RLP list. Consequently the fixture expectation was incorrect. Comparing
all twelve mismatch objects found exactly two differences per object:
AfterTransaction.TimeLocks[1].Items and Reopened.TimeLocks[1].Items were []
rather than nil. No balance, gas, receipt or dirty-state expectation differed.

The sources, overlay hashes, logs, environment and failed result here are
preserved. The [second attempt](../restart-state-rollback-persistence-v2-2026-10-07/README.md)
changes only that fixture expectation and records the exact patch. No runtime
source or release selection was changed.
