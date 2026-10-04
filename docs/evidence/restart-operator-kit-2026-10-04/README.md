# Declared operator-kit rehearsal

This local test composes existing synthetic-history, snapshot restore, node
service and native-purchase checks with the separately built `efsn attach`
console. It is preparation for R6/R9, not a final public release or clean-machine
acceptance result.

Bounds fixed before execution: 24 shared complete synthetic blocks, four to
twelve prepared donation successors, no backup process, a flat snapshot of at
most 64 MiB, 5 GiB free-space reserve, 30 seconds per pack/restore command,
20 seconds per console command, 90 seconds for initial sync, 60 seconds each
for initial donation progress and first entrant purchase, 120 seconds for both
buyers to replenish, 30 seconds for both producers to sign, at most 64 live
blocks, and an eight-minute outer test deadline. Child service deadlines match
the outer deadline. Only enabled loopback exists in a private network namespace.

Public keys 1/2 seed ordinary synthetic history; key 1's tickets are drained
before services start. Key 2 represents donation production; key 3 represents
the entrant, endowed with 50,000 synthetic FSN at genesis. This is explicitly
test funding and no statement about real funds or a universal required reserve.

Require: immutable checksummed package -> fresh restore marker; fresh distinct
P2P identity; automatic full sync crossing the fixed test anchor; actual console
identity/funding queries and static-peer addition; actual console purchase and
successful native receipt; console mining/buying controls; both owners produce
and replenish; clean stop and cold canonical receipts/heads/state/ticket
commitments on both nodes. Audit RPCs may use the existing test API; operator
actions use production console APIs. No `lab_sync` or post-connection manual
block insertion is used. No real key, public connection or large backup copy.

The node services are embedded in the existing race-enabled test harness, which
supplies the synthetic genesis/anchor and unlocked public keys. This does not
verify final CLI node startup, compiled mainnet anchor, real key import/unlock,
production funding intervals, public download/TLS, systemd or host restart.
Those remain final selected-release/host acceptance. This is a fresh datadir on
the existing WSL host, not a new independent machine.

Build source starts from the verified final automatic-sync tree; only the new
test and subcase registration change. Reuse and verify the previously extracted
normal node executable for console calls. Retain source inventories, inputs,
binary identities, logs and failures in separate attempt directories.

Attempt 1 stopped during seed construction in 0.24 seconds: the one-ticket
reserve can leave an owner at zero after the last block, violating the existing
seed helper's positive-reserve precondition. Attempt 2 uses that helper's existing
two-ticket setup. No assertion, timer, production source or launch rule changes.

Attempt 2 passed seed preparation, then stopped before packaging: the earlier
source extraction did not include `snapshot_package.py`. Attempt 3 copies that
existing, unchanged Python helper as an additional recorded build/test input.

Attempt 3 passed in 127.86 seconds. Review then identified that post-stop chain
settling could invalidate an earlier live observation of both producers or
purchases. Attempt 4 repeats those assertions against the settled canonical
suffix and both cold services, including successful native logs for every
purchase, retention of the first entrant transaction, both later producers and
replenishers, and unchanged cold nonce/saved purchase bytes. This tightens
acceptance without changing production code, funding, timing or fork bounds.

Attempt 4 passes in 117.07 seconds (120.21 seconds including process teardown).
It restores five files / 65,563 bytes; the settled and cold head is 34. No selected
case is skipped and no race report occurs. Source/executable readback and all
attempt outcomes are checked in `verify-results.py` and `acceptance.json`.
