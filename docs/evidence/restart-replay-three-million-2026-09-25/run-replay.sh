#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
scripts="$workspace/docs/evidence/restart-replay-three-million-2026-09-25"
results=/home/rehearsal/results/restart-replay-three-million-2026-09-25
target=/home/rehearsal/replay/baseline-mainnet-three-million
stop=/home/rehearsal/replay/STOP-baseline-mainnet-three-million
source=/mnt/fusion-three-million-source
checkpoint=/mnt/fusion-three-million-checkpoint
inspection=/home/rehearsal/results/restart-state-export-2026-09-24/replay-inspection-tests
test -f /home/rehearsal/results/backup-copy-2026-09-23/verified.txt
test "$(cat /home/rehearsal/results/restart-replay-c-storage-2026-09-24/exit-code.txt)" = 0
test "$(sha256sum /home/rehearsal/replay-resume-tests | cut -d ' ' -f 1)" = 004d4eeb16fc27e68564ff34d18b5bb1c48829cb692b98770fe7c52543d26c1e
test "$(sha256sum "$inspection" | cut -d ' ' -f 1)" = 4dd9b2a105c9984d0f0d8ac154582c997e5560818d365c7ce4cef803cd552778
test ! -e "$target"
test ! -e "$results"
test ! -e "$stop"
if pgrep -f '^/home/rehearsal/replay-resume-tests' >/dev/null; then exit 1; fi
exec 8>"$workspace/tmp/replay-mainnet-c.run.lock"
flock -n 8
exec 9>"$target.run.lock"
flock -n 9
mkdir -p "$source" "$checkpoint"
mount --bind /home/rehearsal/data/efsn/chaindata "$source"
mount -o remount,bind,ro "$source"
mount --bind "$workspace/tmp/replay-mainnet-c" "$checkpoint"
mount -o remount,bind,ro "$checkpoint"
findmnt -no OPTIONS -T "$source" | grep -Eq '(^|,)ro(,|$)'
findmnt -no OPTIONS -T "$checkpoint" | grep -Eq '(^|,)ro(,|$)'
runuser -u rehearsal -- python3 "$scripts/copy-checkpoint.py"
{
    date -u +%FT%TZ
    findmnt -no TARGET,FSTYPE,OPTIONS -T "$source"
    findmnt -no TARGET,FSTYPE,OPTIONS -T "$checkpoint"
    findmnt -no TARGET,FSTYPE,OPTIONS -T "$target"
    ip -brief link
    sha256sum /home/rehearsal/replay-resume-tests "$inspection" "$target/replay-identity.json"
} > "$results/isolation.txt"
df -B1 --output=source,size,used,avail / /mnt/c /mnt/d > "$results/capacity-before.txt"
cd /home/rehearsal/fsn-efsn-state-export/tests/restart
runuser -u rehearsal -- env FUSION_RESTART_CHAINDATA="$source" FUSION_RESTART_FULL_AUDIT=1 FUSION_RESTART_INSPECT_REPLAY_DIR="$checkpoint" FUSION_RESTART_INSPECT_REPLAY_HEIGHT=2700000 GOMAXPROCS=2 "$inspection" '-test.run=^TestPreservedReplayHeadReadOnly$' -test.v -test.timeout=5m > "$results/checkpoint-cold-check.txt" 2>&1
date -u +%FT%TZ > "$results/started.txt"
cd /home/rehearsal/fsn-efsn/tests/restart
runuser -u rehearsal -- env FUSION_RESTART_CHAINDATA="$source" FUSION_RESTART_FULL_AUDIT=1 FUSION_RESTART_REPLAY_DIR="$target" FUSION_RESTART_REPLAY_RESUME=1 FUSION_RESTART_REPLAY_END=3000000 FUSION_RESTART_REPLAY_STOP_FILE="$stop" FUSION_RESTART_HOST_STORAGE=/mnt/d GOMAXPROCS=2 /home/rehearsal/replay-resume-tests '-test.run=^TestPreservedHistoryReplay$' -test.v -test.timeout=12h > "$results/replay.txt" 2>&1 &
replay_pid=$!
trap 'if kill -0 "$replay_pid" 2>/dev/null; then printf "Runner interrupted; requesting clean stop\n" > "$stop"; wait "$replay_pid" || true; fi' EXIT
printf '%s\n' "$replay_pid" > "$results/pid.txt"
while kill -0 "$replay_pid" 2>/dev/null; do
    if ! usage=$(du -sB1 "$target" 2>> "$results/size-monitor-errors.txt"); then
        printf 'Size monitor could not inspect every file; requesting clean stop\n' > "$stop"
    fi
    size=$(printf '%s\n' "$usage" | cut -f 1)
    printf '%s %s\n' "$(date -u +%FT%TZ)" "$size" >> "$results/allocated-size-progress.txt"
    if [ "$size" -ge 21474836480 ]; then
        printf '20 GiB target allowance reached; requesting clean stop\n' > "$stop"
    fi
    sleep 30
done
set +e
wait "$replay_pid"
code=$?
set -e
printf '%s\n' "$code" > "$results/exit-code.txt"
date -u +%FT%TZ > "$results/finished.txt"
du -sb "$target" > "$results/size.txt"
du -sB1 "$target" > "$results/allocated-size.txt"
df -B1 --output=source,size,used,avail / /mnt/c /mnt/d > "$results/capacity-after.txt"
tail -n 10 "$results/replay.txt"
if [ "$code" != 0 ]; then exit "$code"; fi
closed=/mnt/fusion-three-million-closed
mkdir -p "$closed"
mount --bind "$target" "$closed"
mount -o remount,bind,ro "$closed"
cd /home/rehearsal/fsn-efsn-state-export/tests/restart
runuser -u rehearsal -- env FUSION_RESTART_CHAINDATA="$source" FUSION_RESTART_FULL_AUDIT=1 FUSION_RESTART_INSPECT_REPLAY_DIR="$closed" FUSION_RESTART_INSPECT_REPLAY_HEIGHT=3000000 GOMAXPROCS=2 "$inspection" '-test.run=^TestPreservedReplayHeadReadOnly$' -test.v -test.timeout=5m > "$results/final-cold-check.txt" 2>&1
date -u +%FT%TZ > "$results/verified.txt"
tail -n 6 "$results/final-cold-check.txt"
