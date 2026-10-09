# Candidate continuation from 2,356,032 through 2,400,000

Declared before execution, 9 October 2026, investigation commit a9c23b4e.
This is the separately requested continuation after the previous 30-minute
stop and successful read-only inspection. Execute only the remaining 43,968
blocks. The original attempt remains incomplete and sealed; do not replace its
result or remove its STOP. Production selection and replay identity are unchanged.

Preserve /home/rehearsal/replay/candidate-ticket-encoding-2400000, whose actual
cold-verified head is 2,356,032. Acquire its run lock and mount it read-only
alongside the backup in private mount/network namespaces. Verify all 1,299
checkpoint file hashes against the stopped inspection, then run the original
exact-height cold helper at 2,356,032. Copy only this closed candidate database
into a fresh candidate-ticket-encoding-2400000-v2 directory; verify every copied
byte and the unchanged identity manifest. Refuse existing targets/results.
Neither baseline database nor the original 2,200,000 checkpoint is opened.

Reuse the retained replay executable from the original attempt, SHA256
b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245.
Copy its bytes without rebuilding. Its existing validated-resume path must
accept unchanged executable/source/configuration identity, start at 2,356,032
and finish at exactly 2,400,000. Reuse the sealed first-range runner's execution,
environment, monitoring, replay and preservation helpers, recording its hash.
Require a fresh absent stop-file path inside this new result directory.
Verify the earlier STOP remains byte-identical before and after.

Build a separate Go 1.27.1 observer with an overlay changing only the previous
inspection observer's height literal from 2356032 to 2400000; its source is
byte-identical to the original attempt's 2,400,000 observer source. Retain the
one-line diff, overlay and binary hash. Do not invoke its replay test.
Capture a fresh backup reference before replay, then perform both cold-head
and cold-details checks in separate processes against the read-only closed
target. Compare complete header/RLP, state/ticket/transaction/receipt commitments,
bloom and TD against the reference. Decode tickets with an empty process-local
cache and recompute their commitment; compare the observed count with the
successful replay's final count rather than inventing an expected value.

Unchanged bounds: initial free space at least 30 GiB Linux and 60 GiB D:;
per-batch reserves 20/50 GiB; sampled 4 GiB target stop; three bounded size
measurement attempts; 30-minute monotonic clean-stop request; one-hour outer
timeout. Use GOMAXPROCS=2, loopback down and offline build inputs. Any mismatch,
short endpoint, timeout or nonzero exit is incomplete evidence. No automatic
extension or retry. A smaller interval does not guarantee completion time.

Verify prior manifests, selected/candidate sources, backup and baseline
metadata, preserved checkpoint and replay binaries before use. Hash the
checkpoint and closed target after inspection and retain all commands, logs,
errors, identity files, preservation results and timestamps. No backup-scale
copy, W: access, mining, real keys or signing is part of this run.

Fresh preflight reports 38,630,641,664 bytes free in Linux (35.98 GiB) and
71,911,133,184 bytes on D: (66.97 GiB); recheck within the runner before work.
The initial namespace/process snapshot contains no replay or node writer.

These heights retain legacy checkpoint shortcuts through 2,680,000. Transaction
execution and state/receipt comparisons run; documented ticket-seal and raw
transaction shortcuts remain. Success advances candidate history only; F12,
independent review and restored-identity safeguards remain open.
