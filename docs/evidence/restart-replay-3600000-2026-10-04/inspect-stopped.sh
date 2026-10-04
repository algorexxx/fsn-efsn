#!/bin/bash
set -euo pipefail
results=/home/rehearsal/results/restart-replay-3600000-2026-10-04
inspection=/home/rehearsal/results/restart-state-export-2026-09-24/replay-inspection-tests
source=/mnt/fusion-3600000-stopped-source
closed=/mnt/fusion-3600000-stopped-closed
test "$(cat "$results/exit-code.txt")" = 1
test ! -e "$results/stopped-cold-check.txt"
test "$(sha256sum "$inspection" | cut -d ' ' -f 1)" = 4dd9b2a105c9984d0f0d8ac154582c997e5560818d365c7ce4cef803cd552778
if pgrep -f '^/home/rehearsal/replay-resume-tests' >/dev/null; then exit 1; fi
exec 9>/home/rehearsal/replay/baseline-mainnet-3600000.run.lock
flock -n 9
mkdir -p "$source" "$closed"
mount --bind /home/rehearsal/data/efsn/chaindata "$source"
mount -o remount,bind,ro "$source"
mount --bind /home/rehearsal/replay/baseline-mainnet-3600000 "$closed"
mount -o remount,bind,ro "$closed"
findmnt -no OPTIONS -T "$source" | grep -Eq '(^|,)ro(,|$)'
findmnt -no OPTIONS -T "$closed" | grep -Eq '(^|,)ro(,|$)'
{
    date -u +%FT%TZ
    findmnt -no TARGET,FSTYPE,OPTIONS -T "$source"
    findmnt -no TARGET,FSTYPE,OPTIONS -T "$closed"
    ip -brief link
} > "$results/stopped-isolation.txt"
cd /home/rehearsal/fsn-efsn-state-export/tests/restart
set +e
runuser -u rehearsal -- env FUSION_RESTART_CHAINDATA="$source" FUSION_RESTART_FULL_AUDIT=1 FUSION_RESTART_INSPECT_REPLAY_DIR="$closed" FUSION_RESTART_INSPECT_REPLAY_HEIGHT=3521056 GOMAXPROCS=2 "$inspection" '-test.run=^TestPreservedReplayHeadReadOnly$' -test.v -test.timeout=5m > "$results/stopped-cold-check.txt" 2>&1
code=$?
set -e
printf '%s\n' "$code" > "$results/stopped-cold-exit.txt"
du -sB1 "$closed" > "$results/stopped-allocated-size.txt"
tail -n 8 "$results/stopped-cold-check.txt"
exit "$code"
