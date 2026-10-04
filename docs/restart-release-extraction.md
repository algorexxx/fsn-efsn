# Proposed release patch extraction

4 October 2026. The production changes are now available as three separate
review patches against upstream. Extraction adds no node behavior and does not
approve the release, toolchain, mainnet anchor or deployment.

Upstream: `c5f0174d88ab2b9c3086c6a9cc9ccf38a072992f`.
Investigation input: `6ecc753f00f6c6ec9ee7ad3855f2f8ff71f1f711`.
The patches contain only changes already present at that investigation commit.

## Review artifacts

| Artifact | Proposed contents | Size |
| --- | --- | --- |
| [01-node.patch](evidence/restart-release-extraction-2026-10-04/01-node.patch) | P1–P17, excluding the recovery signing accessor and optional list trimming | 33 Go files; 109 hunks; 1,145 added / 261 removed lines |
| [02-optional-bootstrap-trim.patch](evidence/restart-release-extraction-2026-10-04/02-optional-bootstrap-trim.patch) | O1: trim/filter explicit v4 bootstrap lists | One file; two added / two removed lines |
| [03-recovery-tool.patch](evidence/restart-release-extraction-2026-10-04/03-recovery-tool.patch) | Ten recovery command/package files plus `SigningPayload` in the shared consensus file | 11 files; 1,494 added lines |

Apply patch 01 to the pinned upstream revision. Patch 02 is optional. Patch 03
depends on 01 and can be applied with or without 02. The build check uses them
in numbered order. Retain the upstream license notices and module identity.

[selection.json](evidence/restart-release-extraction-2026-10-04/selection.json)
pins every included file's before/after hash and each patch hash. The
[hunk map](evidence/restart-release-extraction-2026-10-04/hunk-map.json) assigns
every node hunk to its [P1–P17 review IDs](restart-node-patch-review.md), with
patch line numbers and old/new ranges. A hunk spanning two corrections retains
both IDs; this is not a claim that the 17 rows apply independently.

All 17 observer command/package files are excluded. Gateway Docker/setup/service
changes, root documentation and Git attributes/ignore settings are also excluded
and listed separately. Module manifests are unchanged from upstream. No test or
evidence file is silently included in the production patch.

The largest new node files are the automatic-purchase controller (324 lines),
anchor checks (177) and DNS bootstrap handling (155). These are already in the
review inventory; extraction neither expands their scope nor creates new patch
categories. The real compiled mainnet anchor is still unset.

## Verification

The [evidence bundle](evidence/restart-release-extraction-2026-10-04) records a
clean upstream archive, patch application, complete Go-file inventories, build
inputs, tests and binary hashes. The input archives occupy about 26 MiB; all
builds use disposable Linux source and output directories. No backup, replay
database or real signing key is opened.

Builds use the existing offline Linux amd64 Go 1.21.3 toolchain with CGO enabled,
read-only module resolution and no active network interface. The node is first
built while both recovery and observer sources are absent. Its dependency list
is checked for those packages. Optional O1 is then applied and the node rebuilt;
only afterward are recovery sources applied and their command built.

The selected regression overlay excludes observer tests. It is pinned separately
to the same investigation commit and includes the existing public fixture.
These checks validate extraction and selected behavior, not all ten groups in
the [release matrix](restart-release-matrix.md). They do not approve Go 1.21.3
for production or establish two-build reproducibility for the final release.

The first complete extraction run passed all three builds and twelve of the
thirteen selected restart test groups, including all 36 anchor-enforcement cases.
The storage-error group failed its `has` setup while waiting for the initial
submission-failure warning. Source inspection identifies a test ordering race:
`awaitSubmission` observes the backend result before the controller reports it;
calling `Stop` immediately cancels the context and can suppress that report.

The [test-only patch](evidence/restart-release-extraction-2026-10-04/04-test-ordering.patch)
waits for the required warning before stopping in the `has`/`get` setup. The
`delete` setup still stops before block import. Timers, fault injection, saved-byte
assertions and production code are unchanged. All eight storage cases pass in 97.13 seconds; three
additional repetitions of each affected case also pass with race detection.
The original failed run remains evidence, not an overall passing run.

Snapshot framing and read-only corruption checks passed with race detection.
The initial `params` filter matched no tests; a separate explicit
`TestCheckCompatible` run passed. All checks meet their original deadlines,
with no skipped selected case or race report. The other twelve restart groups
were not rerun: the changed helper is used only by the eight storage cases.

The final correction run reconstructs the small source tree from pinned archives
and repeats all three builds successfully. It checks 821 exact Go files for the
node-only stage, 831 with recovery tooling and 951 with the selected tests. The
only change to that last inventory is the separately hashed test correction.
The final binary hashes are in
[attempt 4](evidence/restart-release-extraction-2026-10-04/attempt-4/binaries.sha256).
The initial failing test executable disappeared with its temporary source tree;
its source/runner/log are retained, but no binary hash is claimed for that run.
The final reconstructed source/binaries remain under
`/home/rehearsal/results/restart-release-extraction-2026-10-04` in FusionRehearsal.

Two earlier attempts stopped at patch application because Windows Git converted
archive text to CRLF. Disabling `core.autocrlf` alone retained native CRLF output;
explicit `core.eol=lf` produces archive bytes identical to the pinned blobs.
The failed logs, runners and archive identities are preserved. No patch context
check was weakened and no runtime correction was needed. The extractor's earlier
v4/v5 uniqueness guard correction is also recorded in the bundle.

## Next bounded sync check

R8 can reuse `seedDenseMinerPair`, `buildAnchorBranch`, `closeTwoMinerSeed` and the
existing process/IPC harness. No further historical database copy is needed.
The planned fixture has 24 shared synthetic blocks, four accepted successors
with the first as anchor, and at most twelve competing successors. Blocks use
ordinary DaTong validation and public test keys; actual cumulative difficulty
must establish that the competing branch is strictly heavier.

Three cases are sufficient: compatible automatic catch-up across the anchor;
an initially unknown incompatible branch refused by an anchored receiver; and
an unanchored control that adopts that same heavier branch. Use the ordinary
ten-second sync scheduler, with at most 90 seconds for each sync result and a
six-minute outer deadline. Do not use `lab_sync` or pre-store foreign ancestry.

The negative case must observe the actual anchor rejection, including the
expected/foreign identity, rather than infer protection from lack of progress.
Check accepted canonical transactions/receipts and all three head markers, then
reopen and compare state/ticket commitments. Keep both mining and automatic
buying stopped during these transport assertions. This is a defined next test,
not a passing result or a year-long fork simulation.

Independent review and final patch/toolchain selection remain open. The
historical baseline is still verified through 3,300,000; extraction does not
extend that replay or establish historical compatibility of these patches.
