#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-partition-history-2026-09-26"
binary="$workspace/tmp/partition-history-2026-09-26/tests"
output="$workspace/tmp/partition-history-2026-09-26/history.rlp"
mode=${1:?build, measure or export}
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
cd "$workspace"
if [[ "$mode" == build ]]; then
  { date -u --iso-8601=seconds; git -c safe.directory="$workspace" rev-parse HEAD; go version; uname -a; df -B1 / /mnt/c /mnt/d; } > "$results/environment.txt"
  runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/build.txt" 2>&1
  sha256sum "$binary" > "$results/binary.sha256"
  exit
fi
if [[ "$mode" == body-check ]]; then
  cd "$workspace/tests/restart"
  unshare --net -- runuser -u rehearsal -- env GOMAXPROCS=2 "$binary" -test.run='^TestFullStateHistoryBodyValidation$' -test.v > "$results/body-validation-verified-race.txt" 2>&1
  tail -n 10 "$results/body-validation-verified-race.txt"
  exit
fi
[[ "$mode" == measure || "$mode" == export ]]
[[ ! -e "$results/$mode.txt" ]]
[[ -f /home/rehearsal/results/backup-copy-2026-09-23/verified.txt ]]
mkdir -p /mnt/fusion-partition-history
set +e
unshare --mount --net --propagation private -- bash -c '
set -euo pipefail
mount --bind /home/rehearsal/data/efsn/chaindata /mnt/fusion-partition-history
mount -o remount,bind,ro /mnt/fusion-partition-history
findmnt -no TARGET,OPTIONS -T /mnt/fusion-partition-history
ip -brief link
cd "$1/tests/restart"
exec runuser -u rehearsal -- env GOMAXPROCS=2 FUSION_RESTART_FULL_AUDIT=1 FUSION_RESTART_CHAINDATA=/mnt/fusion-partition-history FUSION_RESTART_HOST_STORAGE=/mnt/c FUSION_RESTART_HISTORY_MODE="$4" FUSION_RESTART_HISTORY_OUTPUT="$3" "$2" -test.run="^TestExportFullStateHistory$" -test.v -test.timeout=10m
' bash "$workspace" "$binary" "$output" "$mode" > "$results/$mode.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/$mode-exit.txt"
tail -n 8 "$results/$mode.txt"
exit "$status"
