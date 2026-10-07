# F11 isolated candidate and configuration qualification

7 October 2026. Prepared after `ca26e108` on the investigation branch.
**Unselected candidate; no mainnet activation height.** The production
selection remains P1–P17+B1+D1. No files in either selected source tree, the
working checkout's runtime directories, or the preserved chain were changed.

This implements the candidate described by the
[disposition proposal](../../restart-state-rollback-disposition.md). It does
not close F11 or establish a corrected transaction, committed state or block.

## Review artifacts

- [candidate-node.patch](candidate-node.patch): applies to the selected node tree.
- [candidate-recovery.patch](candidate-recovery.patch): applies to the selected
  recovery tree, including its offline reader. The node tree does not contain
  that reader, so the two application patches differ deliberately.
- [candidate-v2.patch](candidate-v2.patch): combined review diff, including
  the new configuration tests. Use the appropriate tree-specific patch above
  when applying to a selected tree.
- [base-inputs.json](base-inputs.json): source paths, exact pre-change hashes,
  availability in each tree and module hashes.
- `inputs/`: exact formatted overlay sources used by the successful run.
- [qualification-v2/run.json](qualification-v2/run.json): commands, working
  directories, timestamps, exits, compiler environment per selection, input
  hashes and built-binary hashes. Binaries remain in the local rehearsal
  results directory; they are not release artifacts.
- [verification.json](verification.json): patch application checks, unchanged
  selected inputs and the exact limited StateDB delta.
- [qualification specification](../../restart-state-rollback-qualification.md):
  remaining acceptance work and its limits.

`prepare.py` copies only the eight touched existing files from the selected
inputs and makes checked edits. The two new parameter files are in `inputs/`.
`qualify.py` generates the combined patch, runs the parameter suite and builds
the two commands using Go overlays. `verify.py` checks hashes and generates
the per-tree application patches without applying them. These artifacts are
frozen; runners refuse reuse of their output paths. Use a fresh directory for
any new experiment, preserving this record.

## Candidate scope

Eight runtime files are affected across both selected trees:

| Area | Candidate change |
| --- | --- |
| `params/config.go` and new `params/suicide_timelock_fix.go` | Optional serialized fork height; inclusive block rules; compatibility check; shared mainnet schedule resolver. Defaults remain unset. |
| `core/vm/interface.go`, `noop.go`, `instructions.go` | Required rule parameter passed from the EVM's block-specific rules to StateDB. |
| `core/state/statedb.go` | The parameter sets the time-lock journal discriminator. Removing those two additions exactly reproduces the selected original file. No journal or account-encoding implementation was changed. |
| `core/genesis.go` | Resolve and validate the schedule before configuration writes; report this rule's active incompatibility as an ordinary startup error before the backend's rewind path. |
| `internal/recovery/chain.go` | Resolve the same effective configuration in memory while keeping the database read-only. Existing approval hashing therefore sees the effective schedule. |

Two test files accompany those changes: a new parameter test file and the
one-argument call adaptation in the selected legacy `statedb_test.go`.
That adaptation is not a state-suite port. The separately retained modernized
state fixtures still require an explicit API adaptation for future candidate
tests; do not overwrite or reinterpret their original evidence.

For recognized mainnet, a future approved schedule may fill a missing legacy
field only before activation. A missing field at/after activation, a conflicting
schedule, an invalid height or the wrong chain identity is rejected. An
unselected build rejects a supplied mainnet schedule. Other genesis identities
retain their own validated schedule. No command-line bypass was added.

This is not a general startup refactor. The candidate also moves the persisted
header-height lookup ahead of the missing-config and custom-chain return paths;
those paths now require a recorded header height. Integration qualification
must account for that behavior, as well as the new rule itself.

## Observed results

| Check | Result |
| --- | --- |
| Complete selected-node `params` suite with race detection | PASS: five top-level tests, including 28 new table subtests and one JSON serialization test. |
| Selected-node `efsn` candidate build | PASS. |
| Selected-recovery `fsn-recovery` candidate build | PASS. |
| Patch applicability to each unchanged selected source tree | PASS, without applying patches. |
| Both attempts' input hashes and selected source/module hashes | PASS. |
| State/EVM rollback, transaction/commit, block import, startup integration, recovery approval integration and historical replay | Not run in this pass. |

The successful run used Go 1.27.1, Linux amd64 v1, CGO, two workers and cached
dependencies. The parameter suite had a two-minute test timeout; each command
had a seven-minute outer limit. Capacity floors were 30 GiB in Linux and
60 GiB on D:. No backup copy, network-drive restore or chain replay was used.

The successful launcher created a private network namespace before dropping
to the rehearsal user (UID 1000). The run records different nonempty parent
and child namespace IDs and only a down loopback device. Go dependency
downloads were also disabled. This records the isolation mechanism and its
observed state; no packet-capture claim is made. The launcher command was:

```powershell
wsl.exe -d FusionRehearsal -u root -- python3 /mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-state-rollback-candidate-2026-10-07/launch.py
```

Root was used to create the namespace; the compiler and tests ran as rehearsal.
Do not run that frozen command again expecting new evidence in the same paths.

The [initial attempt note](attempt-1-note.md) explains its incorrect JSON
expectation and incomplete namespace comparison. `candidate.patch`, the
archived test/runner and `qualification/` preserve that failed attempt. The
test correction follows the selected source's `omitempty` tag, not a copied
observed result. Production candidate sources were identical between attempts.

The next acceptance work is startup and recovery integration using disposable
small databases, followed by the retained rollback comparisons and the explicit
transaction/block boundary review. F11-b, independent review and G1 historical
compatibility remain open; no release approval follows from these builds.
