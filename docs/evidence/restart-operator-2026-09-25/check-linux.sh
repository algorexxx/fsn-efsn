#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-operator-2026-09-25"
binary="$workspace/tmp/recovery-operator-linux-tests"
command="$workspace/tmp/fsn-recovery-operator-linux"
temporary="$workspace/tmp/recovery-guard-linux-gotmp"
cd "$workspace"
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$temporary" TMPDIR="$temporary" go test -race -p=2 -mod=readonly -count=1 -v ./internal/recovery ./cmd/fsn-recovery > "$results/linux-unit-race.txt" 2>&1
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$temporary" go build -race -p=2 -mod=readonly -o "$command" ./cmd/fsn-recovery > "$results/linux-command-build.txt" 2>&1
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$temporary" go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/linux-integration-build.txt" 2>&1
cd tests/restart
unshare --net -- runuser -u rehearsal -- env GOMAXPROCS=2 TMPDIR="$temporary" FUSION_RESTART_CHAINDATA= FUSION_RESTART_OFFLINE_FULL_STATE_ROOT= FUSION_RECOVERY_OPERATOR="$command" "$binary" '-test.run=^Test(RecoveryOperatorCLI|KeystorePreflightLocksAndUncertain|ApprovedOffline(ProcessCuts|Refusals)|OfflineRecovery(ProcessCuts|UncertainCuts|Refusals))$' -test.v -test.timeout=5m > "$results/linux-integration-race.txt" 2>&1
tail -n 6 "$results/linux-integration-race.txt"
