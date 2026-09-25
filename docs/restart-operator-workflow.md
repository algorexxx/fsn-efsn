# Offline operator commands and credential preflight

25 September 2026. Baseline `7c389ab`, on `codex/restart-investigation-wip`.
This implements the operator commands and local encrypted-key adapter around
the reviewed-input policy. It is a tested prototype, not launch authorization.
All signing in this investigation uses public private scalars 1 and 2.

## Implemented behavior

`fsn-recovery` now supports `review`, `prepare`, `init-journal`, `sign` and
`export`. The previous flag-only unsigned review invocation remains supported.
The command opens a stopped chain read-only; it does not start a node, submit a
purchase, import a block, broadcast a signature or enable ordinary mining.

`prepare` rebuilds the complete report from the stopped chain and requires exact
canonical report bytes, including the human-readable header, receipt, ticket,
selection and retreat fields. It then produces the canonical approval and prints
its SHA-256 for independent review. Preparing a file is not itself approving it.
The three acting commands require a separately supplied `-approved-sha256`;
they never silently replace that value with the current file's digest.

`init-journal` verifies the approval, runtime pins, first-stage parent and rebuilt
unsigned block before creating the journal. Its existing parent directory must
be separate from chain data. Existing paths, including links, are refused; the
command neither replaces a journal nor upgrades a legacy journal.

`sign` checks the approval and journal policy, rebuilds the candidate, checks the
sequence/quota, and looks for a completed or unfinished record before opening a
key. A completed attempt returns its original block without a password/key file.
An unfinished attempt remains refused. For a new attempt, it validates/decrypts
the key before reserving anything, while retaining both chain and journal locks.
Only then does it synchronously reserve, sign, and synchronously complete the
record. Signing prints the block hash; export is a separate command.

The local key session verifies the derived public address and permits only one
signature of the exact reviewed DaTong payload. It closes after completion,
reservation-write failure, callback failure or panic. Password/plaintext buffers
owned by the adapter and the private scalar's backing words are cleared on normal
unwinding. Go runtime, immutable string and upstream cryptographic-library copies
are not guaranteed to be erased; this is not an HSM or memory-forensics guarantee.

`export` uses the reviewed approval and existing journal, without opening a chain
or key. It verifies the policy and exact unsigned bytes against the saved signed
block before creating a new RLP file. It works after import has advanced the head.
Existing/partial output files are refused. Retry export to a new path; never
re-sign to repair an export. Keep output outside chain data and the journal.

## Supported key input

- Encrypted version 3 JSON, AES-128-CTR, scrypt, matching the approved address.
- Exactly 32-byte ciphertext, MAC and salt; 16-byte IV; 32-byte derived key.
- Power-of-two scrypt N from 2 through 262,144, r=8, integral p from 1 through 16,
  and N*p no greater than 1,048,576. This includes the existing normal/light
  Fusion keystore settings and caps scrypt's main memory allocation near 256 MiB.
- Key and public input files are bounded at one MiB. Passwords are bounded at
  4,096 bytes. Wrong passwords, malformed/unsupported formats and wrong derived
  addresses fail before reservation. No wallet is left persistently unlocked.

Passwords are read only with explicit `-password-stdin`, from a pipe. Console
input and regular-file stdin are refused; there is no echoing prompt fallback,
password command-line argument or environment-variable password option. Supply
the pipe from a local secret provider that does not print or log its output.
There is no built-in interactive hidden-password prompt in this version. Password
spaces are preserved; one final LF/CRLF is removed. Legacy V1 and PBKDF2 key files
are unsupported; the tool never rewrites or converts a key file.

## Reviewable operator sequence

The names below are placeholders. CHAIN and JOURNAL are absolute directories;
output filenames and KEYFILE are absolute paths. All outputs must be new files.
Use disposable working/verifier copies and keep the original backup immutable.

```text
fsn-recovery review -chaindata CHAIN -plan PLAN.json -purchase PURCHASE.rlp -out REPORT.json
fsn-recovery prepare -chaindata CHAIN -report REPORT.json -purchase PURCHASE.rlp -blocks 1 -out APPROVAL.json
```

Review the plan, exact report and approval, funded purchase, timestamps, eligible
successor ticket, fees, refunds/retreats and runtime pins. Independently record
the approval digest and verify the executable against the intended build.
For the backup signer, `-blocks 1` buys only for the distinct donation address.
Only after that review:

```text
fsn-recovery init-journal -chaindata CHAIN -approval APPROVAL.json -approved-sha256 REVIEWED_DIGEST -journal JOURNAL
fsn-recovery sign -chaindata CHAIN -approval APPROVAL.json -approved-sha256 REVIEWED_DIGEST -journal JOURNAL -keyfile KEYFILE -password-stdin
fsn-recovery export -approval APPROVAL.json -approved-sha256 REVIEWED_DIGEST -journal JOURNAL -out SIGNED.rlp
```

The `sign` line requires its password pipe; do not paste a password into shell
arguments. Independently verify/import the exported block before preparing the
next stage. Init/sign can fail if another process has the database open.

For the donation jump, generate a new report/approval with `-blocks 2`, initialize
its separate journal at the actual signed backup block, then sign/export/verify
and import. For donation cleanup, retain that first donation policy:

```text
fsn-recovery prepare -chaindata CHAIN -report CLEANUP-REPORT.json -purchase CLEANUP-PURCHASE.rlp -policy-from DONATION-FIRST-APPROVAL.json -policy-sha256 FIRST_REVIEWED_DIGEST -out CLEANUP-APPROVAL.json
```

Review the new cleanup approval and its own digest; use the existing donation
journal for sign/export. Do not initialize another journal for cleanup. The
policy continues to enforce the two consecutive donation blocks. The correct
next parent comes from actual verified signed output, not a predicted signature.

Before reservation, a credential failure can be corrected and retried. After
reservation, an uncertain result must stop signing. Retrieve a completed record
if present; do not delete, copy back, reinitialize or bypass the journal. A changed
binary/configuration stops new signatures but does not prevent saved export.

## Evidence and limits

Windows checks and Linux race checks cover:

- Actual executable review/prepare/init/sign/export for all three controlled
  blocks, with exact reference RLP, separate imports and cold ledger agreement.
- Wrong password followed by a successful attempt at each stage; no reservation
  exists after the wrong password. Completed repeats succeed with a missing key.
- Refusal of altered report metadata, existing journals/exports and an export
  approval for different unsigned bytes; no output is created on refused export.
- Both locks remain held during credential validation. An uncertain signature
  is refused before opening a missing key or reading a password.
- Forced termination after decrypting a key but before reservation; reopening
  safely makes one signing attempt. Existing post-reservation interruption tests
  retain their refusal/exact-recovery behavior.
- Key-session identity/payload limits, cleanup on success/failure/panic, bounded
  key parsing and preservation of the encrypted source file.

Fixtures are sparse synthetic databases on C:; test keystores deliberately use a
cheap scrypt setting because their scalars/passwords are public. No real keystore,
W: data, preserved-state copy or replay checkpoint was opened. The Linux command
and integration binary both use race detection inside an isolated network
namespace. This does not repeat the complete-state rehearsal with the new CLI,
prove power-loss durability or establish a reproducible release build.

Next rehearse these final commands against fresh complete-state copies, then
finish the actual-address/time-interval review, live backup purchase drain,
one-active-key custody, independent verifier/import procedure and final anchor/
release/data-distribution gates. The journal cannot control another holder using
the same key elsewhere; it does not restrict the backup owner's later node.

Evidence: [`restart-operator-2026-09-25`](evidence/restart-operator-2026-09-25).
