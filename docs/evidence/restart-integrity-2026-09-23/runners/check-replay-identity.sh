set -euo pipefail
mountpoint=/mnt/fusion-replay-identity
target=/home/rehearsal/replay/resume-validation
results=/home/rehearsal/results/restart-resume-2026-09-23
mkdir -p "$mountpoint"
mount --bind /home/rehearsal/data/efsn/chaindata "$mountpoint"
mount -o remount,bind,ro "$mountpoint"
findmnt -no OPTIONS -T "$mountpoint" | grep -Eq '(^|,)ro(,|$)'
cp "$target/replay-identity.json" "$results/original-identity.json"
trap 'cp "$results/original-identity.json" "$target/replay-identity.json"; chown rehearsal:rehearsal "$target/replay-identity.json"' EXIT
python3 - <<'PY'
import json
from pathlib import Path
path = Path('/home/rehearsal/replay/resume-validation/replay-identity.json')
identity = json.loads(path.read_text(encoding='utf-8'))
identity['ExecutableHash'] = 'deliberately-different-replay-build'
path.write_text(json.dumps(identity) + '\n', encoding='utf-8')
PY
cd /home/rehearsal/fsn-efsn/tests/restart
set +e
runuser -u rehearsal -- env FUSION_RESTART_CHAINDATA="$mountpoint" FUSION_RESTART_FULL_AUDIT=1 FUSION_RESTART_REPLAY_DIR="$target" FUSION_RESTART_REPLAY_END=10001 FUSION_RESTART_REPLAY_RESUME=1 FUSION_RESTART_HOST_STORAGE=/mnt/d GOMAXPROCS=2 /home/rehearsal/replay-resume-tests '-test.run=^TestPreservedHistoryReplay$' -test.v -test.timeout=10m > "$results/identity-mismatch.txt" 2>&1
result=$?
set -e
printf '%s\n' "$result" > "$results/identity-mismatch-exit-code.txt"
test "$result" -ne 0
grep -q 'resume identity differs' "$results/identity-mismatch.txt"
tail -n 5 "$results/identity-mismatch.txt"
