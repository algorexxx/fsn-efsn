# Complete preserved-data package and restore rehearsal

Status: passed on 25 September 2026 at 01:25:57 Stockholm time. The complete
package, original-manifest comparison, restored-file readback, identical index
reports and two fresh-process node service checks all pass. This is investigation
tooling, not a release artifact or launch approval.

The compact state export is useful for synthetic recovery but omits historical
bodies and log indexes. This experiment preserves every file of the stopped
original chain database, restores it into a new directory, and checks whether
the actual client can reopen and serve it. It adds test tools only; it changes
neither consensus nor the agreed one-backup-block/donation-wallet handover.

## Source, storage and identity

The input is `C:/Users/Peter/Documents/CODING/fusion-node/data/efsn/chaindata`:
56,107 files containing 117,170,022,674 bytes. The database is flat LevelDB, with
no ancient-data directory. The package allowlist accepts only its LevelDB data,
manifest, log and lock filenames. It excludes the sibling keystore, P2P node key,
transaction journal and validator configuration.

The preserved identity is:

| Field | Value |
| --- | --- |
| Genesis | `0xc2422b1d9d16331be2a5b207c0783027d4419498003f729f4b9e9c5c1838623a` |
| Chain ID | 32659 |
| Head | 15,130,080 |
| Head hash | `0xe93ffded087a79097d4309c7831690161db6ed136f4b1a22c4c83a99db80f99f` |
| State root | `0x1526799d6f10f4a4467e4dd4f3b1f81ca1479822bb2c24aa541ac66f889ccffc` |
| Ticket commitment | `0xe4e079c525c189eb30ca22ba57bbd4af8b44050e2fc1618c2157107b00820e2c` |
| Tickets | 491 |

Bulk output is under `W:/FusionRestart/restore-rehearsal-2026-09-24`, on the
user-selected ZFS network share. The package is in `package`; the verified
restored instance is `restored-node/efsn/chaindata`. The tools reserve 100 GiB
of free space and never overwrite an existing restore directory. No new bulk
dataset is placed on D:. Network-share performance here is not a validator
storage performance recommendation.

The existing independently retained SHA-256 manifest is
`tmp/restart-linux/backup-copy-2026-09-23/sha256sum.txt`, whose SHA-256 is
`a41ebd5f4f250cbb22b7c0d9ac484b7b1a503d6bc6ff7ff57cec97915cbe88c6`.
Every newly packaged file must match it before restoration is accepted.

The completed package contains 220 archives totalling 117,176,535,900 bytes.
All 56,107 individual file hashes match that original manifest exactly. The
final package manifest SHA-256 is
`9477c409cdc4972cbd1ccfd6306062ffebf277b84f043b4ff867b279452ef2e9`.
The resumed full packaging test passed in 3,518.64 seconds; the earlier two-part
pilot passed in 42.14 seconds.

## Packaging and failure behavior

[`snapshot_package_test.go`](../tests/restart/snapshot_package_test.go) opens the
source read-only and holds the database lock throughout the Python child process.
It checks the fixed historical identity and agreeing head markers. A separate
disposable-database test confirms a concurrent writable open is refused.

[`snapshot_package.py`](../tests/restart/snapshot_package.py) splits whole files
into approximately 512 MiB uncompressed ZIP64 archives. Each file is hashed while
read; each completed archive is flushed and read back for its own hash. A small
JSON file commits each part. The final manifest is created only after every part
has completed and the source inventory has been checked again.

The source plan pins the file inventory, identity, layout and exact packer bytes.
An explicit resume verifies committed archives and their source files before
continuing. Changed input, identity, tool bytes or layout is refused. An archive
left between its rename and metadata commit is fully checked against the source
before adoption. Incomplete `.partial` files never count as completed parts.
The two-part real-data pilot exercises a bounded stop followed by full resume.

Thirteen small failure/roundtrip cases pass on Windows and Linux, including
source-content changes with unchanged size/time and exclusion across processes.
A second process was also refused the actual active package lock on W: during
the full run. These checks do not simulate every SMB or server failure.

Use the `STOP-PACKAGE` file in the rehearsal root for a requested stop at a part
boundary. Do not forcibly terminate the Go lock-holder while its Python child
is still reading. This test wrapper does not yet provide a production supervisor
that couples their process lifetimes across every possible parent crash.

Restoration requires the separately trusted final-manifest hash. It verifies
metadata, archive hashes, member paths, sizes and individual file hashes. It
then rereads every output file before writing `restored.json`. Missing that
marker means the target is incomplete and must not be started. Restore currently
requires a new target; it does not resume into partially restored data.

After a writable node opens the restored copy, LevelDB may change its physical
files. The marker records the initial verified restore, not a continuing claim
that the working database remains byte-identical to the archives. Keep the
immutable package separately; later backups need their own manifests.

These checks establish the bytes observed through the filesystem. They do not
prove NAS power-loss durability or that rereads bypass client/server caches.
Neither the package hash nor a restored state root proves historical execution
or independence of the original backup provider.

## Validation scope

The source index inspection passed:

- Transaction and receipt commitments at 69 heights spanning genesis to the
  preserved head, including the legacy-checkpoint cutoff and replay endpoint.
- 105 first/last transaction lookups and their receipt lookups, with none missing.
- All 3,693 completed bloom-index section heads against canonical history.
- All 2,048 bloom vectors reconstructed from headers in each of the first and
  last completed sections (8,192 headers altogether).
- The preserved head, current ticket commitment and all 491 current tickets.

The same inspection passed on the restored database in 619.94 seconds, with
byte-identical JSON results (SHA-256
`f547b5bba2e1bbecd1d86b725dbd358afb91221299bd80f87dac44bd362ff294`).
It samples transaction indexes and bloom vectors; it is not an exhaustive
check of every transaction index or every bloom vector. The earlier
[complete structural history and current-state traversal](restart-integrity-investigation.md)
remain separate evidence. Full historical transaction execution has reached
2,700,000, including 20,000 blocks beyond the legacy checkpoint range.

The restored-service test passed a startup/read/clean-stop cycle in each of two
separate processes (198.34 and 35.41 seconds), preventing reuse of the first
process's caches. It checked agreeing head markers, historical in-process RPC block/log/receipt
reads, an address-filtered historical bloom-index query, and actual loopback P2P
requests for headers, bodies, receipts and the
committed current-state root node. It has no validator wallet, mining, discovery
or non-loopback peer access. Public test scalars 3 and 4 identify its P2P peers;
they are not validator signers. Only the restored copy is opened for writing.

Native and Ethereum-compatible balance RPCs also reproduced the preserved
backup/donation balances (respectively `3225543308109480158626` and
`12020102000000000000000` wei) and nonces (233427 and 0). These expected values
come from the earlier pinned-head wallet observations and saved-backup inventory.

The peer check follows Fusion's header semantics: its `sha3Uncles` field stores
the PoS sorting hash from PoS V2 onward. It is not an Ethereum uncle-list commitment
at those heights. The test compares returned uncle content to the preserved
body and transaction content to the header's transaction root; it does not
substitute Ethereum's header rule for Fusion's existing rule.

This bounded peer exercise is not a genesis downloader run or complete peer
state acquisition. The earlier two-node recovery rehearsal separately proves
live suffix propagation and downloader catch-up after a process restart.

## Reproduction and remaining release work

Source and evidence are in
[`restart-snapshot-2026-09-24`](evidence/restart-snapshot-2026-09-24).
The Python helper uses the standard library. Windows builds use Go 1.21.3,
`CGO_ENABLED=0`, `GOMAXPROCS=2` and pinned offline module caches. Large test runs
are opt-in through explicit absolute paths; ordinary package tests skip them.

Before any operator distribution:

1. Retain this passing package/restore baseline and review it alongside the
   final release procedure; it does not certify the later recovery dataset.
2. Specify the supported release toolchain and operating systems. This run
   exercises a Windows restore on SMB, not all filesystems or platforms.
3. Produce the final recovery dataset after the exact real-address sequence and
   mandatory ancestry anchor are reviewed. This preserved backup predates that
   recovery and cannot itself authorize post-restart economic use.
4. Publish signed manifest provenance, complete part metadata and archives,
   download/retry instructions, expected head/configuration, disk requirements
   and fresh node-identity/key setup. Demonstrate transfer through the chosen
   hosting/mirror path and joining the declared release network.
5. Keep genesis resynchronization, full peer state acquisition, pruning/freezer
   recovery and storage-outage behavior explicitly unproven until tested or
   excluded from the supported release scope.

No real private key is read, no real recovery block is signed, and no package
is published by this rehearsal. Production signing custody and live backup-wallet
purchase draining remain independent launch gates.
