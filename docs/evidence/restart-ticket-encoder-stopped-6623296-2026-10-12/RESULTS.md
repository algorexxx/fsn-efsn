# Saved checkpoint verified at 6,623,296

The attempted 6,900,000 range remains failed. It stopped after three consecutive
du scans reported disappearing .ldb files. Its STOP, original inputs, exit-1
completion and sealed evidence are retained. No consensus mismatch is reported.

The separate bounded read-only inspection and evidence verifier pass. All five
commands and twelve preservation checks pass, with 1,986 prior evidence files,
16,893 closed target-file hashes and 1,383 separate recovery hashes verified.
Protected backup/baseline metadata, source/executable/toolchain, replay identity
and original STOP are unchanged. The exact saved head, full header/RLP, state,
ticket/transaction/receipt commitments, bloom and total difficulty match the
backup. Cold reconstruction finds 4,923 tickets and 148 transactions/receipts.
There is no final warm ticket count for the stopped run.

This adds 23,296 verified blocks: coverage reaches 6,623,296, including 3,943,296
beyond the 2,680,000 legacy boundary. Another 8,506,784 blocks remain to the
15,130,080 backup tip. F12/G1 and final release/startup/recovery/handover remain
open. The cold working allocation is 35,399,045,120 bytes (32.968 GiB).
No old failed attempt is relabeled or passing history rerun.
