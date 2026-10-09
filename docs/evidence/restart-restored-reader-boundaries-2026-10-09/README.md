# Restored startup reader boundaries — 9 October 2026

**PASS: ten in-memory characterization cases, not a startup safeguard.**
The existing recovery reader checks configuration presence and agreement of the
stored heads. It does not authenticate the expected network or open the head's
state/body during construction. Reusing it alone would leave the F12 restored-
startup requirement incomplete. This is a boundary of a low-level reader, not a
new consensus finding or a claim that recovery signing bypasses its own checks.

The [verifier result](verification.json), [test output](qualification/boundaries.stdout.txt)
and [fixture](qualification/reader_test.go) retain the exact observations.

| Fixture | `NewReader` result | Additional observation |
| --- | --- | --- |
| Complete historical mainnet genesis | Accept | Head state opens and body exists |
| Empty database | Refuse | Missing DaTong configuration |
| Missing DaTong configuration | Refuse | Missing DaTong configuration |
| Split full/header/fast/canonical heads | Refuse | Heads disagree |
| Missing head header and its number index | Refuse | Cannot establish agreeing heads |
| Different genesis, same chain ID | Accept | Does not authenticate expected genesis |
| Mainnet genesis, wrong stored chain ID | Accept | Returns the stored chain ID |
| Mainnet genesis, changed stored fork schedule | Accept | Returns the stored fork schedule |
| Missing head state trie root | Accept | Subsequent `StateAt` fails |
| Missing head body | Accept | Subsequent `GetBlock` returns nil |

Every case compares all database key/value contents before and after reader
construction and subsequent observations. They remain identical. This is an
in-memory observation; it does not establish LevelDB locking, filesystem path
handling, service refusal before writes, or absence of all filesystem side effects.
Opening a state root also does not prove every descendant account/storage/code
entry is available. The separate complete-state checks retain that scope.

## Identity and bounds

- Investigation parent: `3d754b61c648bdcda01c2314ccdff7bc8d490ba7`.
- Retained encoder-candidate **recovery** source from 8 October, with all 1,211
  source files checked before and after. The preceding candidate bundle's 352
  manifested files verify. No F11 patch or source-selection change was added.
- Pinned Go 1.27.1; toolchain identity and full environment are in
  [run.json](qualification/run.json). The test binary SHA256 is
  `a3076e6b5fb605ea2c767328fc179cf964e15389959a5d112b61699da0c4f856`.
- One Go overlay adds the fixture without writing to the retained candidate.
  Mainnet-genesis assertions depend on its legacy-compatible encoder; this is
  not a qualification of the unchanged modern-compiler baseline.
- Separate network namespace, only loopback present and down; uid 1000;
  offline module settings, `GOMAXPROCS=1`, build `-p=1`, niceness 10.
- Build ceiling three minutes; test timeout 60 seconds, external ceiling
  90 seconds, ten-second kill grace. Build and test both return zero.
- Run: 12:57:30–12:57:35 UTC. Retained run files before the final JSON occupied
  11,473,443 logical bytes, including the local executable. No historical
  database was opened, copied or hashed. Replay continued independently.
- Free space before: 30,347,796,480 bytes Linux / 61,292,204,032 bytes D:;
  after: 30,331,129,856 / 61,292,204,032. These are shared-volume readings during
  replay, not isolated attribution of disk consumption. Floors were 21/51 GiB
  for this small cached build; the historical job retains its separate limits.

The fixture was temporarily placed at `internal/recovery/reader_test.go` in
the investigation checkout, then copied into this bundle by the runner. That
temporary file was removed after verification; no package test or runtime
source change is part of this commit. Its bytes remain preserved here. The
executed scripts and their recorded hashes are unchanged. To reproduce in a
separate review checkout, restore that fixture path, use a fresh result/bundle
directory and review the explicitly pinned parent/source identities. Never
rerun into this sealed bundle. `verify.py` can check the retained result without
running Go or opening a database.

## Next bounded acceptance work

The next candidate should enforce the existing supported restore policy before
ordinary node construction opens or initializes writable chain data. Keep this
separate from ticket fork choice and ongoing finality. Inspect existing launch
and configuration paths before choosing the smallest implementation; no shipping
guard or release input is selected by this report.

1. Bind the resolved datadir and expected network configuration to the reviewed
   release/restore inputs. An untrusted local marker or chain ID alone is
   insufficient. The trusted package manifest and expected genesis have distinct
   roles: exact file hashes authenticate a cold restore, not every later restart.
2. Demonstrate refusal of an absent/empty directory, mispointed database, wrong
   genesis, wrong chain ID and inconsistent fork/anchor configuration **before**
   the service or writable chain database starts. Compare cold files and process
   outcomes, including refusal without automatic genesis initialization/repair.
3. Exercise minimum head readiness separately: internally consistent heads,
   readable head header/body and available required state/tickets. Reuse existing
   complete-state integrity evidence; do not claim a cheap root-open check is a
   complete state scan. Distinguish repair/recovery from normal launch behavior.
4. Reuse the existing fixed-anchor validation. Authenticate the accepted restore
   base and support legitimate later descendants; do not freeze routine startup
   to the original backup head or its original file hashes. Preserve the existing
   distinction between catching up below an anchor and being ready to produce.
5. Prove a valid restored node can start, advance within an isolated synthetic
   chain, stop and restart. Check the actual CLI/service path so a passing helper
   test cannot mask a missing call site. Begin with small data, not another large
   restore beside the active replay.
6. Keep recovery-tool parent/plan authentication and its test-key handover
   acceptance separate from ordinary post-recovery startup. The eventual public
   recovery anchor cannot be assumed to exist before it has been constructed and
   approved. Real-key operations and production selection remain outside testing.

Existing unchanged anchor, package, recovery and handover cases do not need a
blanket rerun. Add cases only for a changed path or an uncovered acceptance
condition. F12/G1 and final selected-candidate acceptance remain open.
