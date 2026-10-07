# F11 block import — retained first attempt

7 October 2026. All 16 baseline subtests stopped at import header validation
with invalid baseFee: have 0, want 1000000000. No block was accepted and the
candidate was not run. This is a fixture error, not a runtime finding.

The transaction-only fixture allowed an arbitrary zero-base-fee context. The
block fixture mistakenly retained it. consensus/misc/eip1559.go explicitly
requires 1 gwei before ECO and a 1-gwei floor for decreasing fees after ECO.
This parent has zero gas use, so a 1-gwei base fee is required.

The second attempt sets parent/child base fees and transaction gas prices to
one gwei, increases sender funding to 1000000000000000 base units, and derives
expected balances from the same gas-unit counts. The one-unit prior transfer
is unchanged. No consensus check is skipped or weakened. The exact fixture
patch is retained in the [second attempt](../restart-state-rollback-block-v2-2026-10-07/README.md).
