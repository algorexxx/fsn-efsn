# Authorized remaining-fixture archive

Peter explicitly authorized archiving necessary folders and deleting unnecessary
copies on 10 October 2026 after the host-reserve stop. Copy the exact 14 roots in
proposal.json to W:\FusionRestart\remaining-fixtures-copy-2026-10-10. Preserve
all failures, originals and replay/recovery data. This phase copies only. A
separate verified retirement must precede any D: deletion.

Reuse the previous copy worker with the recorded patch. Verify the exact source
counts/bytes, evidence mappings and manifests; obtain database lock handles;
check exact paths and reparse points; hash all source bytes, copy and flush,
then independently rehash source and destination. Preserve partial outputs on
failure. Require FusionRehearsal stopped and no native rehearsal executables.
Record unchanged VHD size/write time and unchanged D: root names. These metadata
checks do not replace later cold replay verification.

The old archive worker required 50 GiB free on D: although it did not write there.
This explicitly approved replacement reads D: only and writes records on C: and
archives on W:. Its output reserves are C: 5 GiB and W: 100 GiB. No database may
start during copying. The replay's 20/50 GiB reserves and cold-inspection starting
floors remain unchanged. No VHD compaction, expansion or live SMB database.

Bounds: 14 roots, 9,191 files, 13,630,973,746 logical bytes; two-hour cooperative
limit and 7,500-second external timeout. No continuation or deletion on failure.
Future retirement must reverify both complete copies and preserve all evidence.
