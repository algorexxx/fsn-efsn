#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-release-jwt-2026-10-04"
previous="$workspace/docs/evidence/restart-release-selection-2026-10-04"
work=/home/rehearsal/results/restart-release-jwt-2026-10-04
selected=/home/rehearsal/results/restart-release-selection-2026-10-04
test -s "$evidence/module-download.json"
test "$(cat "$evidence/baseline-jwt-test-exit.txt")" = 1
grep -q 'module lookup disabled by GOPROXY=off' "$evidence/baseline-jwt-test.txt"
test -s "$evidence/testify-download.json"
test ! -e "$evidence/qualification-resumed.txt"
export PATH="$selected/toolchain/go/bin:/usr/bin:/bin"
export GOTOOLCHAIN=local GOWORK=off GOPROXY=off GOSUMDB=off GOFLAGS=-mod=readonly
export CGO_ENABLED=1 GOAMD64=v1 GOMAXPROCS=2 GOCACHE="$selected/repeat-cache" GOTMPDIR="$work/tmp" TMPDIR="$work/tmp"
date -u +%FT%TZ > "$evidence/qualification-resumed.txt"
ip -brief link > "$evidence/resumed-test-network.txt"
python3 - "$workspace" "$evidence" "$previous" "$work" "$selected" <<'PY'
import hashlib, json, shutil, sys
from pathlib import Path
workspace, evidence, previous, work, selected = map(Path, sys.argv[1:])
assert shutil.disk_usage(work).free > 30 * 1024**3
assert shutil.disk_usage('/mnt/d').free > 60 * 1024**3
inputs = json.loads((evidence / 'patch-inputs.json').read_text(encoding='utf-8'))
assert hashlib.sha256((evidence / '08-jwt-dependency.patch').read_bytes()).hexdigest() == inputs['patch_sha256']
for name, folder in [('node', 'source'), ('recovery', 'repeat')]:
    source = selected / folder
    expected = json.loads((previous / ('selected-' + name + '-inventory.json')).read_text(encoding='utf-8'))
    if name == 'recovery':
        expected['p2p/rlpx_test.go'] = hashlib.sha256((workspace / 'p2p/rlpx_test.go').read_bytes().replace(b'\r\n', b'\n')).hexdigest()
    actual = {p.relative_to(source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*') if p.is_file()}
    assert expected == actual, name
    copied = {p.relative_to(work / name).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in (work / name).rglob('*') if p.is_file()}
    assert expected == copied, name
    expected.update(inputs['after'])
    (evidence / (name + '-inventory.json')).write_text(json.dumps(expected, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print('PASS retained and copied source inventories before resumed qualification')
PY
cd "$work/node"
set +e
timeout --signal=TERM --kill-after=20s 7m go test -race -p=2 -count=1 -timeout=5m -run '^TestJWT$' -v ./node > "$evidence/baseline-jwt-ready.txt" 2>&1
code=$?
set -e
printf '%s\n' "$code" > "$evidence/baseline-jwt-ready-exit.txt"
test "$code" = 0
for name in node recovery; do
    cd "$work/$name"
    git apply --check "$evidence/08-jwt-dependency.patch"
    git apply "$evidence/08-jwt-dependency.patch"
done
cd "$work/node"
set +e
timeout --signal=TERM --kill-after=20s 7m go test -race -p=2 -count=1 -timeout=5m -v ./node > "$evidence/node-package-test.txt" 2>&1
code=$?
set -e
printf '%s\n' "$code" > "$evidence/node-package-test-exit.txt"
test "$code" = 0
cd /home/rehearsal/go/pkg/mod/github.com/golang-jwt/jwt/v4@v4.5.2
set +e
timeout --signal=TERM --kill-after=20s 7m go test -race -p=2 -count=1 -timeout=5m -run '^(TestSplitToken|TestParser_Parse|TestParser_ParseWithClaims|TestSetPadding)$' -v . > "$evidence/upstream-parser-tests.txt" 2>&1
code=$?
set -e
printf '%s\n' "$code" > "$evidence/upstream-parser-tests-exit.txt"
test "$code" = 0
for name in efsn fsn-recovery; do
    if [ "$name" = efsn ]; then folder=node; else folder=recovery; fi
    cd "$work/$folder"
    set +e
    timeout --signal=TERM --kill-after=20s 10m go build -p=2 -trimpath -buildvcs=false -o "$work/bin/$name" "./cmd/$name" > "$evidence/build-$name.txt" 2>&1
    code=$?
    set -e
    printf '%s\n' "$code" > "$evidence/build-$name-exit.txt"
    test "$code" = 0
    go version -m "$work/bin/$name" > "$evidence/build-info-$name.txt"
    sha256sum "$work/bin/$name" > "$evidence/binary-$name.sha256"
done
"$work/bin/efsn" version > "$evidence/cli-version.txt" 2>&1
"$work/bin/efsn" --help > "$evidence/cli-help.txt" 2>&1
"$work/bin/fsn-recovery" --help > "$evidence/recovery-help.txt" 2>&1
date -u +%FT%TZ > "$evidence/qualification-finished.txt"
tail -n 4 "$evidence/node-package-test.txt"
tail -n 4 "$evidence/upstream-parser-tests.txt"
