#!/bin/bash
set -euo pipefail
results=/home/rehearsal/results/restart-node-rehearsal-2026-09-24/final-lifecycle
test "$(cat "$results/full-exit-code.txt")" = 0
test ! -e "$results/repeated-completion.txt"
cd /home/rehearsal/fsn-efsn-node-rehearsal/tests/restart
set +e
unshare --net -- bash -c 'set -e; ip link set lo up; ip -brief link; exec runuser -u rehearsal -- env FUSION_RESTART_NODE_REHEARSAL=1 GOMAXPROCS=2 "$1" "-test.run=^Test(RestartNodeRehearsal|AutoBuyRuntime)$" -test.v -test.count=2 -test.timeout=6m' bash "$results/node-tests" > "$results/repeated-completion.txt" 2>&1
code=$?
printf '%s\n' "$code" > "$results/repeated-exit-code.txt"
date -u +%FT%TZ > "$results/repeated-finished.txt"
tail -n 7 "$results/repeated-completion.txt"
exit "$code"
