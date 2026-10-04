#!/bin/bash
set -euo pipefail
evidence=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-release-text-2026-10-04
work=/home/rehearsal/results/restart-release-text-2026-10-04
selected=/home/rehearsal/results/restart-release-selection-2026-10-04
test ! -e "$evidence/completion-started.txt"
test "$(cat "$evidence/build-efsn-exit.txt")" = 1
grep -q 'missing go.sum entry' "$evidence/build-efsn.txt"
export PATH="$selected/toolchain/go/bin:/usr/bin:/bin"
export GOTOOLCHAIN=local GOWORK=off GOPROXY=off GOSUMDB=off GOFLAGS=-mod=readonly
export CGO_ENABLED=1 GOAMD64=v1 GOMAXPROCS=2 GOCACHE="$selected/repeat-cache" GOTMPDIR="$work/tmp" TMPDIR="$work/tmp"
date -u +%FT%TZ > "$evidence/completion-started.txt"
ip -brief link > "$evidence/completion-test-network.txt"
for name in node recovery; do
    cd "$work/$name"
    go mod download -json golang.org/x/sync@v0.21.0 > "$evidence/$name-sync-checksum.json"
done
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
cd "$work/node"
for package in eth/tracers/js console; do
    run_check "candidate-complete-${package//\//-}" 7m go test -race -p=2 -count=1 -timeout=5m -v "./$package"
done
run_check affected-network-tests 7m go test -race -p=2 -count=1 -timeout=5m -v ./p2p/nat ./node ./rpc golang.org/x/sync/errgroup
for name in efsn fsn-recovery; do
    if [ "$name" = efsn ]; then folder=node; else folder=recovery; fi
    cd "$work/$folder"
    run_check "build-complete-$name" 10m go build -p=2 -trimpath -buildvcs=false -o "$work/bin/$name" "./cmd/$name"
    test "$(cat "$evidence/build-complete-$name-exit.txt")" = 0
    go version -m "$work/bin/$name" > "$evidence/build-info-$name.txt"
    sha256sum "$work/bin/$name" > "$evidence/binary-$name.sha256"
    run_check "dependencies-$name" 3m go list -deps -json "./cmd/$name"
done
run_check cli-version 30s "$work/bin/efsn" version
run_check cli-help 30s "$work/bin/efsn" --help
run_check recovery-help 30s "$work/bin/fsn-recovery" --help
date -u +%FT%TZ > "$evidence/completion-finished.txt"
