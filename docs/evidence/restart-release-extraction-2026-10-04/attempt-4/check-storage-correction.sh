#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-release-extraction-2026-10-04"
inputs="$workspace/tmp/release-extraction-2026-10-04-exact"
work=/home/rehearsal/results/restart-release-extraction-2026-10-04
results="$evidence/attempt-4"
[[ ! -e "$work" && ! -e "$results" ]]
mkdir -p "$work/source" "$work/bin" "$results"
cp "$evidence/check-storage-correction.sh" "$results/check-storage-correction.sh"
cp "$evidence/verify-tree.py" "$results/verify-tree.py"
cp "$evidence/README.md" "$results/declared-scope.md"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
export GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp TMPDIR=/tmp
df -B1 "$work" /mnt/c /mnt/d > "$results/capacity-before.txt"
ip -brief link > "$results/network.txt"
go version > "$results/toolchain.txt"
gcc --version >> "$results/toolchain.txt"
python3 - "$inputs" "$evidence" "$work" <<'PY'
import hashlib, json, shutil, sys
from pathlib import Path
inputs, evidence, work = map(Path, sys.argv[1:])
assert shutil.disk_usage(work).free > 10 * 1024**3
manifest = json.loads((evidence / 'input-archives.json').read_text(encoding='utf-8'))
for name in ['baseline.tar', 'tests.tar']:
    assert hashlib.sha256((inputs / name).read_bytes()).hexdigest() == manifest[name]
PY
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
tar -xf "$inputs/baseline.tar" -C "$work/source"
cd "$work/source"
git apply --check "$evidence/01-node.patch" > "$results/node-apply.txt" 2>&1
git apply "$evidence/01-node.patch" >> "$results/node-apply.txt" 2>&1
python3 "$evidence/verify-tree.py" "$evidence" "$inputs" "$work/source" 1 > "$results/node-tree.txt"
chown -R rehearsal:rehearsal "$work"
run_check build-node go build -p=2 -mod=readonly -trimpath -o "$work/bin/efsn-node" ./cmd/efsn
git apply --check "$evidence/02-optional-bootstrap-trim.patch" > "$results/optional-apply.txt" 2>&1
git apply "$evidence/02-optional-bootstrap-trim.patch" >> "$results/optional-apply.txt" 2>&1
python3 "$evidence/verify-tree.py" "$evidence" "$inputs" "$work/source" 2 > "$results/optional-tree.txt"
run_check build-node-optional go build -p=2 -mod=readonly -trimpath -o "$work/bin/efsn-optional" ./cmd/efsn
git apply --check "$evidence/03-recovery-tool.patch" > "$results/recovery-apply.txt" 2>&1
git apply "$evidence/03-recovery-tool.patch" >> "$results/recovery-apply.txt" 2>&1
python3 "$evidence/verify-tree.py" "$evidence" "$inputs" "$work/source" 3 > "$results/recovery-tree.txt"
run_check build-recovery go build -p=2 -mod=readonly -trimpath -o "$work/bin/fsn-recovery" ./cmd/fsn-recovery
tar -xf "$inputs/tests.tar" -C "$work/source"
python3 "$evidence/verify-tree.py" "$evidence" "$inputs" "$work/source" 4 > "$results/before-tree.txt"
git apply --check "$evidence/04-test-ordering.patch" > "$results/test-apply.txt" 2>&1
git apply "$evidence/04-test-ordering.patch" >> "$results/test-apply.txt" 2>&1
python3 "$evidence/verify-tree.py" "$evidence" "$inputs" "$work/source" 5 > "$results/after-tree.txt"
[[ -z "$(gofmt -l tests/restart/purchase_storage_test.go)" ]]
chown -R rehearsal:rehearsal "$work/source"
run_check build-restart-tests go test -race -p=2 -mod=readonly -c -o "$work/bin/restart-tests-corrected" ./tests/restart
cd tests/restart
run_check storage-all "$work/bin/restart-tests-corrected" '-test.run=^TestAutomaticPurchaseStorageErrors$' -test.v -test.timeout=3m
run_check storage-has-get-repeat "$work/bin/restart-tests-corrected" '-test.run=^TestAutomaticPurchaseStorageErrors$/(has|get)$' -test.v -test.count=3 -test.timeout=2m
sha256sum "$work/bin/"* > "$results/binaries.sha256"
go version -m "$work/bin/efsn-node" > "$results/node-build-info.txt"
df -B1 /tmp /mnt/c /mnt/d > "$results/capacity-after.txt"
printf '0\n' > "$results/exit-code.txt"
tail -n 6 "$results/storage-has-get-repeat.txt"
