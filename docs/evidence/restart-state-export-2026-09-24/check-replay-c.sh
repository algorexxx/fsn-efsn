#!/bin/bash
set -euo pipefail
base=/home/rehearsal/results/restart-state-export-2026-09-24
results=/home/rehearsal/results/restart-replay-c-storage-2026-09-24
test "$(cat "$results/exit-code.txt")" = 0
mkdir -p /mnt/fusion-replay-c-closed /mnt/fusion-replay-c-inspection-source
mount --bind /mnt/c/Users/Peter/Documents/CODING/fsn-efsn/tmp/replay-mainnet-c /mnt/fusion-replay-c-closed
mount -o remount,bind,ro /mnt/fusion-replay-c-closed
mount --bind /home/rehearsal/data/efsn/chaindata /mnt/fusion-replay-c-inspection-source
mount -o remount,bind,ro /mnt/fusion-replay-c-inspection-source
{
    date -u +%FT%TZ
    findmnt -no TARGET,OPTIONS -T /mnt/fusion-replay-c-closed
    findmnt -no TARGET,OPTIONS -T /mnt/fusion-replay-c-inspection-source
    ip -brief link
    sha256sum "$base/replay-inspection-tests"
} > "$results/cold-head-check.txt"
cd /home/rehearsal/fsn-efsn-state-export/tests/restart
runuser -u rehearsal -- env FUSION_RESTART_CHAINDATA=/mnt/fusion-replay-c-inspection-source FUSION_RESTART_FULL_AUDIT=1 FUSION_RESTART_INSPECT_REPLAY_DIR=/mnt/fusion-replay-c-closed FUSION_RESTART_INSPECT_REPLAY_HEIGHT=2700000 GOMAXPROCS=2 "$base/replay-inspection-tests" '-test.run=^TestPreservedReplayHeadReadOnly$' -test.v -test.timeout=5m >> "$results/cold-head-check.txt" 2>&1
tail -n 6 "$results/cold-head-check.txt"
