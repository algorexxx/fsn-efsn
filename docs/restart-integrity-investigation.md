# Complete integrity checks and replay — 23 September 2026

The Linux investigation was committed as `bf71410` on
`codex/restart-investigation-wip`. This follow-up adds read-only full-data checks
and a bounded historical replay runner, committed as `d82a229`. All baseline
data checks and replay use unchanged production code. The subsequent
[corrections](restart-corrections.md) are tested in a separate source tree.

## Complete-data checks

`TestPreservedStateIntegrity` traverses every reachable account and its storage,
rebuilds their Merkle roots using a separate stack trie, and checks every
referenced code/native-data blob against its committed Keccak hash. Iterator
errors are checked for each trie. This is stronger than opening the root or
looking up selected accounts, but still depends on this client's trie/RLP
implementation. Address-preimage coverage and unreachable database records are
not included.

`TestPreservedHistoryIntegrity` scans canonical heights zero through 15,130,080.
It checks canonical block identity, number indexes, parent links, transaction
commitments, decoded receipt commitments/blooms, and accumulated difficulty. It
also totals the RLP block-stream size to inform export/replay capacity planning.
An absent receipt record is allowed only for a transaction-free block with an
empty receipt root, and is counted explicitly. Malformed stored receipt data
does not take that exception.

The history scan does not execute transactions, verify signatures/ticket
selection, validate every historical state, or inventory transaction lookup
indexes. Fusion uses the header's uncle-hash field for its PoS commitment;
ordinary Ethereum uncle-root validation would be inappropriate here. Its
`VerifyUncles` currently returns nil. These checks must not be described as full
independent consensus verification.

A later [read-only ticket inventory probe](restart-observer-preserved-inventory.md)
confirms sparse historical state in this same backup. Twelve sampled headers
exist, but only the head, head minus one and head minus 127 samples expose their
ticket state; even head minus two is unavailable. That is consistent with the
client's shutdown checkpoints, not a continuous recent-state guarantee. Preserve
the observer's wallet baselines before restart production.

Checker tests exercise intact in-memory data and deliberately missing/corrupt
account roots, storage roots, code, bodies, receipts, total difficulty,
transactions and parent links. All eleven cases passed before the real scan.

The full scan started at 20:21:26 UTC in a private mount/network namespace,
with the verified database mounted read-only. Its live log is
`/home/rehearsal/results/restart-integrity-2026-09-23/full-integrity.txt`.
The complete current-state scan passed in 1,287.81 seconds: 801,355 accounts,
2,886,305 storage leaves, and 33,437 code/native-data references totalling
262,368,983 referenced bytes. The rebuilt root matches the observed head and
no missing/corrupt reachable data was reported. References can share blobs;
these are not unique code-size totals.

The complete history scan also passed, finishing at 23:28:23 UTC on 23 September.
It checked 15,130,081 blocks including genesis, 419,409,946 transactions and the
same number of receipts, with no absent empty-block receipt records. The final
hash matches `B`, and accumulated difficulty is 63,370,514,513. The history phase
took 9,928.76 seconds. Its calculated block-stream RLP size is 76,291,252,333
bytes (about 71.05 GiB); this excludes receipt/state/database overhead and is
not an export artifact or a complete backup-size estimate. Completed logs and
isolation/exit records are in [the follow-up evidence](evidence/restart-validation-2026-09-24).

## Replay pilot

The unchanged client replayed genesis through block 10,000 in a newly created
database at `/home/rehearsal/replay/baseline-10000`. The source remained mounted
read-only, with no network, node service, or signing key involved.

| Item | Observed |
| --- | --- |
| Runtime | 71.95 seconds, while the separate state scan was active |
| Logical database size after clean shutdown | 117,083,563 bytes |
| Final block hash | `0x1830e440e17cda3a26d02ea650331a584d58a499cbbd3821c622568c8de9b470` |
| Final state root | `0xc85623ffdf98796fb39d437ceff4626b7aa56bb5ee12c8b1491a7524ad85cfbf` |
| Ticket commitment | `0x0f8a8be52d2df5f43c50a33049c1594252d48c6fb523fc35adac5c27750c5456` |
| Tickets | 1,817 |
| Legacy checkpoint range retained | Through height 2,680,000 |

This is a successful baseline execution pilot. The legacy checkpoint range
still skips normal ticket-seal checks and raw-transaction validation, while
retaining the checks the old code performs before that shortcut. The pilot
therefore does not establish independent verification of ticket consensus.
Later transaction volume and state size can differ sharply; do not extrapolate
its runtime or bytes per block into a reliable full-replay estimate.

The existing CLI import handler logs `ImportChain` errors but can return nil.
The rehearsal runner instead fails on an import error or unexpected head and
checks the resulting ticket commitment. The initial pilot accepted only a new
output directory; the later validated resume mode is described below. Before each 128-block
batch it checks reserves of 50 GiB on the Windows host drive and 20 GiB inside
Linux. Cleanup stops the chain and closes the output database so a controlled
test failure does not intentionally discard pending state.

D: is a Samsung SSD 970 EVO 500GB NVMe device, reported healthy by Windows.
The pilot left 78,689,280,000 bytes available in Linux and 151,710,142,464 bytes
on D:. The 200 GB virtual-disk capacity is a separate limit from host free space.
No additional full database, network archive, or long replay has been assumed
to fit. The existing C: preservation copy and explorer gateway remain intact.

A second fresh replay through 100,000 blocks passed in 397.06 seconds
(20:46:38–20:53:15 UTC). Its closed database occupies 227,214,790 bytes.
The final hash is `0x0e4a4045c06984472f86bb8f1e40bb70dee87b6227877ffcaeab7624db745cd2`,
root `0x95697b558879524bead323328c9e97adce259ac7047a2140107704bf930d4741`,
and ticket commitment `0x1860459771b267e3b319ed899deb55a4ab973562f0d923309263244e1630020d`
with 2,630 tickets. Both pilot databases are retained. The smaller incremental
growth illustrates why a fixed bytes-per-block estimate from the first pilot
would have been misleading; it still does not establish the full replay size.

## Replay continuation and bounded long runs

The later runner records the exact executable hash, source genesis/head and
source/replay configurations in a target manifest. Reuse requires explicit
`FUSION_RESTART_REPLAY_RESUME=1` and an identical manifest. Before writable open,
it checks the target's genesis/configuration, all three head pointers, head body
and receipt commitments, cumulative difficulty and available head ticket state
against the preserved source. Startup must retain that validated head. A missing
state after an unclean termination fails preflight; it does not authorize a
silent rewind or manual manifest rewrite.

Continuation testing created a fresh database through 1,024, rejected accidental
reuse and an end below the existing head, stopped through the explicit stop-file
path, then resumed to 10,000 with the same hash/root/ticket commitment as the
original fresh pilot. A deliberately mismatched executable identity was also
rejected; the test restored the original manifest afterward. These intentional
nonzero test exits are expected rejection evidence, not successful replays.

At 21:02:03 UTC the first million-block baseline phase started in a new database:

- Source: `/home/rehearsal/data/efsn/chaindata`, read-only mount in a private
  mount/network namespace.
- Retained executable: `/home/rehearsal/replay-resume-tests`, compiled from the
  baseline production tree with the updated replay harness.
- Target: `/home/rehearsal/replay/baseline-mainnet`.
- Results: `/home/rehearsal/results/restart-replay-million-2026-09-23`.
- End height: 1,000,000. This bounded first phase completed successfully, not a full-chain replay.
- Stop file: `/home/rehearsal/replay/STOP-baseline-mainnet`. Creating it requests
  a controlled test failure at the next batch boundary, followed by normal
  chain/database cleanup. Do not terminate WSL to pause a replay.

The first million-block phase finished at 22:14:08 UTC on 23 September after
4,324.80 seconds. Its closed database occupies 1,158,354,931 bytes (about 1.08
GiB), with 4,598 tickets. The resulting commitments are:

- Block: `0x4b0d0d5a0739c801c3d4fe91258d3b9ddf81f471464e221921442ea503d711a6`.
- State: `0x882b7092542a98dfd38dcc253304b17e7d713dcc2aed65222399e0042ec81ad3`.
- Tickets: `0xe8850a91eff584a180740c12f9279a5ce973fb57884c43b75466fbe9d3c3b614`.

After confirming exit code zero, no remaining writer and the retained executable
identity, continuation to **2,000,000** started at 05:40:23 UTC on 24 September.
The preflight successfully reopened and validated height 1,000,000 before
resuming. This phase completed at 07:22:21 UTC, with exit zero after 5,928.57
seconds. It remains within the original checkpoint shortcut range. Its result directory is
`/home/rehearsal/results/restart-replay-two-million-2026-09-24`; the source,
target, executable and stop-file paths above are unchanged. The runner adds
a writer lock and preserves the existing 20 GiB Linux / 50 GiB Windows reserves.
At launch Linux had 76,551,995,392 free bytes and D: had 87,101,820,928 free bytes.
Available host space had fallen since the previous phase, so capacity is checked
throughout instead of assuming the full replay fits.

At 06:42:36 UTC on 24 September, while the separate anchor prototype was being
tested, this replay had reached 1,604,288 with no reported import failure.
Linux had 75,352,391,680 free bytes and D: had 79,522,516,992. The retained replay
executable still matched its original digest. This is an intermediate observation,
not phase-completion evidence; see the [sampled log and capacity record](evidence/restart-anchor-implementation-2026-09-24/replay-progress.txt).

Do not run two writers or edit the retained executable. Any later extension must
first confirm completion/clean shutdown and use that same executable with
explicit resume and a newly chosen end. The old 10,000/100,000 pilot targets
predate the identity manifest and are not eligible for automatic resume.
Full replay remains conditional on continued storage checks and results.

The exact machine-specific runner scripts are archived in
[the evidence runners](evidence/restart-integrity-2026-09-23/runners). Invoke
isolation scripts through `wsl -d FusionRehearsal -u root --exec unshare --mount
--net --propagation private -- bash <script-path>`. Review their target/result
paths before reusing them; most intentionally reject an existing target.

## Historical reconstruction check

The read-only `TestPreservedTicketReconstruction` validates the signatures and
ticket selection of actual headers 15,129,955 through 15,130,080, then repeats
each validation with its parent state deliberately unavailable and the ticket
cache evicted. At the final header it also forces reconstruction across 16 and
126 missing state roots, back to retained state 15,129,953. All 128 cases pass
on the unchanged client, with identical selected/retreated tickets. These recent
heights are outside the legacy checkpoint range. No blocks are signed or written.
This is real historical reconstruction coverage; it does not include an expiry
boundary, for which the synthetic tests remain the demonstrated regression.

The existing miner package tests do not compile on the baseline: they reference
removed `ethash`/`clique` symbols, the old `newWorker` signature and old balance
APIs. DaTong has no package tests. This pre-existing test-suite gap is recorded
in `baseline-package-tests.txt`; the dedicated restart tests exercise the actual
miner through an external test package without silently repairing or excluding
those stale files.

Completed logs, isolation records and source hashes are preserved in
[the original evidence directory](evidence/restart-integrity-2026-09-23) and
[the completed-scan/continuation evidence](evidence/restart-validation-2026-09-24).
The completed two-million phase is archived in the
[node rehearsal evidence](evidence/restart-node-rehearsal-2026-09-24).
The closed replay database occupies 2,261,867,399 bytes (about 2.11 GiB), with
5,449 tickets. All final commitments match the source:

- Block: `0x4592c42db8ddf3343dc242770d13de5d158c5e7fc1120870805b1e8731ed43cf`.
- State: `0x3c3a1d38a0f4022f738b8e494becb823867562b7424166043e76df69543f04a2`.
- Tickets: `0x5ec663a1a3e90d9270733d5aa20d99108f4d0d12e5e2c99e71a5a87bf666ba5b`.

At completion Linux had 74,905,395,200 free bytes and D: had 74,497,351,680.
Continuation to the next bounded target, 2,700,000, started at 08:00:40 UTC on
24 September. The read-only preflight validated the complete 2,000,000 head
before writable resume. This phase was stopped cleanly before its target; its
results directory is
`/home/rehearsal/results/restart-replay-checkpoint-boundary-2026-09-24` and its
[exact runner](evidence/restart-node-rehearsal-2026-09-24/run-replay-checkpoint-boundary.sh)
is archived. The intended target crosses the last legacy checkpoint at
2,680,000; it does not retroactively remove verification shortcuts from earlier
blocks. The source, retained executable, target, identity manifest and per-batch
20 GiB Linux / 50 GiB Windows reserves remain unchanged. Full historical execution
remains pending.

At 10:34:28 UTC on 24 September the existing stop-file mechanism closed the
replay after block 2,613,376, before attempting 2,613,377. This was an intentional
storage stop as D: approached its 50 GiB reserve; exit code 1 records the stop
request, not an invalid historical block. The closed database occupies
3,736,629,446 bytes. A fresh process with both source and replay mounted read-only
passed the existing resume checks and an exact-height check: all three heads,
canonical identity, transaction/receipt commitments and bloom, cumulative
difficulty, available head state and ticket commitment agree with the source.

- Block: `0xa701593c60162b41f1fdb21c4bb06dee3ab3f1330c2a9d6f4186a57f8f97f858`.
- State: `0xccd632d317aa6881d339cacb90c56db337639dbc4f8fc488a2a7afeec0c0dd27`.
- Tickets: `0xadea244a3f8392d706a4d41fd812b4c055f4952791e8235f0910b6ff4385a5f5`.

The [state-export evidence](evidence/restart-state-export-2026-09-24) retains the
closed replay log and cold inspection. The original retained replay executable
and identity manifest are unchanged. The stop file remains present. Do not
resume that D: target until host capacity again satisfies the reserve;
archive/remove that explicit stop request only as part of a deliberate validated
resume.

C: has enough space for a separate working copy. With the D: replay mounted
read-only, all 1,694 files (3,736,629,446 bytes) were copied into the ignored
workspace directory `tmp/replay-mainnet-c`. Every destination file was reread
and its SHA-256/length checked against the source; the inventory was checked
before writing a completed-copy marker. The original D: checkpoint is preserved.
This uses NTFS through WSL for a bounded disposable replay, following the
extraction's filesystem-specific process-crash/reopen checks. It does not change
the eventual production storage decision.

The retained original executable resumed that C: copy at 10:51:04 UTC, with the
original source mounted read-only and no networking. Its ordinary resume preflight
checked the identity and source commitments before writable open. It retained the 20 GiB
output-filesystem / 50 GiB host reserve, now correctly naming `/mnt/c` as the
host drive. Results are in
`/home/rehearsal/results/restart-replay-c-storage-2026-09-24`; the copy and run
scripts are retained in the [state-export evidence](evidence/restart-state-export-2026-09-24).
Its separate optional stop file is
`C:/Users/Peter/Documents/CODING/fsn-efsn/tmp/STOP-replay-mainnet-c`.
The C: phase completed successfully at 11:15:52 UTC on 24 September 2026,
reporting 1,406.51 test seconds. The closed database occupies 3,978,652,725 bytes
(about 3.71 GiB), with 4,851 tickets. It reached 2,700,000 with all final
commitments matching the preserved source:

- Block: `0xfa99e1a18636a767938436e35708e8583fe031abf7d16d6cf04149bccfce2ac6`.
- State: `0x5745b4d10f3725fe2ee65457802e7e94e19242dfae0ca285ef1666b447e56d4a`.
- Tickets: `0x7fbbb4af2e6e4ea56f9b5451a0d7114313517ae9a5f23eca6beafaad8a6889c2`.

A fresh, isolated process with source and C: replay mounted read-only then
passed the exact-height and resume-invariant checks in 37.74 seconds. This
completes the checkpoint-boundary gate, including 20,000 subsequent blocks under
the ordinary checks outside the legacy shortcut range. It does not retroactively
validate the skipped historical ticket seals/raw-transaction checks or complete
the remaining history through 15,130,080. Neither replay copy has an active writer.

## D: continuation through 3,000,000

On 25 September, after D: recovered to roughly 162 GiB free, the user authorized
the next bounded replay. A new Linux ext4 target,
`/home/rehearsal/replay/baseline-mainnet-three-million`, received the closed C:
checkpoint: 1,836 files totaling 3,978,652,725 bytes. Every destination length and
SHA-256 was checked against the read-only source. Neither the original D:
checkpoint nor the C: checkpoint is reused as the new writable target.

An independent read-only check again matched exactly 2,700,000, in 8.49 seconds.
The unchanged retained replay executable began continuation at 12:16:18 UTC,
targeting exactly 3,000,000. It performs its own identity and head preflight
before writable open. This is baseline execution, not historical validation of
the newer P1–P9 candidate changes. All new blocks lie beyond the legacy
checkpoint shortcut range, but earlier shortcut coverage is not retroactively
strengthened.

The wrapper uses private mount/network namespaces, read-only source history and
checkpoint mounts, the existing 20 GiB Linux / 50 GiB Windows per-batch reserves,
and a sampled 20 GiB total working-directory allowance that requests a clean
stop. It automatically runs a separate read-only exact-height/head/state/ticket
check after successful completion. Only that check writes `verified.txt`.

The run completed successfully on 25 September. The test reports 4,452.18
seconds (74 minutes 12 seconds); the wrapper recorded completion at 13:33:32
UTC, and the separate cold check passed in 12.81 seconds. Final acceptance was
recorded at 13:33:45 UTC, about 77 minutes 27 seconds after the wrapper start.
Both replay exit code and exact-height cold check pass; the process has exited.

The closed target contains 4,988,076,554 logical bytes (about 4.65 GiB), or
4,992,933,888 allocated bytes. Its logical growth from the copied checkpoint is
1,009,423,829 bytes (about 0.94 GiB). The size monitor recorded no errors and did
not request a stop. At completion D: had 166,929,305,600 bytes free (about
155.47 GiB), while Linux had 65,357,578,240 bytes free (about 60.87 GiB). Neither
reserve was approached; this measured growth is not a full-replay size estimate.

At height 3,000,000, the replay and source agree on 4,652 tickets and these
commitments, also confirmed after closing and reopening read-only:

- Block: `0xc43580bdd7ff045050c5b555fc1bf1c0f663223c19fd597eef469a258cdb22ab`.
- State: `0x0c335e82c32a866e9e86e0fc9f9d8c04eb1dc152d1aa2ccc770c07dc2078459a`.
- Tickets: `0xb56ef7f45f19f42e4af92715c425e18629c13df1c1fbec58b1a88be319e1dc1b`.

The final check also verifies persisted full/header/fast heads, canonical indexes,
head transaction/receipt commitments, bloom, cumulative difficulty and available
head state against the preserved source. The retained baseline has now executed
320,000 blocks beyond the legacy checkpoint boundary; the remaining history
through 15,130,080 and historical execution of the newer candidate patches are
still separate work. At that completion, no replay beyond 3,000,000 had been
launched.

Original Linux results are
`/home/rehearsal/results/restart-replay-three-million-2026-09-25`;
the explicit clean-stop file is
`/home/rehearsal/replay/STOP-baseline-mainnet-three-million`.
Scripts, startup and final evidence are retained in
[the three-million evidence directory](evidence/restart-replay-three-million-2026-09-25).

## D: continuation through 3,300,000 — complete

On 4 October, fresh capacity checks found about 62.2 GiB available inside Linux
and 112.3 GiB on D:. The existing reserves permit another bounded range. The
closed three-million checkpoint remains preserved; a new D:-backed Linux ext4
target at `/home/rehearsal/replay/baseline-mainnet-3300000` received its 2,351 files,
totaling 4,988,076,554 bytes. Every copied file was reread and checked for SHA-256
and length, with the complete inventory verified before replay.

The separate read-only checkpoint check passed at exactly 3,000,000 in 4.89
seconds. The unchanged retained baseline executable resumed at 13:28:37 UTC
(15:28:37 Stockholm), targeting exactly 3,300,000. The startup capture at
13:29:50 UTC records progress through 3,004,608 and makes no completion claim.
Replay passed in 4,555.02 seconds. The wrapper recorded completion at
14:45:28 UTC; the independent read-only exact-height check passed in 9.52 seconds
and wrote its verified marker at 14:45:38 UTC (16:45:38 Stockholm).

| Final checkpoint | Observed |
| --- | --- |
| Height | 3,300,000 |
| Block hash | `0x74a4fb230a6ee77b9f6e8ca536d7b2e0ffb4abd9796de23ef37c7951cc31583b` |
| State root | `0x8c54be811459cc46df46350d9b2266652806a07fe9cff87a592e42fdeb0f7045` |
| Ticket commitment | `0xfe0cce5c894d9a202ea3a8cf751c2c1eb70436626793b33443da21300aea5143` |
| Tickets | 4,716 |
| Closed logical / allocated bytes | 6,521,468,908 / 6,527,746,048 |
| Linux / D: free bytes at completion | 60,154,019,840 / 113,771,839,488 |

Replay and cold inspection agree with the preserved source. The unchanged
baseline has now executed 620,000 blocks beyond the legacy shortcut boundary;
those earlier shortcuts remain. The size monitor reported no error. The range
stopped at its requested height. A later continuation is recorded below.

The reused runner checks the retained executable hashes, holds source and target
runner locks, mounts original history and checkpoint read-only, and uses private
mount/network namespaces. It preserves the existing 20 GiB Linux / 50 GiB D:
free-space reserves and sampled 20 GiB target allowance. After copying, Linux
had 61,801,828,352 available bytes and D: had 116,254,617,600. No W: storage is
used, and no large copy is placed on C:. No real key or signing is involved.

This continues baseline historical execution above the legacy shortcut boundary.
It does not establish historical compatibility of the current P1–P17 candidate
patches or complete the remaining history through 15,130,080. The runner ends
at the bounded target; it does not launch a further range automatically.

Live Linux results are
`/home/rehearsal/results/restart-replay-3300000-2026-10-04`;
the explicit clean-stop path is
`/home/rehearsal/replay/STOP-baseline-mainnet-3300000`.
The [range evidence directory](evidence/restart-replay-3300000-2026-10-04)
retains scripts, checksummed copy/preflight records, the provisional startup
snapshot and final acceptance. `final-capture.json` records `completion_claim=true`
only after exit code zero, the exact-height cold check and verified marker were
present. The earlier startup capture remains explicitly provisional.

## D: continuation through 3,600,000 — complete after monitor recovery

Fresh checks later on 4 October found 58,757,775,360 free bytes inside Linux
(54.7 GiB) and 112,664,543,232 on D: (104.9 GiB). The completed 3,300,000
checkpoint remains preserved and mounted read-only. Its new separate copy at
`/home/rehearsal/replay/baseline-mainnet-3600000` verified all 3,026 files and
6,521,468,908 bytes by SHA-256, length and complete inventory after rereading.
No W: storage or large C: copy is needed for this range.

The independent read-only checkpoint check passed at exactly 3,300,000 in
5.51 seconds, matching the block hash, state root and ticket commitment recorded
above. The same retained baseline executable resumed at 17:40:48 UTC
(19:40:48 Stockholm), targeting 3,600,000. The provisional capture at
17:44:29 UTC records progress through 3,314,336, 48.60 GiB Linux / 95.96 GiB D:
free, no size-monitor errors and a latest allocated-size sample of
6,560,456,704 bytes. This is progress evidence, not final acceptance.

The runner preserves the previous source/destination locking, executable hash
checks, read-only source/checkpoint mounts, private network namespace, 128-block
batch checks and 12-hour ceiling. The existing 20 GiB Linux / 50 GiB D: free-space
reserves and sampled 20 GiB target allowance remain unchanged. It stops at the
requested height and launches no further range automatically. The verified
baseline remains 3,300,000 until replay exits zero and a separate fresh read-only
exact-height 3,600,000 check passes. Candidate-patch compatibility and the rest
of the history through 15,130,080 remain open.

Live results are `/home/rehearsal/results/restart-replay-3600000-2026-10-04`;
the clean-stop request path is
`/home/rehearsal/replay/STOP-baseline-mainnet-3600000`.
The [range evidence directory](evidence/restart-replay-3600000-2026-10-04)
retains the runner and checksummed startup records with `completion_claim=false`.
This range changes no node code and involves no real keys or signing.

Later update: the original run stopped at 18:32:38 UTC, before block 3,521,057,
after `du` could not stat three disappearing `.ldb` files. It exited 1 through
the existing clean-stop path. No block/state mismatch was reported. A separate
read-only inspection passed at 3,521,056 in 6.98 seconds, with hash
`0xfff6ae4ff23211b76165e8b5201fd1a8719aa65e3b46d926245ca07a353228aa`,
root `0x92b1b7a3f89f0f6605bc742758f327bcde2fa3e75f384d35dacc6299d1b08399`
and ticket commitment
`0xa5cdd2d349d602bffea2ff6da359e1297da94dcbb3c5c0f9efc7daeba4e228b2`.
The closed copy occupies 7,289,987,072 allocated bytes. Logs are retained under
the evidence directory's `stopped/` folder; this is not a successful 3,600,000 run.

After a first continuation preflight correctly refused a missing read-only
mount, the corrected wrapper resumed the same validated disposable copy at
18:44:57 UTC, with 46.25 GiB Linux / 93.43 GiB D: free before starting. No bulk
copy or replay-code change was needed. Three bounded size-measurement attempts
now allow transient failures to recover; all errors are retained and persistent
failure still requests a stop. Existing reserves and workload limits remain.
New results are `/home/rehearsal/results/restart-replay-3600000-resume-v2-2026-10-04`;
the new stop path is `/home/rehearsal/replay/STOP-baseline-mainnet-3600000-resume-v2`.
The final exact-height cold check remains pending. Use `status.py --resume` for
current progress; original failures and complete 3,300,000 checkpoint remain intact.

Final update: the resumed replay passed in 1,024.07 seconds; its wrapper recorded
exit zero at 19:03:13 UTC. A separate process then passed the exact-height
read-only cold check in 10.39 seconds, writing the verified marker at
19:03:25 UTC. Both checks match height 3,600,000 and these preserved commitments:

| Commitment | Value |
| --- | --- |
| Block hash | `0x1013c88fb0a8be3b78a0a3acdb287f6e9a6f65e81353aadaccac7a580a5a1c74` |
| State root | `0xff355f1211571f85f3f3c6731db375c6d7c581a8e0c70db1f82382752f3ca0e8` |
| Ticket commitment | `0x09785f30d672027af83e75cb7e71882e52d84d40282d1ebc6f74a977b0fb79d1` |
| Replayed active tickets | 4,549 |

Final cold allocation is 7,534,972,928 bytes. The final evidence capture found
45.84 GiB Linux / 93.02 GiB D: free, with no resumed monitor errors. The
[completion capture](evidence/restart-replay-3600000-2026-10-04/resume/resume-final-capture.json)
records true only after checking both passes. The original exit-1 run remains
a monitor interruption with a separately validated stopped head. Original data
and previous checkpoints remain preserved. The unchanged baseline is now
complete through 3,600,000, subject to its recorded legacy shortcuts; later
history and patched-client compatibility remain open. No new range has started.

## Next gates

1. Continue bounded execution replay, investigating any failure. Current-state
   traversal and complete structural history validation have both passed;
   neither substitutes for full historical execution.
2. Use the measured export size and progressively measured replay growth to
   choose the full replay layout. W: remains a preservation option requiring a
   fresh accessibility/capacity check. The preserved source and D: checkpoint
   remain on Linux ext4; the latest replay uses a new D:-backed ext4 target, while
   the completed C: checkpoint and compact export remain preserved. Production
   storage is still a separate decision.
3. Retain explicit distinction between replay with historical checkpoint
   shortcuts and any subsequent stricter verification experiment.
4. Prepare the demonstrated corrections and then the full-state recovery and
   restart-anchor rehearsals under the signing/artifact policy in the main plan.
