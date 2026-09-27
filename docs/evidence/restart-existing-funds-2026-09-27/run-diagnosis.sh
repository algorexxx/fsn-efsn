#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-existing-funds-2026-09-27"
binary="$workspace/tmp/existing-funds-2026-09-27/tests-diagnosis"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
cd "$workspace"
[[ ! -e "$binary" && ! -e "$results/diagnosis-race.txt" ]]
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/diagnosis-build.txt" 2>&1
sha256sum "$binary" > "$results/diagnosis-binary.sha256"
set +e
unshare --net -- bash -c 'set -e; ip -brief link; cd "$1/tests/restart"; exec env GOMAXPROCS=2 FUSION_RESTART_CHAINDATA= FUSION_RESTART_HOST_STORAGE=/mnt/c FUSION_RESTART_FUNDING_DIAGNOSIS="$1/tmp/full-state-existing-funds-2026-09-27" "$2" -test.run="^TestFullStateFundingColdDiagnosis$" -test.v -test.timeout=5m' bash "$workspace" "$binary" > "$results/diagnosis-race.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/diagnosis-exit.txt"
tail -n 12 "$results/diagnosis-race.txt"
exit "$status"
