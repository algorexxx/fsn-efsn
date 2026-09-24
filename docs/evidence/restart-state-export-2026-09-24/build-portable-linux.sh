#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
source=/home/rehearsal/fsn-efsn-state-export-portable
results=/home/rehearsal/results/restart-state-export-2026-09-24
binary="$workspace/tmp/state-export-portable-linux-tests"
test ! -e "$source"
test ! -e "$binary"
mkdir "$source"
tar -xf "$workspace/tmp/restart-state-export-base.tar" -C "$source"
for path in state_export_test.go state_export_checks_test.go state_export_linux_test.go state_export_verify_test.go replay_inspection_linux_test.go; do
    cp "$workspace/tests/restart/$path" "$source/tests/restart/$path"
done
chown -R rehearsal:rehearsal "$source"
cd "$source"
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/build-portable-race.txt" 2>&1
sha256sum "$binary" tests/restart/state_export_test.go tests/restart/state_export_checks_test.go tests/restart/state_export_linux_test.go tests/restart/state_export_verify_test.go tests/restart/replay_inspection_linux_test.go > "$results/portable-linux-identity.txt"
cd tests/restart
unshare --net -- runuser -u rehearsal -- env GOMAXPROCS=2 "$binary" '-test.run=^TestStateExport' -test.v -test.count=1 -test.timeout=3m > "$results/portable-linux-race.txt" 2>&1
tail -n 6 "$results/portable-linux-race.txt"
