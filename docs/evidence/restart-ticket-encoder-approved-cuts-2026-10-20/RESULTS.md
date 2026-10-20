# Candidate approved-signing interruption acceptance

Passed on 20 October 2026 at 06:08:52 UTC, including preservation checks, source
unmount and host exit. The separate [record/artifact review](verification.json)
passes. Preparation/start records are historical and are superseded by this result.

All three selected tests and thirteen subtests pass with race detection, no
skips, no race reports and empty stderr:

- Nine completed-signature cuts: completion, export and import at each of three
  recovery stages. Exact bytes are recovered without another signing callback;
  independent imports and fresh cold ledger checks agree.
- Two uncertain cuts: reservation and signature. Repeat signing and export
  refuse; chain bytes stay unchanged.
- Eight changed-approval refusals, plus digest, executable/configuration
  identity and legacy-journal/wrapper bypass refusals.
- Credential preflight keeps both chain and journal locks. A wrong password
  permits retry; an ambiguous signature attempt refuses subsequent key access.

The nine archived recovered blocks match their independently constructed
reference bytes. The six original exports also match. All seven fixture cases
produce the same three reference blocks; uncertain/refused cases have no export.
The retained tests enforce public scalars 1/2 only.

The race-enabled harness SHA-256 is
`1d1aa86ed667833b3e58052eec1932d2adb69ba0c9a992dd6cd88de31c4a7370`.
Runtime code is the unchanged retained candidate-recovery selection plus the
unselected encoder. Source, compiler, input and executable identities passed
before/after checks. The 109-file completed-operator and 139-file regression
evidence seals were verified before execution.

All seven small synthetic cases remain in the matching C: `tmp/` directory,
including both uncertain attempts. Their 348 closed-file hashes are preserved;
50 small reviewable artifacts are archived here. The sole fixture behavior
adaptation retains temporary directories instead of deleting them. Three
inherited helper import groups received blank separators before input freezing;
the initial formatting observation and provenance are retained. Runtime and
assertion logic did not change.

All nine resource samples pass. Minimum free capacity: Linux 21.47 GiB,
D: 50.95 GiB, C: 242.37 GiB. Peak sampled logical job size was 0.274 GiB against
its 4 GiB cap. Build/test commands took 125.008/46.019 monotonic seconds and
finished within their 900/960-second limits. Total worker duration was 261.241
seconds, within the 2,100-second cooperative and 2,400-second host limits.

The 06:09:58 UTC actual-state check finds no test/node/build process, matching
mount or loop device, and the investigation owner lock is free. Original backup,
local fallback and independent recovery metadata remain unchanged. Both detached
W: image sizes and UTC timestamp ticks match. No historical database or image
content was opened or hashed by this test.

Together with the [complete-state command result](../restart-ticket-encoder-full-state-operator-2026-10-20/RESULTS.md),
the candidate now has bounded success-path and approved interruption/refusal
evidence. Additional unchanged tests do not resolve the remaining review gates.
The currently authorized local F12/G1/startup/recovery acceptance investigation
is ready for independent review; no further test is queued.

Still required: independent codec/consensus and maintenance review, an explicit
accepted-parent/trust decision including early replay shortcuts and missing
samples, release-selection decisions and final package/clean-host acceptance,
and real-address/timing/funding/key-custody review. F5/F10/F11 dispositions and
other final release gates remain as recorded in the canonical plan.
This run does not change the release selection or authorize signing, mining,
network contact or production activation. It does not certify power-loss
durability, journal rollback/copy resistance or independent human approval.
