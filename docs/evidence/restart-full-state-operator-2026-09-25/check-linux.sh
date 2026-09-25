#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-full-state-operator-2026-09-25"
binary="$workspace/tmp/full-state-operator-linux-tests"
command="$workspace/tmp/fsn-recovery-operator-linux"
temporary="$workspace/tmp/recovery-guard-linux-gotmp"
echo "0493d62bacc5b4b168353d0cb9cf33863df64ba0b957ad3102314fe79c45c7c8  $command" | sha256sum --check
cd "$workspace"
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$temporary" go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/linux-build.txt" 2>&1
cd tests/restart
unshare --net -- runuser -u rehearsal -- env GOMAXPROCS=2 TMPDIR="$temporary" FUSION_RESTART_CHAINDATA= FUSION_RECOVERY_OPERATOR="$command" "$binary" '-test.run=^TestRecoveryOperatorCLI$' -test.v -test.timeout=3m > "$results/linux-regression-race.txt" 2>&1
unshare --net -- runuser -u rehearsal -- env GOMAXPROCS=2 TMPDIR="$temporary" FUSION_RESTART_CHAINDATA= FUSION_RECOVERY_OPERATOR="$command" FUSION_RESTART_OPERATOR_FULL_STATE_ROOT="$workspace/tmp/full-state-operator-linux-2026-09-25" "$binary" '-test.run=^TestFullStateRecoveryOperator$' -test.v -test.timeout=10m > "$results/linux-full-state-race.txt" 2>&1
tail -n 12 "$results/linux-full-state-race.txt"
