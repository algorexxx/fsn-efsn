#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
source="$workspace/tmp/full-state-handover-linux-final-src"
results="$workspace/docs/evidence/restart-full-state-handover-2026-09-24"
binary="$workspace/tmp/full-state-handover-final-linux-tests"
test ! -e "$source"
test ! -e "$binary"
mkdir "$source"
tar -xf "$workspace/tmp/full-state-handover-base.tar" -C "$source"
cp "$workspace"/tests/restart/full_state_handover*_test.go "$workspace/tests/restart/full_state_rehearsal_test.go" "$workspace/tests/restart/handover_cleanup_test.go" "$source/tests/restart/"
cd "$source"
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/full-state-handover-linux-gotmp" go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/linux-final-build.txt" 2>&1
sha256sum "$binary" tests/restart/full_state_handover*_test.go tests/restart/full_state_rehearsal_test.go tests/restart/handover_cleanup_test.go > "$results/linux-final-identity.txt"
cd tests/restart
unshare --net -- runuser -u rehearsal -- env GOMAXPROCS=2 FUSION_RESTART_HANDOVER_AUDIT="$workspace/tmp/full-state-handover-v2-producer" FUSION_RESTART_HANDOVER_BLOCKS="$workspace/tmp/full-state-handover-blocks" "$binary" '-test.run=^Test(HandoverMissingRecoveryPurchase|HandoverFundingGuard|HandoverTemporalAccounting|FullStateHandoverAccounting|FullStateDifferenceAccounting|FullStateContextIntegrity|SingleBackupBlockHandover|SingleBackupBlockRejectsShortSuccessorTicket)$' -test.v -test.count=2 -test.timeout=3m > "$results/linux-final-focused-race.txt" 2>&1
tail -n 5 "$results/linux-final-focused-race.txt"
