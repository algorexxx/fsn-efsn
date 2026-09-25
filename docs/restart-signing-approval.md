# Reviewed signing inputs and bounded handover journals

25 September 2026. Baseline `cedde9f`, on `codex/restart-investigation-wip`.
This adds the library controls for the operator workflow. It does not add a
real-key loader, signing CLI, RPC method, consensus rule or launch authorization.
The subsequent [operator command and credential follow-up](restart-operator-workflow.md)
now implements the local CLI/key adapter and passes small-state command rehearsals;
the original results below remain scoped to their recorded source.

## Problem and change

The original journal reserves one payload per parent. That prevents retrying an
uncertain attempt or signing a conflicting block for that parent, but permits
signing another parent. It therefore cannot enforce the agreed one-backup-block
handover by itself.

`CreateApprovedSigningJournal` now explicitly creates a new journal containing
an immutable `SigningPolicy`, in the same synchronous database batch as its
signer identity. The policy pins:

- The first parent hash and number.
- The donation purchase owner.
- One permitted block for a backup signer buying for that different owner, or
  two permitted blocks for a donation signer buying for itself.
- The SHA-256 of the executing program and of the chain configuration.

Every open validates stored reservations against the policy. Every new signing
reservation must extend the completed previous block, starting at the pinned
parent. An unfinished reservation prevents advancing the sequence. Reservations
consume the allowance; failures do not release it. There is no quota-reset or
policy-edit API. Existing legacy journals are not silently upgraded.

The older `Sign` and `SignOffline` operations refuse policy journals. The new
`SignApprovedOffline` operation requires a policy journal and a version-1
`SigningApproval`, containing that policy, the exact plan, the signed purchase
RLP and the reviewed unsigned block RLP. A separate caller-supplied SHA-256 must
match the exact approval bytes. Approval JSON must be precisely the output of
`EncodeSigningApproval`: two-space indented JSON plus one newline. Changed
whitespace, duplicate fields, unknown fields, trailing data, unsupported versions
and inputs over one MiB are refused, including when their own digest is supplied.

The wrapper holds the existing stopped-chain read-only lock and journal lock.
It compares the approval with the stored policy, checks the purchaser and hashes
the current executable and loaded chain configuration before rebuilding the
candidate. The existing builder still validates execution, the purchase,
surviving ticket and exact unsigned bytes before the journal reserves/signs.
Configuration hashing uses `json.Marshal` of the loaded `params.ChainConfig`;
the executable hash is over the file returned by `os.Executable`.

Completed blocks remain available through `ExportSavedBlock`, without key access
or requiring the old chain head. Repeating the same approved request against its
unchanged parent returns the completed block without invoking the signer again.
After head advancement, retrieve the saved artifact instead of asking to sign.

## Tested scope

Windows tests and Linux race tests exercise the approved path through all three
controlled handover blocks, using the small synthetic fixture and public private
scalars 1 and 2. Each platform covers nine completed process cuts and two
unfinished first-block cuts. Working/verifier imports and cold ledgers agree
with the independent reference builder. Signing/export-only cuts leave chain
files unchanged. The legacy offline path and journal tests also run as regressions.

Additional tests verify quota exhaustion across reopen, different-parent and
out-of-sequence refusal, stored out-of-policy reservations, invalid roles/pins,
refusal of unfinished donation advancement, exact approval hashing, canonical
JSON, changed policy/input refusal, executable/configuration mismatch and refusal
to use a legacy journal or bypass policy through the old signing API.

This step uses only small temporary C: fixtures and existing compiler caches.
It opens no real key, compact preserved-state copy, W: package/restore or replay
checkpoint. The earlier complete-state interruption result remains recorded
against its original source/binaries; it has not been repeated with this new
approval layer. Windows again skips only the symbolic-link case that requires
privileges unavailable to this account; Linux covers it.

Evidence and exact commands:
[`restart-signing-approval-2026-09-25`](evidence/restart-signing-approval-2026-09-25).

## Operator sequence to implement

1. Review the actual-address funding/ticket ledger, fresh timestamps, backup
   purchase drain and existing-signature inventory. Establish one active holder
   per signing key. Select and independently verify the exact controlled-signing
   executable and chain configuration before initializing either policy.
2. Create the backup journal once, pinned to the accepted preserved parent,
   donation purchaser and one-block allowance. Keep it on reliable local storage
   outside chain snapshots. Preserve its identity and policy digest separately.
3. Build and inspect the first candidate, including its purchase, receipt,
   ticket interval, retreats/refunds and successor eligibility. Save the canonical
   approval and record its SHA-256 through the operator's trusted review channel.
   The eventual command must take that already-reviewed digest explicitly; it
   must not compute a new digest from whatever file happens to be present and
   treat that as approval.
4. Validate inputs and obtain bounded key access. Sign only through the approved
   wrapper. Export the completed journal record and independently verify/import
   the exact block. Disable our access to the backup key after verified handover.
5. Initialize the donation journal at the verified signed handover block, with
   a two-block allowance. Prepare/review/sign/import its jump, then do the same
   for cleanup. Each next plan binds the actual preceding signed block; do not
   assume an external signer will return a predictable signature in advance.
6. After independently verified cleanup, select the mandatory public restart
   anchor, prepare the release/data package and enable ordinary donation mining
   under the separate operator procedure. Ordinary mining does not use this
   exhausted two-block recovery journal.

The signing executable/configuration must remain pinned throughout the controlled
sequence. A mismatch stops new signing; it is not a reason to recreate a journal.
Saved artifact retrieval remains available without those signing checks.

## Remaining limits and key adapter work

The approval digest binds bytes; it does not authenticate a person, prove their
review or independently attest a trustworthy executable. A caller that replaces
both the file and the supplied digest has bypassed its own approval procedure.
The immutable policy still limits that journal's role and sequence. Protect the
review channel, executable, filesystem and journal. Journal deletion, rollback,
copies, malicious database edits or another holder using the key elsewhere are
outside these local controls. This is a quota on one journal, not a global
restriction on a wallet or its rightful owner's later operation.

The later operator implementation resolves the credential-preflight gap: it
validates/decrypts a bounded V3 scrypt keystore before reservation, after review
and sequence checks and while retaining both locks. Wrong passwords can be
corrected without consuming the allowance. Completed and uncertain attempts
never reopen credentials. Its local key session signs only the approved payload
once and closes afterward. Review/prepare/init/sign/export commands pass synthetic
end-to-end tests, and the [complete-state follow-up](restart-full-state-operator.md)
passes with the same executables. Final operator/custody rehearsals remain before
real-key use; callback failures after reservation remain uncertain.

No real signature, real purchase submission or public release was performed.
Power-loss durability, complete historical execution, general sync/distribution
and the other launch gates in the main plan are unchanged.
