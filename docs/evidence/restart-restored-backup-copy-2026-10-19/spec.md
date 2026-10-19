# Prepare a complete backup copy for writable restored-startup testing

19 October 2026. The encoder replay has reached backup tip 15,130,080 and is
closed, verified and detached. The next acceptance gap is actual writable
startup and fresh restart of the unselected guard/encoder on complete backup
data. This finite preparation job creates and verifies its disposable fixture;
it does not run a writable node or change any production profile or selection.

Source is `/home/rehearsal/data/efsn/chaindata`, 56,107 files and
117,170,022,674 bytes. Pin the original 23 September hash inventory
`a41ebd5f4f250cbb22b7c0d9ac484b7b1a503d6bc6ff7ff57cec97915cbe88c6`,
retained here byte-for-byte as backup-SHA256SUMS. Copy only allowlisted flat
LevelDB files. No sibling keystore, node identity or signing material is copied.

Destination is a fresh 256 GiB virtual ext4 image at
`W:/FusionRestart/restored-backup-2026-10-19/startup.ext4`, containing
`/checkpoint`. It is distinct from the final replay image and all protected
backups/recovery/fallbacks. No existing image is attached or changed. Preserve
all failed output and partial files. There is no retry, cleanup deletion or
D: expansion. Native ext4 is needed because direct DrvFs LevelDB directory
fsync failed in the retained storage qualification. Reuse the existing migration
launch/copy/read-only-reattach helpers; the source provenance and observers now
refer to the complete original backup and the final-tip evidence.

The parent holds the backup LOCK shared and the image-owner lock exclusive.
Only one image/job is allowed, with no node/replay/observer running beforehand.
Source is bind-mounted read-only, each copied file is hashed against the original
manifest and fsynced, metadata is preserved, then the destination is unmounted,
filesystem-checked and detached. Reattach read-only, verify the UUID, hash all
copied files again, and run the two existing hash-pinned cold observers.
Require the exact final-tip state/ticket/header/receipt/TD observation, 491 tickets
and one transaction/receipt. Verify source/destination metadata and observer
identities again. The final replay database is never opened by this job.

Private mount/network namespaces, only loopback down, UID 1000 workers,
nice 10 and GOMAXPROCS=1 remain. W: is the already authorized backing share;
no chain peers or external services are contacted. Host mapping is verified.
Start requires more than 21/51/356 GiB free Linux/D:/W:, charging the entire
256 GiB virtual ceiling to W: plus its reserve. Workers sample Linux/D:/W:/image
reserves of 20/50/100/20 GiB every 30 seconds during loops. Capacity is checked
before each phase. New space use on Linux/D: is limited to control activity;
evidence is on C: and bulk bytes on W:.

Each copy/verification phase retains a 12,600-second cooperative deadline and
12,720-second external timeout, with 20 seconds kill grace. The whole job has
28,800 seconds plus 20 seconds kill grace: up to seven hours for both phases
and one hour for formatting, checks and detach. This explicit larger whole-job
bound reflects the 109.12 GiB complete backup versus the earlier 44 GiB copy.
Format/filesystem check each cap at 1,200 seconds; observers at five minutes
(four minutes internal). Bounds can stop an unfinished job; elapsed time does
not waive verification. A failed job remains failed and requires diagnosis.

Before dispatch, check the adapted source-copy guards with a small isolated
fixture: correct copy, incorrect expected hash and existing destination. Verify
the original backup manifest and final-tip evidence provenance. These checks
exercise the adapted fixture preparation, not unchanged consensus/runtime cases.

Completion requires verification.json, migration.json, cleanup.json, outer
completion.json and host exit all passing, then actual detached-state review
and sealed evidence. This establishes a byte-exact, cold-readable fixture, not
writable startup or independent operator acceptance. A subsequent separate
bounded startup/restart job can use this disposable image with the retained
unselected CLI and a test-only trusted mainnet anchor. It must check identity,
normal-pruning shutdown and cold restart without signing, mining or networking.
Human consensus/accepted-parent review and final selected recovery/handover
remain open. No further historical replay or unchanged small rerun is justified.

Review of the reused migration's cold-head log found that its invocation was
skipped because FULL_AUDIT was not set. Its separate cold-details observation
and complete copied-file hashes remain recorded; do not count that skipped
invocation as a head check. The final replay's two observers actually ran and
passed. This preparation explicitly sets the audit/source environment, uses the
retained test working directory and pinned responses, and requires actual PASS
markers with no SKIP plus the exact head line. Original evidence is unchanged.
