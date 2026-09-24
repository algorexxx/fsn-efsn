# Guarded recovery and two-node evidence

24 September 2026. Baseline `a17f56be630b4077977f05d0771a3952881391af`
plus the changes identified in `identities.json`. Go 1.21.3 on Windows/amd64
and Linux/amd64; Linux test executables use race detection.

Read [the investigation report](../../restart-recovery-construction.md) for
scope, identities and remaining gates. Every signature belongs to public test
key 1 or 2. These blocks are synthetic evidence, never production anchors.

## Successful checks

| Evidence | Result |
| --- | --- |
| `step-*-command.txt`, `step-*-readonly.txt` | Three actual Windows command invocations; all 232/233/234 LevelDB files unchanged respectively |
| `construction/` | Three reviewed plans, signed public-test purchases, unsigned reports, sealed blocks and complete account-difference ledgers |
| `windows-focused-correct-directory.txt` | Guard success, 17 rejection cases, unfunded replacement rejection; logical database unchanged |
| `windows-command-unit-final.txt` | Command compilation and successful-receipt/native-error rejection, even with otherwise matching ticket fields |
| `linux-focused-race.txt` | Guard and missing-recovery-purchase counterexamples, twice under race detection |
| `linux-command-unit-final.txt` | Command compilation and strengthened native-error check under race detection |
| `linux-v5-two-nodes-race.txt` | Full-state services, three guarded blocks, two ordinary worker blocks, SIGKILL/reopen, one more worker block, peer/downloader catch-up, two cold ledgers and six-block ownership audit |
| `node-blocks/` | All six final blocks and complete account-difference/receipt/ticket ledgers |
| `linux-v5-existing-node-cases-race.txt` | All four existing service/anchor cases pass with the final harness |
| `windows-prior-ten-block-audit.txt` | Earlier ten-block evidence still passes the generalized accounting helper |

`fixture/` contains the original complete-state substitution ledger, the separate
donation funding ledger, original artifact identity and copy proof. The existing
256-header/body context is retained in
`../restart-full-state-2026-09-24/context.rlp`. The report's final six-block state
was reopened and compared but was not subjected to another complete trie scan.

## Retained failures

- `windows-focused.txt`: test invoked from the repository root instead of
  `tests/restart`; failed to locate the relative RPC fixture. The correctly
  located rerun passes. No chain logic failed in that invocation.
- `linux-two-nodes-race.txt`: first guarded block passed, then a stale advertised
  peer head caused downloader ancestor search to leave the available full-body
  context. The test constructor subsequently gained the ordinary mined-block
  announcement event. The compact artifact remains unsuitable for general
  historical synchronization or complete bloom indexing.
- `linux-v2-two-nodes-race.txt`: three peer-imported controlled blocks and two
  automatic blocks passed, then an exclusive-create helper refused to overwrite
  the test node's restart configuration. Corrected only the harness writer.
- `linux-v3-two-nodes-race.txt`: cold production resumed with an identical
  nonce-5 purchase (`0x42db9e30dc36b1441c8daf79812ce3a55a8ab8cb8c57500017d27cd6e687a83f`),
  but the subsequent peer connection did not finish within ten seconds. This
  run also used a changed ephemeral listening port after restart.
- `linux-v4-two-nodes-race.txt`: fixed port, same ten-second peer timeout. The
  client's existing `dialHistoryExpiration` is 30 seconds. The final v5 harness
  allows 45 seconds; no production peer timing was changed.

The expected `canonical block #1 unknown` bloom-index messages describe the
fixture's missing history and remain visible even in passing runs. They are not
a claim that historical log queries are ready for operators.

## Reproduction and retained paths

The scripts refuse existing target paths and retain failed runs. Do not delete
the preserved source or overwrite a prior result to rerun them.

1. Build `./cmd/fsn-recovery` into `tmp/fsn-recovery.exe` and compile
   `./tests/restart` into `tmp/recovery-construction-tests.exe` with Go 1.21.3,
   cached dependencies and `CGO_ENABLED=0` on Windows.
2. `run-windows.ps1` checks the 230-file original state artifact manifest, copies
   it onto C:, prepares public-key substitutions, constructs the three reviewed
   blocks in separate stopped-database phases and checks read-only behavior.
3. `prepare-nodes.ps1 -RunName recovery-node-v5` creates fresh checked node copies
   and copies the reviewed construction artifacts. Choose new names and update
   the script paths for any subsequent run.
4. `check-linux-v5.sh` builds from `tmp/recovery-guard-base.tar` (the baseline Git
   archive) plus the listed new/modified sources. It runs the service test in a
   new enabled-loopback-only namespace. Its `legacy` mode runs the four existing
   node cases in another private namespace.

Closed disposable data retained under the workspace:

- `tmp/guarded-recovery-constructor`: reviewed three-block prefix.
- `tmp/guarded-recovery-backup` / `donation`: first failed service attempt.
- `tmp/recovery-node-v2`, `v3`, `v4`: subsequent failed harness attempts.
- `tmp/recovery-node-v5/guarded-recovery-backup` and `guarded-recovery-donation`:
  final matching six-block heads, both stopped.
- `tmp/recovery-guard-linux*-src` and the named Windows/Linux executables:
  retained source/build inputs, with executable hashes recorded.

The original `tmp/preserved-head-state` artifact is unchanged. No new chain
copies or historical replay were placed on D:. Node processes are stopped;
there are no ongoing public services or mining jobs from this rehearsal.
