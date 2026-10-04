#!/bin/bash
set -euo pipefail
export LC_ALL=C
previous=/home/rehearsal/results/restart-replay-3600000-2026-10-04
results=/home/rehearsal/results/restart-replay-3600000-resume-2026-10-04
target=/home/rehearsal/replay/baseline-mainnet-3600000
stop=/home/rehearsal/replay/STOP-baseline-mainnet-3600000-resume
source=/mnt/fusion-3600000-resume-source
inspection=/home/rehearsal/results/restart-state-export-2026-09-24/replay-inspection-tests
test "$(cat "$previous/exit-code.txt")" = 1
test "$(cat "$previous/stopped-cold-exit.txt")" = 0
grep -q 'closed replay matched: height=3521056 ' "$previous/stopped-cold-check.txt"
test "$(sha256sum /home/rehearsal/replay-resume-tests | cut -d ' ' -f 1)" = 004d4eeb16fc27e68564ff34d18b5bb1c48829cb692b98770fe7c52543d26c1e
test "$(sha256sum "$inspection" | cut -d ' ' -f 1)" = 4dd9b2a105c9984d0f0d8ac154582c997e5560818d365c7ce4cef803cd552778
test ! -e "$results"
test ! -e "$stop"
if pgrep -f '^/home/rehearsal/replay-resume-tests' >/dev/null; then exit 1; fi
exec 9>"$target.run.lock"
flock -n 9
python3 - <<'PY'
from pathlib import Path
import shutil
target = Path('/home/rehearsal/replay/baseline-mainnet-3600000')
assert target.is_dir() and not target.is_symlink() and target.resolve() == target
assert shutil.disk_usage(target).free > 30 * 1024**3
assert shutil.disk_usage('/mnt/d').free > 60 * 1024**3
PY
mkdir "$results"
mkdir -p "$source"
mount --bind /home/rehearsal/data/efsn/chaindata "$source"
mount -o remount,bind,ro "$source"
findmnt -no OPTIONS -T "$source" | grep -Eq '(^|,)ro(,|$)'
{
    date -u +%FT%TZ
    findmnt -no TARGET,FSTYPE,OPTIONS -T "$source"
    findmnt -no TARGET,FSTYPE,OPTIONS -T "$target"
    ip -brief link
    sha256sum /home/rehearsal/replay-resume-tests "$inspection" "$target/replay-identity.json"
} > "$results/isolation.txt"
df -B1 --output=source,size,used,avail / /mnt/c /mnt/d > "$results/capacity-before.txt"
cd /home/rehearsal/fsn-efsn-state-export/tests/restart
runuser -u rehearsal -- env FUSION_RESTART_CHAINDATA="$source" FUSION_RESTART_FULL_AUDIT=1 FUSION_RESTART_INSPECT_REPLAY_DIR="$target" FUSION_RESTART_INSPECT_REPLAY_HEIGHT=3521056 GOMAXPROCS=2 "$inspection" '-test.run=^TestPreservedReplayHeadReadOnly$' -test.v -test.timeout=5m > "$results/checkpoint-cold-check.txt" 2>&1
date -u +%FT%TZ > "$results/started.txt"
cd /home/rehearsal/fsn-efsn/tests/restart
runuser -u rehearsal -- env FUSION_RESTART_CHAINDATA="$source" FUSION_RESTART_FULL_AUDIT=1 FUSION_RESTART_REPLAY_DIR="$target" FUSION_RESTART_REPLAY_RESUME=1 FUSION_RESTART_REPLAY_END=3600000 FUSION_RESTART_REPLAY_STOP_FILE="$stop" FUSION_RESTART_HOST_STORAGE=/mnt/d GOMAXPROCS=2 /home/rehearsal/replay-resume-tests '-test.run=^TestPreservedHistoryReplay$' -test.v -test.timeout=12h > "$results/replay.txt" 2>&1 &
replay_pid=$!
trap 'if kill -0 "$replay_pid" 2>/dev/null; then printf "Runner interrupted; requesting clean stop\n" > "$stop"; wait "$replay_pid" || true; fi' EXIT
printf '%s\n' "$replay_pid" > "$results/pid.txt"
while kill -0 "$replay_pid" 2>/dev/null; do
    measured=0
    for attempt in 1 2 3; do
        if usage=$(timeout --kill-after=2s 15s du -sB1 "$target" 2>> "$results/size-monitor-errors.txt"); then
            measured=1
            break
        fi
        printf '%s attempt=%s measurement failed; bounded retry\n' "$(date -u +%FT%TZ)" "$attempt" >> "$results/size-monitor-errors.txt"
        sleep 1
    done
    if [ "$measured" = 0 ]; then
        printf 'Size monitor failed all three attempts; requesting clean stop\n' > "$stop"
    else
        size=$(printf '%s\n' "$usage" | cut -f 1)
        if [[ ! "$size" =~ ^[0-9]+$ ]]; then
            printf 'Invalid size measurement; requesting clean stop\n' > "$stop"
        else
            printf '%s %s\n' "$(date -u +%FT%TZ)" "$size" >> "$results/allocated-size-progress.txt"
            if [ "$size" -ge 21474836480 ]; then
                printf '20 GiB target allowance reached; requesting clean stop\n' > "$stop"
            fi
        fi
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
closed=/mnt/fusion-3600000-resume-closed
mkdir -p "$closed"
mount --bind "$target" "$closed"
mount -o remount,bind,ro "$closed"
cd /home/rehearsal/fsn-efsn-state-export/tests/restart
runuser -u rehearsal -- env FUSION_RESTART_CHAINDATA="$source" FUSION_RESTART_FULL_AUDIT=1 FUSION_RESTART_INSPECT_REPLAY_DIR="$closed" FUSION_RESTART_INSPECT_REPLAY_HEIGHT=3600000 GOMAXPROCS=2 "$inspection" '-test.run=^TestPreservedReplayHeadReadOnly$' -test.v -test.timeout=5m > "$results/final-cold-check.txt" 2>&1
date -u +%FT%TZ > "$results/verified.txt"
tail -n 6 "$results/final-cold-check.txt"
