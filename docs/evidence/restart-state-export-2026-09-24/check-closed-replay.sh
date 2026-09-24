#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
source=/home/rehearsal/fsn-efsn-state-export
results=/home/rehearsal/results/restart-state-export-2026-09-24
test -f /home/rehearsal/results/restart-replay-checkpoint-boundary-2026-09-24/finished.txt
cp "$workspace/tests/restart/replay_inspection_linux_test.go" "$source/tests/restart/replay_inspection_linux_test.go"
chown rehearsal:rehearsal "$source/tests/restart/replay_inspection_linux_test.go"
cd "$source"
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 go test -p=2 -mod=readonly -c -o "$results/replay-inspection-tests" ./tests/restart > "$results/build-replay-inspection.txt" 2>&1
sha256sum "$results/replay-inspection-tests" tests/restart/replay_inspection_linux_test.go > "$results/replay-inspection-identity.txt"
unshare --mount --net --propagation private -- bash -c '
set -euo pipefail
mkdir -p /mnt/fusion-closed-replay /mnt/fusion-closed-replay-source
mount --bind /home/rehearsal/replay/baseline-mainnet /mnt/fusion-closed-replay
mount -o remount,bind,ro /mnt/fusion-closed-replay
mount --bind /home/rehearsal/data/efsn/chaindata /mnt/fusion-closed-replay-source
mount -o remount,bind,ro /mnt/fusion-closed-replay-source
findmnt -no TARGET,OPTIONS -T /mnt/fusion-closed-replay
findmnt -no TARGET,OPTIONS -T /mnt/fusion-closed-replay-source
ip -brief link
cd /home/rehearsal/fsn-efsn-state-export/tests/restart
exec runuser -u rehearsal -- env FUSION_RESTART_CHAINDATA=/mnt/fusion-closed-replay-source FUSION_RESTART_FULL_AUDIT=1 FUSION_RESTART_INSPECT_REPLAY_DIR=/mnt/fusion-closed-replay FUSION_RESTART_INSPECT_REPLAY_HEIGHT=2613376 GOMAXPROCS=2 /home/rehearsal/results/restart-state-export-2026-09-24/replay-inspection-tests -test.run=^TestPreservedReplayHeadReadOnly$ -test.v -test.timeout=5m
' > "$results/replay-cold-check.txt" 2>&1
tail -n 9 "$results/replay-cold-check.txt"
