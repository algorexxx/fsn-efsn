#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-release-extraction-2026-10-04"
inputs="$workspace/tmp/release-extraction-2026-10-04-exact"
work=/tmp/fsn-release-extraction-2026-10-04-exact
results="$evidence/attempt-3"
[[ ! -e "$work" && ! -e "$results" ]]
mkdir -p "$work/source" "$work/bin" "$results"
cp "$evidence/run-linux.sh" "$results/run-linux.sh"
cp "$evidence/verify-tree.py" "$results/verify-tree.py"
cp "$evidence/README.md" "$results/declared-scope.md"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
export GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp TMPDIR=/tmp
df -B1 /tmp /mnt/c /mnt/d > "$results/capacity-before.txt"
ip -brief link > "$results/network.txt"
go version > "$results/toolchain.txt"
gcc --version >> "$results/toolchain.txt"
python3 - "$inputs" "$evidence" <<'PY'
import hashlib, json, shutil, sys
from pathlib import Path
inputs, evidence = map(Path, sys.argv[1:])
assert shutil.disk_usage('/tmp').free > 10 * 1024**3
manifest = json.loads((evidence / 'input-archives.json').read_text(encoding='utf-8'))
for name in ['baseline.tar', 'tests.tar']:
    assert hashlib.sha256((inputs / name).read_bytes()).hexdigest() == manifest[name]
PY
tar -xf "$inputs/baseline.tar" -C "$work/source"
cd "$work/source"
git apply --check "$evidence/01-node.patch" > "$results/node-apply.txt" 2>&1
git apply "$evidence/01-node.patch" >> "$results/node-apply.txt" 2>&1
python3 "$evidence/verify-tree.py" "$evidence" "$inputs" "$work/source" 1 > "$results/node-tree.txt"
chown -R rehearsal:rehearsal "$work"
run_check() {
    local name="$1"
    shift
    set +e
    runuser -u rehearsal -- "$@" > "$results/$name.txt" 2>&1
    local code=$?
    set -e
    printf '%s\n' "$code" > "$results/$name-exit.txt"
    [[ "$code" == 0 ]]
}
run_check build-node go build -p=2 -mod=readonly -trimpath -o "$work/bin/efsn-node" ./cmd/efsn
run_check node-version "$work/bin/efsn-node" version
run_check node-dependencies go list -mod=readonly -deps ./cmd/efsn
! grep -E '/internal/(observe|recovery)$' "$results/node-dependencies.txt"
git apply --check "$evidence/02-optional-bootstrap-trim.patch" > "$results/optional-apply.txt" 2>&1
git apply "$evidence/02-optional-bootstrap-trim.patch" >> "$results/optional-apply.txt" 2>&1
python3 "$evidence/verify-tree.py" "$evidence" "$inputs" "$work/source" 2 > "$results/optional-tree.txt"
run_check build-node-optional go build -p=2 -mod=readonly -trimpath -o "$work/bin/efsn-optional" ./cmd/efsn
git apply --check "$evidence/03-recovery-tool.patch" > "$results/recovery-apply.txt" 2>&1
git apply "$evidence/03-recovery-tool.patch" >> "$results/recovery-apply.txt" 2>&1
python3 "$evidence/verify-tree.py" "$evidence" "$inputs" "$work/source" 3 > "$results/recovery-tree.txt"
run_check build-recovery go build -p=2 -mod=readonly -trimpath -o "$work/bin/fsn-recovery" ./cmd/fsn-recovery
tar -xf "$inputs/tests.tar" -C "$work/source"
chown -R rehearsal:rehearsal "$work/source"
python3 "$evidence/verify-tree.py" "$evidence" "$inputs" "$work/source" 4 > "$results/test-tree.txt"
run_check focused-packages go test -race -p=2 -mod=readonly ./params ./consensus/datong ./ethdb/leveldb -run '^(TestRestart.*|TestSnapshot.*|TestReadOnlyCorruptionDoesNotRepair)$' -count=1 -v -timeout=3m
run_check build-restart-tests go test -race -p=2 -mod=readonly -c -o "$work/bin/restart-tests" ./tests/restart
cd tests/restart
run_check restart-tests "$work/bin/restart-tests" '-test.run=^(TestRestartAnchorEnforcement|TestRestartAnchorConfiguration|TestRestartRollbackDatabaseModes|TestReconstructionAcrossMissingStates|TestReconstructionAtHistoricalExpiryBoundary|TestReconstructionWithMissingAncestorReturnsError|TestHeaderBatchUsesUnstoredParents|TestFinalizeParentIsolatedFromConcurrentImport|TestColdHeaderValidationBoundaries|TestAutoBuyRuntime|TestAutomaticPurchaseRecovery|TestAutomaticPurchaseStorageErrors|TestSubmittedTicketReplacementAllowsExplicitRetry)$' -test.v -test.timeout=6m
sha256sum "$work/bin/"* > "$results/binaries.sha256"
go version -m "$work/bin/efsn-node" > "$results/node-build-info.txt"
df -B1 /tmp /mnt/c /mnt/d > "$results/capacity-after.txt"
printf '0\n' > "$results/exit-code.txt"
tail -n 8 "$results/restart-tests.txt"
