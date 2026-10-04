#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-release-followup-2026-10-04"
previous="$workspace/docs/evidence/restart-release-selection-2026-10-04"
work=/home/rehearsal/results/restart-release-followup-2026-10-04
selected=/home/rehearsal/results/restart-release-selection-2026-10-04
test ! -e "$work/network-source"
export PATH="$selected/toolchain/go/bin:/usr/bin:/bin"
export GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off GOFLAGS=-mod=readonly CGO_ENABLED=1 GOMAXPROCS=2
export GOCACHE="$selected/repeat-cache" GOTMPDIR="$work/tmp" TMPDIR="$work/tmp"
python3 - "$evidence" "$previous" "$selected/source" "$work/network-source" <<'PY'
import hashlib, json, shutil, sys
from pathlib import Path
evidence, previous, source, target = map(Path, sys.argv[1:])
assert shutil.disk_usage(source).free > 30 * 1024**3
assert shutil.disk_usage('/mnt/d').free > 60 * 1024**3
expected = json.loads((previous / 'selected-node-inventory.json').read_text(encoding='utf-8'))
actual = {p.relative_to(source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*') if p.is_file()}
assert expected == actual
shutil.copytree(source, target)
inputs = json.loads((evidence / 'test-inputs.json').read_text(encoding='utf-8'))
for path, digest in inputs['baseline_overlay'].items():
    data = (evidence / 'baseline-tests' / Path(path).name).read_bytes()
    assert hashlib.sha256(data).hexdigest() == digest
    (target / path).write_bytes(data)
    expected[path] = digest
actual = {p.relative_to(target).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in target.rglob('*') if p.is_file()}
assert expected == actual
assert hashlib.sha256((evidence / '07-discovery-fixtures.patch').read_bytes()).hexdigest() == inputs['patch_sha256']
expected.update(inputs['after'])
(evidence / 'network-source-inventory.json').write_text(json.dumps(expected, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print('PASS selected production tree and matching baseline discovery tests')
PY
ip -brief link > "$evidence/test-network.txt"
date -u +%FT%TZ > "$evidence/discovery-started.txt"
cd "$work/network-source"
set +e
timeout --signal=TERM --kill-after=20s 5m go test -race -p=2 -count=1 -timeout=3m -run '^(TestParseNode|TestForwardCompatibility)$' -v ./p2p/discover > "$evidence/discovery-before.txt" 2>&1
code=$?
set -e
printf '%s\n' "$code" > "$evidence/discovery-before-exit.txt"
test "$code" = 1
grep -q -- '--- FAIL: TestParseNode' "$evidence/discovery-before.txt"
grep -q -- '--- FAIL: TestForwardCompatibility' "$evidence/discovery-before.txt"
git apply --check "$evidence/07-discovery-fixtures.patch"
git apply "$evidence/07-discovery-fixtures.patch"
set +e
timeout --signal=TERM --kill-after=20s 5m go test -race -p=2 -count=1 -timeout=3m -run '^(TestParseNode|TestNodeString|TestForwardCompatibility)$' -v ./p2p/discover > "$evidence/discovery-focused.txt" 2>&1
code=$?
set -e
printf '%s\n' "$code" > "$evidence/discovery-focused-exit.txt"
test "$code" = 0
set +e
timeout --signal=TERM --kill-after=20s 5m go test -race -p=2 -count=1 -timeout=3m -v ./p2p/discover > "$evidence/discovery-package.txt" 2>&1
code=$?
set -e
printf '%s\n' "$code" > "$evidence/discovery-package-exit.txt"
python3 - "$evidence" "$work/network-source" <<'PY'
import hashlib, json, sys
from pathlib import Path
evidence, source = map(Path, sys.argv[1:])
expected = json.loads((evidence / 'network-source-inventory.json').read_text(encoding='utf-8'))
actual = {p.relative_to(source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*') if p.is_file()}
assert expected == actual
print('PASS full source inventory after tests; production selection unchanged')
PY
date -u +%FT%TZ > "$evidence/discovery-finished.txt"
tail -n 8 "$evidence/discovery-package.txt"
exit "$code"
