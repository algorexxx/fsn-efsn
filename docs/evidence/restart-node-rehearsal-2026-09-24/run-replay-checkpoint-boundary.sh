set -euo pipefail
source=/home/rehearsal/data/efsn/chaindata
mountpoint=/mnt/fusion-replay-checkpoint-boundary
results=/home/rehearsal/results/restart-replay-checkpoint-boundary-2026-09-24
target=/home/rehearsal/replay/baseline-mainnet
test -f /home/rehearsal/results/backup-copy-2026-09-23/verified.txt
test "$(cat /home/rehearsal/results/restart-replay-two-million-2026-09-24/exit-code.txt)" = 0
test -f "$target/replay-identity.json"
test "$(sha256sum /home/rehearsal/replay-resume-tests | cut -d ' ' -f 1)" = 004d4eeb16fc27e68564ff34d18b5bb1c48829cb692b98770fe7c52543d26c1e
test ! -e "$results"
test ! -e /home/rehearsal/replay/STOP-baseline-mainnet
if pgrep -f '^/home/rehearsal/replay-resume-tests' >/dev/null; then
    printf 'Refusing a second replay writer\n' >&2
    exit 1
fi
exec 9>/home/rehearsal/replay/baseline-mainnet.run.lock
flock -n 9
mkdir -p "$mountpoint" "$results"
mount --bind "$source" "$mountpoint"
mount -o remount,bind,ro "$mountpoint"
findmnt -no TARGET,OPTIONS -T "$mountpoint" > "$results/isolation.txt"
findmnt -no OPTIONS -T "$mountpoint" | grep -Eq '(^|,)ro(,|$)'
ip -brief link >> "$results/isolation.txt"
sha256sum /home/rehearsal/replay-resume-tests >> "$results/isolation.txt"
df -B1 --output=source,size,used,avail / /mnt/d > "$results/capacity-before.txt"
date --utc --iso-8601=seconds | tee "$results/started.txt"
cd /home/rehearsal/fsn-efsn/tests/restart
set +e
runuser -u rehearsal -- env FUSION_RESTART_CHAINDATA="$mountpoint" FUSION_RESTART_FULL_AUDIT=1 FUSION_RESTART_REPLAY_DIR="$target" FUSION_RESTART_REPLAY_RESUME=1 FUSION_RESTART_REPLAY_END=2700000 FUSION_RESTART_REPLAY_STOP_FILE=/home/rehearsal/replay/STOP-baseline-mainnet FUSION_RESTART_HOST_STORAGE=/mnt/d GOMAXPROCS=2 /home/rehearsal/replay-resume-tests '-test.run=^TestPreservedHistoryReplay$' -test.v -test.timeout=12h > "$results/replay.txt" 2>&1
result=$?
printf '%s\n' "$result" > "$results/exit-code.txt"
date --utc --iso-8601=seconds | tee "$results/finished.txt"
du -sb "$target" > "$results/size.txt"
df -B1 --output=source,size,used,avail / /mnt/d > "$results/capacity-after.txt"
tail -n 10 "$results/replay.txt"
exit "$result"
