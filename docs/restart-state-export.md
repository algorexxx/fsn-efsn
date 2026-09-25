# Preserved-state extraction rehearsal

This investigation extracts the complete state at the preserved head into a
separate, much smaller database. It does not change consensus, construct a new
genesis, sign blocks, or activate the restart anchor. Production code is unchanged.

The source is the verified disposable WSL copy of the preserved backup. The
original backup remains untouched. The candidate historical parent is still
15,130,080, block
`0xe93ffded087a79097d4309c7831690161db6ed136f4b1a22c4c83a99db80f99f`,
with state root
`0x1526799d6f10f4a4467e4dd4f3b1f81ca1479822bb2c24aa541ac66f889ccffc`.

## Extraction and verification

The test-only extractor uses the existing `core/state.NewStateSync` scheduler.
It follows account and storage tries and retrieves all referenced code, including
Fusion native records stored as account code/data. Each retrieved blob must hash
to its requested Keccak identity before the scheduler receives it. Both legacy
unprefixed and prefixed code records are read through the existing rawdb helper;
the output uses the current prefixed format.

The output directory must be absolute and new, and the output database must be
empty. An identity file records the preserved header, genesis, stored chain
configuration and the retained writer executable's SHA-256. No canonical-chain
indexes, genesis state or head markers are installed. There is no resume mode:
an interrupted directory cannot silently become a new attempt.

The Linux runner uses a private mount/network namespace and an unprivileged
writer. The source mount and database handle are both read-only. Only a disabled
loopback interface exists. Output-filesystem free space must remain above 20 GiB,
and its Windows host drive above 50 GiB, checked around each scheduler batch.
The optional stop file requests
normal test cleanup at a batch boundary. Neither these checks nor LevelDB close
constitutes a power-loss guarantee.

After the writer closes, the source alias is unmounted. A separate process opens
only the output database, read-only, with the source environment unset. The
portable verifier defaults to requiring its own executable to be the retained
writer. A different build or platform must explicitly name the trusted retained
writer binary; its bytes must match the artifact's writer hash. Both writer and
verifier hashes are logged. It:

- Checks the identity against the saved gateway observations and retained writer.
- Rebuilds every account/storage trie root and hashes all code/native data using
  the existing traversal, independently of the extraction scheduler.
- Requires the previously measured inventory: 801,355 accounts, 2,886,305 storage
  leaves, 33,437 code/native-data references and 262,368,983 referenced bytes.
- Loads all 491 tickets from cold state, compares them with the saved RPC map,
  and checks their compressed commitment.
- Checks that canonical genesis and the three head markers remain absent.

Only successful verification followed by database close writes `verified.json`.
That file records the verified inventory; it is evidence of this check, not a
replacement for parsing the identity or validating checksums when copying the
artifact. A crash during marker creation can leave a partial JSON file, which
must not be accepted merely because the filename exists.

The archive step also compares the complete exported chain configuration with
the independently retained earlier replay identity, not just the chain ID.
It checks genesis, preserved head, executable SHA-256 and the three extraction
source-file hashes. That cross-check passes for this run. The writer's original
Linux test file is archived verbatim because its verifier was subsequently moved
into the portable test file; the writer executable itself remains unchanged.

## Results

The ordinary Windows restart suite passes in 97.600 seconds. The new synthetic
extraction tests pass twice under the Linux race detector in a network namespace.
They cover valid native/EVM data, legacy code encoding, missing/corrupt account
root, storage and code/native blobs, stops before fetch and after a fetch step,
nonempty targets, directory reuse, and a child process exiting immediately before
or after the first actual LevelDB batch write. The small crash fixture fits in
one batch; these two cuts do not claim exhaustive multi-batch or in-write crash
coverage. Every corruption/stop fixture also checks that source keys remain
unchanged. Existing opt-in node/peer and 46-cut consensus crash suites were not
rerun for these test-only changes; their earlier evidence remains applicable.

The first extraction started at 10:31:13 UTC on 24 September 2026. It stopped
at the configured D: reserve after 330.72 seconds; the last progress report had
910,473 fetched trie nodes. Its partial artifact,
`/home/rehearsal/replay/preserved-head-state`, remains unverified and is not reused.
The original log and nonzero exit status are retained. This is a demonstrated
storage guard, not evidence of source corruption.

C: had about 110 GiB available. The same synthetic extraction suite, including
actual LevelDB process exits and cold reopen, passed twice with its temporary
databases on the C: workspace filesystem. A fresh extraction started at
10:38:17 UTC with the same retained executable, writing to
`C:/Users/Peter/Documents/CODING/fsn-efsn/tmp/preserved-head-state` through WSL's
`/mnt/c` mount. Its host reserve is correctly checked against C:. This limited
use of NTFS/WSL is for the derived state artifact, not a decision about production
node storage. The 117 GB source copy and stopped replay remain on Linux ext4.

Extraction passed, reporting 1,896.18 test seconds: 4,121,587 fetched trie-node
requests, 2,041 code/data requests, 433,136,773 fetched bytes and 8,049 written
batches. These counters describe retrieval, not account counts or unique
referenced-code inventory.

Cold verification passed natively on Windows in 230.38 seconds, with the exact
original root, all four expected inventory totals, all 491 tickets across eight
owners and their commitment. The writer hash was explicitly checked against the
retained Linux binary. A wrong-writer attempt was rejected before database open
and produced no verification marker. The final portable layout also passed
focused Windows tests and Linux race tests. No production code changed.

The closed database is 528,814,572 bytes (about 504 MiB); the artifact directory
including identity and verification metadata is 528,817,080 bytes. All 230 files
have been SHA-256 hashed and reread against the manifest. The manifest's SHA-256
is `a6c86fc58a9f7b482a02b787a337d600e32a447551e45dbe40d210b498341bbf`.
At final capture C: had 113,963,089,920 free bytes, so two additional state copies
fit comfortably within the retained reserve. Recheck capacity at copy time.

The initial Linux cold reader made progress through WSL's C: filesystem but was
substantially slower. It was deliberately terminated after native verification
succeeded; its partial scan and nonzero exit are retained and are not claimed as
a completed Linux traversal. The initial Windows launcher also had an argument
quoting error before any tests ran; that original log is retained separately.

Completed extraction and the partial Linux verification results:
`/home/rehearsal/results/restart-state-export-2026-09-24/c-storage`.
The retained source checkout is `/home/rehearsal/fsn-efsn-state-export`.
Exact runners and completed evidence are retained in
[the evidence directory](evidence/restart-state-export-2026-09-24).

The parallel historical replay was deliberately stopped through its existing
stop file as D: approached the reserve. It closed at 2,613,376; the new read-only
inspection probe confirmed that exact head and the existing resume invariants in
7.86 seconds. See the [replay report](restart-integrity-investigation.md). The
fully checksummed C: copy then completed 2,700,000 and passed a separate cold
reopen check. That final replay is about 3.71 GiB. It includes 20,000 blocks
beyond the legacy checkpoint shortcut range. The D: checkpoint and its stop
file remain preserved; neither replay copy has an active writer.

## Use and remaining work

This is a state artifact, not a bootable chain database, full historical archive,
or demonstration of peer state download. Address preimages and unrelated database
keys are not part of the state commitment and are not exported. Source corruption
fails the extraction; incomplete output is disposable and remains unverified.

The separate [complete preserved-data restore rehearsal](restart-snapshot-restore.md)
now passes packaging and restoration of the original database, including
historical bodies and indexes, on W:, followed by actual node service checks.
Its results and limitations are tracked separately from this compact artifact.

Preserve the exact exported state before constructing separately labelled
rehearsal copies. Measure those copies against available space before making
them. Public test-key substitutions must have a complete difference ledger,
including collision checks at the synthetic address, original nonce and funding,
ticket ownership, native ticket commitment and the resulting changed state/header
identities. Such a fixture cannot be described as a valid mainnet continuation.

Do not copy the old sparse fixture's funding setup directly into the full state:
crediting the public test address while leaving the same FSN funding at the
original owner would duplicate it. Specify and record any corresponding debit,
the exact time-lock intervals, nonce setup and ticket reassignment. Preserve
unrelated assets, contract storage, swap ownership and all other accounts. The
changed owner and parent hash can also change ticket ordering, transaction IDs
and subsequent ticket IDs; synthetic success cannot establish the exact future
sequence for the original signer.

A state-only artifact also needs explicit historical context before execution:
`core/evm.go` uses the parent timestamp and resolves ancestor hashes, with the EVM
limiting `BLOCKHASH` to the previous 256 blocks. The DaTong sealing-delay adjustment
reads the parent and the header ten blocks before it. Ticket reconstruction can
walk further back until an available state, using headers, receipts and snapshots;
there is no universal fixed lookback bound for that fallback. Copy and verify the
necessary contiguous context, then instrument missing reads to fail clearly.
Keeping the exported parent state available bounds reconstruction of a short
rehearsal suffix; it does not validate arbitrary sparse-history node operation.
Deleting that only retained parent state must fail explicitly unless an older
verified state and the complete intervening context were deliberately included.

The [full-state bridge rehearsal](restart-full-state-rehearsal.md) now provides
independent import, complete synthetic accounting, cold restart and bounded
ticket reconstruction evidence using copies of this artifact. Actual mining and
replenishment with a deliberate ticket runway, original-history signatures, the
final recovery sequence and production anchor remain later review gates.
