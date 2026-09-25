# Offline recovery signing and interruption rehearsal

Updated: 25 September 2026. Initial baseline: `0ad0136` on
`codex/restart-investigation-wip`. The offline library integration passes on
Windows and Linux, with Linux race detection. This is a synthetic rehearsal;
the production key adapter and launch authorization remain separate work.

## Change

[`internal/recovery/offline.go`](../internal/recovery/offline.go) adds two
operations around the existing guarded builder and signing journal:

- `SignOffline` opens an existing stopped LevelDB chain read-only, checks its
  agreeing head markers, opens the existing journal for the planned identity,
  rebuilds the reviewed candidate and signs through the journal. It holds the
  chain lock until signing returns. Absolute paths and separate chain/journal
  directories are required; symbolic links are resolved before overlap checks.
- `ExportSavedBlock` opens the existing journal and exports the exact completed
  block for a specified parent. It has no signer callback or chain-head
  dependency. It creates a new RLP file, flushes it and checks close success;
  existing files and output within the journal directory are refused.

Neither operation creates a missing journal. Signing does not import or export;
export does not sign. There is no new CLI signing flag, RPC method, real-key
loader, consensus rule or change to ordinary mining. The unsigned recovery
command continues to prepare review reports only.

The stopped-chain lock closes a gap in composing the previous prototype: the
test-only live node constructor's `IsMining()` check alone did not freeze peer
imports. An importer using the same database cannot open it while the offline
wrapper owns its lock. This does not coordinate a copied database or another
holder of the same private key.

## Results

The test uses the existing sparse, funded handover fixture and public private
scalars 1 and 2. Each initial database copy is capped at four MiB of logical
records. It creates working and verification databases in disposable C: paths;
no preserved full-state copy, replay checkpoint, W: data or real key is opened.
Existing compiler caches are reused.

For each of the three controlled blocks, a child process is forcibly terminated
at each boundary below, then fresh processes recover and verify it:

| Interruption | Result |
| --- | --- |
| Completed journal record, before export | Exact saved block exported; no second signing callback |
| Export complete, before import | Original export unchanged; exact artifact recovered and imported |
| Import verified, before acknowledgement or chain close | Cold head retained; journal export works after head advance; no second signature or transaction execution |
| Reservation written, before signature | Re-signing and export refused as uncertain |
| Signature produced, before journal completion | Re-signing and export refused as uncertain |

The first three boundaries cover all three stages: one backup-signer block,
donation-signer jump and donation-signer cleanup. The two uncertain boundaries
are exercised at the first stage. The existing journal unit tests continue to
cover callback failures, damaged records, concurrent access and earlier cuts.

Each completed block matches an independently implemented synthetic builder
byte for byte. Separate chain imports and cold reopen reproduce its header,
receipts, ticket set and complete account differences within this small fixture.
The block identities remain the previously recorded sparse-fixture hashes:

- 15,130,081: `0xd9fd675271d97015f3aaa637f1d3a96b40d1a7096f03bd1fd2731c724bc47dfe`
- 15,130,082: `0x09723c3036c31b0eb6d3be9a966988f1a255c7efe53fb4a2d32592b4a236a114`
- 15,130,083: `0x3b8f3d38e52732ad599473fa628de1af9b975f1067ec2fb261280ea344cd931e`

These are not production anchors. The first two completed boundaries and both
uncertain boundaries also leave every chain file's name and SHA-256 unchanged.
The import boundary deliberately changes the working chain.

Additional passing checks refuse an active chain writer, an active journal,
missing or overlapping directories, changed unsigned bytes/purchase/identity/
parent/horizon, conflicting candidates and disagreeing head markers. A callback
also attempts a writable chain open and confirms the read-only lock remains held
during signing. Refused inputs do not call the signer or repair chain data.

Linux passes the symbolic-link overlap checks. Windows cannot create the test
link with this account's privileges, so that specific case is explicitly skipped
for Windows. Its direct-path overlap checks pass. Initial Windows sandbox runs
refused `EvalSymlinks`; the same checks pass outside that sandbox. The failures
and capability limitation are retained in the evidence, without removing the
production path checks.

## Complete-state follow-up

The 25 September follow-up, based on `45ad8af`, repeats all eleven interruption
cases above against the complete preserved account state: nine completed cuts
(three boundaries for each of three blocks) and two uncertain first-block cuts.
It reuses the same signing library and child-process harness; only test code
changes. It also reruns the small-state interruption and refusal regressions.

Both platforms pass: Windows completes the full-state test in 35.91 seconds;
Linux under race detection completes it in 294.60 seconds. Their reviewed
plans, signed blocks, substitution records and changed-account ledgers are
byte-identical. No production code change was needed for this follow-up.

Each platform starts with nine fresh copies of the immutable compact export,
verified against manifest
`a6c86fc58a9f7b482a02b787a337d600e32a447551e45dbe40d210b498341bbf`:
230 files and 528,817,080 bytes per copy. All new copies are on C:, with a 50 GiB
reserve enforced. The original backup, replay checkpoints and W: package/restore
are untouched. Existing fixture preparation substitutes public scalars 1 and 2
for the backup/donation wallets, preserving their recorded funding and ticket
rights. No real key is used. The compact export contains current state and the
rehearsal adds retained historical header context; it is not a full-history node
distribution.

The independently built reference prefix passes owner-by-owner accounting of
future FSN rights across liquid balances, time locks and tickets. Only ordinary
fees, rewards and existing first-retreat penalties are permitted. Other assets,
code, storage and notation remain unchanged. The retired signer account is
unchanged after its first block. The resulting complete-state fixture has:

| Stage | Height | Stored tickets | Changed accounts |
| --- | --- | --- | --- |
| Backup handover | 15,130,081 | 485 | 8 |
| Donation jump | 15,130,082 | 480 | 2 |
| Donation cleanup | 15,130,083 | 1 | 2 |

The jump's stored count still includes expired tickets; cleanup leaves the
required usable donation replacement. Each block carries one successful funded
purchase, a fee of 42,448,000,000,000 wei and the ordinary 0.3125 FSN reward.

Completed cuts recover the exact reference RLP without another signing callback.
Separate working/verifier imports and fresh-process reopening agree on all head
markers, receipts, tickets and complete changed-account ledgers. The 256-header
EVM context remains readable. Signing/export-only cuts leave every chain file
unchanged; reservation/signature cuts refuse both re-signing and export.

Evidence, platform results, source/binary identities and the compared review
plans, blocks and ledgers are retained in
[`restart-full-state-offline-2026-09-25`](evidence/restart-full-state-offline-2026-09-25).
The fixed September test dates and substituted identities are not launch
parameters or production anchors. This follow-up does not repeat the earlier
complete trie traversal or extend historical execution beyond 2,700,000.

## Remaining limits and next work

The [full database restore](restart-snapshot-restore.md) also passed on
25 September, including file readback, index comparison and two service starts.
These rehearsals do not prove machine power-loss durability or public data
distribution.

An export interrupted during its write may leave a partial file. Export again
to a new filename from the completed journal; never erase a reservation or
request another signature. The exporter provides no atomic publication or
directory-flush guarantee. Independently verify the RLP, signature, expected
block identity and import results before accepting an artifact. Keep exports
outside chain data as well as outside the journal.

Before real-key use:

1. Review the [implemented operator commands and bounded key preflight](restart-operator-workflow.md)
   and their passing [complete-state command rehearsal](restart-full-state-operator.md).
   Command and interruption tests pass on Windows and Linux, including wrong-password recovery before reservation,
   refusal to reopen keys for uncertain/completed attempts and report rebuilding.
   These controls do not authenticate the reviewer or externally attest the
   executable; finish actual operator review and key custody before real-key use.
2. Keep the authoritative journal on reliable local storage outside snapshots;
   enforce one active holder per key and the approved one-backup-block custody
   sequence. Path separation cannot detect journal rollback, copied journals or
   signatures made elsewhere. Legacy journals have no lifetime quota; the new
   policy journal limits its own handover sequence, not all use of a wallet key.
3. Complete the live backup-wallet purchase drain, real-address ledger/timing
   review, independent recovery import and mandatory ancestry-anchor selection.
   Enable ordinary donation mining only after the controlled sequence is verified.

Evidence and exact reproduction commands:
[`restart-offline-signing-2026-09-24`](evidence/restart-offline-signing-2026-09-24).
