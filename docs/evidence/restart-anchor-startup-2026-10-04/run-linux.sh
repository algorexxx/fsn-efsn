#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-anchor-startup-2026-10-04"
attempt="${1:?explicit attempt name required}"
test_run="${2:-^TestRestartAnchorStartupCost$}"
[[ "$attempt" =~ ^attempt-[1-9][0-9]*$ ]]
results="$evidence/$attempt"
[[ ! -e "$results" ]]
mkdir "$results"
cp "$evidence/run-linux.sh" "$results/run-linux.sh"
cp "$workspace/tests/restart/anchor_startup_test.go" "$results/anchor_startup_test.go.txt"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
export GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp TMPDIR=/tmp
export FUSION_RESTART_ANCHOR_STARTUP=1
cd "$workspace"
df -B1 /tmp /mnt/c /mnt/d > "$results/capacity-before.txt"
ip -brief link > "$results/network.txt"
go version > "$results/toolchain.txt"
git -c safe.directory="$workspace" rev-parse HEAD > "$results/baseline.txt"
git -c safe.directory="$workspace" ls-files -z '*.go' go.mod go.sum | sort -z | xargs -0 sha256sum > "$results/tracked-sources.sha256"
sha256sum tests/restart/anchor_startup_test.go > "$results/added-test.sha256"
sha256sum docs/evidence/restart-2026-09-23/responses.json > "$results/fixture-source.sha256"
set +e
runuser -u rehearsal -- env PATH="$PATH" go test -p=2 -mod=readonly -c -o /tmp/fsn-anchor-startup-tests ./tests/restart > "$results/build.txt" 2>&1
code=$?
set -e
printf '%s\n' "$code" > "$results/build-exit.txt"
[[ "$code" == 0 ]]
sha256sum /tmp/fsn-anchor-startup-tests > "$results/binary.sha256"
cd tests/restart
set +e
runuser -u rehearsal -- /usr/bin/time -v /tmp/fsn-anchor-startup-tests "-test.run=$test_run" -test.v -test.timeout=12m > "$results/startup.txt" 2> "$results/resources.txt"
code=$?
set -e
printf '%s\n' "$code" > "$results/test-exit.txt"
df -B1 /tmp /mnt/c /mnt/d > "$results/capacity-after.txt"
tail -n 12 "$results/startup.txt"
[[ "$code" == 0 ]]
