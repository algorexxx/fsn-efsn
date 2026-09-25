# Complete-state recovery command rehearsal

25 September 2026, following `04a676c`. The Windows and Linux recovery
executables are the exact binaries recorded in the preceding
[operator workflow](restart-operator-workflow.md). This follow-up changes tests
and documentation only; it adds no node or recovery-tool behavior.

## Scope

Each platform starts with three fresh copies of the 528,817,080-byte compact
preserved-state export: reference, working and verifier. All 230 files are
verified against the original pinned manifest before use. The copies contain
complete preserved account state plus the previously reviewed historical context,
not the complete block-history/index database for a publicly downloadable node.

Preparation reuses the explicitly accounted substitutions from the
[complete-state handover](restart-full-state-handover.md): backup ticket/funding
ownership moves to public scalar 1; the preserved donation balance moves to
public scalar 2. No real private key is used. These substitutions and synthetic
parent hashes are test scaffolding, not a proposed mainnet state edit.

The reference builder constructs the three previously reviewed handover blocks.
The actual command executable then performs review, approval preparation,
journal initialization, encrypted-key signing and export on the working copy.
All reviewed unsigned bytes and exported signed bytes must match the reference.

For each block, both working and verifier imports run in separate processes.
Each is then reopened in another fresh process and checked again. This prevents
the imports from inheriting the reference builder's process-global caches.
There are twelve import/cold-check processes per platform. They run the same
client implementation; this is process independence, not a second implementation.

## Results

| Check | Windows | Linux with race detection |
| --- | --- | --- |
| Small-state command regression with separate imports/cold checks | PASS, 4.42 s | PASS, 41.00 s |
| Complete-state command workflow, three blocks | PASS, 11.72 s | PASS, 120.23 s |
| Exact command output, independent import and complete changed-account ledger agreement | PASS | PASS |
| Wrong password leaves no reservation; completed repeat needs no key; altered report/export rejected | PASS | PASS |
| Source database files unchanged by command operations before import | PASS | PASS |

Both platforms produce identical plans, reports, purchase transactions and signed
blocks. Their approval files intentionally differ in the executable SHA-256 pin.
The eleven reference plans/blocks/ledgers/substitution records are byte-identical
to the earlier complete-state offline rehearsal, so those records are referenced
by hash instead of duplicated. Every original compact-source file is rechecked
afterward and remains unchanged.

The owner-by-owner audit again accounts for future FSN rights across liquid
balances, time locks and tickets, including ordinary fees, rewards and retreat
penalties. Ticket counts after the three blocks are 485, 480 and 1; changed
account counts are 8, 2 and 2. The retired signer's account remains unchanged in
the two donation-signer blocks. Unrelated assets, code, storage, notation and
nonces are checked in the account-difference ledger.

## Limits and next work

This closes the complete-state integration gap for the existing operator
commands. It does not repeat the complete trie traversal, extend historical
replay, add new forced-crash cuts or test machine power loss. Earlier
[offline interruption tests](restart-offline-signing.md) and
[credential preflight tests](restart-operator-workflow.md) remain separate
evidence. Linux command and import children use an isolated network namespace;
all tests use public keys and disposable C: data. No W: data, original 117 GB
database, live gateway, replay checkpoint or production wallet is opened.

Actual-address accounting with fresh launch timing, live backup purchase
inventory/drain, one-active-key custody, final anchor and release/data
distribution remain unfinished. The source patch candidates are now explicitly
listed for independent review in the [node patch inventory](restart-node-patch-review.md).
The subsequent [automatic-purchase interruption rehearsal](restart-purchase-crash-rehearsal.md)
passes sixteen application-boundary cases per platform without production changes.
Live peer-reorg, storage-write failure and power-loss behavior remain separate
concerns; passing the offline operator workflow does not resolve them.

Exact scripts, logs, command artifacts and source/binary identities:
[`restart-full-state-operator-2026-09-25`](evidence/restart-full-state-operator-2026-09-25).
