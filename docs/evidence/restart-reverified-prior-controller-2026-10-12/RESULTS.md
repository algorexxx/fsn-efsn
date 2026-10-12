# Controller qualification for separately verified prior evidence

All 24 bounded offline monitor/controller checks pass as rehearsal UID 1000
with private networking and loopback DOWN. No blockchain database was opened.
Only the test controller and its tests changed; selected node/replay runtime,
consensus rules, release inputs and executable identities did not change.

The ordinary successful-prior gate remains. An explicit separate-verification
path now requires both a named follow-up and its SHA256 manifest pin, verifies
the original and follow-up file manifests, and ties successful cold results to
the completed execution while retaining the original exit-1 record. It refuses
mixed stopped-attempt provenance, missing identity fields, wrong endpoints,
mutated bytes, incomplete review, added STOP and replacement verification.
The next job retains both manifests for final verification.

Observer preparation now checks the exact one-height source change and canonical
patch filename labels before long replay work. A label mismatch is rejected
early; no old input or result is rewritten. The test result records source
hashes, exact patch versus its base commit, isolation, command and exit status.
The preflight and final verifier also enforce the same accepted prior proof.
