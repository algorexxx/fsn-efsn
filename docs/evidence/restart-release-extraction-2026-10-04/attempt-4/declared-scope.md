# Production patch extraction

4 October 2026. Inputs are pinned in `selection.json`: upstream `c5f0174d`
and investigation `6ecc753f`. This is a proposed review bundle, not an approved
release. No source file in the investigation checkout is modified by extraction.

## Declared acceptance before execution

1. Account for every changed non-test Go file as node, recovery tool or excluded
   observer. Keep gateway/deployment changes and test/evidence files separate.
2. Apply the node patch to a clean upstream export and verify the complete Go
   source inventory. Build `cmd/efsn` without recovery or observer sources.
3. Apply optional O1 and rebuild. Apply the recovery-tool patch separately and
   build its command. Require exact selected source hashes after each stage.
4. Overlay pinned investigation test files and the existing public fixture.
   Run the selected anchor, rollback, reconstruction, parent isolation, cold
   header, purchase/miner and snapshot/read-only regressions with Linux race
   detection. The shell runner gives package checks three minutes and the
   restart executable six minutes. Unexpected failure or skip is not acceptance.
5. Record apply/build/test exits, toolchain, binary hashes, source hashes and
   namespace/capacity observations. No network interface is brought up. Reserve
   at least 10 GiB inside Linux before creating the disposable source tree.

Go 1.21.3 is the existing offline rehearsal toolchain, not a final release
selection. This check establishes extraction/build independence and the selected
regressions; it does not close the whole release matrix, reproduce a final
release build twice, activate a mainnet anchor or exercise real signing.

## Contents and use

- `01-node.patch`: P1–P17, 33 production Go files. Shared-file hunks stay together
  so the combined candidate can be built; the review IDs are not separate
  independently applicable patches.
- `02-optional-bootstrap-trim.patch`: O1 only, two replacements in the v4 CLI
  list parser. Apply after patch 01 if retained. The inherited v5 parser stays
  exactly as upstream.
- `03-recovery-tool.patch`: ten recovery command/package files and the
  `SigningPayload` accessor in the shared consensus file. Apply after patch 01;
  it is independent of the optional trimming patch.
- `selection.json`: file boundaries, source/patch hashes, excluded observer and
  deployment paths. `input-archives.json` pins the clean upstream and test-overlay
  archives plus each test input; archives remain under ignored `tmp`.
- `extract.py`: reproduces the bundle from the two Git commits, refusing reuse
  of its scratch directory. `verify-tree.py` checks all Go files at each stage.
- `run-linux.sh`: applies/builds/checks in a new `/tmp` tree in WSL. Invoke through
  a private network namespace, as root for namespace creation and ownership;
  builds and tests run as the existing `rehearsal` user. It refuses existing work
  and result directories and never opens a blockchain backup.

The first extraction attempt stopped at a uniqueness assertion before writing
patches: the generic bootnodes expression also exists in the unchanged v5
function. The corrected extractor limits both O1 replacements to
`setBootstrapNodes`, preserving v5 byte-for-byte. This is an extraction-script
correction, not a node defect or change.

The complete extraction run built all three commands, but one of eight storage
fault cases failed before fault injection: the fixture stopped the controller
before waiting for its initial submission-failure warning. Cancellation suppresses
that warning in the production controller. Patch 04 changes test ordering only:
observe the expected warning before stopping for the `has`/`get` setup, while
keeping the delete setup stopped before block import. No timeout, assertion or
production source changes. The original failure remains in `attempt-3`.

Correction acceptance is declared as all eight storage cases once (three-minute
outer timeout), then the two affected `has`/`get` cases three times each
(two-minute outer timeout), using the same extracted production source and race
detection. `attempt-4` verifies the entire source tree before and after the one
explicit test patch. The other twelve selected restart groups already passed;
they are not repeated because this helper is used only by the storage cases.
Final correction results are pending. See the [release matrix](../../restart-release-matrix.md)
and [patch inventory](../../restart-node-patch-review.md) for required independent
review, existing evidence and final acceptance boundaries.
