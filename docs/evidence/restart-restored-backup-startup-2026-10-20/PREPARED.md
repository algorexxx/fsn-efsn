# Complete-backup writable startup and restart

Prepared 20 October 2026, after verified fixture-copy commit `2f2c9b70`.
This closes a distinct acceptance gap: the retained unselected guard/encoder CLI
has passed synthetic lifecycle and read-only complete-backup checks, but has not
started writable and restarted against the complete original history.
No further historical range exists in this backup. Existing passing small
refusals, synthetic pruning and read-only backup checks are not rerun.

Use only the separate, disposable
`W:\FusionRestart\restored-backup-2026-10-19\startup.ext4`, 256 GiB, UUID
`0b18a87d-e8ee-413f-b37f-01eec39b0c48`, database `/checkpoint`.
The 56,107-file copy's full readback and actual cold readers passed; its seal is
`583a515b708a24fc835a7dbe41eb23b2db0d1d230f0a261bd684575095236069`.
The original backup, protected final replay image, local fallback, separate
recovery checkpoint, archives and previous failed/sealed evidence remain retained.
There is no automatic cleanup, overwrite, retry or second owner.

The existing actual CLI SHA-256 is
`07aa74a3f58132e5ff1465152402d5ea3b01738c0017af5dfd5672a75a2550cd`.
Its complete retained source inventory and frozen offline TOML are checked before
and after each phase. No executable is rebuilt. `profile.json` carries the
mainnet configuration from that pinned source, unchanged fork heights and a
test-only anchor at the independently recorded backup endpoint 15,130,080.
This is not a production parent decision or a release-selection change.
The CLI's existing test injection is used only in this private fixture.

Sequence:

1. Verify all sealed inputs, copy evidence, executable/source identities, capacity,
   absence of another image/process, common image-owner lock and actual backup
   shared LOCK. Enter private mount and network namespaces, only loopback DOWN.
2. Bind the original backup read-only. Attach only the disposable image read-only,
   verify UUID and geometry, then rehash every closed database file against the
   original sealed manifest. Require unchanged exact backup metadata.
3. Detach, reattach writable, check filesystem without repair, and create a fresh
   runtime datadir inside the disposable image. Bind `/checkpoint` as its
   `efsn/chaindata`. Run normal full-sync/full-pruning service startup and then a
   separate fresh CLI process, each querying the exact expected head/hash/root/
   ticket commitment and false mining/automatic ticket purchase.
4. Require read-only restored guard before writable protocol initialization and
   clean shutdown state writes at 15,130,080, 15,130,079 and 15,129,953 for each
   process. Reject panic, fatal/critical errors, failed recent-state commits,
   dangling tries, wrong endpoints or unexpected keystore material.
5. Unmount, check filesystem without repair, detach and reattach read-only.
   Hash all closed post-startup database files; run the pinned actual cold-head
   and detailed readers with FULL_AUDIT enabled, reject skipped tests, and compare
   the exact full endpoint against sealed historical evidence. Require unchanged
   read-only metadata, original backup and all executable/source identities.
6. Detach and record cleanup, host exit, protected metadata and resource evidence.
   Preserve partial/failed runs. A later independent record review and evidence
   seal are required before claiming this acceptance complete.

Only one CLI process runs at a time as uid 1000, nice 10, GOMAXPROCS=1, cache64.
Discovery/dialing, HTTP/WS, IPC, mining, auto-buy and USB are disabled. P2P ports
are isolated in the private network namespace. The fresh runtime can contain an
ephemeral node identity, never real signing keys; no node-key file is exported
to evidence. There is no local block import, key signing or external peer contact.

Limits: entire host job 28,800 seconds plus 20 seconds forced-stop grace. Each
hash phase has a 12,600-second cooperative and 12,720-second external limit.
Each CLI invocation is capped at 600 seconds plus 20 seconds; combined CLI phase
at 1,500 seconds. Cold readers use 240-second internal/300-second external caps.
Filesystem checks are capped at 1,200 seconds. Whole-job cap takes precedence.
Thirty-second samples retain >20/50/100/20 GiB Linux/D:/W:/image reserves;
CLI sampling also enforces <128 GiB allocated database size. Starting reserves
include another GiB on Linux, D: and W:. No further D: expansion is authorized.
No LevelDB hashes are taken while writable; metadata-only allocation sampling
during CLI execution is distinct from content hashing.

The launcher adapts the sealed complete-copy job's namespace, command, loop
identity and cleanup helpers, omitting creation/format/copy. The worker reuses
that sealed job's exact file/provenance helpers and the earlier normal-pruning
acceptance requirements. `checks.py` validates the test profile against the
pinned source and exercises acceptance on preserved passing logs plus wrong-head,
missing-guard, missing-shutdown and failed-commit mutations. It does not rerun
the prior node tests. `adaptation.patch` preserves launcher differences.

This qualification still cannot close selected-release startup, independent
codec/consensus and parent trust review, arbitrary pruning recovery, real-key
handover or complete portable-package acceptance. Evaluate those distinct gaps
only after this job's completion and verification; do not run a duplicate writer.
