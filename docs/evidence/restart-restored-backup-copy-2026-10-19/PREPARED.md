# Prepared complete-backup fixture copy

Prepared 19 October 2026 after final-tip evidence commit `c5b09c44`.
Three adapted copy controls pass: valid content, wrong expected hash and
existing destination. The source fixture remains unchanged. Prior final-tip
and original backup manifest provenance checks pass.

Fresh 20:54 UTC preflight finds no node/replay/observer or attached loop image.
All 56,107 original-backup metadata entries exactly match the final replay's
preservation record. Replay/observer/retained startup CLI and response hashes
match their recorded identities. This preflight did not hash database files.
Windows has about 9.06 GiB available physical memory; Linux/D: free space is
about 21.48/52.67 GiB and W: about 2.90 TiB. W: mapping and absent destination
pass. The launcher repeats ownership, identity and capacity gates before writing.

The reviewed adaptation and spec pin the fresh 256 GiB image, original hash
manifest, offline isolation, independent final replay checkpoint, phase deadlines,
eight-hour whole-job bound and running reserves. There is no automatic CLI start,
replay continuation or deletion. Only the new copy is disposable. The existing
W: replay image is left detached and unchanged.

INPUT_SHA256SUMS covers this prepared packet. A separate START_SHA256SUMS will
cover dispatch and observed startup records. Completion is provisional until
copy/reattach hashes, actual cold tests, cleanup and host exit have been reviewed.
