# F11 recovery CLI configuration binding

7 October 2026. Four top-level tests and ten subtests pass with race detection
on Go 1.27.1. This completes the remaining bounded CLI check from
[phase 2](../../restart-state-rollback-qualification.md), following the
[startup/reader integration](../restart-state-rollback-integration-2026-10-07/README.md).
The F11 candidate remains unselected; no production activation is configured.

## What was exercised

The fixture invokes the real `runCommand` dispatcher, argument parsing,
`runReview`, `buildReviewReport`, `recovery.Build` and `runPrepare` in the
`cmd/fsn-recovery` package. It uses temporary LevelDB databases, real report and
approval files, the DaTong engine and an ordinary synthetic ticket purchase.
There are no replacement runtime methods or database responses.

| Cases | Required observation / result |
| --- | --- |
| Legacy schedule resolved, already matching schedule, unselected rule, other genesis with the same chain ID, custom schedule | All five reports contain the independently expected configuration JSON. Prepared policies contain its independently calculated SHA-256, the intended first-stage identity/role, and the running test executable's checksum. The reviewed unsigned block bytes are retained. |
| Schedule removed or changed in the saved report | Both are rejected by the complete canonical-report comparison; no approval output is created. |
| Prior approval with matching, legacy or different configuration checksum | Matching context succeeds. The other two are rejected by the prior-policy runtime check, even when the supplied digest correctly identifies the changed prior file; no output is created. |
| Stored configuration conflicts with the registered schedule | Review fails at reader configuration resolution before creating a report. |

Every case compares all chain key/value contents before and after. All remain
unchanged. This is a logical database-content check, not a claim that LevelDB
never touches lock/log files. The earlier integration bundle separately counts
database mutation attempts on its reader/startup cases.

The expected configuration vectors come from `config_vectors.py`, using Python
JSON and SHA-256 over a literal synthetic configuration in the declared Go
field order. They are not copied from observed Go output. These vectors include
the early execution forks required by this purchase fixture and therefore have
different hashes from the earlier reader-only fixture.

## Scope and provenance

The fixture has a fixed timestamp, one genesis ticket, a funded purchase owner
and one unsigned successor block. Its synthetic chain is temporarily registered
as the test network when the case requires that branch; globals are restored
after each case and cases are not parallelized. Custom cases retain the real
registered hash so their synthetic genesis remains a different network.
This does not retest or resolve F12's default-mainnet genesis mismatch.

The purchase is signed only with the public test scalar `2`, constructed in
memory. No real key is loaded, no block is signed or imported, no signing
journal is initialized, and nothing is published. The prior-approval positive
control reuses the first-stage context to isolate configuration binding; it
does not claim to test progression through the three-block handover.

These are in-process CLI-entry tests inside a Go test executable. Its checksum
is the executable identity used by the approval fixture. A separately launched
production executable, full service restart and actual recovery approvals
remain part of the final rehearsal. The report builder executes and finalizes
the ordinary purchase in memory, but this supplies no F11 rollback, persisted
state, accepted-block or historical compatibility result. Phases 3 and 4 remain
open, along with independent review of the inactive missing-header rejection.

`run.py` uses the immutable candidate overlay from `8357c5fe`, checks its
manifest and the recorded base-source hashes, and additionally checks the five
CLI/builder/approval source files in `cli-source-inputs.json` before and after
execution. Selected source and module inputs remain unchanged.

`launch.py` creates a private network namespace and drops to UID 1000 before
running Go. `qualification/run.json` records distinct parent/child namespace
IDs, a down loopback link, exact command, toolchain environment, overlay input
hashes, timestamps, capacity and exit code. Cached dependencies/offline flags
supplement that isolation. The test used two workers, a two-minute inner and
seven-minute outer timeout; the existing free-space floors were checked. No
backup restore or large disk workload was needed.

The first run passed; there are no omitted failed attempts in this bundle.
`verify.py` checks retained inputs, prior manifests, vectors and selected source
hashes; its result is in `verification.json`. `SHA256SUMS` covers this bundle's
files byte-for-byte. For a repeat, use a fresh runner/output location; preserve
this evidence and do not overwrite its recorded run directory.
