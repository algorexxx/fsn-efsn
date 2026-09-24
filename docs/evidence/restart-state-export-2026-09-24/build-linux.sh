#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
source=/home/rehearsal/fsn-efsn-state-export
results=/home/rehearsal/results/restart-state-export-2026-09-24
test ! -e "$source"
test ! -e "$results"
mkdir "$source" "$results"
tar -xf "$workspace/tmp/restart-state-export-base.tar" -C "$source"
for path in tests/restart/state_export_test.go tests/restart/state_export_checks_test.go tests/restart/state_export_linux_test.go; do
    preserved="$workspace/docs/evidence/restart-state-export-2026-09-24/writer-$(basename "$path").txt"
    if [ -f "$preserved" ]; then
        cp "$preserved" "$source/$path"
    else
        cp "$workspace/$path" "$source/$path"
    fi
done
chown -R rehearsal:rehearsal "$source" "$results"
cd "$source"
export PATH=/opt/fusion-toolchain/go/bin:$PATH
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 go test -race -p=2 -mod=readonly -c -o "$results/export-race-tests" ./tests/restart > "$results/build-race.txt" 2>&1
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 go test -p=2 -mod=readonly -c -o "$results/export-tests" ./tests/restart > "$results/build-tests.txt" 2>&1
{
    date -u +%FT%TZ
    go version
    gcc --version | head -n 1
    sha256sum "$workspace/tmp/restart-state-export-base.tar" "$results/export-tests" "$results/export-race-tests"
    sha256sum tests/restart/state_export_test.go tests/restart/state_export_checks_test.go tests/restart/state_export_linux_test.go
} > "$results/identity.txt"
cd tests/restart
unshare --net -- runuser -u rehearsal -- env GOMAXPROCS=2 "$results/export-race-tests" '-test.run=^TestStateExport' -test.v -test.count=2 -test.timeout=3m > "$results/focused-race.txt" 2>&1
tail -n 8 "$results/focused-race.txt"
