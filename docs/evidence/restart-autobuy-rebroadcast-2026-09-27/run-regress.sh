#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-autobuy-rebroadcast-2026-09-27"
binary="$workspace/tmp/autobuy-rebroadcast-2026-09-27/restart-tests"
cd "$workspace/tests/restart"
[[ ! -e "$results/regression-final-race.txt" ]]
set +e
unshare --net -- env GOMAXPROCS=2 FUSION_RESTART_CHAINDATA= "$binary" -test.run='^(TestAutoBuyRuntime|TestAutomaticPurchaseRecovery|TestAutomaticPurchaseStorageErrors|TestSubmittedTicketReplacementAllowsExplicitRetry)$' -test.v -test.timeout=10m > "$results/regression-final-race.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/regression-final-exit.txt"
tail -n 22 "$results/regression-final-race.txt"
exit "$status"
