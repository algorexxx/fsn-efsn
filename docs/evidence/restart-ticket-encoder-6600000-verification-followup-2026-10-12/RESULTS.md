# Replay through 6,600,000 verified separately; original verifier failure retained

The 6,300,000 to 6,600,000 replay and both cold checks passed. The original
dispatcher finished with exit 1 at 00:20:33 UTC on 12 October 2026 because its
evidence verifier rejected the recorded observer patch's filename labels.
The failed completion, stderr, inputs and all original manifests remain intact.
This follow-up does not turn that original automatic verification into a pass.

## Exact cause and bounded correction

The preparation recorded `prior/details_test.go` and `inputs/details_test.go`
in the unified diff header; the verifier expected `a/details_test.go` and
`b/details_test.go`. The remainder of the patch is identical. The observer's
actual source is exactly the preceding source with its single height literal
changed from 6,300,000 to 6,600,000. Neither runtime bytes nor a consensus result
differed because of this reporting error.

[reverify.py](reverify.py) reconstructs the expected one-literal source change
and complete patch, verifies that precisely those two labels differ, then runs
the original verifier in memory with the labels corrected and its output
redirected into this new evidence directory. [verifier-change.patch](verifier-change.patch)
shows both changes. Every original assertion is retained, including full patch
equality, source/executable identities, original snapshot hashes, previous
manifests, endpoint comparisons, isolation, preservation and resource limits.
This is a separately executed verification of existing evidence, not a rerun
of history or a new database inspection. No database was opened or hashed here.

The follow-up [verification](verification.json) passed at 00:22:52 UTC.
The six original manifest sets (9/16/2/3/28/52 entries) verify both before and
after; their hashes are recorded in [review.json](review.json). The original
52-file root manifest remains
`f05c82a8d1633eec0ae9883052ccc58e93c1849534bfa31511a3bf778791ef9d`.
No original `verification.json` was inserted and no completion was rewritten.

## Accepted historical evidence and its limits

- All seven recorded commands and nine additional preservation checks pass.
- Full header/RLP, state, ticket, transaction/receipt commitments, bloom and TD
  agree with the preserved backup at 6,600,000. Warm/cold ticket counts agree
  at 4,786; the endpoint has one transaction and one receipt.
- All 16,672 closed target file hashes were unchanged during the original cold
  inspection. The 1,383 recovery hashes, backup/baseline metadata and source,
  executable, toolchain and replay identity checks pass. The 1,879 preceding
  evidence files verify. This follow-up verifies those preserved records; it
  does not claim another fresh full-file database hash.
- The retained replay executable remains
  `b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245`.
- This adds 300,000 executed blocks, reaching 3,920,000 blocks beyond the legacy
  boundary. Another 8,530,080 remain to the backup tip. F12/G1 remain open.
- Recorded replay duration is 145.728 minutes by timestamps and 135.611 minutes
  by monotonic time. Their difference remains unexplained. Four transient
  allocation-read failures recovered within the existing retry policy.

The evidence establishes historical coverage through 6,600,000. It does not
satisfy the existing controller's automatic successful-prior-job gate: that
gate correctly refuses the original exit-1 completion. Before any continuation,
add and test explicit acceptance of this separately qualified provenance, or
provide another independently qualified read-only checkpoint. Do not fabricate
a successful original completion, reuse the stopped-STOP/host-reserve path, or
repeat 300,000 passing blocks merely to change a patch filename label. Future
preparation must generate the canonical labels expected by the verifier.

## Capacity and next decision

[capacity-review.json](capacity-review.json) records no replay/observer/node
process and an exited dispatcher. At 00:23 UTC Linux has about 24.251 GiB free
and D: 67.324 GiB. Closed working allocation is 34,987,921,408 bytes (32.585 GiB),
up 5.517 GiB in this interval.

A proposed next 300,000-block interval to 6,900,000 with a 39 GiB ceiling allows
6.415 GiB growth. The unchanged starting gate requires Linux >27.415 GiB and
D: >60 GiB; Linux fails. Only about 3.251 GiB remains above the Linux reserve
and preparation margin. Reducing the next range to fit that small allowance
would return to the repeated short jobs the user asked to avoid.

The next capacity proposal is to expand only FusionRehearsal's virtual disk
from 220 to 230 GiB, using the previously qualified native procedure, unchanged
20/50 GiB reserves and before/after preservation checks. Its prior approval
named 200 to 220 GiB; the further expansion is pending a user decision. It
increases the virtual limit, not immediately the host allocation, and does not
prove all remaining history will fit. Retain the verified W: image and separate
recovery checkpoint. No expansion, deletion, compaction, new replay, production
activation or release selection occurred in this follow-up.

The current job is finished. Dependent replay is held for that storage decision
and explicit qualification of the separate-verification provenance. Existing
passing startup/refusal fixtures need no repeated run while waiting.
