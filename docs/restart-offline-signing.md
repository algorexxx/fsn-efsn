# Offline recovery signing and interruption rehearsal

Date: 24 September 2026. Baseline: `0ad0136` on
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

## Remaining limits and next work

This establishes composition with small synthetic state. It does not repeat the
full preserved-state handover or prove machine power-loss durability. The
full database restore remains a separate running
investigation; this work does not certify its result.

An export interrupted during its write may leave a partial file. Export again
to a new filename from the completed journal; never erase a reservation or
request another signature. The exporter provides no atomic publication or
directory-flush guarantee. Independently verify the RLP, signature, expected
block identity and import results before accepting an artifact. Keep exports
outside chain data as well as outside the journal.

Before real-key use:

1. Repeat these composed interruption boundaries with the complete synthetic
   preserved-state fixture once bulk validation is finished.
2. Integrate bounded key access and an operator workflow pinning the reviewed
   plan, purchase, unsigned report, configuration and executable. The library
   checks chain identity and reviewed block bytes; it does not authenticate the
   operator's approval or attest the executable/configuration externally.
3. Keep the authoritative journal on reliable local storage outside snapshots;
   enforce one active holder per key and the approved one-backup-block custody
   sequence. Path separation cannot detect journal rollback, copied journals or
   signatures made elsewhere. The journal is not a lifetime one-block quota.
4. Complete the live backup-wallet purchase drain, real-address ledger/timing
   review, independent recovery import and mandatory ancestry-anchor selection.
   Enable ordinary donation mining only after the controlled sequence is verified.

Evidence and exact reproduction commands:
[`restart-offline-signing-2026-09-24`](evidence/restart-offline-signing-2026-09-24).
