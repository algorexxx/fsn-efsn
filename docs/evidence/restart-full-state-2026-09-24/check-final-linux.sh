#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
source=/home/rehearsal/fsn-efsn-full-state-final
results="$workspace/docs/evidence/restart-full-state-2026-09-24"
binary="$workspace/tmp/full-state-final-linux-tests"
test ! -e "$source"
test ! -e "$binary"
mkdir "$source"
tar -xf "$workspace/tmp/full-state-base.tar" -C "$source"
cp "$workspace"/tests/restart/full_state*test.go "$source/tests/restart/"
mkdir "$source/docs/evidence/restart-full-state-2026-09-24"
cp "$results/context.rlp" "$source/docs/evidence/restart-full-state-2026-09-24/"
chown -R rehearsal:rehearsal "$source"
cd "$source"
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/final-linux-build.txt" 2>&1
sha256sum "$binary" tests/restart/full_state*test.go > "$results/final-linux-identity.txt"
cd tests/restart
unshare --net -- runuser -u rehearsal -- env GOMAXPROCS=2 "$binary" '-test.run=^TestFullState(DifferenceAccounting|ContextIntegrity)$' -test.v -test.count=2 -test.timeout=3m > "$results/final-linux-race.txt" 2>&1
unshare --net -- runuser -u rehearsal -- env GOMAXPROCS=2 FUSION_RESTART_FULL_STATE_LEDGER="$workspace/tmp/full-state-producer" FUSION_RESTART_FULL_STATE_BLOCKS="$workspace/tmp/full-state-bridge" FUSION_RESTART_FULL_STATE_ACCOUNTING="$results/accounting-linux.json" "$binary" '-test.run=^TestFullStateLedgerAudit$' -test.v -test.timeout=2m > "$results/final-linux-accounting.txt" 2>&1
cmp "$results/accounting.json" "$results/accounting-linux.json"
tail -n 4 "$results/final-linux-race.txt"
tail -n 4 "$results/final-linux-accounting.txt"
