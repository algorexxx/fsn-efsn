#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
source=/home/rehearsal/fsn-efsn-single-block-handover
results="$workspace/docs/evidence/restart-single-block-handover-2026-09-24"
binary="$workspace/tmp/single-block-handover-linux-tests"
test ! -e "$source"
test ! -e "$binary"
mkdir "$source"
tar -xf "$workspace/tmp/single-block-handover-base.tar" -C "$source"
cp "$workspace/tests/restart/single_block_handover_test.go" "$source/tests/restart/"
chown -R rehearsal:rehearsal "$source"
cd "$source"
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/linux-build.txt" 2>&1
sha256sum "$binary" tests/restart/single_block_handover_test.go tests/restart/handover_test.go > "$results/linux-identity.txt"
cd tests/restart
unshare --net -- runuser -u rehearsal -- env GOMAXPROCS=2 "$binary" '-test.run=^Test(SingleBackupBlockHandover|SingleBackupBlockRejectsShortSuccessorTicket|LastTicketHandover|SingleRemainingTicketRequiresReplacement)$' -test.v -test.count=2 -test.timeout=3m > "$results/linux-race.txt" 2>&1
tail -n 8 "$results/linux-race.txt"
