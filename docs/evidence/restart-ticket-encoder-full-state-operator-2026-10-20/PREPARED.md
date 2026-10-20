# Candidate complete-state recovery command and handover

Prepared 20 October 2026 after complete-backup startup evidence commit
`0b1616e8`. The completed startup bundle has 145 sealed files, manifest
`21ad995e396685a4e6e97ff84a5c7a0beab7bcbfe3203edb3667435011da48c0`.
Its actual commands, cold checks, resource records and detached post-state have
been reviewed. No historical range or repeated backup copy is needed.

## Evidence value and precise scope

The 8 October encoder regression qualified sparse synthetic recovery fixtures.
The 25 September complete-state operator workflow qualified the legacy encoder
and Go 1.21.3. This test fills that intersection for the unselected candidate:
the unchanged recovery source selected for D1 plus the exact candidate encoder,
using the already pinned Go 1.27.1 toolchain. It does not add the node startup
guard to the separate recovery command or change the release selection.

Run only `TestFullStateRecoveryOperator`. Reuse the 13 retained fixture/helper
selections recorded in `harness-provenance.json`; extracted declaration bodies
are byte-exact, with only unused imports omitted. Both core operator test files
still match their sealed September source hashes. No runtime implementation is
changed. The current retained candidate-recovery inventory has 1,225 files;
its earlier test harness is replaced only in a new disposable source copy.
The original retained source and selected source stay untouched.

Build the actual `cmd/fsn-recovery` executable and the test executable with
`-race -p=1 -trimpath -buildvcs=false`. Toolchain executable SHA-256:
`30969f97169d7f43fe6a085873d75613adc21e30818a8c61d95bd27275df4624`.
Verify the preceding candidate regression manifest
`59bea0c464a9a089518e3454c646b381369691f3f4e00ee774730a4c8c2b400c`,
the completed startup seal, all runtime source identities and fixture input pins.

## Fixture and observations

Use three fresh copies of `tmp/preserved-head-state`: reference, working and
verifier. Each has 230 files and 528,817,080 bytes, checked against the original
compact export manifest
`a6c86fc58a9f7b482a02b787a337d600e32a447551e45dbe40d210b498341bbf`.
The source is mounted read-only and locked during copying/hash verification.
All destination hashes are checked before use; original source hashes and
metadata are checked again after the test. This compact export contains complete
account state and retained historical context, not complete block history.

Existing helpers substitute only the explicitly audited public scalar 1 and 2
identities and balances on disposable copies. The three stages exercise actual
review, preparation, journal initialization, encrypted public-test-key signing
and export; wrong-password and altered-report/export refusals are part of that
same workflow. Twelve fresh import/cold-check child processes verify working
and verifier states. Compare all eleven reference plan/block/ledger/substitution
artifacts byte-for-byte with the sealed legacy evidence. Require the exact
PASS marker, all three command-stage observations, no skipped test, no race
warning, and unchanged stopped-chain hashes during command operations.

Closed destination inventories are hashed only after all children exit.
Command reports, test artifacts, binary/source hashes, commands, failures,
resource samples and cleanup are retained. Full trie traversal and previously
passing interruption/refusal suites are not repeated.

## Capacity, isolation and finite limits

Fresh read-only capacity observation: C: approximately 246 GiB free, Linux
21.47 GiB and D: 50.95 GiB. All new source, build cache, temporary files, binaries
and roughly 1.48 GiB initial fixture copies use C:. W: image files receive
Windows metadata observations only; neither image is attached or changed.
The existing W: filesystem is not mounted in this WSL namespace and is not
needed for this test. No storage expansion, archival or cleanup is needed.

Require 50 GiB free on C: and 2 GiB host RAM at dispatch; sample running reserves
of 40/20/50 GiB on C:/Linux/D: and a 12 GiB logical disposable-work ceiling
every 30 seconds during subprocesses. Capacity stops are sampled, not quotas.
Use GOMAXPROCS=1 and GOMEMLIMIT=512MiB, with all Go dependency fetching disabled.

Private mount/network namespaces must differ from the parent and contain only
loopback down. The shared investigation owner lock and a compact-source owner
lock prevent another compliant writer. Refuse efsn/replay/recovery/build
processes and all image loops except separately identified, read-only autoclear
Docker ISO loops. No loop or existing host service is changed.

Command build is bounded to 1,200 seconds, harness build to 900 seconds and the
test to 600 seconds internally / 660 seconds externally, each with a 20-second
termination grace. Worker deadline is 3,300 seconds cooperatively / 3,420 seconds
externally, within a 3,600-second host cap. Any nonzero exit or failed observation
is incomplete evidence; never retry an existing directory or dispatch claim.
Keep every failed attempt. Empty read-only mountpoints are retained after unmount.

Original backup, local fallback and independent recovery metadata are recorded
before and after without opening those databases. Windows records both retained
W: images' size and modification time before and after. All originals, failed
runs, sealed evidence and independent checkpoints remain preserved.

## Limits

This is Linux candidate acceptance against the same implementation's independent
processes and existing deterministic legacy artifacts. It does not supply an
independent implementation review, Windows qualification, real launch timing/
wallet inventory, real-key custody, machine power-loss evidence, final package/
clean-host acceptance or a release decision. No production activation, public
mining or network contact is authorized by this job. After completion, review
these remaining acceptance gaps for evidence value before choosing another test.
