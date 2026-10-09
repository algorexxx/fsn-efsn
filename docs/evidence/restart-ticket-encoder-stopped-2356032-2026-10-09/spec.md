# Read-only inspection of the stopped candidate

Declared after the 2,400,000 attempt stopped, before this inspection runs.
The attempt remains incomplete. Its stop-before-2,356,033 log supplies the
height to investigate, not an expected hash or proof of persisted state.

Inspect exactly 2,356,032, using the retained replay executable for the head
check. Build only a separate observer, changing the preceding observer's height
literal. Capture the backup reference before inspecting the stopped target;
this reference is post-replay, not a pre-replay reference for the partial height.
Compare complete header/RLP, body/receipt commitments, bloom and TD. In a fresh
process with an empty ticket cache, open state, decode tickets and recompute the
ticket commitment. Record the count as an observation; the interrupted replay
has no final warm ticket-count observation to compare.

Use private mount/network namespaces, loopback down, offline build inputs and
read-only mounts for backup, stopped target and original 2,200,000 checkpoint.
Acquire both replay run locks; record processes before inspection. Refuse an
existing inspection result. Build limit: seven minutes; each observation:
three-minute outer/two-minute Go limit. No block import, database copy, replay
resume, stop-file deletion, limit extension or W: access.

Verify the sealed incomplete attempt and all of its prior manifests, original
checkpoint inventory, retained executable and source identities before use.
Hash every stopped-target file before and after; check the original checkpoint,
sources, executable/observer, stop file, evidence inputs and backup/baseline
metadata remain unchanged. Preserve failures and every command exit. A cold
pass validates only the stopped checkpoint; it cannot make the requested
2,400,000 range pass or close F12. Legacy shortcuts still apply through 2,680,000.
