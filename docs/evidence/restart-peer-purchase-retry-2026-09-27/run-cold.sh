#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-peer-purchase-retry-2026-09-27"
binary="$workspace/tmp/peer-purchase-retry-2026-09-27/live-tests"
cd "$workspace/tests/restart"
[[ ! -e "$results/cold-race.txt" ]]
set +e
unshare --net -- env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_HOST_STORAGE=/mnt/c FUSION_RESTART_FUNDING_DIAGNOSIS="$workspace/tmp/full-state-peer-reconnect-2026-09-27" "$binary" -test.run='^TestFullStateFundingColdDiagnosis$' -test.v -test.timeout=3m > "$results/cold-race.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/cold-exit.txt"
tail -n 16 "$results/cold-race.txt"
exit "$status"
