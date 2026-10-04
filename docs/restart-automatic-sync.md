# Unknown heavier histories through automatic full sync

4 October 2026. This closes the bounded investigation gap in R8 of the
[release matrix](restart-release-matrix.md). The new
[test](../tests/restart/automatic_sync_linux_test.go) uses the existing Linux
service harness and complete synthetic history. It changes no production code
and leaves the compiled mainnet recovery anchor unset.

## Fixture and checks

Four small, separate LevelDBs share a normally executed synthetic genesis and
24 blocks. Public fixture keys 1 and 2 construct two continuations: four accepted
blocks, with height 25 fixed as the anchor, and six incompatible blocks. Their
cumulative difficulties are **484** and **498** respectively; the shared parent
has difficulty **372**. The foreign branch is genuinely heavier under the
existing calculation. No foreign header or body is stored in any receiver before
connection. Additional receiver databases import the same shared/accepted blocks
through ordinary validation during fixture preparation.

The services use real devp2p over enabled loopback in a private network namespace,
with discovery disabled. The ordinary ten-second sync scheduler drives full sync.
There is no `lab_sync` call, post-connection manual import or active miner/buyer.
The fixture uses fixed historical timestamps; blocks are already signed before
the transport assertions, and services produce no signatures during them.

| Case | Required outcome |
| --- | --- |
| Compatible catch-up | Receiver at 24, configured for anchor 25, automatically reaches accepted head 28. |
| Anchored refusal | Receiver at 28 sees the unknown, heavier foreign head 30; downloader explicitly rejects the mismatch at 25, reporting both hashes. Accepted heads and canonical lookups remain intact. |
| Unanchored control | A receiver with the same accepted history but no anchor adopts that exact foreign head 30. Accepted-branch transaction/receipt lookups cease to be canonical. |

Each case checks canonical headers and every successor transaction and successful
receipt, all three persisted head markers, state root and ticket commitment. The
receiver then shuts down cleanly and starts in a fresh process with the same
checks repeated. Re-injected pending transactions are permitted in the control,
but cannot retain canonical block or receipt lookups.

## Results and reproduction

The first race-enabled run passed all three cases in **43.39 seconds**. Its custom
hash summaries used a raw-byte formatting verb; the downloader's rejection line
already contained correct hexadecimal identities. A test-only formatting
correction makes the custom summaries readable. The final run passes all three
cases in **43.42 seconds** (45.74 seconds including the race-detector exit wait).
Compatible catch-up took 9.06 seconds, anchored refusal 9.08 seconds and the
unanchored switch 9.57 seconds from connection initiation. All original limits
were met, with no skipped selected case or race report. The final run and its
exact source/binary identities are retained alongside the first in the
[evidence bundle](evidence/restart-automatic-sync-2026-10-04).

The runner verifies the prior clean extraction tree before copying it, overlays
only the two test files, records all source-file hashes and hashes the executable
before execution. It uses the existing offline Go 1.21.3 Linux amd64 toolchain
with CGO and race detection. Source and executables remain in separate Linux
results directories; no preserved-history data or real key is opened.

Entry point: `TestRestartNodeRehearsal/unknown_heavier_automatic_sync`, with
`FUSION_RESTART_NODE_REHEARSAL=1`. The namespace guard requires exactly one
enabled loopback interface. The preserved runner contains setup and build
commands and refuses existing result directories. Declared bounds remain 24
shared blocks, four accepted successors, at most twelve foreign successors,
90 seconds per connection/sync result and six minutes for the complete test.

## What this establishes

The receiver can discover and download previously unknown incompatible ancestry
through ordinary scheduling, and the fixed anchor rejects it even when the
foreign chain is heavier. The passing unanchored control establishes that refusal
is caused by the anchor rather than an inability to connect or synchronize.

This is a shallow synthetic fork and an embedded real node service, not a final
release CLI, a year-long fork, full historical replay, a state-download test or a
mainnet launch. Clean reopen checks commitments and lookups, not power-loss
durability or an independent implementation's state ledger. Compatible forks
after the same anchor still follow ordinary fork choice; no ongoing finality is
added. Final selected-source/toolchain and actual-host acceptance remain in R8/R9.
Historical baseline replay remains verified through 3,300,000.
