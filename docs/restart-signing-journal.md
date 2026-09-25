# Recovery signing journal and saved-backup purchase inventory

Date: 24 September 2026. Baseline: `3ae0c82` on
`codex/restart-investigation-wip`. This is a tested recovery-library prototype,
not an enabled production signer. Only public test keys 1 and 2 were used.
The ordinary miner, public network, real keystores and production anchor were
not activated or changed by this investigation.

## Why the reservation precedes the signature

DaTong's `CheckAddingReport` accepts two distinct signed headers with the same
parent and coinbase as evidence of multiple mining. It compares complete header
hashes and verifies both signatures; neither header needs to have become
canonical. Even signing the same message again is unsafe if a signer can return
a different valid ECDSA signature. An unpublished rehearsal is not automatically
safe to repeat with a real staking key.

The new `internal/recovery.SigningJournal` uses the existing LevelDB dependency
directly, with exclusive process locking, strict corruption checks and synchronous
writes. It never calls automatic database repair. Its identity binds one signer,
genesis hash and chain ID. Creation is explicit; opening a missing journal or one
with a different identity fails. The journal contains public blocks/signatures,
not private keys.

`Sign` follows this order:

1. Hold the journal's mutex and check its identity against the plan.
2. Rebuild the candidate with the existing recovery guard against a stopped
   chain reader. Require exact byte equality with the reviewed unsigned block.
3. Look up the parent reservation. Refuse a different unsigned block, or any
   unfinished attempt. Return an already completed block without calling the key.
4. Save the complete unsigned block under that parent with `Sync: true`.
5. Invoke the supplied signer with DaTong's actual signing payload. The newly
   exported `datong.SigningPayload` calls the existing encoding; it does not
   change consensus. `SealHash` remains unsuitable as a replacement.
6. Require a 65-byte signature and verify it recovers the intended coinbase.
7. Save that exact signature synchronously, then return the sealed block.

The final block is reconstructed from the reserved unsigned RLP and saved
signature. `Saved(parent)` retrieves it after a process restart or chain-head
advance without requesting another signature. Import/publication remains a
separate operation requiring independent validation. No signing flag was added
to the unsigned `fsn-recovery` command.

## Crash and conflict results

Windows and Linux pass the following tests; Linux uses the race detector.

| Failure boundary or condition | Observed behavior after reopen |
| --- | --- |
| Process killed before reservation | First signing attempt can proceed |
| Process killed after synced reservation, before signature | No new signer call; unfinished reservation error |
| Process killed after signature, before completion record | No new signer call; unfinished reservation error |
| Process killed after completion | Exact saved block returned; no new signer call |
| Callback error, panic, short signature or wrong key | Reservation remains unfinished and cannot be retried |
| Journal closed during callback, simulating failed completion persistence | No completed artifact returned; reopened reservation remains unfinished |
| Reserved WAL truncated by one byte | Strict open refuses corruption instead of dropping the reservation |
| Corrupt saved signature | Open refuses the journal |
| Missing journal, changed genesis/chain ID/signer | Refused |
| Second process opens the same active journal | Exclusive lock refuses the second process |
| A different reviewed candidate for the same parent | Refused without another signature |

`TestRecoveryJournalHandover` repeats the three controlled stages using the
existing sparse funded fixture. Eight concurrent requests for each stage cause
exactly one signer callback. Unreviewed bytes, an unsafe ticket horizon and a
wrong-chain plan cause none. A separately implemented signing builder produces
byte-identical blocks. Both chains independently import the results, including
retrieval from a reopened journal after the producer has already advanced.
Chain-database logical digests remain unchanged by construction/signing itself.

The three synthetic block hashes are:

- 15,130,081: `0xd9fd675271d97015f3aaa637f1d3a96b40d1a7096f03bd1fd2731c724bc47dfe`
- 15,130,082: `0x09723c3036c31b0eb6d3be9a966988f1a255c7efe53fb4a2d32592b4a236a114`
- 15,130,083: `0x3b8f3d38e52732ad599473fa628de1af9b975f1067ec2fb261280ea344cd931e`

These are sparse-fixture identities, not the earlier complete-state hashes and
not proposed production anchors. This follow-up did not repeat the complete-state
two-node test or the full trie traversal. Their prior evidence remains in the
[construction report](restart-recovery-construction.md).

## Limits and custody requirements

An unfinished reservation deliberately sacrifices automatic recovery for safety.
The process may have signed even when no signature reached the journal. There
is no reset, delete-pending or external-signature adoption API. Stop and preserve
the journal, signer records and candidate. Do not recreate it or use a different
signing path to get past this error. Recovering a signature from an external
signer, if possible, needs a separately reviewed procedure.

The tests cover process termination and specific file/persistence failures.
They do not prove durability through a host power failure, a controller that
lies about flushes, filesystem loss, journal rollback, or a copied journal on
another host. Store the authoritative journal on reliable local storage, outside
disposable chain snapshots. Copying or restoring an old journal must never be
treated as authorization to sign again. The same-parent restriction cannot
detect signatures made before initialization or through another key holder.

This library is not wired into the ordinary miner or the previous test-only
node constructor. One active signer per key remains an operational requirement.
The journal does not enforce a lifetime one-block quota on the backup wallet;
that is the approved launch sequence and subsequent custody restriction, not a
new consensus rule. A production adapter still needs bounded key access,
stopped-chain enforcement, exact build/configuration review, artifact export,
independent import verification and the transition to ordinary donation mining.
The donor's normal mining and the original owner's later independent operation
must not overlap uncontrolled signing access to the same key.

## Saved-backup purchase inventory

The read-only probe opened only `transactions.rlp` and `chaindata` under:
`C:\Users\Peter\Documents\CODING\fusion-node\data\efsn`.
It required the preserved head hash before reading wallet records:
`0xe93ffded087a79097d4309c7831690161db6ed136f4b1a22c4c83a99db80f99f`
at height 15,130,080. No private-key file contents were opened.

| Item | Result |
| --- | --- |
| Saved `transactions.rlp` | 0 bytes; zero transactions |
| Backup wallet canonical nonce | 233427 |
| Backup wallet `fsn-auto-ticket-v1-` record | Absent |
| Donation wallet canonical nonce | 0 |
| Donation wallet `fsn-auto-ticket-v1-` record | Absent |

The automatic-purchase key is the literal prefix followed by the wallet's raw
20 address bytes. Its absence is expected in an old backup predating the new
controller; it says nothing about later gateway activity.

Before and after inspection, all 56,107 database file names, lengths and last-write
timestamps agree. All seven mutable metadata/WAL/lock files were SHA-256 checked,
as was the empty transaction journal. The immutable SST/freezer contents were
not rehashed in this step. A compressed file inventory and equality hashes are
retained with the evidence; the original backup was not copied or replayed.

This closes the inventory of the known saved backup, not the live purchase-drain
gate. Before custody handover:

1. Inventory the actual gateway/miner's runtime pool and effective startup
   configuration; record all backup-wallet signed purchases, including any
   automatic journal, against the canonical nonce and receipt.
2. Stop its mining/purchase controller and wait for shutdown. Remove automatic
   buying from the approved future startup configuration. Do not equate the
   `miner_stopAutoBuyTicket` response with a drained pool or durable stop.
3. Reopen the stopped live data read-only and reconcile its transaction journal
   and automatic record. Quarantine unexpected signed transactions for review;
   erasing a local file does not revoke copies held by peers.
4. Start the controlled recovery service with only the approved purchase input.
   Verify that the backup wallet signs one block and buys no replacement, then
   disable our access before returning operational custody to its owner.

No live gateway pool was queried or modified in this step. There was no request
for a real key, real block signature, transaction submission or public launch.

A later read-only [saved-header probe](evidence/restart-snapshot-2026-09-24/source-signing-context.json)
enumerated canonical and noncanonical header records at heights 15,130,080
through 15,130,083. It found the expected preserved head, verified its signature,
and found no stored headers at the three proposed recovery heights. Iterator
errors were checked before release. This rules out conflicting header signatures
stored at those heights in this database; it cannot establish what another
operator, signer, log or unpublished artifact may contain. It does not replace
the signing journal or the one-active-signer custody requirement.

## Read-only database repair correction

The existing `ethdb/leveldb.NewCustom` retried certain corruption errors with
`leveldb.RecoverFile(file, nil)`, including when its initial options were read-only.
This could change a preservation database. The wrapper now permits that repair
fallback only for writable opens. Writable behavior is otherwise unchanged.

The regression creates a tiny disposable database, empties its manifest, then
opens it read-only. The original wrapper silently repairs it and fails the test;
the corrected wrapper returns the corruption error and leaves every file's hash
unchanged, on both Windows and Linux. An earlier test corrupted `CURRENT`; that
different error type was already refused by the original wrapper. Both results
are retained so the passing earlier case is not mistaken for proof of this fix.

## Next work

The [complete preserved-data package investigation](restart-snapshot-restore.md)
now passes packaging and exact comparison of every source-file hash to the
retained original manifest; its full W: restore, identical index report and two
fresh-process service checks passed overnight on 25 September.
The compact preserved-state fixture remains a separate artifact. Keep the
original and both replay checkpoints.

The [offline signing integration](restart-offline-signing.md) now uses the
existing read-only `Reader` with the chain service stopped and its database
lock held. It opens an existing journal and exports completed artifacts without
a signer callback. Windows and Linux tests pass all three controlled stages
across completion-before-export, export-before-import and import-before-acknowledgment
process cuts using small synthetic databases and, in the 25 September follow-up,
complete preserved state with public test-key substitutions. Unfinished attempts
are refused. The test-only node
constructor in `node_rehearsal_linux_test.go` checks `IsMining()` before building
and sealing, but that does not freeze peer imports or serialize all concurrent
construction requests. It only accepts public test keys and is not a production
signing API. Adding the journal to that live RPC method alone would not enforce
the stopped-chain precondition of `SigningJournal.Sign`.

The operator workflow around these library operations still needs to:

1. Pin the exact reviewed plan, signed purchase, unsigned block bytes, source
   identity and build/configuration. Require an explicitly initialized existing
   journal on reliable local storage outside chain snapshots. Bulk backup use of
   W: does not change that journal placement requirement.
2. Open the stopped working chain read-only, rebuild the candidate and compare
   its bytes before invoking the bounded signing callback. Do not expose generic
   arbitrary-plan signing over the node's RPC interfaces.
3. Commit and export the exact signed artifact, then independently import it
   into the isolated verifier/working chain before constructing the next stage.
   If interruption follows a completed journal write, use `Saved(parent)` to
   recover those bytes, including after the working head has advanced. Never
   recreate a missing journal or retry an unfinished reservation.
4. Enforce the reviewed one-backup-block sequence in the adapter's approved
   inputs and custody procedure. The journal's same-parent restriction is not
   a lifetime block quota. Enable ordinary donation mining only after controlled
   construction has ended and the reviewed cleanup state is present.

The complete-state offline rehearsal now passes nine completed process cuts and
two unfinished cuts per platform, alongside the small-state conflicting-input
regressions. Exact artifact recovery, no second callback, independent imports,
cold ledgers and owner-by-owner accounting agree. Production key access and the
operator approval/custody workflow above remain unproven; the tests use only
public scalars 1 and 2.

In parallel with release preparation, finish the real signer custody/adapter and
live purchase-drain procedures above, review the actual-address ledger and fresh
ticket intervals, then select the authorized recovery artifact and anchor. Full
historical execution still stops at 2,700,000; this work does not extend that claim.

Evidence: [restart-signing-journal-2026-09-24](evidence/restart-signing-journal-2026-09-24).
