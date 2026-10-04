#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-release-text-2026-10-04"
work=/home/rehearsal/results/restart-release-text-2026-10-04
base=/home/rehearsal/results/restart-release-jwt-2026-10-04
selected=/home/rehearsal/results/restart-release-selection-2026-10-04
test ! -e "$evidence/qualification-started.txt"
export PATH="$selected/toolchain/go/bin:/usr/bin:/bin"
export GOTOOLCHAIN=local GOWORK=off GOPROXY=off GOSUMDB=off GOFLAGS=-mod=readonly
export CGO_ENABLED=1 GOAMD64=v1 GOMAXPROCS=2 GOCACHE="$selected/repeat-cache" GOTMPDIR="$work/tmp" TMPDIR="$work/tmp"
date -u +%FT%TZ > "$evidence/qualification-started.txt"
ip -brief link > "$evidence/test-network.txt"
python3 - "$base" "$work" "$evidence" <<'PY'
import hashlib, json, shutil, sys
from pathlib import Path
base, work, evidence = map(Path, sys.argv[1:])
assert shutil.disk_usage(work).free > 30 * 1024**3
assert shutil.disk_usage('/mnt/d').free > 60 * 1024**3
for name in ('node', 'recovery'):
    expected = json.loads((evidence.parent / 'restart-release-jwt-2026-10-04' / (name + '-inventory.json')).read_text(encoding='utf-8'))
    actual = {p.relative_to(base / name).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in (base / name).rglob('*') if p.is_file()}
    assert actual == expected
for name in ('go.mod', 'go.sum'):
    shutil.copy2(work / 'node' / name, work / 'recovery' / name)
PY
run_check() {
    local label="$1"
    local limit="$2"
    shift 2
    set +e
    timeout --signal=TERM --kill-after=20s "$limit" "$@" > "$evidence/$label.txt" 2>&1
    local code=$?
    set -e
    printf '%s\n' "$code" > "$evidence/$label-exit.txt"
    printf '%s exit=%s\n' "$label" "$code"
}
for stage in baseline candidate; do
    if [ "$stage" = baseline ]; then cd "$base/node"; else cd "$work/node"; fi
    for package in internal/jsre eth/tracers/js console; do
        label="${stage}-${package//\//-}"
        run_check "$label" 7m go test -race -p=2 -count=1 -timeout=5m -v "./$package"
    done
done
cd "$work/node"
run_check upstream-text-tests 7m go test -race -p=2 -count=1 -timeout=5m -v golang.org/x/text/unicode/norm golang.org/x/text/collate golang.org/x/text/cases
mkdir "$work/bin"
for name in efsn fsn-recovery; do
    if [ "$name" = efsn ]; then folder=node; else folder=recovery; fi
    cd "$work/$folder"
    run_check "build-$name" 10m go build -p=2 -trimpath -buildvcs=false -o "$work/bin/$name" "./cmd/$name"
    test "$(cat "$evidence/build-$name-exit.txt")" = 0
    go version -m "$work/bin/$name" > "$evidence/build-info-$name.txt"
    sha256sum "$work/bin/$name" > "$evidence/binary-$name.sha256"
    run_check "dependencies-$name" 3m go list -deps -json "./cmd/$name"
done
run_check cli-version 30s "$work/bin/efsn" version
run_check cli-help 30s "$work/bin/efsn" --help
run_check recovery-help 30s "$work/bin/fsn-recovery" --help
date -u +%FT%TZ > "$evidence/qualification-finished.txt"
