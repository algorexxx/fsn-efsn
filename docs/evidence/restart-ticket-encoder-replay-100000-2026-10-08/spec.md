# Candidate replay execution scope

Declared before execution. Follow [plan-at-start.md](plan-at-start.md) exactly:
fresh D1 node plus the previously qualified, unselected encoder patch; Go
1.27.1; historical blocks 1 through 100,000; separate identity-bound target;
read-only backup; private mount/network namespaces; bounded space and time.

Copy replay_linux_test.go, replay_resume_linux_test.go and
replay_inspection_linux_test.go unchanged from investigation commit aeb0a8c7.
Extract exactly five existing declarations from fixture_test.go and
integrity_test.go, preserving bytes and recording source hashes/line ranges:
rpcObservation, readRPCObservations, requireNoError, inspectionBackup and
openInspectionBackup. Copy the existing RPC observation JSON unchanged.
No synthetic fixture construction, signing or recovery code is invoked.

The additional details_test.go only observes block 100,000 before replay and
after a clean stop. Its reference is the already-preserved source, not the
candidate's output. It verifies body/receipt commitments and records full
header RLP, roots, bloom, counts and TD. The cold-details process independently
checks its ticket cache is initially empty, decodes state tickets and verifies
their recompressed commitment. Compare its observation to the captured source
exactly, except ticket count, which is separately observed only on replay.

Run the original exact-height cold-head test and cold-details in separate
fresh processes on the read-only target mount. Hash every target file before
and after those reads. Compare backup metadata to the earlier compression
inventory and again after work. Compare both existing baseline replay
directories' metadata before and after; do not open their databases.

All helpers compile into one non-race test executable, retained with exact
hash for future validated continuation. No production binary or existing
replay identity is replaced. Preserve failed attempts; never change expected
commitments to match replay output. A stopped, skipped, short or mismatching
run is incomplete. Only a clean replay plus both cold checks and preservation
checks can mark this bounded run complete.
