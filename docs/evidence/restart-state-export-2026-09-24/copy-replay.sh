#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
test -f /home/rehearsal/results/restart-replay-checkpoint-boundary-2026-09-24/finished.txt
if pgrep -f '^/home/rehearsal/replay-resume-tests' >/dev/null; then exit 1; fi
mkdir -p /mnt/fusion-replay-copy-source
mount --bind /home/rehearsal/replay/baseline-mainnet /mnt/fusion-replay-copy-source
mount -o remount,bind,ro /mnt/fusion-replay-copy-source
python3 "$workspace/docs/evidence/restart-state-export-2026-09-24/copy-replay.py"
